import time
import cv2 # OpenCV for image processing
import numpy as np # For numerical operations
from ultralytics import YOLO # For object detection
from pathlib import Path

# =========================================================
# Load Models
# =========================================================
MOTOR_MODEL = YOLO("yolo11m.pt") 
HELMET_MODEL = YOLO(r"C:\Users\Lenovo\Desktop\traffic_base_project\runs\helmet_detection2\v1\weights\best.pt")

# =========================================================
# Triple Riding Geometry Check
# Checks whether at least three detected head/helmet boxes are side by side.
# =========================================================
def are_three_heads_side_by_side(head_boxes):
  
    if len(head_boxes) < 3:
        return False

    # Sort head boxes from left to right by center x.
    boxes = sorted(head_boxes, key=lambda b: (b[0] + b[2]) / 2)

    # Check every group of 3 consecutive boxes.
    for i in range(len(boxes) - 2):
        group = boxes[i:i + 3]

        centers = []
        widths = []
        heights = []

        for box in group:
            x1, y1, x2, y2 = box

            # Calculate center, width, and height of each box.
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

        # Calculate average width and height of the three boxes.
        avg_width = sum(widths) / len(widths)
        avg_height = sum(heights) / len(heights)

        x_values = [c[0] for c in centers]
        y_values = [c[1] for c in centers]

        # Vertical alignment check:
        # Three heads should be approximately on the same horizontal line.
        max_y_diff = max(y_values) - min(y_values)
        same_horizontal_level = max_y_diff < avg_height * 0.8

        # Horizontal distance check:
        # Heads should not be extremely far away from each other.
        gap_1 = x_values[1] - x_values[0]
        gap_2 = x_values[2] - x_values[1]

        close_enough = (
            gap_1 < avg_width * 3.5
            and gap_2 < avg_width * 3.5
        )

        # Separation check:
        # Prevents counting overlapping duplicate detections as three riders.
        separated = (
            gap_1 > avg_width * 0.3
            and gap_2 > avg_width * 0.3
        )

        if same_horizontal_level and close_enough and separated:
            return True

    return False

