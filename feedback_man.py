import os
import json
from datetime import datetime


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FEEDBACK_FILE = os.path.join(BASE_DIR, "feedback_data.json")

# Load feedback records from JSON file
def load_feedback():
    if not os.path.exists(FEEDBACK_FILE):
        return []

    try:
        with open(FEEDBACK_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    except json.JSONDecodeError:
        return []

    except Exception:
        return []

# Save feedback records into JSON file
def save_feedback(records):
    with open(FEEDBACK_FILE, "w", encoding="utf-8") as file:
        json.dump(records, file, indent=4, ensure_ascii=False)


def add_or_update_feedback(
    archive_id,
    filename,
    feedback,
    note="",
    corrected_motorcycles=None,
    corrected_helmets=None,
    corrected_violations=None
):
    records = load_feedback()

    new_record = {
        "archive_id": archive_id,
        "filename": filename,
        "feedback": feedback,
        "note": note,
        "corrected_motorcycles": corrected_motorcycles,
        "corrected_helmets": corrected_helmets,
        "corrected_violations": corrected_violations,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    updated = False # Check if feedback for the same archive_id exists
    # If feedback for the same archive_id exists, update it
    for index, record in enumerate(records):
        if record.get("archive_id") == archive_id: 
            records[index] = new_record
            updated = True
            break
    # if not, add new record
    if not updated:
        records.insert(0, new_record)

    save_feedback(records)

    return new_record

# To search by archive_id when user clicks "View Feedback" button
def get_feedback_by_archive_id(archive_id):
    records = load_feedback()

    for record in records:
        if record.get("archive_id") == archive_id:
            return record

    return None