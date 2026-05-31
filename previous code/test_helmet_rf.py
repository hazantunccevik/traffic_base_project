from ultralytics import YOLO
from pathlib import Path
from multiprocessing import freeze_support


def main():
    # Kullanmak istediğin eğitilmiş model
    model_path = Path(r"runs/detect/runs/detect/motorbike_rf_best_v1/weights/best.pt")

    # Test edilecek görüntü klasörü
    source_path = Path(r"datasets/CCTV_helmet_ware/test/images")

    print("Using model:", model_path.resolve())
    print("model exists:", model_path.exists())

    print("Using source:", source_path.resolve())
    print("source exists:", source_path.exists())

    model = YOLO(str(model_path))

    results = model.predict(
        source=str(source_path),
        conf=0.25,              # istersen sonra artırırız
        imgsz=640,
        device=0,
        save=True,              # tahminli görselleri kaydeder
        save_txt=True,          # txt prediction dosyalarını da kaydeder
        save_conf=True,         # txt içinde confidence da yazar
        project="runs/detect",
        name="helmet_ware_test_v1",
        exist_ok=True,          # aynı klasöre tekrar yazabilsin
        show=False
    )

    print("Prediction finished.")
    print("Saved to: runs/detect/helmet_ware_test_v1")
    return results


if __name__ == "__main__":
    freeze_support()
    main()