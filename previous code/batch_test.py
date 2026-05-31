import os
import uuid
import shutil
from datetime import datetime

from pipeline2 import process_image
from video_pipeline import run_stabilized_pipeline
from archieve_man import create_archive_record, add_archive_record


UPLOAD_FOLDER = "static/uploads"
OUTPUT_FOLDER = "static/outputs"
TEST_FOLDER = "datasets/test_data"

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}


os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def is_image(filename):
    return os.path.splitext(filename)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


def is_video(filename):
    return os.path.splitext(filename)[1].lower() in ALLOWED_VIDEO_EXTENSIONS


def normalize_summary(summary):
    """
    Makes sure all expected values exist.
    Adjust key names here if your pipeline uses different names.
    """
    return {
        "motorcycles": summary.get("motorcycles", 0),
        "helmets": summary.get("helmets", 0),
        "violations": summary.get("violations", 0),
        "helmet_violations": summary.get("helmet_violations", summary.get("violations", 0)),
        "triple_riding": summary.get("triple_riding", 0),
        "confidence": summary.get("confidence", 0),
        "processing_time": summary.get("processing_time", 0),
    }


def process_file(file_path):
    original_filename = os.path.basename(file_path)
    extension = os.path.splitext(original_filename)[1].lower()

    file_id = str(uuid.uuid4())
    uploaded_filename = f"{file_id}_{original_filename}"

    input_path = os.path.join(UPLOAD_FOLDER, uploaded_filename)
    shutil.copy(file_path, input_path)

    if is_image(original_filename):
        file_type = "image"
        output_filename = f"output_{uploaded_filename}"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        summary = process_image(input_path, output_path)

    elif is_video(original_filename):
        file_type = "video"
        output_filename = f"output_{os.path.splitext(uploaded_filename)[0]}.mp4"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        summary = run_stabilized_pipeline(input_path, output_path)

    else:
        print(f"Skipped unsupported file: {original_filename}")
        return

    summary = normalize_summary(summary)

    input_url = f"/static/uploads/{uploaded_filename}"
    output_url = f"/static/outputs/{output_filename}"

    record = create_archive_record(
        file_id=file_id,
        original_filename=original_filename,
        input_url=input_url,
        output_url=output_url,
        summary=summary,
        file_type=file_type
    )

    add_archive_record(record)

    print(f"Processed: {original_filename}")
    print(f"  Type: {file_type}")
    print(f"  Motorcycles: {summary['motorcycles']}")
    print(f"  Helmets: {summary['helmets']}")
    print(f"  Helmet Violations: {summary['helmet_violations']}")
    print(f"  Triple Riding: {summary['triple_riding']}")
    print(f"  Confidence: {summary['confidence']}")
    print(f"  Time: {summary['processing_time']} ms")
    print("-" * 50)


def main():
    if not os.path.exists(TEST_FOLDER):
        print(f"Test folder not found: {TEST_FOLDER}")
        return

    files = [
        os.path.join(TEST_FOLDER, file)
        for file in os.listdir(TEST_FOLDER)
        if os.path.isfile(os.path.join(TEST_FOLDER, file))
    ]

    if not files:
        print("No files found in test_dataset folder.")
        return

    print(f"Found {len(files)} files.")
    print("Starting batch test...")
    print("=" * 50)

    for file_path in files:
        process_file(file_path)

    print("Batch test completed.")
    print("Results were added to archive_data.json.")


if __name__ == "__main__":
    main()