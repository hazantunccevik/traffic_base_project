import cv2
import numpy as np
from ultralytics import YOLO
from pathlib import Path

# Load Models
MOTOR_MODEL = YOLO('yolov8s.pt') 
HELMET_MODEL = YOLO(r"C:\Users\Lenovo\Desktop\traffic_base_project\runs\detect_helmet_detect\runs\helmet_detection\v12\weights\best.pt")

SOURCE_PATH = r"C:\Users\Lenovo\Desktop\traffic_base_project\datasets\test_images_v1"
OUTPUT_DIR = r"C:\Users\Lenovo\Desktop\traffic_base_project\runs\test2_v1"

def process_image(image_path):
    img = cv2.imread(str(image_path))
    if img is None: return
    h, w = img.shape[:2]
    
    # 1. Scale UI elements based on image size
    # We use a base size of 1280px width for scaling
    ui_scale = max(0.4, w / 1280)
    font_scale = 0.6 * ui_scale
    header_h = int(50 * ui_scale)

    # 2. DETECT MOTORCYCLES (Class 3) AND PERSONS (Class 0)
    # We detect persons to help with POV shots where the bike is hidden
    results = MOTOR_MODEL.predict(img, classes=[0, 3], conf=0.30, iou=0.45, verbose=False)[0]
    
    bike_count = 0
    violation_count = 0
    detections = []

    for box in results.boxes:
        cls = int(box.cls[0])
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        
        # Only process:
        # A) Motorcycles
        # B) Persons who are "large" (to handle POV/close-ups)
        if cls == 3 or (cls == 0 and (x2-x1) > w*0.3):
            if cls == 3: bike_count += 1
            
            # Check Helmet ROI
            roi_y1 = max(0, y1 - int((y2-y1)*0.35))
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

    # 3. DRAW UI
    # Header Overlay
    header_overlay = img.copy()
    cv2.rectangle(header_overlay, (0, 0), (w, header_h), (25, 25, 25), -1)
    cv2.addWeighted(header_overlay, 0.7, img, 0.3, 0, img)
    
    # Header Text
    status_color = (0, 0, 255) if violation_count > 0 else (0, 255, 0)
    cv2.putText(img, f"TRAFFIC AI | BIKES: {bike_count} | VIOLATIONS: {violation_count}", 
                (20, int(header_h*0.7)), cv2.FONT_HERSHEY_DUPLEX, font_scale, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.line(img, (0, header_h), (w, header_h), status_color, max(1, int(2*ui_scale)))

    for d in detections:
        x1, y1, x2, y2 = d['box']
        
        if d['violation']:
            color = (0, 0, 255)
            label = "NO HELMET"
            thickness = 2
        else:
            color = (0, 255, 0)
            label = "SAFE"
            thickness = 1
        
        # Draw Bike Box
        cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)
        
        # Position label (Flip inside if too high)
        label_y = y1 + int(20*ui_scale) if y1 < header_h + 30 else y1 - 5
        
        # Draw small label tab
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale*0.8, 1)
        cv2.rectangle(img, (x1, label_y - th - 4), (x1 + tw + 6, label_y + 2), color, -1)
        cv2.putText(img, label, (x1 + 3, label_y - 2), cv2.FONT_HERSHEY_SIMPLEX, font_scale*0.8, (255, 255, 255), 1, cv2.LINE_AA)

        # Helmet highlight
        if d['h_box']:
            hx1, hy1, hx2, hy2 = d['h_box']
            cv2.rectangle(img, (hx1, hy1), (hx2, hy2), (0, 255, 0), 1)

    cv2.imwrite(str(Path(OUTPUT_DIR) / image_path.name), img)

def main():
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    images = []
    for ext in ['*.jpg', '*.png', '*.jpeg']:
        images.extend(list(Path(SOURCE_PATH).glob(ext)))
    
    for img_p in images:
        process_image(img_p)
    print(f"Submission version ready in: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()