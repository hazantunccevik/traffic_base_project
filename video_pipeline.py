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


# =========================================================
# Triple Riding Geometry Check
# =========================================================
def are_three_heads_side_by_side(head_boxes):
    """
    Checks whether at least three detected head/helmet boxes are side by side.

    This function is used frame-by-frame in the video pipeline.
    The result is then stabilized using triple_hits / frames_seen.

    head_boxes format:
    [
        (x1, y1, x2, y2),
        (x1, y1, x2, y2),
        ...
    ]
    """

    if len(head_boxes) < 3:
        return False

    # Sort boxes from left to right.
    boxes = sorted(head_boxes, key=lambda b: (b[0] + b[2]) / 2)

    for i in range(len(boxes) - 2):
        group = boxes[i:i + 3]

        centers = []
        widths = []
        heights = []

        for box in group:
            x1, y1, x2, y2 = box

            box_w = x2 - x1
            box_h = y2 - y1

            if box_w <= 0 or box_h <= 0:
                continue

            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2

            centers.append((center_x, center_y))
            widths.append(box_w)
            heights.append(box_h)

        if len(centers) < 3:
            continue

        avg_width = sum(widths) / len(widths)
        avg_height = sum(heights) / len(heights)

        x_values = [c[0] for c in centers]
        y_values = [c[1] for c in centers]

        # Three heads should be approximately aligned vertically.
        max_y_diff = max(y_values) - min(y_values)
        same_horizontal_level = max_y_diff < avg_height * 0.8

        gap_1 = x_values[1] - x_values[0]
        gap_2 = x_values[2] - x_values[1]

        # Heads should be close enough to belong to the same motorcycle.
        close_enough = (
            gap_1 < avg_width * 3.5
            and gap_2 < avg_width * 3.5
        )

        # Prevent duplicate overlapping detections from being counted as riders.
        separated = (
            gap_1 > avg_width * 0.3
            and gap_2 > avg_width * 0.3
        )

        if same_horizontal_level and close_enough and separated:
            return True

    return False

# =========================================================
# Stabilized Video Pipeline
# =========================================================
"""
    Processes video with tracking and voting.

    Added features:
    - Tracks each motorcycle using ByteTrack.
    - Keeps helmet_hits for stable helmet violation decision.
    - Keeps triple_hits for stable triple riding decision.
    - Returns triple_riding_detected for frontend popup usage.
    """
