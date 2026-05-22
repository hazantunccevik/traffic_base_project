import time
import cv2
from ultralytics import YOLO


# =========================================================
# Load Models
# =========================================================

# COCO:
# class 0 -> person
# class 3 -> motorcycle
MOTOR_MODEL = YOLO("yolov8s.pt")

HELMET_MODEL = YOLO(
    r"C:\Users\Lenovo\Desktop\traffic_base_project\runs\helmet_detection2\v1\weights\best.pt"
)


# =========================================================
# Label Helpers
# =========================================================

def normalize_label(label: str) -> str:
    return label.lower().strip().replace("-", " ").replace("_", " ")


def is_helmet_label(label: str) -> bool:
    """
    True helmet classes:
    helmet, wearing helmet, full-faced, half-faced etc.
    """
    label = normalize_label(label)

    if "no" in label:
        return False

    if "not" in label:
        return False

    if "without" in label:
        return False

    return (
        "helmet" in label
        or "full faced" in label
        or "half faced" in label
    )


def is_no_helmet_label(label: str) -> bool:
    """
    Explicit no helmet classes:
    no_helmet, no helmet, not wearing helmet, without helmet etc.
    """
    label = normalize_label(label)

    return (
        "no helmet" in label
        or "nohelmet" in label
        or "not wearing helmet" in label
        or "without helmet" in label
        or label == "no"
    )


# =========================================================
# Geometry Helpers
# =========================================================

def get_overlap_area(box_a, box_b):
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b

    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)

    inter_w = max(0, inter_x2 - inter_x1)
    inter_h = max(0, inter_y2 - inter_y1)

    return inter_w * inter_h


def center_of(box):
    x1, y1, x2, y2 = box
    return (x1 + x2) / 2, (y1 + y2) / 2


def is_valid_motorcycle_box(motor_box, img_w, img_h):
    """
    Softer motorcycle filter.

    We do not make this too strict because frontal scooters/motorcycles
    can look vertical in camera images.
    """
    x1, y1, x2, y2 = motor_box

    box_w = x2 - x1
    box_h = y2 - y1
    area = box_w * box_h
    img_area = img_w * img_h

    if box_w <= 0 or box_h <= 0:
        return False

    # Remove only extremely tiny detections
    if area < img_area * 0.001:
        return False

    aspect_ratio = box_w / max(1, box_h)

    # Frontal motorcycles can be vertical, so keep this threshold low.
    if aspect_ratio < 0.35:
        return False

    return True


def make_motorcycle_upper_roi(motor_box, img_w, img_h):
    """
    Fallback ROI when rider/person detection is weak.
    Uses upper area around motorcycle where rider/head usually appears.
    """
    mx1, my1, mx2, my2 = motor_box

    motor_w = mx2 - mx1
    motor_h = my2 - my1

    roi_x1 = max(0, mx1 - int(motor_w * 0.15))
    roi_x2 = min(img_w, mx2 + int(motor_w * 0.15))

    roi_y1 = max(0, my1 - int(motor_h * 0.60))
    roi_y2 = min(img_h, my1 + int(motor_h * 0.45))

    return roi_x1, roi_y1, roi_x2, roi_y2


def make_rider_head_roi(rider_box, img_w, img_h):
    """
    Head ROI from person/rider box.
    """
    rx1, ry1, rx2, ry2 = rider_box

    rider_w = rx2 - rx1
    rider_h = ry2 - ry1

    roi_x1 = max(0, rx1 - int(rider_w * 0.20))
    roi_x2 = min(img_w, rx2 + int(rider_w * 0.20))

    roi_y1 = max(0, ry1)
    roi_y2 = min(img_h, ry1 + int(rider_h * 0.48))

    return roi_x1, roi_y1, roi_x2, roi_y2


# =========================================================
# Rider Matching
# =========================================================

