import time
import cv2
from ultralytics import YOLO


# =========================================================
# Load Models
# =========================================================

MOTOR_MODEL = YOLO("yolov8m.pt")

HELMET_MODEL = YOLO(
    r"C:\Users\Lenovo\Desktop\traffic_base_project\runs\helmet_detection2\v1\weights\best.pt"
)


# =========================================================
# Helper Functions
# =========================================================

def is_helmet_label(label: str) -> bool:
    """
    Returns True if detected class represents helmet.
    This function avoids counting 'no helmet' as helmet.
    """
    label = label.lower()

    if "no" in label:
        return False

    if "not" in label:
        return False

    return "helmet" in label


def draw_header(img, bike_count, helmet_count, violation_count, ui_scale, header_h):
    """
    Draws a dark header overlay on the output image.
    """
    h, w = img.shape[:2]

    header_overlay = img.copy()

    cv2.rectangle(
        header_overlay,
        (0, 0),
        (w, header_h),
        (25, 25, 25),
        -1
    )

    cv2.addWeighted(header_overlay, 0.70, img, 0.30, 0, img)

    status_color = (0, 0, 255) if violation_count > 0 else (0, 200, 0)

    font_scale = 0.60 * ui_scale

    header_text = (
        f"TRAFFIC AI | "
        f"MOTORCYCLES: {bike_count} | "
        f"HELMETS: {helmet_count} | "
        f"VIOLATIONS: {violation_count}"
    )

    cv2.putText(
        img,
        header_text,
        (20, int(header_h * 0.70)),
        cv2.FONT_HERSHEY_DUPLEX,
        font_scale,
        (255, 255, 255),
        1,
        cv2.LINE_AA
    )

    cv2.line(
        img,
        (0, header_h),
        (w, header_h),
        status_color,
        max(1, int(2 * ui_scale))
    )


def draw_detection_box(img, box, label, color, ui_scale, header_h):
    """
    Draws detection bounding box and label tab.
    """
    x1, y1, x2, y2 = box

    font_scale = 0.60 * ui_scale
    label_font_scale = font_scale * 0.80

    thickness = 2 if label == "NO HELMET" else 1

    cv2.rectangle(
        img,
        (x1, y1),
        (x2, y2),
        color,
        thickness
    )

    label_y = y1 + int(20 * ui_scale) if y1 < header_h + 30 else y1 - 5

    (tw, th), _ = cv2.getTextSize(
        label,
        cv2.FONT_HERSHEY_SIMPLEX,
        label_font_scale,
        1
    )

    cv2.rectangle(
        img,
        (x1, label_y - th - 4),
        (x1 + tw + 6, label_y + 2),
        color,
        -1
    )

    cv2.putText(
        img,
        label,
        (x1 + 3, label_y - 2),
        cv2.FONT_HERSHEY_SIMPLEX,
        label_font_scale,
        (255, 255, 255),
        1,
        cv2.LINE_AA
    )


# =========================================================
# Main Pipeline Function for Web Backend
# =========================================================

