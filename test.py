import cv2
import numpy as np
from ultralytics import YOLO
from pathlib import Path

# Load Models
MOTOR_MODEL = YOLO('yolov8m.pt') 
HELMET_MODEL = YOLO(r"C:\Users\Lenovo\Desktop\traffic_base_project\runs\detect_helmet_detect\runs\helmet_detection\v12\weights\best.pt")

SOURCE_PATH = r"C:\Users\Lenovo\Desktop\traffic_base_project\datasets\test_images_v1"
OUTPUT_DIR = r"C:\Users\Lenovo\Desktop\traffic_base_project\runs\p1"

def process_image(image_path):
    img = cv2.imread(str(image_path))
    if img is None: return
    h, w = img.shape[:2]
    
    # Scale factor based on width (Safe minimum of 0.5 to avoid tiny text)
    scaling_factor = max(0.5, w / 1000) 
    font_scale = 0.5 * scaling_factor
    header_h = int(60 * scaling_factor)
    
    # SAFE THICKNESS: Always at least 1
    line_thickness = max(1, int(2 * scaling_factor))
    box_thickness = max(1, int(2 * scaling_factor))

    # 1. DETECT MOTORCYCLES
    results = MOTOR_MODEL.predict(img, classes=[3], conf=0.30, iou=0.45, verbose=False)[0]
    
    bike_count = 0
    violation_count = 0
    detections = []

    for box in results.boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        bike_count += 1
        
        # Check Helmet ROI
        roi_y1 = max(0, y1 - int((y2-y1)*0.45))
        roi_y2 = y1 + int((y2-y1)*0.3)
        head_roi = img[roi_y1:roi_y2, x1:x2]
        
        is_violation = True
        helmet_coords = None
        if head_roi.size > 0:
            h_res = HELMET_MODEL.predict(head_roi, conf=0.25, verbose=False)[0]
            for hb in h_res.boxes:
                label = HELMET_MODEL.names[int(hb.cls[0])].lower()
                if "helmet" in label and "no" not in label:
                    is_violation = False
                    hx1, hy1, hx2, hy2 = map(int, hb.xyxy[0])
                    helmet_coords = (x1+hx1, roi_y1+hy1, x1+hx2, roi_y1+hy2)

        if is_violation: violation_count += 1
        detections.append({'box': (x1, y1, x2, y2), 'violation': is_violation, 'h_box': helmet_coords})

    # 2. DRAW DASHBOARD (Background Layer)
    overlay = img.copy()
    cv2.rectangle(overlay, (0, 0), (w, header_h), (30, 30, 30), -1)
    cv2.addWeighted(overlay, 0.7, img, 0.3, 0, img)
    
    # Status Accent Line
    accent = (0, 0, 255) if violation_count > 0 else (0, 255, 0)
    cv2.line(img, (0, header_h), (w, header_h), accent, line_thickness)

    # Dashboard Text
    cv2.putText(img, "AI SAFETY SYSTEM", (20, int(header_h*0.65)), 
                cv2.FONT_HERSHEY_SIMPLEX, font_scale*1.1, (255,255,255), 1, cv2.LINE_AA)
    cv2.putText(img, f"BIKES: {bike_count} | VIOLATIONS: {violation_count}", 
                (int(w*0.35), int(header_h*0.65)), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255,255,255), 1, cv2.LINE_AA)

    # 3. DRAW DETECTIONS
    for d in detections:
        x1, y1, x2, y2 = d['box']
        color = (0, 0, 255) if d['violation'] else (255, 150, 0)
        label = "!!! NO HELMET !!!" if d['violation'] else "SAFE"
        
        # Draw Bike Box
        cv2.rectangle(img, (x1, y1), (x2, y2), color, box_thickness)
        
        # Position label inside if near top dashboard
        label_y_offset = int(25 * scaling_factor)
        label_y = y1 + label_y_offset if y1 < header_h + 50 else y1 - 5
        
        # Label Background & Text
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 1)
        cv2.rectangle(img, (x1, label_y - th - 5), (x1 + tw + 10, label_y + 5), color, -1)
        cv2.putText(img, label, (x1 + 5, label_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255,255,255), 1, cv2.LINE_AA)

        # Helmet Box (Green)
        if d['h_box']:
            cx1, cy1, cx2, cy2 = d['h_box']
            cv2.rectangle(img, (cx1, cy1), (cx2, cy2), (0, 255, 0), max(1, int(1*scaling_factor)))

    # Save to output
    cv2.imwrite(str(Path(OUTPUT_DIR) / image_path.name), img)

def main():
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    # Search for common image formats
    image_files = []
    for ext in ['*.jpg', '*.png', '*.jpeg', '*.webp']:
        image_files.extend(list(Path(SOURCE_PATH).glob(ext)))
        
    if not image_files:
        print(f"Error: No images found in {SOURCE_PATH}")
        return

    for img_p in image_files:
        process_image(img_p)
    print(f"Success! Processed {len(image_files)} images. Saved in: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()