def find_riders_for_motorcycle(motor_box, person_boxes, img_w, img_h):
    """
    Returns rider candidates related to the motorcycle.

    Important:
    - Person alone is never a violation.
    - A person must be spatially related to a motorcycle.
    - Allows max 2 riders for two-person motorcycle cases.
    """
    mx1, my1, mx2, my2 = motor_box

    motor_w = mx2 - mx1
    motor_h = my2 - my1

    motor_cx, motor_cy = center_of(motor_box)

    # Search area around motorcycle
    sx1 = max(0, mx1 - int(motor_w * 0.35))
    sx2 = min(img_w, mx2 + int(motor_w * 0.35))
    sy1 = max(0, my1 - int(motor_h * 1.60))
    sy2 = min(img_h, my2 + int(motor_h * 0.45))

    riders = []

    for person in person_boxes:
        person_box = person["box"]
        px1, py1, px2, py2 = person_box

        person_w = px2 - px1
        person_h = py2 - py1

        if person_w <= 0 or person_h <= 0:
            continue

        pcx, pcy = center_of(person_box)

        # Person center should be inside the extended motorcycle zone
        center_inside_search = sx1 <= pcx <= sx2 and sy1 <= pcy <= sy2

        if not center_inside_search:
            continue

        # Horizontal relation between motorcycle and person
        horizontal_overlap = max(0, min(px2, mx2) - max(px1, mx1))
        horizontal_overlap_ratio = horizontal_overlap / max(1, min(person_w, motor_w))

        center_distance_x = abs(pcx - motor_cx) / max(1, motor_w)

        horizontally_related = (
            horizontal_overlap_ratio >= 0.10
            or center_distance_x <= 0.55
        )

        if not horizontally_related:
            continue

        # Person bottom should be near motorcycle body
        bottom_near_motor = (
            py2 >= my1 - int(motor_h * 0.70)
            and py2 <= my2 + int(motor_h * 1.00)
        )

        if not bottom_near_motor:
            continue

        # Ignore very tiny persons compared to the motorcycle
        size_reasonable = person_h >= motor_h * 0.25

        if not size_reasonable:
            continue

        score = 0

        # More horizontal overlap is better
        score += horizontal_overlap_ratio

        # Prefer centered persons
        score += max(0, 0.60 - center_distance_x)

        # Prefer person bottom near motorcycle center/body
        distance_bottom = abs(py2 - motor_cy) / max(1, motor_h)
        score += max(0, 0.50 - distance_bottom)

        riders.append({
            "box": person_box,
            "score": score,
            "conf": person["conf"]
        })

    # Keep likely riders
    riders = [r for r in riders if r["score"] >= 0.20]

    # Sort best first
    riders.sort(key=lambda r: r["score"], reverse=True)

    # Keep max 2 riders
    return riders[:2]


# =========================================================
# Helmet Decision
# =========================================================

def detect_helmet_in_roi(img, roi_box, conf=0.20):
    """
    Runs helmet model inside a given ROI.

    Returns:
        decision: "helmet", "no_helmet", or "unknown"
        detected_box_abs: absolute helmet/no_helmet box if found
        confidence: confidence value

    Important:
        Helmet must be high confidence to be SAFE.
        Weak helmet predictions become CHECK.
    """

    HELMET_SAFE_CONF = 0.55
    NO_HELMET_CONF = 0.35

    x1, y1, x2, y2 = roi_box

    roi = img[y1:y2, x1:x2]

    if roi.size == 0:
        return "unknown", None, 0.0

    results = HELMET_MODEL.predict(
        source=roi,
        conf=conf,
        verbose=False
    )[0]

    best_helmet = None
    best_no_helmet = None

    for box in results.boxes:
        cls_id = int(box.cls[0])
        label = HELMET_MODEL.names[cls_id]
        box_conf = float(box.conf[0])

        bx1, by1, bx2, by2 = map(int, box.xyxy[0])

        abs_box = (
            x1 + bx1,
            y1 + by1,
            x1 + bx2,
            y1 + by2
        )

        if is_no_helmet_label(label):
            if best_no_helmet is None or box_conf > best_no_helmet["conf"]:
                best_no_helmet = {
                    "box": abs_box,
                    "conf": box_conf
                }

        elif is_helmet_label(label):
            if best_helmet is None or box_conf > best_helmet["conf"]:
                best_helmet = {
                    "box": abs_box,
                    "conf": box_conf
                }

    # Explicit no_helmet has priority if confidence is enough
    if best_no_helmet is not None and best_no_helmet["conf"] >= NO_HELMET_CONF:
        return "no_helmet", best_no_helmet["box"], best_no_helmet["conf"]

    # Helmet is accepted as SAFE only if confidence is high enough
    if best_helmet is not None and best_helmet["conf"] >= HELMET_SAFE_CONF:
        return "helmet", best_helmet["box"], best_helmet["conf"]

    # Weak helmet/no_helmet predictions become CHECK
    return "unknown", None, 0.0


