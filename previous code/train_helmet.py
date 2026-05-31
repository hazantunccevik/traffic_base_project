from ultralytics import YOLO
import torch

def train_model():
    # 1. Load the base YOLOv8 model
    model = YOLO('yolov8n.pt') 

    # 2. Check if you have an NVIDIA GPU
    device = 0 if torch.cuda.is_available() else 'cpu'
    print(f"Training on: {device}")

    # 3. Start training
    model.train(
        data='datasets/helmet_data/data.yaml', # Path to your fixed yaml
        epochs=50,                             # 50 is usually enough for helmets
        imgsz=640,                             # Resolution
        batch=8,     
        workers=0,                          # Decrease to 8 if your computer is slow
        device=device,                         # Uses GPU if available
        project='runs/helmet_detection',       # Where to save results
        name='v1'
    )

if __name__ == '__main__':
    train_model()