import cv2
import numpy as np
from ultralytics import YOLO
from pathlib import Path
import time
from itertools import combinations


# =========================================================
# 1. LOAD MODELS
# =========================================================
MOTOR_MODEL = YOLO("yolo11s.pt")
HELMET_MODEL = YOLO(
    r"C:\Users\Lenovo\Desktop\traffic_base_project\runs\helmet_detection2\v1\weights\best.pt"
)


# =========================================================
# Triple Riding Check
# =========================================================
def are_three_riders_present(head_boxes, motor_box):
    """
    Detects triple riding by checking if 3 or more heads/helmets are present
    within or near the motorcycle bounding box.

    It supports:
    - front-to-back rider layout,
    - side-by-side layout,
    - diagonal layout.
    """

    if len(head_boxes) < 3:
        return False

    x1m, y1m, x2m, y2m = motor_box
    motor_w = x2m - x1m
    motor_h = y2m - y1m

    valid_boxes = []

    for box in head_boxes:
        bx1, by1, bx2, by2 = box
        bw = bx2 - bx1
        bh = by2 - by1

        if bw <= 0 or bh <= 0:
            continue

        # Too narrow: mirror, pole, cargo, or noise.
        if bw < motor_w * 0.08:
            continue

        # Too wide: probably not a single head.
        if bw > motor_w * 0.7:
            continue

        cx = (bx1 + bx2) / 2
        cy = (by1 + by2) / 2

        margin_x = motor_w * 0.3
        margin_y = motor_h * 0.4

        if not (x1m - margin_x <= cx <= x2m + margin_x):
            continue

        if not (y1m - margin_y <= cy <= y2m + margin_y):
            continue

        valid_boxes.append((bx1, by1, bx2, by2))

    if len(valid_boxes) < 3:
        return False

    # Check every group of three valid head boxes.
    for group in combinations(valid_boxes, 3):
        centers = [
            ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
            for b in group
        ]

        widths = [
            b[2] - b[0]
            for b in group
        ]

        heights = [
            b[3] - b[1]
            for b in group
        ]

        avg_w = sum(widths) / len(widths)
        avg_h = sum(heights) / len(heights)

        x_vals = [c[0] for c in centers]
        y_vals = [c[1] for c in centers]

        x_spread = max(x_vals) - min(x_vals)
        y_spread = max(y_vals) - min(y_vals)

        # Reject duplicate detections almost on top of each other.
        if x_spread < avg_w * 0.3 and y_spread < avg_h * 0.3:
            continue

        # Front-to-back layout.
        front_to_back = (
            y_spread > avg_h * 0.8
            and x_spread < avg_w * 3.5
        )

        # Side-by-side layout.
        side_by_side = (
            x_spread > avg_w * 1.5
            and y_spread < avg_h * 0.9
        )

        # Diagonal layout.
        diagonal = (
            x_spread > avg_w * 0.5
            and y_spread > avg_h * 0.5
            and x_spread < motor_w * 0.85
            and y_spread < motor_h * 0.85
        )

        if front_to_back or side_by_side or diagonal:
            return True

    return False