def process_image(input_path, output_path):
    """
    Web-compatible image pipeline.

    Input:
        input_path  -> uploaded image path
        output_path -> result image save path

    Output:
        summary dictionary for frontend dashboard
    """

    start_time = time.time()

    img = cv2.imread(str(input_path))

    if img is None:
        raise ValueError("Image could not be read. Please check the uploaded file.")

    h, w = img.shape[:2]

    # UI scaling for drawn output image
    ui_scale = max(0.4, w / 1280)
    header_h = int(50 * ui_scale)

    # Counters for dashboard
    bike_count = 0
    helmet_count = 0
    violation_count = 0
    confidence_values = []

    detections = []

    # =====================================================
    # 1. Detect motorcycles and persons using YOLOv8s
    # COCO classes:
    # 0 -> person
    # 3 -> motorcycle
    # =====================================================

    motor_results = MOTOR_MODEL.predict(
        source=img,
        classes=[0, 3],
        conf=0.30,
        iou=0.45,
        verbose=False
    )[0]

    for box in motor_results.boxes:
        cls = int(box.cls[0])
        conf = float(box.conf[0])

        x1, y1, x2, y2 = map(int, box.xyxy[0])

        box_width = x2 - x1
        box_height = y2 - y1

        # Process:
        # A) motorcycles
        # B) large persons, for close-up / POV images
        is_motorcycle = cls == 3
        is_large_person = cls == 0 and box_width > w * 0.30

        if not (is_motorcycle or is_large_person):
            continue

        if is_motorcycle:
            bike_count += 1

        confidence_values.append(conf)

        # =================================================
        # 2. Create head / helmet ROI
        # =================================================

        roi_y1 = max(0, y1 - int(box_height * 0.35))
        roi_y2 = min(h, y1 + int(box_height * 0.30))

        roi_x1 = max(0, x1)
        roi_x2 = min(w, x2)

        head_roi = img[roi_y1:roi_y2, roi_x1:roi_x2]

        is_violation = True
        helmet_coords = None

        # =================================================
        # 3. Helmet detection inside ROI
        # =================================================

        if head_roi.size > 0:
            helmet_results = HELMET_MODEL.predict(
                source=head_roi,
                conf=0.25,
                verbose=False
            )[0]

            for helmet_box in helmet_results.boxes:
                helmet_cls = int(helmet_box.cls[0])
                helmet_conf = float(helmet_box.conf[0])
                helmet_label = HELMET_MODEL.names[helmet_cls].lower()

                confidence_values.append(helmet_conf)

                if is_helmet_label(helmet_label):
                    is_violation = False
                    helmet_count += 1

                    hx1, hy1, hx2, hy2 = map(int, helmet_box.xyxy[0])

                    helmet_coords = (
                        roi_x1 + hx1,
                        roi_y1 + hy1,
                        roi_x1 + hx2,
                        roi_y1 + hy2
                    )

                    # One valid helmet is enough for this ROI
                    break

        if is_violation:
            violation_count += 1

        detections.append({
            "box": (x1, y1, x2, y2),
            "violation": is_violation,
            "helmet_box": helmet_coords
        })

    # =====================================================
    # 4. Draw final visual output
    # =====================================================

    draw_header(
        img=img,
        bike_count=bike_count,
        helmet_count=helmet_count,
        violation_count=violation_count,
        ui_scale=ui_scale,
        header_h=header_h
    )

    for detection in detections:
        x1, y1, x2, y2 = detection["box"]

        if detection["violation"]:
            color = (0, 0, 255)
            label = "NO HELMET"
        else:
            color = (0, 255, 0)
            label = "SAFE"

        draw_detection_box(
            img=img,
            box=(x1, y1, x2, y2),
            label=label,
            color=color,
            ui_scale=ui_scale,
            header_h=header_h
        )

        if detection["helmet_box"] is not None:
            hx1, hy1, hx2, hy2 = detection["helmet_box"]

            cv2.rectangle(
                img,
                (hx1, hy1),
                (hx2, hy2),
                (0, 255, 0),
                1
            )

    # =====================================================
    # 5. Save output image
    # =====================================================

    cv2.imwrite(str(output_path), img)

    # =====================================================
    # 6. Create summary for frontend
    # =====================================================

    processing_time = round((time.time() - start_time) * 1000)

    if confidence_values:
        avg_confidence = round(
            (sum(confidence_values) / len(confidence_values)) * 100
        )
    else:
        avg_confidence = 0

    summary = {
        "motorcycles": bike_count,
        "helmets": helmet_count,
        "violations": violation_count,
        "avg_confidence": avg_confidence,
        "processing_time": processing_time,
        "resolution": f"{w}x{h}",
        "model": "YOLOv8s + Helmet ROI Pipeline"
    }

    return summary 