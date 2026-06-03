from ultralytics import YOLO
import torch

def train_model():
    # Existing helmet model
    model_path = r"C:\Users\Lenovo\Desktop\traffic_base_project\runs\detect_helmet_detect\runs\helmet_detection\v12\weights\best.pt"
    model = YOLO(model_path)

    # Check for GPU
    device = 0 if torch.cuda.is_available() else "cpu"
    print(f"Training on: {device}")

    # Fine-tuning
    model.train(
        data=r"C:\Users\Lenovo\Desktop\traffic_base_project\datasets\helmet_data_v2\data.yaml",
        epochs=50,
        imgsz=640,
        batch=8,
        workers=0,
        device=device,
        project=r"C:\Users\Lenovo\Desktop\traffic_base_project\runs\helmet_detection2",
        name="v1",
        patience=15
    )

if __name__ == "__main__":
    train_model()