# =========================================================
# Main Stabilized Video Pipeline
# =========================================================
def run_stabilized_pipeline(video_in, video_out):
    start_time = time.time()

    track_history = {}
    all_confidences = []

    total_stable_violations = 0
    total_triple_riding = 0

    cap = cv2.VideoCapture(video_in)

    if not cap.isOpened():
        raise ValueError(f"Video could not be opened: {video_in}")

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))

    if fps == 0:
        fps = 25

    Path(video_out).parent.mkdir(parents=True, exist_ok=True)

    fourcc = cv2.VideoWriter_fourcc(*"avc1")
    writer = cv2.VideoWriter(video_out, fourcc, fps, (w, h))

    if not writer.isOpened():
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(video_out, fourcc, fps, (w, h))

    print(f"Starting High-Precision Processing: {video_in}")

    while cap.isOpened():
        success, frame = cap.read()

        if not success:
            break

        # =================================================
        # 1. Track Motorcycles
        # =================================================
        results = MOTOR_MODEL.track(
            frame,
            classes=[3],
            conf=0.45,
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

                # Ignore very small / far motorcycles.
                if mh < (h * 0.15):
                    continue

                bikes_in_frame += 1

                # =================================================
                # Initialize Track Memory
                # =================================================
                if track_id not in track_history:
                    track_history[track_id] = {
                        "frames_seen": 0,
                        "helmet_hits": 0,
                        "no_helmet_hits": 0,
                        "triple_hits": 0,
                        "is_logged": False,
                        "triple_logged": False,
                        "status": "ANALYZING",
                        "triple_riding": False
                    }

                track_history[track_id]["frames_seen"] += 1

                # =================================================
                # 2. Head ROI
                # =================================================
                roi_y1 = max(0, y1 - int(mh * 0.55))
                roi_y2 = min(h, y1 + int(mh * 0.25))

                pad = int(mw * 0.2) if mw > mh else 0

                roi_x1 = max(0, x1 - pad)
                roi_x2 = min(w, x2 + pad)

                head_roi = frame[roi_y1:roi_y2, roi_x1:roi_x2]

                head_boxes_only = []
                head_boxes_for_drawing = []

                # =================================================
                # 3. Helmet / Head Detection inside ROI
                # =================================================
                if head_roi.size > 0:
                    h_results = HELMET_MODEL.predict(
                        head_roi,
                        conf=0.45,
                        imgsz=960,
                        verbose=False
                    )[0]

                    frame_has_helmet = False
                    frame_has_no_helmet = False

                    for hb in h_results.boxes:
                        label = HELMET_MODEL.names[int(hb.cls[0])].lower()
                        conf_val = float(hb.conf[0])
                        all_confidences.append(conf_val)

                        hx1, hy1, hx2, hy2 = map(int, hb.xyxy[0])

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
                            frame_has_no_helmet = True
                            head_boxes_for_drawing.append((abs_h_box, (0, 0, 255)))

                    if frame_has_helmet:
                        track_history[track_id]["helmet_hits"] += 1

                    if frame_has_no_helmet:
                        track_history[track_id]["no_helmet_hits"] += 1

                    # =================================================
                    # Triple Riding Check
                    # =================================================
                    motor_box = (x1, y1, x2, y2)

                    if are_three_riders_present(head_boxes_only, motor_box):
                        track_history[track_id]["triple_hits"] += 1

                # =================================================
                # 4. Stable Decision Logic
                # =================================================
                if track_history[track_id]["frames_seen"] > 15:
                    frames_seen = track_history[track_id]["frames_seen"]

                    helmet_ratio = (
                        track_history[track_id]["helmet_hits"] / frames_seen
                    )

                    no_helmet_ratio = (
                        track_history[track_id]["no_helmet_hits"] / frames_seen
                    )

                    # If more than 20% of the frames show a helmet, consider it safe.
                    if helmet_ratio > 0.20:
                        track_history[track_id]["status"] = "SAFE"
                    
                    # If more than 15% of the frames show no helmet, consider it a violation.
                    elif no_helmet_ratio > 0.15:
                        track_history[track_id]["status"] = "VIOLATION"

                        if not track_history[track_id]["is_logged"]:
                            total_stable_violations += 1
                            track_history[track_id]["is_logged"] = True

                    # If it's still early or mixed, keep analyzing.
                    else:
                        if track_history[track_id]["status"] == "ANALYZING":
                            track_history[track_id]["status"] = "ANALYZING"
                    
                    # Triple riding becomes stable after several positive frames.
                    if track_history[track_id]["triple_hits"] > 5:
                        track_history[track_id]["triple_riding"] = True

                        if not track_history[track_id]["triple_logged"]:
                            total_triple_riding += 1
                            track_history[track_id]["triple_logged"] = True

                # =================================================
                # 5. Drawing
                # =================================================
                status = track_history[track_id]["status"]

                if track_history[track_id]["triple_riding"] and status == "VIOLATION":
                    display_status = "TRIPLE + NO HELMET"
                
                elif track_history[track_id]["triple_riding"]:
                    display_status = "TRIPLE RIDING"
                else:
                    display_status = status

                if display_status == "SAFE":
                    color = (0, 255, 0)
                elif display_status == "ANALYZING":
                    color = (0, 255, 255)
                else:
                    color = (0, 0, 255)

                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

                cv2.putText(
                    frame,
                    f"ID:{track_id} {display_status}",
                    (x1, max(20, y1 - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    color,
                    2
                )

                for h_box, h_color in head_boxes_for_drawing:
                    cv2.rectangle(
                        frame,
                        (h_box[0], h_box[1]),
                        (h_box[2], h_box[3]),
                        h_color,
                        1
                    )

                if track_history[track_id]["triple_riding"]:
                    cv2.putText(
                        frame,
                        "TRIPLE RIDING DETECTED",
                        (x1, min(h - 10, y2 + 25)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.55,
                        (0, 0, 255),
                        2
                    )

        # =================================================
        # 6. Dashboard UI
        # =================================================
        cv2.rectangle(frame, (0, 0), (w, 60), (20, 20, 20), -1)

        dashboard_text = (
            f"AI SAFETY LAB | "
            f"BIKES: {bikes_in_frame} | "
            f"VIOLATIONS: {total_stable_violations} | "
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

    # =================================================
    # Final Metric Calculation
    # =================================================
    end_time = time.time()
    duration = int((end_time - start_time) * 1000)

    avg_conf = int(np.mean(all_confidences) * 100) if all_confidences else 0

    stable_tracks = [
        t for t in track_history.values()
        if t["frames_seen"] > 30
    ]

    stable_helmets = [
        t for t in stable_tracks
        if t["status"] == "SAFE"
    ]

    stable_triple_riding = [
        t for t in stable_tracks
        if t["triple_riding"]
    ]

    return {
        "motorcycles": len(stable_tracks),
        "helmets": len(stable_helmets),
        "violations": total_stable_violations,

        "triple_riding": len(stable_triple_riding),
        "triple_riding_detected": len(stable_triple_riding) > 0,
        "checks": len(stable_triple_riding),

        "popup_message": (
            "Triple riding detected!"
            if len(stable_triple_riding) > 0
            else ""
        ),

        "resolution": f"{w}x{h}",
        "processing_time": duration,
        "avg_confidence": avg_conf
    }