# =========================================================
# Drawing Helpers
# =========================================================

def draw_header(img, bike_count, helmet_count, violation_count, check_count, ui_scale, header_h):
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

    if violation_count > 0:
        status_color = (0, 0, 255)
    elif check_count > 0:
        status_color = (0, 165, 255)
    else:
        status_color = (0, 200, 0)

    font_scale = max(0.35, 0.60 * ui_scale)

    header_text = (
        f"TRAFFIC AI | "
        f"MOTORCYCLES: {bike_count} | "
        f"HELMETS: {helmet_count} | "
        f"VIOLATIONS: {violation_count} | "
        f"CHECK: {check_count}"
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


def draw_box_with_label(img, box, label, color, ui_scale, header_h):
    x1, y1, x2, y2 = box

    font_scale = max(0.35, 0.60 * ui_scale)
    label_font_scale = font_scale * 0.80

    thickness = 2

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
        (x1 + tw + 8, label_y + 3),
        color,
        -1
    )

    cv2.putText(
        img,
        label,
        (x1 + 4, label_y - 2),
        cv2.FONT_HERSHEY_SIMPLEX,
        label_font_scale,
        (255, 255, 255),
        1,
        cv2.LINE_AA
    )


def draw_small_box(img, box, color, ui_scale):
    x1, y1, x2, y2 = box

    cv2.rectangle(
        img,
        (x1, y1),
        (x2, y2),
        color,
        max(1, int(1 * ui_scale))
    )


# =========================================================
# Main Web Pipeline
# =========================================================

