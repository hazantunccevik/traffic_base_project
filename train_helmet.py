from ultralytics import YOLO
import torch

def train_model():
    model = YOLO('yolov8n.pt') 

    # Check for GPU
    device = 0 if torch.cuda.is_available() else 'cpu'
    print(f"Training on: {device}")

    # Training
    model.train(
        data='datasets/helmet_data/data.yaml', 
        epochs=50,                             # 50 is usually enough for helmets
        imgsz=640,                             # Resolution for helmet detection
        batch=8,                               # Every step will process 8 images (adjust based on your GPU)
        workers=0,                             # Decrease to 8 if your computer is slow
        device=device,                         # Uses GPU if available
        project='runs/helmet_detection',       # Where to save results
        name='v1'
    )

if __name__ == '__main__':
    train_model()