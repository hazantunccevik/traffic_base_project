import time
import datetime 

import cv2
import numpy as np
from ultralytics import YOLO
from pathlib import Path

# =========================================================
# Load Models
# =========================================================
MOTOR_MODEL = YOLO("yolo11m.pt") # High-quality base
HELMET_MODEL = YOLO(r"C:\Users\Lenovo\Desktop\traffic_base_project\runs\helmet_detection2\v1\weights\best.pt")

# =========================================================
# Refined Geometry & Logic
# =========================================================
def get_iou(boxA, boxB):
    """Standard IoU to match riders to motorcycles."""
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    interArea = max(0, xB - xA) * max(0, yB - yA)
    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
    return interArea / float(boxAArea + boxBArea - interArea + 1e-6)

def make_rider_head_roi(rider_box, img_w, img_h):
    """
    Refined ROI: Looks higher above the head to catch helmets 
    that protrude outside the YOLO person box.
    """
    rx1, ry1, rx2, ry2 = rider_box
    rw = rx2 - rx1
    rh = ry2 - ry1

    # Look 20% higher than the person box start point
    roi_y1 = max(0, ry1 - int(rh * 0.15)) 
    # Only need the top 40% of the person's body
    roi_y2 = min(img_h, ry1 + int(rh * 0.35))
    # Widen horizontally to catch leaning riders
    roi_x1 = max(0, rx1 - int(rw * 0.1))
    roi_x2 = min(img_w, rx2 + int(rw * 0.1))
    
    return [roi_x1, roi_y1, roi_x2, roi_y2]

def detect_helmet_refined(img, roi_box):
    """
    Enhanced detection with Cap-Filtering logic.
    """
    x1, y1, x2, y2 = map(int, roi_box)
    roi = img[y1:y2, x1:x2]
    if roi.size == 0: return "unknown", None, 0.0

    # Increase imgsz to 960 for helmet check to distinguish textures (caps vs helmets)
    results = HELMET_MODEL.predict(source=roi, conf=0.35, imgsz=960, verbose=False)[0]

    best_conf = 0
    decision = "unknown"
    box_abs = None

    for box in results.boxes:
        label = HELMET_MODEL.names[int(box.cls[0])].lower()
        conf = float(box.conf[0])
        hx1, hy1, hx2, hy2 = map(int, box.xyxy[0])
        
        # FEATURE FILTER: Helmets are usually wider and boxier than caps
        # Caps are very flat. We check aspect ratio.
        hw = hx2 - hx1
        hh = hy2 - hy1
        aspect_ratio = hw / float(hh + 1e-6)

        is_helmet = "helmet" in label and "no" not in label
        
        # If it's a helmet but too 'flat' or small, it's likely a cap or noise
        if is_helmet:
            if aspect_ratio > 1.8 or hh < (roi.shape[0] * 0.2):
                continue # Skip suspicious small/flat detections
            
            if conf > best_conf:
                best_conf = conf
                decision = "helmet"
                box_abs = (x1+hx1, y1+hy1, x1+hx2, y1+hy2)
        
        elif "no" in label:
            if conf > best_conf:
                best_conf = conf
                decision = "no_helmet"
                box_abs = (x1+hx1, y1+hy1, x1+hx2, y1+hy2)

    return decision, box_abs, best_conf

# =========================================================
# Main Processing Logic
# =========================================================

def process_image(image_path, output_path):
    start_time = time.time() 

    img = cv2.imread(str(image_path))
    if img is None:
        return None

    h, w = img.shape[:2]
    ui_scale = max(0.5, w / 1280)
    all_confidences = []

    # Indent this exactly 4 spaces from the 'def'
    results = MOTOR_MODEL.predict(img, classes=[3], conf=0.25, iou=0.5, verbose=False)[0]

    bike_count = 0
    total_violations = 0

    for box in results.boxes:
        conf = float(box.conf[0])
        all_confidences.append(conf)
        
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        mw, mh = x2 - x1, y2 - y1
        bike_count += 1
        
        # Determine ROI
        is_side_view = mw > mh * 0.8 
        if is_side_view:
            roi_x1, roi_x2 = max(0, x1 - int(mw*0.1)), min(w, x2 + int(mw*0.1))
        else:
            roi_x1, roi_x2 = x1 + int(mw*0.1), x2 - int(mw*0.1)

        roi_y1 = max(0, y1 - int(mh * 0.45))
        roi_y2 = y1 + int(mh * 0.3)
        head_roi = img[roi_y1:roi_y2, roi_x1:roi_x2]
        
        rider_count = 0
        helmet_count = 0
        no_helmet_count = 0
        head_boxes = []

        if head_roi.size > 0:
            h_results = HELMET_MODEL.predict(head_roi, conf=0.35, imgsz=960, verbose=False)[0]
            for hb in h_results.boxes:
                h_conf = float(hb.conf[0])
                all_confidences.append(h_conf)
                rider_count += 1 
                label = HELMET_MODEL.names[int(hb.cls[0])].lower()
                hx1, hy1, hx2, hy2 = map(int, hb.xyxy[0])
                abs_h_box = (roi_x1 + hx1, roi_y1 + hy1, roi_x1 + hx2, roi_y1 + hy2)
                
                if "helmet" in label and "no" not in label and h_conf > 0.50:
                    helmet_count += 1
                    head_boxes.append((abs_h_box, (0, 255, 0)))
                else:
                    no_helmet_count += 1
                    head_boxes.append((abs_h_box, (0, 0, 255)))

        is_violation = (no_helmet_count > 0) or (rider_count > 2) or (rider_count == 0)
        if is_violation:
            total_violations += 1

        color = (0, 0, 255) if is_violation else (0, 255, 0)
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
        
        status_text = f"RIDERS:{rider_count}"
        cv2.putText(img, status_text, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.4*ui_scale, color, 1)

        for h_box, h_color in head_boxes:
            cv2.rectangle(img, (h_box[0], h_box[1]), (h_box[2], h_box[3]), h_color, 1)

    cv2.rectangle(img, (0,0), (w, int(60*ui_scale)), (20,20,20), -1)
    cv2.imwrite(str(output_path), img)

    avg_conf_val = int(np.mean(all_confidences) * 100) if all_confidences else 0
    end_time = time.time()
    total_duration_ms = int((end_time - start_time) * 1000)

    return {
        "motorcycles": bike_count,
        "violations": total_violations,
        "helmets": bike_count - total_violations, 
        "avg_confidence": avg_conf_val,
        "resolution": f"{w}x{h}",
        "processing_time": total_duration_ms
    }