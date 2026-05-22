import datetime

import cv2
import numpy as np
from ultralytics import YOLO
from pathlib import Path
import time 

# =========================================================
# 1. LOAD MODELS
# =========================================================
MOTOR_MODEL = YOLO("yolo11s.pt")
HELMET_MODEL = YOLO(r"C:\Users\Lenovo\Desktop\traffic_base_project\runs\helmet_detection2\v1\weights\best.pt")

def run_stabilized_pipeline(video_in, video_out):
    start_time = time.time()
    # Initialize internal memory for this specific run
    track_history = {}
    total_stable_violations = 0
    all_confidences = []

    cap = cv2.VideoCapture(video_in)
    if not cap.isOpened():
        raise ValueError(f"Video could not be opened: {video_in}")

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    if fps == 0: fps = 25
    
    # Define codec: 'avc1' is H.264 (Web Standard). 
    # If the system lacks the driver, it falls back to 'mp4v'.
    fourcc = cv2.VideoWriter_fourcc(*'avc1')
    writer = cv2.VideoWriter(video_out, fourcc, fps, (w, h))

    if not writer.isOpened():
        print("Codec 'avc1' failed. Falling back to 'mp4v'...")
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(video_out, fourcc, fps, (w, h))

    Path(video_out).parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Starting processing: {video_in}")

    while cap.isOpened():
        success, frame = cap.read()
        if not success: break

        results = MOTOR_MODEL.track(
            frame, 
            classes=[3], 
            conf=0.40, 
            persist=True, 
            tracker="bytetrack.yaml", 
            iou=0.3,
            verbose=False
        )[0]

        bikes_in_frame = 0

        if results.boxes.id is not None:
            boxes = results.boxes.xyxy.cpu().numpy().astype(int)
            ids = results.boxes.id.cpu().numpy().astype(int)

            for box, track_id in zip(boxes, ids):
                x1, y1, x2, y2 = box
                mw, mh = x2 - x1, y2 - y1

                # Distance Filter: Ignore far bikes
                if mh < (h * 0.15): continue 
                
                bikes_in_frame += 1

                # FIX 1: Consistent Key Names ("frames_seen" and "is_logged")
                if track_id not in track_history:
                    track_history[track_id] = {
                        "frames_seen": 0, 
                        "helmet_hits": 0, 
                        "is_logged": False, 
                        "status": "ANALYZING"
                    }

                track_history[track_id]["frames_seen"] += 1

                # Head ROI
                roi_y1 = max(0, y1 - int(mh * 0.5))
                roi_y2 = min(h, y1 + int(mh * 0.2))
                head_roi = frame[roi_y1:roi_y2, x1:x2]

                if head_roi.size > 0:
                    h_results = HELMET_MODEL.predict(head_roi, conf=0.4, verbose=False)[0]
                    frame_has_helmet = False
                    for hb in h_results.boxes:
                        label = HELMET_MODEL.names[int(hb.cls[0])].lower()
                        # Capture the confidence of this specific detection
                        conf_val = float(hb.conf[0])
                        all_confidences.append(conf_val)
                        
                        if "helmet" in label and "no" not in label:
                            frame_has_helmet = True
                    
                    if frame_has_helmet: 
                        track_history[track_id]["helmet_hits"] += 1
                
                # Voting Logic (Wait for 15 frames)
                if track_history[track_id]["frames_seen"] > 15:
                    ratio = track_history[track_id]["helmet_hits"] / track_history[track_id]["frames_seen"]
                    if ratio > 0.3:
                        track_history[track_id]["status"] = "SAFE"
                    else:
                        track_history[track_id]["status"] = "VIOLATION"
                        if not track_history[track_id]["is_logged"]:
                            total_stable_violations += 1
                            track_history[track_id]["is_logged"] = True
                   
                # DRAWING
                status = track_history[track_id]["status"]
                color = (0, 255, 0) if status == "SAFE" else (0, 0, 255)
                if status == "ANALYZING": color = (0, 255, 255)
                
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, f"ID:{track_id} {status}", (x1, y1-10), 0, 0.6, color, 2)
                
        # DASHBOARD UI
        cv2.rectangle(frame, (0,0), (w, 60), (20,20,20), -1)
        cv2.putText(frame, f"AI SAFETY LAB | BIKES: {bikes_in_frame} | TOTAL VIOLATIONS: {total_stable_violations}", 
                    (30, 40), cv2.FONT_HERSHEY_DUPLEX, 0.7, (255,255,255), 1)

        writer.write(frame)

    cap.release()
    writer.release()
    
    end_time = time.time()
    # Calculate total time in milliseconds (ms)
    total_duration_ms = int((end_time - start_time)* 1000)

    # Calculate the average as a whole number (e.g., 88)
    if all_confidences:
        avg_val = int(np.mean(all_confidences) * 100)
    else:
        avg_val = 0 # Fallback to 0 if no detections made

    stable_tracks = [t for t in track_history.values() if t["frames_seen"] > 15]
    stable_helmets = [t for t in stable_tracks if t["status"] == "SAFE"]

    return {
        "motorcycles": len(stable_tracks),
        "helmets": len(stable_helmets),
        "violations": total_stable_violations,
        "resolution": f"{w}x{h}",
        "processing_time": total_duration_ms,
        "avg_confidence": avg_val 
    }