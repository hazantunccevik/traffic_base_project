import cv2
from ultralytics import YOLO
from pathlib import Path

# ==============================
# LOAD MODELS
# ==============================

# Main motorcycle detector
MOTOR_MODEL = YOLO("yolo11m.pt")

# Helmet / No Helmet detector
HELMET_MODEL = YOLO(
    r"C:\Users\Lenovo\Desktop\traffic_base_project\runs\helmet_detection2\v1\weights\best.pt"
)


# ==============================
# VIDEO PROCESSING FUNCTION
# ==============================

def process_video(video_path, output_path):
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise ValueError(f"Video could not be opened: {video_path}")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))

    if fps == 0:
        fps = 25

    # Setup Video Writer
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    # Prevent duplicate violation logs for the same tracked motorcycle
    logged_violations = set()

    ui_scale = max(0.5, width / 1280)

    frame_no = 0

    while cap.isOpened():
        success, frame = cap.read()

        if not success:
            break

        frame_no += 1

        # ==============================
        # 1. TRACK MOTORCYCLES
        # COCO class 3 = motorcycle
        # ==============================

        results = MOTOR_MODEL.track(
            frame,
            classes=[3],
            persist=True,
            tracker="bytetrack.yaml",
            verbose=False
        )[0]

        bike_count_in_frame = 0

        if results.boxes.id is not None:
            boxes = results.boxes.xyxy.cpu().numpy().astype(int)
            ids = results.boxes.id.cpu().numpy().astype(int)

            for box, track_id in zip(boxes, ids):
                bike_count_in_frame += 1

                x1, y1, x2, y2 = box
                mw = x2 - x1
                mh = y2 - y1

                # ==============================
                # 2. HEAD ROI CROP
                # Helmet detection only runs near rider head area
                # ==============================

                roi_y1 = max(0, y1 - int(mh * 0.4))
                roi_y2 = min(height, y1 + int(mh * 0.25))
                roi_x1 = max(0, x1)
                roi_x2 = min(width, x2)

                head_roi = frame[roi_y1:roi_y2, roi_x1:roi_x2]

                # Default assumption:
                # If no helmet is found, mark as violation
                is_violation = True

                if head_roi.size > 0:
                    h_results = HELMET_MODEL.predict(
                        head_roi,
                        conf=0.40,
                        verbose=False
                    )[0]

                    for hb in h_results.boxes:
                        label = HELMET_MODEL.names[int(hb.cls[0])].lower()

                        # Example labels:
                        # helmet, no_helmet, no helmet, not wearing helmet
                        if "helmet" in label and "no" not in label and "not" not in label:
                            is_violation = False

                # ==============================
                # 3. UNIQUE VIOLATION LOGIC
                # ==============================

                if is_violation:
                    if track_id not in logged_violations:
                        logged_violations.add(track_id)

                # ==============================
                # 4. DRAWING
                # ==============================

                color = (0, 0, 255) if is_violation else (0, 255, 0)
                status_text = "NO HELMET" if is_violation else "SAFE"

                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

                cv2.putText(
                    frame,
                    f"ID:{track_id} {status_text}",
                    (x1, max(30, y1 - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5 * ui_scale,
                    color,
                    2
                )

                # Optional: show ROI area
                cv2.rectangle(
                    frame,
                    (roi_x1, roi_y1),
                    (roi_x2, roi_y2),
                    (255, 255, 0),
                    1
                )

        # ==============================
        # 5. HUD DASHBOARD
        # ==============================

        cv2.rectangle(
            frame,
            (0, 0),
            (width, int(60 * ui_scale)),
            (20, 20, 20),
            -1
        )

        cv2.putText(
            frame,
            f"LIVE TRAFFIC MONITOR | BIKES: {bike_count_in_frame} | TOTAL VIOLATIONS: {len(logged_violations)}",
            (20, int(40 * ui_scale)),
            cv2.FONT_HERSHEY_DUPLEX,
            0.7 * ui_scale,
            (255, 255, 255),
            1
        )

        out.write(frame)

        if frame_no % 30 == 0:
            print(f"Processed frame: {frame_no}")

    cap.release()
    out.release()

    print("Video processing completed.")
    print(f"Output saved to: {output_path}")

    return output_path


# ==============================
# RUN VIDEO PROCESSING
# ==============================

if __name__ == "__main__":
    input_video = r"C:\Users\Lenovo\Desktop\traffic_base_project\test_videos\input.mp4"
    output_video = r"C:\Users\Lenovo\Desktop\traffic_base_project\outputs\result_video.mp4"

    Path(output_video).parent.mkdir(parents=True, exist_ok=True)

    process_video(input_video, output_video)