def process_image(input_path, output_path):
    start_time = time.time()

    img = cv2.imread(str(input_path))

    if img is None:
        raise ValueError("Image could not be read. Please check the uploaded file.")

    h, w = img.shape[:2]

    ui_scale = max(0.4, w / 1280)
    header_h = int(50 * ui_scale)

    bike_count = 0
    helmet_count = 0
    violation_count = 0
    check_count = 0
    confidence_values = []

    detections = []

    # =====================================================
    # 1. Detect motorcycles and persons
    # =====================================================

    motor_results = MOTOR_MODEL.predict(
        source=img,
        classes=[0, 3],
        conf=0.20,
        iou=0.45,
        verbose=False
    )[0]

    motorcycle_boxes = []
    person_boxes = []

    for box in motor_results.boxes:
        cls = int(box.cls[0])
        conf = float(box.conf[0])
        x1, y1, x2, y2 = map(int, box.xyxy[0])

        if cls == 3:
            motor_box = (x1, y1, x2, y2)

            if not is_valid_motorcycle_box(motor_box, w, h):
                continue

            motorcycle_boxes.append({
                "box": motor_box,
                "conf": conf
            })

        elif cls == 0:
            person_boxes.append({
                "box": (x1, y1, x2, y2),
                "conf": conf
            })

    # =====================================================
    # 2. Process each motorcycle
    # =====================================================

    for motorcycle in motorcycle_boxes:
        bike_count += 1

        motor_box = motorcycle["box"]
        motor_conf = motorcycle["conf"]
        confidence_values.append(motor_conf)

        riders = find_riders_for_motorcycle(
            motor_box=motor_box,
            person_boxes=person_boxes,
            img_w=w,
            img_h=h
        )

        final_label = "CHECK"
        final_status = "check"
        helmet_box = None
        rider_boxes = []

        # -------------------------------------------------
        # Case A: rider/person matched
        # -------------------------------------------------

        if riders:
            rider_decisions = []

            for rider in riders:
                rider_box = rider["box"]
                rider_boxes.append(rider_box)

                head_roi = make_rider_head_roi(rider_box, w, h)

                decision, detected_box, det_conf = detect_helmet_in_roi(
                    img,
                    head_roi,
                    conf=0.20
                )

                if det_conf > 0:
                    confidence_values.append(det_conf)

                rider_decisions.append({
                    "decision": decision,
                    "box": detected_box,
                    "conf": det_conf
                })

            no_helmet_decisions = [
                d for d in rider_decisions if d["decision"] == "no_helmet"
            ]

            helmet_decisions = [
                d for d in rider_decisions if d["decision"] == "helmet"
            ]

            if no_helmet_decisions:
                best = max(no_helmet_decisions, key=lambda d: d["conf"])
                final_label = "NO HELMET"
                final_status = "violation"
                helmet_box = best["box"]

            elif helmet_decisions:
                best = max(helmet_decisions, key=lambda d: d["conf"])
                final_label = "SAFE"
                final_status = "safe"
                helmet_box = best["box"]

            else:
                final_label = "CHECK"
                final_status = "check"

        # -------------------------------------------------
        # Case B: no rider matched
        # Fallback motorcycle upper ROI
        # -------------------------------------------------

        else:
            upper_roi = make_motorcycle_upper_roi(motor_box, w, h)

            decision, detected_box, det_conf = detect_helmet_in_roi(
                img,
                upper_roi,
                conf=0.20
            )

            if det_conf > 0:
                confidence_values.append(det_conf)

            if decision == "no_helmet":
                final_label = "NO HELMET"
                final_status = "violation"
                helmet_box = detected_box

            elif decision == "helmet":
                final_label = "SAFE"
                final_status = "safe"
                helmet_box = detected_box

            else:
                final_label = "CHECK"
                final_status = "check"

        if final_status == "violation":
            violation_count += 1
        elif final_status == "safe":
            helmet_count += 1
        else:
            check_count += 1

        detections.append({
            "motor_box": motor_box,
            "rider_boxes": rider_boxes,
            "helmet_box": helmet_box,
            "label": final_label,
            "status": final_status
        })

    # =====================================================
    # 3. Draw output
    # =====================================================

    draw_header(
        img=img,
        bike_count=bike_count,
        helmet_count=helmet_count,
        violation_count=violation_count,
        check_count=check_count,
        ui_scale=ui_scale,
        header_h=header_h
    )

    for det in detections:
        label = det["label"]

        if label == "NO HELMET":
            color = (0, 0, 255)       # red
        elif label == "SAFE":
            color = (0, 200, 0)       # green
        else:
            color = (0, 165, 255)     # orange / CHECK

        draw_box_with_label(
            img=img,
            box=det["motor_box"],
            label=label,
            color=color,
            ui_scale=ui_scale,
            header_h=header_h
        )

        # Draw matched rider boxes in blue/orange
        for rider_box in det["rider_boxes"]:
            draw_small_box(
                img=img,
                box=rider_box,
                color=(255, 180, 0),
                ui_scale=ui_scale
            )

        # Draw helmet/no_helmet box
        if det["helmet_box"] is not None:
            if label == "NO HELMET":
                small_color = (0, 0, 255)
            else:
                small_color = (0, 255, 0)

            draw_small_box(
                img=img,
                box=det["helmet_box"],
                color=small_color,
                ui_scale=ui_scale
            )

    # =====================================================
    # 4. Save output
    # =====================================================

    success = cv2.imwrite(str(output_path), img)

    if not success:
        raise ValueError("Output image could not be saved.")

    # =====================================================
    # 5. Summary
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
        "checks": check_count,
        "avg_confidence": avg_confidence,
        "processing_time": processing_time,
        "resolution": f"{w}x{h}",
        "model": "YOLOv8s + Rider/Helmet ROI Pipeline with CHECK"
    }

    return summary