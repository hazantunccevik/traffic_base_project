import os
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARCHIVE_FILE = os.path.join(BASE_DIR, "archive_data.json")

# Load archive records from JSON file
def load_archive():
    if not os.path.exists(ARCHIVE_FILE):
        return []

    try:
        # Load the archive data from the JSON file - reading without trouble with turkish char.
        with open(ARCHIVE_FILE, "r", encoding="utf-8") as file:
            return json.load(file) # JSON -> Python dictİonary

    except json.JSONDecodeError:
        return []

    except Exception:
        return []

# Save to archive records into JSON file 
def save_archive(records):
    with open(ARCHIVE_FILE, "w", encoding="utf-8") as file:
        json.dump(records, file, indent=4, ensure_ascii=False)


def add_archive_record(record):
    records = load_archive()
    records.insert(0, record)
    save_archive(records)


def clear_archive():
    save_archive([])


# After detection 
def create_archive_record(
    file_id,
    original_filename,
    input_url,
    output_url,
    summary,
    file_type
):
    return {
        "id": file_id,
        "type": file_type,
        "original_filename": original_filename,
        "input_url": input_url,
        "output_url": output_url,

        "motorcycles": summary.get("motorcycles", 0),
        "helmets": summary.get("helmets", 0),
        "violations": summary.get("violations", 0),
        "triple_riding": summary.get("triple_riding", 0),
        "triple_riding_detected": summary.get("triple_riding_detected", False),

        # Check Labelling Logic: If triple riding is detected
        "checks": summary.get("checks", summary.get("triple_riding", 0)),
        "needs_check": summary.get("triple_riding_detected", False),
        "check_reason": (
            "Triple Riding"
            if summary.get("triple_riding_detected", False)
            else ""
        ),

        "avg_confidence": summary.get("avg_confidence", 0),
        "processing_time": summary.get("processing_time", 0),
        "resolution": summary.get("resolution", "-"),
        "model": summary.get("model", "YOLO ROI Pipeline"),

        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


# Calculate performance metrics for Performance Metrics page
def calculate_performance_metrics(records):

    total_records = len(records)
    total_motorcycles = sum(item.get("motorcycles", 0) for item in records)
    total_helmets = sum(item.get("helmets", 0) for item in records)
    total_violations = sum(item.get("violations", 0) for item in records)
    total_checks = sum(item.get("checks", 0) for item in records)

    if total_records > 0:
        avg_confidence = round(
            sum(item.get("avg_confidence", 0) for item in records) / total_records
        )

        avg_processing_time = round(
            sum(item.get("processing_time", 0) for item in records) / total_records
        )
    else:
        avg_confidence = 0
        avg_processing_time = 0

    # Prepare data for charts - reverse order for chronological display
    chart_labels = [
        item.get("original_filename", f"Record {index + 1}")
        for index, item in enumerate(records)
    ][::-1]

    chart_motorcycles = [
        item.get("motorcycles", 0)
        for item in records
    ][::-1]

    chart_violations = [
        item.get("violations", 0)
        for item in records
    ][::-1]

    chart_checks = [
        item.get("checks", 0)
        for item in records
    ][::-1]

    chart_confidence = [
        item.get("avg_confidence", 0)
        for item in records
    ][::-1]

    chart_processing_time = [
        item.get("processing_time", 0)
        for item in records
    ][::-1]

    # Return the calculated metrics through app.py to performance.html
    return {
        "total_records": total_records,
        "total_motorcycles": total_motorcycles,
        "total_helmets": total_helmets,
        "total_violations": total_violations,
        "total_checks": total_checks,
        "avg_confidence": avg_confidence,
        "avg_processing_time": avg_processing_time,
        "chart_labels": chart_labels,
        "chart_motorcycles": chart_motorcycles,
        "chart_violations": chart_violations,
        "chart_checks": chart_checks,
        "chart_confidence": chart_confidence,
        "chart_processing_time": chart_processing_time
    }