# =========================================================
# Main Processing Logic
# This function processes a single image
# Detects motorcycles and helmets, checks for violations, and draws results.
# =========================================================
def process_image(image_path, output_path):

    start_time = time.time() 

    img = cv2.imread(str(image_path)) # Load image using OpenCV
    if img is None:
        return None

    # Get image dimensions (height, width)
    h, w = img.shape[:2] 

    # Scale UI elements based on image width
    ui_scale = max(0.5, w / 1280) 
    
    # Collect confidence scores for both motorcycle and helmet 
    all_confidences = [] 

    # Detect motorcycles
    results = MOTOR_MODEL.predict(
        img, 
        classes=[3], # COCO class motorcycle
        conf=0.25, # Priority is to catch all motorcycles
        iou=0.5, # High overlap = ignore duplicates 
        verbose=False
    )[0]

    bike_count = 0
    total_violations = 0
    triple_riding_count = 0

    # Process each detected motorcycle box
    for box in results.boxes:
        motor_conf = float(box.conf[0])
        all_confidences.append(motor_conf)
        
        #Motorcycle width and height for ROI calculation.
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        mw = x2 - x1
        mh = y2 - y1

        bike_count += 1
        
        # =================================================
        # Motorcycle-based Head ROI Calculation
        # =================================================
  
        is_side_view = mw > mh * 0.8 
        if is_side_view: # Expand horizontally 
            roi_x1 = max(0, x1 - int(mw*0.1)) 
            roi_x2 = min(w, x2 + int(mw*0.1))
        else:
            roi_x1 = max(0, x1 + int(mw * 0.1))
            roi_x2 = min(w, x2 - int(mw * 0.1))

        # Vertical expansion = above the motorcycle box
        roi_y1 = max(0, y1 - int(mh * 0.45))
        roi_y2 = min(h, y1 + int(mh * 0.3))

        head_roi = img[roi_y1:roi_y2, roi_x1:roi_x2]
        
        rider_count = 0
        helmet_count = 0
        no_helmet_count = 0

        # Helmet/no_helmet boxes + Color 
        head_boxes_for_drawing = []

        # Box coordinates for triple riding geometry check.
        head_boxes_only = []

        # =================================================
        # Helmet / Head Detection inside ROI
        # =================================================
        if head_roi.size > 0:
            
            h_results = HELMET_MODEL.predict(
                head_roi, 
                conf=0.35, # Helmet's models best F1 conf = 0.34
                imgsz=960, # To detail small helmet/no-helmet boxes
                verbose=False
            )[0]
            
            # For each detected head/helmet box, determine status
            for hb in h_results.boxes:
                
                h_conf = float(hb.conf[0])
                all_confidences.append(h_conf)

                # Detected class label (helmet or no_helmet)
                label = HELMET_MODEL.names[int(hb.cls[0])].lower()
                
                hx1, hy1, hx2, hy2 = map(int, hb.xyxy[0])
                
                # Convert ROI-local helmet box to full-image coordinates.
                abs_h_box = (
                    roi_x1 + hx1, 
                    roi_y1 + hy1, 
                    roi_x1 + hx2, 
                    roi_y1 + hy2
                )
                
                rider_count += 1
                head_boxes_only.append(abs_h_box) # Triple riding check 

                if "helmet" in label and "no" not in label and h_conf > 0.50:
                    helmet_count += 1
                    head_boxes_for_drawing.append((abs_h_box, (0, 255, 0))) # B G R
                else:
                    no_helmet_count += 1
                    head_boxes_for_drawing.append((abs_h_box, (0, 0, 255)))


        # =================================================
        # Triple Riding Check
        # =================================================
        triple_riding_detected = are_three_heads_side_by_side(head_boxes_only)

        if triple_riding_detected:
            triple_riding_count += 1

        # =================================================
        # Final Violation Decision
        # =================================================
        
        is_violation = (
            no_helmet_count > 0 
            or triple_riding_detected 
            or rider_count == 0
        )

        if is_violation:
            total_violations += 1

        # =================================================
        # Drawing
        # =================================================
        
        color = (0, 0, 255) if is_violation else (0, 255, 0)
        
        # Draw motorcycle box
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)

        if triple_riding_detected:
            status_text = f"TRIPLE RIDING | RIDERS:{rider_count}"
        else:
            status_text = f"RIDERS:{rider_count}"

        # Drawing status text above the motorcycle box
        cv2.putText(
            img,
            status_text,
            (x1, max(20, y1 - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.4 * ui_scale,
            color,
            1
        )

        # Draw detected helmet / no_helmet boxes.
        for h_box, h_color in head_boxes_for_drawing:
            cv2.rectangle(
                img,
                (h_box[0], h_box[1]),
                (h_box[2], h_box[3]),
                h_color,
                1
            )

        # Draw triple riding warning near the motorcycle.
        if triple_riding_detected:
            cv2.putText(
                img,
                "TRIPLE RIDING DETECTED",
                (x1, min(h - 10, y2 + 25)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5 * ui_scale,
                (0, 0, 255),
                2
            )

    # =====================================================
    # Top Dashboard Bar
    # =====================================================
    
    # Black dasboard for summary 
    cv2.rectangle(img, (0, 0), (w, int(60 * ui_scale)), (20, 20, 20), -1)

    dashboard_text = (
        f"Motorcycles: {bike_count} | "
        f"Violations: {total_violations} | "
        f"Triple Riding: {triple_riding_count}"
    )

    cv2.putText(
        img,
        dashboard_text,
        (20, int(38 * ui_scale)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55 * ui_scale,
        (255, 255, 255),
        1
    )

    # Save the annotated image to the output path
    cv2.imwrite(str(output_path), img)

    # Calculate avg. confidence 
    avg_conf_val = int(np.mean(all_confidences) * 100) if all_confidences else 0


    # Stop timer & calculate processing time in ms
    end_time = time.time()
    total_duration_ms = int((end_time - start_time) * 1000)

    return {
        "motorcycles": bike_count,
        "violations": total_violations,
        "helmets": bike_count - total_violations, 
        
        "triple_riding": triple_riding_count,
        "triple_riding_detected": triple_riding_count > 0,
        "popup_message": (
            "Triple riding detected!"
            if triple_riding_count > 0
            else ""
        ),

        "avg_confidence": avg_conf_val,
        "resolution": f"{w}x{h}",
        "processing_time": total_duration_ms
    }