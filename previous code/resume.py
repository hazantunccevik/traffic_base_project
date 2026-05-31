from ultralytics import YOLO

def resume_training():
    last_model_path = r"C:\Users\Lenovo\Desktop\traffic_base_project\runs\helmet_detection2\v1\weights\last.pt"

    model = YOLO(last_model_path)

    model.train(
        resume=True
    )

if __name__ == "__main__":
    resume_training()