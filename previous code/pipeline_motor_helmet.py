import cv2
import numpy as np
from ultralytics import YOLO
from pathlib import Path

# =========================
# MODEL PATHS (Keep yours same)
# =========================
MOTOR_MODEL_PATH = r"runs/detect_street_view/street_view_base_v1/runs/weights/best.pt"
HELMET_MODEL_PATH = r"C:\Users\Lenovo\Desktop\traffic_base_project\runs\detect_helmet_detect\runs\helmet_detection\v12\weights\best.pt"

SOURCE_PATH = r"C:\Users\Lenovo\Desktop\traffic_base_project\datasets\test_images_v1"
OUTPUT_DIR = r"C:\Users\Lenovo\Desktop\traffic_base_project\runs\pipeline_motor_helmet_v8"

# =========================
# SENSITIVITY SETTINGS (Lowered to catch more)
# =========================
MOTOR_CONF = 0.15  # MUCH LOWER to catch bikes in the distance
MOTOR_IMGSZ = 1024 # HIGHER resolution to find small bikes

HELMET_CONF = 0.25 # Lowered to catch blurry helmets
HELMET_IMGSZ = 640

ROI_PADDING = 0.50 # HUGE padding to ensure we don't miss the rider's head
HELMET_SEARCH_TOP_RATIO = 0.60 

def expand_box(x1, y1, x2, y2, img_w, img_h, padding=0.25):
    box_w, box_h = x2 - x1, y2 - y1
    pad_w, pad_h = int(box_w * padding), int(box_h * padding)
    # Expand significantly upwards for POV shots
    new_x1 = max(0, x1 - pad_w)
    new_y1 = max(0, y1 - int(box_h * 0.8)) # Search much higher above the bike
    new_x2 = min(img_w, x2 + pad_w)
    new_y2 = min(img_h, y2 + pad_h)
    return new_x1, new_y1, new_x2, new_y2

def draw_label(img, text, x1, y1, color):
    cv2.putText(img, text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

def process_image(image_path, motor_model, helmet_model, output_dir):
    image = cv2.imread(str(image_path))
    if image is None: return

    img_h, img_w = image.shape[:2]
    output_img = image.copy()
    motorcycle_count = 0
    violation_count = 0

    # 1. DETECT MOTORCYCLES (Using 1024 imgsz for better detection)
    motor_results = motor_model.predict(source=image, conf=MOTOR_CONF, imgsz=MOTOR_IMGSZ, verbose=False)[0]

    for box in motor_results.boxes:
        # REMOVED CLASS NAME FILTER: If your motor model detects it, we trust it's a bike
        motorcycle_count += 1
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        m_conf = float(box.conf[0])

        # 2. CREATE ROI
        rx1, ry1, rx2, ry2 = expand_box(x1, y1, x2, y2, img_w, img_h, ROI_PADDING)
        
        # Crop search area
        helmet_roi = image[ry1:ry1 + int((ry2-ry1)*HELMET_SEARCH_TOP_RATIO), rx1:rx2]

        if helmet_roi.size == 0: continue

        # 3. DETECT HELMETS
        h_res = helmet_model.predict(source=helmet_roi, conf=HELMET_CONF, imgsz=HELMET_IMGSZ, verbose=False)[0]
        
        has_no_helmet = False
        for hbox in h_res.boxes:
            h_name = helmet_model.names[int(hbox.cls[0])].lower()
            h_conf = float(hbox.conf[0])
            hx1, hy1, hx2, hy2 = map(int, hbox.xyxy[0])
            
            fx1, fy1, fx2, fy2 = rx1 + hx1, ry1 + hy1, rx1 + hx2, ry1 + hy2

            # LOGIC: Anything with "no" in the name is a violation
            if "no" in h_name:
                has_no_helmet = True
                cv2.rectangle(output_img, (fx1, fy1), (fx2, fy2), (0, 0, 255), 2)
                draw_label(output_img, "NO HELMET", fx1, fy1, (0, 0, 255))
            else:
                cv2.rectangle(output_img, (fx1, fy1), (fx2, fy2), (0, 255, 0), 2)

        # 4. MARK VIOLATION
        if has_no_helmet:
            violation_count += 1
            cv2.rectangle(output_img, (x1, y1), (x2, y2), (0, 0, 255), 4)
            draw_label(output_img, f"VIOLATION {m_conf:.2f}", x1, y1, (0, 0, 255))
        else:
            cv2.rectangle(output_img, (x1, y1), (x2, y2), (255, 0, 0), 2)

    # CLEANER SUMMARY
    summary = f"Bikes: {motorcycle_count} | Violations: {violation_count}"
    cv2.rectangle(output_img, (0,0), (img_w, 60), (0,0,0), -1)
    cv2.putText(output_img, summary, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)

    output_path = Path(output_dir) / image_path.name
    cv2.imwrite(str(output_path), output_img)
    print(f"Processed {image_path.name}: Found {motorcycle_count} bikes.")

def main():
    out_dir = Path(OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    m_model = YOLO(MOTOR_MODEL_PATH)
    h_model = YOLO(HELMET_MODEL_PATH)
    source = Path(SOURCE_PATH)
    images = [p for p in source.iterdir() if p.suffix.lower() in [".jpg", ".jpeg", ".png"]]
    
    for img_p in images:
        process_image(img_p, m_model, h_model, out_dir)

if __name__ == "__main__":
    main()