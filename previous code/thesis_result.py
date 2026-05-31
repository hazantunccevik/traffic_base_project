import os
import json
import glob
from pathlib import Path
from statistics import mean

import pandas as pd
import yaml


# ==============================
# EDIT THESE PATHS IF NEEDED
# ==============================

PROJECT_ROOT = Path(r"C:\Users\Lenovo\Desktop\traffic_base_project")

HELMET_DATA_YAML = PROJECT_ROOT / "datasets" / "helmet_data" / "data.yaml"

# Eğer motorcycle dataset data.yaml farklı yerdeyse burayı düzelt.
MOTORCYCLE_DATA_YAML = PROJECT_ROOT / "datasets" / "motorbike_rf" / "data.yaml"

# Helmet training result klasörü. results.csv, confusion_matrix.png burada olmalı.
HELMET_RUN_DIR = PROJECT_ROOT / "runs" / "helmet_detection2" / "v1"

# Eğer motorcycle training result klasörün varsa burayı düzelt.
MOTORCYCLE_RUN_DIR = PROJECT_ROOT / "runs" / "motorcycle_finetune" / "v1"

ARCHIVE_FILE = PROJECT_ROOT / "archive_data.json"


# ==============================
# HELPER FUNCTIONS
# ==============================

def resolve_dataset_path(data_yaml_path, value):
    """
    data.yaml içindeki train/val/test pathlerini çözer.
    Relative path varsa data.yaml klasörüne göre tamamlar.
    """
    if value is None:
        return None

    if isinstance(value, list):
        return [resolve_dataset_path(data_yaml_path, v) for v in value]

    value_path = Path(str(value))

    if value_path.is_absolute():
        return value_path

    return (data_yaml_path.parent / value_path).resolve()


def count_images(path_value):
    """
    Verilen klasör veya liste içindeki image sayısını sayar.
    """
    if path_value is None:
        return 0

    if isinstance(path_value, list):
        return sum(count_images(p) for p in path_value)

    path_value = Path(path_value)

    if not path_value.exists():
        return 0

    image_exts = ["*.jpg", "*.jpeg", "*.png", "*.bmp", "*.webp"]

    if path_value.is_file():
        return 1 if path_value.suffix.lower() in [".jpg", ".jpeg", ".png", ".bmp", ".webp"] else 0

    total = 0
    for ext in image_exts:
        total += len(list(path_value.rglob(ext)))

    return total