def run_stabilized_pipeline(video_in, video_out):
    start_time = time.time()
    
    # Initialize internal memory for this specific run
    track_history = {}
    
    total_stable_violations = 0
    total_triple_riding = 0

    all_confidences = []

    cap = cv2.VideoCapture(video_in)

    if not cap.isOpened():
        raise ValueError(f"Video could not be opened: {video_in}")

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    if fps == 0: 
        fps = 25
    
    # Make sure output folder exists before creating writer.
    Path(video_out).parent.mkdir(parents=True, exist_ok=True)

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


        # =================================================
        # Motorcycle Tracking
        # =================================================
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
                
                mw = x2 - x1
                mh = y2 - y1

                # Distance Filter: Ignore very small / far bikes
                if mh < (h * 0.08): continue 
                
                bikes_in_frame += 1

                # =================================================
                # Initialize Track Memory
                # =================================================
                if track_id not in track_history:
                    track_history[track_id] = {
                        "frames_seen": 0, 
                        "helmet_hits": 0,  # Helmet voting memory
                        "triple_hits": 0,  # Triple riding voting memory
                        "is_logged": False,  # Logging flags prevent double counting.
                        "triple_logged": False,
                        "status": "ANALYZING",
                        "triple_riding": False # Final triple riding decision for this track
                    }

                track_history[track_id]["frames_seen"] += 1

                # =================================================
                # Head ROI for this tracked motorcycle
                # =================================================
                roi_x1 = max(0, x1 - int(mw * 0.25))
                roi_x2 = min(w, x2 + int(mw * 0.25))

                roi_y1 = max(0, y1 - int(mh * 0.55))
                roi_y2 = min(h, y1 + int(mh * 0.25))

                head_roi = frame[roi_y1:roi_y2, roi_x1:roi_x2]

                head_boxes_only = []
                head_boxes_for_drawing = []

                # =================================================
                # Helmet / Head Detection inside ROI
                # =================================================
                if head_roi.size > 0:
                    h_results = HELMET_MODEL.predict(
                        head_roi, conf=0.2, imgsz=960, verbose=False
                    )[0]

                    frame_has_helmet = False
                    
                    for hb in h_results.boxes:
                        label = HELMET_MODEL.names[int(hb.cls[0])].lower()
                        
                        # Capture the confidence of this specific detection
                        conf_val = float(hb.conf[0])
                        all_confidences.append(conf_val)
                        
                        hx1, hy1, hx2, hy2 = map(int, hb.xyxy[0])

                        # Convert ROI-local helmet box to full-frame coordinates.
                        abs_h_box = (
                            roi_x1 + hx1,
                            roi_y1 + hy1,
                            roi_x1 + hx2,
                            roi_y1 + hy2
                        )

                        head_boxes_only.append(abs_h_box)

                        if "helmet" in label and "no" not in label:
                            frame_has_helmet = True
                            head_boxes_for_drawing.append((abs_h_box, (0, 255, 0)))
                        else:
                            head_boxes_for_drawing.append((abs_h_box, (0, 0, 255)))

                     # Helmet voting:
                    # If helmet is seen in this frame, increase helmet_hits.
                    if frame_has_helmet: 
                        track_history[track_id]["helmet_hits"] += 1
                    
                    # Triple riding frame-level check:
                    # If three heads are side by side in this frame, increase triple_hits.
                    if len(head_boxes_only) >= 3:
                        track_history[track_id]["triple_hits"] += 1

                # =================================================
                # Stable Decision Logic
                # =================================================
                # Wait until the object is seen enough frames.
                if track_history[track_id]["frames_seen"] > 15:
                    frames_seen = track_history[track_id]["frames_seen"]

                    helmet_ratio = (
                        track_history[track_id]["helmet_hits"] / frames_seen
                    )

                    triple_ratio = (
                        track_history[track_id]["triple_hits"] / frames_seen
                    )
                    
                    # Helmet decision:
                    # If helmet appears in enough frames, mark as SAFE.
                    # Otherwise mark as VIOLATION.
                    if helmet_ratio > 0.3:
                        track_history[track_id]["status"] = "SAFE"
                    else:
                        track_history[track_id]["status"] = "VIOLATION"

                        if not track_history[track_id]["is_logged"]:
                            total_stable_violations += 1
                            track_history[track_id]["is_logged"] = True

                    # Triple riding decision:
                    # A lower ratio is used because triple riding may not be visible
                    # clearly in every frame.
                    if track_history[track_id]["triple_hits"] >= 2:
                        track_history[track_id]["triple_riding"] = True

                        if not track_history[track_id]["triple_logged"]:
                            total_triple_riding += 1
                            track_history[track_id]["triple_logged"] = True
                   
                # =================================================
                # Drawing Status
                # =================================================
                status = track_history[track_id]["status"]

                # Triple riding has display priority because it is a separate violation.
                if track_history[track_id]["triple_riding"]:
                    status = "TRIPLE RIDING"

                if status == "SAFE":
                    color = (0, 255, 0)
                elif status == "ANALYZING":
                    color = (0, 255, 255)
                else:
                    color = (0, 0, 255)

                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

                cv2.putText(
                    frame,
                    f"ID:{track_id} {status}",
                    (x1, max(20, y1 - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    color,
                    2
                )

                # Draw helmet / no_helmet boxes.
                for h_box, h_color in head_boxes_for_drawing:
                    cv2.rectangle(
                        frame,
                        (h_box[0], h_box[1]),
                        (h_box[2], h_box[3]),
                        h_color,
                        1
                    )

                # Draw triple riding warning near the motorcycle.
                if track_history[track_id]["triple_riding"]:
                    cv2.putText(
                        frame,
                        "TRIPLE RIDING DETECTED",
                        (x1, min(h - 10, y2 + 25)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 0, 255),
                        2
                    )
         # =====================================================
        # Dashboard UI
        # =====================================================
        cv2.rectangle(frame, (0, 0), (w, 60), (20, 20, 20), -1)
        dashboard_text = (
            f"AI SAFETY LAB | "
            f"BIKES: {bikes_in_frame} | "
            f"HELMET VIOLATIONS: {total_stable_violations} | "
            f"TRIPLE RIDING: {total_triple_riding}"
        )

        cv2.putText(
            frame,
            dashboard_text,
            (30, 40),
            cv2.FONT_HERSHEY_DUPLEX,
            0.7,
            (255, 255, 255),
            1
        )

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

    stable_tracks = [
        t for t in track_history.values() 
        if t["frames_seen"] > 15
    ]

    stable_helmets = [
        t for t in stable_tracks 
        if t["status"] == "SAFE"
    ]

    return {
        "motorcycles": len(stable_tracks),
        "helmets": len(stable_helmets),
        "violations": total_stable_violations,
        "triple_riding": total_triple_riding,
        "triple_riding_detected": total_triple_riding > 0,
        "popup_message": (
            "Triple riding detected!"
            if total_triple_riding > 0
            else ""
        ),
        "resolution": f"{w}x{h}",
        "processing_time": total_duration_ms,
        "avg_confidence": avg_val 
    }