def analyze_dataset(name, data_yaml_path):
    print(f"\n==============================")
    print(f"{name} DATASET SPLIT")
    print(f"==============================")

    if not data_yaml_path.exists():
        print(f"data.yaml not found: {data_yaml_path}")
        return None

    with open(data_yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    train_path = resolve_dataset_path(data_yaml_path, data.get("train"))
    val_path = resolve_dataset_path(data_yaml_path, data.get("val"))
    test_path = resolve_dataset_path(data_yaml_path, data.get("test"))

    train_count = count_images(train_path)
    val_count = count_images(val_path)
    test_count = count_images(test_path)

    names = data.get("names", [])
    if isinstance(names, dict):
        classes = list(names.values())
    else:
        classes = names

    print("data.yaml:", data_yaml_path)
    print("Classes:", classes)
    print("Train images:", train_count, "| path:", train_path)
    print("Validation images:", val_count, "| path:", val_path)
    print("Test images:", test_count, "| path:", test_path)

    return {
        "dataset": name,
        "train": train_count,
        "val": val_count,
        "test": test_count,
        "classes": classes
    }


def analyze_results_csv(name, run_dir):
    print(f"\n==============================")
    print(f"{name} TRAINING METRICS")
    print(f"==============================")

    csv_path = run_dir / "results.csv"

    if not csv_path.exists():
        print(f"results.csv not found: {csv_path}")
        return None

    df = pd.read_csv(csv_path)
    df.columns = [c.strip() for c in df.columns]

    print("results.csv:", csv_path)
    print("Columns:")
    for col in df.columns:
        print(" -", col)

    # Ultralytics column names usually contain these
    precision_col = next((c for c in df.columns if "metrics/precision" in c), None)
    recall_col = next((c for c in df.columns if "metrics/recall" in c), None)
    map50_col = next((c for c in df.columns if "metrics/mAP50(" in c), None)
    map5095_col = next((c for c in df.columns if "metrics/mAP50-95" in c), None)

    metric_cols = {
        "Precision": precision_col,
        "Recall": recall_col,
        "mAP50": map50_col,
        "mAP50-95": map5095_col
    }

    final_row = df.iloc[-1]
    summary = {}

    print("\nMetric Summary:")
    for label, col in metric_cols.items():
        if col is None:
            print(f"{label}: column not found")
            continue

        best_value = float(df[col].max())
        final_value = float(final_row[col])
        best_epoch = int(df[col].idxmax() + 1)

        summary[label] = {
            "best": best_value,
            "best_epoch": best_epoch,
            "final": final_value
        }

        print(f"{label}: best={best_value:.5f} at epoch {best_epoch}, final={final_value:.5f}")

    # Loss final values
    print("\nFinal Loss Values:")
    for col in df.columns:
        if "loss" in col:
            print(f"{col}: {float(final_row[col]):.5f}")

    return summary


def check_run_images(name, run_dir):
    print(f"\n==============================")
    print(f"{name} RESULT IMAGES")
    print(f"==============================")

    image_names = [
        "results.png",
        "confusion_matrix.png",
        "confusion_matrix_normalized.png",
        "F1_curve.png",
        "P_curve.png",
        "R_curve.png",
        "PR_curve.png"
    ]

    found = []
    for img_name in image_names:
        img_path = run_dir / img_name
        if img_path.exists():
            found.append(img_path)
            print("FOUND:", img_path)
        else:
            print("MISSING:", img_path)

    return found


def analyze_archive():
    print(f"\n==============================")
    print("SYSTEM PERFORMANCE / ARCHIVE DATA")
    print(f"==============================")

    if not ARCHIVE_FILE.exists():
        print(f"archive_data.json not found: {ARCHIVE_FILE}")
        return None

    with open(ARCHIVE_FILE, "r", encoding="utf-8") as f:
        records = json.load(f)

    print("Total records:", len(records))

    confidences = []
    times = []

    total_motorcycles = 0
    total_helmets = 0
    total_violations = 0

    image_times = []
    video_times = []

    print("\nRecent Records:")
    for r in records:
        filename = r.get("original_filename", "unknown")
        file_type = r.get("type", "unknown")

        motorcycles = int(r.get("motorcycles", 0))
        helmets = int(r.get("helmets", 0))
        violations = int(r.get("violations", 0))

        confidence = r.get("avg_confidence", r.get("confidence", 0))
        processing_time = r.get("processing_time", r.get("time", 0))

        try:
            confidence = float(confidence)
        except Exception:
            confidence = 0

        try:
            processing_time = float(processing_time)
        except Exception:
            processing_time = 0

        confidences.append(confidence)
        times.append(processing_time)

        if file_type == "image":
            image_times.append(processing_time)
        elif file_type == "video":
            video_times.append(processing_time)

        total_motorcycles += motorcycles
        total_helmets += helmets
        total_violations += violations

        print(
            f"{filename} | type: {file_type} | motorcycles: {motorcycles} "
            f"| helmets: {helmets} | violations: {violations} "
            f"| confidence: {confidence}% | time: {int(processing_time)} ms"
        )

    print("\nPerformance Summary:")
    print("Total motorcycles:", total_motorcycles)
    print("Total helmets:", total_helmets)
    print("Total violations:", total_violations)
    print("Average confidence:", round(mean(confidences), 2) if confidences else 0, "%")
    print("Average processing time:", round(mean(times), 2) if times else 0, "ms")

    if image_times:
        print("Average image processing time:", round(mean(image_times), 2), "ms")
    if video_times:
        print("Average video processing time:", round(mean(video_times), 2), "ms")

    return records


def find_output_examples():
    print(f"\n==============================")
    print("OUTPUT EXAMPLE FILES")
    print(f"==============================")

    possible_dirs = [
        PROJECT_ROOT / "static" / "outputs",
        PROJECT_ROOT / "outputs",
        PROJECT_ROOT / "runs"
    ]

    image_exts = ["*.jpg", "*.jpeg", "*.png", "*.webp"]
    video_exts = ["*.mp4", "*.avi", "*.mov"]

    found_images = []
    found_videos = []

    for d in possible_dirs:
        if not d.exists():
            continue

        for ext in image_exts:
            found_images.extend(d.rglob(ext))
        for ext in video_exts:
            found_videos.extend(d.rglob(ext))

    print("\nExample output images:")
    for p in found_images[:10]:
        print(p)

    print("\nExample output videos:")
    for p in found_videos[:10]:
        print(p)

    if not found_images and not found_videos:
        print("No output examples found in common output folders.")


# ==============================
# MAIN
# ==============================

if __name__ == "__main__":
    analyze_dataset("Helmet Detection", HELMET_DATA_YAML)
    analyze_dataset("Motorcycle Detection", MOTORCYCLE_DATA_YAML)

    analyze_results_csv("Helmet Detection", HELMET_RUN_DIR)
    analyze_results_csv("Motorcycle Detection", MOTORCYCLE_RUN_DIR)

    check_run_images("Helmet Detection", HELMET_RUN_DIR)
    check_run_images("Motorcycle Detection", MOTORCYCLE_RUN_DIR)

    analyze_archive()
    find_output_examples()