import os # For file handling and path management
import uuid # For generating unique IDs for uploaded files and archive records

# Flask imports for web app functionality
from flask import Flask, render_template, request, jsonify, url_for

# For secure filename handling 
from werkzeug.utils import secure_filename

# Image / video processing pipelines
from pipeline2 import process_image
from video_pipeline import run_stabilized_pipeline

# Archive management functions
from archieve_man import (
    load_archive,
    add_archive_record,
    clear_archive,
    create_archive_record,
    calculate_performance_metrics
)

# Feedback management functions
from feedback_man import (
    load_feedback,
    add_or_update_feedback,
    get_feedback_by_archive_id 
)

#Main Application Setup
app = Flask(__name__)

# =========================================================
# FOLDERS
# =========================================================

UPLOAD_FOLDER = "static/uploads"
OUTPUT_FOLDER = "static/outputs"

# Create folders if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# =========================================================
# ALLOWED FILE TYPES CHECKS 
# Split filename by last dot to get extension, check if in allowed set.
# =========================================================

ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "bmp", "webp"}
ALLOWED_VIDEO_EXTENSIONS = {"mp4", "avi", "mov", "mkv", "webm"}

def allowed_image(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS
    )

def allowed_video(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS
    )

# =========================================================
# PAGES
# =========================================================
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/methodology")
def methodology():
    return render_template("methodology.html")

@app.route("/archive")
def archive():
    records = load_archive() # Load all archive records 
    feedback_records = load_feedback() # Load all feedback records

    # Map archive records with their feedback with Dictionary=(key=ID value) 
    feedback_map = {
        feedback.get("archive_id"): feedback
        for feedback in feedback_records
    }

    # Send both archive records and feedback map to template.
    return render_template(
        "archive.html",
        records=records,
        feedback_map=feedback_map
    )

@app.route("/performance")
def performance():
    records = load_archive()

    # Calculate performance metrics based on archive records and feedback.
    metrics = calculate_performance_metrics(records)
    return render_template(
        "performance.html",
        records=records,
        **metrics
    )

# =========================================================
# IMAGE DETECTION API
# This route handles image uploads from the frontend
# Runs image detection pipeline.,
# Saves result to archive.
# Create URL for input and output files, return result and summary to frontend.
# =========================================================
@app.route("/api/detect", methods=["POST"])
def detect():
    if "file" not in request.files:
        return jsonify({
            "success": False,
            "error": "No file uploaded."
        }), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({
            "success": False,
            "error": "No selected file."
        }), 400

    if not allowed_image(file.filename):
        return jsonify({
            "success": False,
            "error": "For now, only image files are supported. Please upload jpg, jpeg, png, bmp, or webp."
        }), 400

    #Secure filename and extention
    original_filename = secure_filename(file.filename)
    extension = original_filename.rsplit(".", 1)[1].lower()

    #Create unique ID, filename and paths
    file_id = str(uuid.uuid4())

    input_filename = f"{file_id}.{extension}"
    output_filename = f"{file_id}_result.jpg"

    input_path = os.path.join(UPLOAD_FOLDER, input_filename)
    output_path = os.path.join(OUTPUT_FOLDER, output_filename)

    file.save(input_path)

    # Run image processing pipeline and handle result
    try:
        summary = process_image(input_path, output_path)

        # Create URLs for input and output files to be used in frontend display.
        input_url = url_for("static", filename=f"uploads/{input_filename}")
        output_url = url_for("static", filename=f"outputs/{output_filename}")

        archive_record = create_archive_record(
            file_id=file_id,
            original_filename=original_filename,
            input_url=input_url,
            output_url=output_url,
            summary=summary,
            file_type="image"
        )

        add_archive_record(archive_record) 

        # Return the summary and URLs to the frontend for display.
        return jsonify({
            "success": True,
            "type": "image",
            "input_url": input_url,
            "output_url": output_url,
            "summary": summary,
            "record": archive_record,
            "triple_riding_detected": summary.get("triple_riding_detected", False),
            "popup_message": summary.get("popup_message", "")
        })
    #Detection error handling, return error message 
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# =========================================================
# VIDEO DETECTION API
# This route handles video uploads from the frontend
# Runs video detection pipeline.
# Saves result to archive.
# Create URL for input and output files, return result and summary to frontend.
# =========================================================

@app.route("/api/detect-video", methods=["POST"])
def detect_video():
    if "file" not in request.files:
        return jsonify({
            "success": False,
            "error": "No video file uploaded."
        }), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({
            "success": False,
            "error": "No selected video."
        }), 400

    if not allowed_video(file.filename):
        return jsonify({
            "success": False,
            "error": "Only video files are supported. Please upload mp4, avi, mov, mkv, or webm."
        }), 400

    #Secure filename and extention
    original_filename = secure_filename(file.filename)
    extension = original_filename.rsplit(".", 1)[1].lower()

    #Create unique ID, filename and paths
    file_id = str(uuid.uuid4())
    
    input_filename = f"{file_id}.{extension}"
    output_filename = f"{file_id}_result.mp4"

    input_path = os.path.join(UPLOAD_FOLDER, input_filename)
    output_path = os.path.join(OUTPUT_FOLDER, output_filename)

    file.save(input_path)

    # Run video processing pipeline and handle result
    try:
        summary = run_stabilized_pipeline(input_path, output_path)
        
        # Create URLs for input and output files to be used in frontend display.
        input_url = url_for("static", filename=f"uploads/{input_filename}")
        output_url = url_for("static", filename=f"outputs/{output_filename}")

        archive_record = create_archive_record(
            file_id=file_id,    
            original_filename=original_filename,
            input_url=input_url,
            output_url=output_url,
            summary=summary,
            file_type="video"
        )
        add_archive_record(archive_record) 
    
        # Return the summary and URLs to the frontend for display.
        return jsonify({
            "success": True,
            "type": "video",
            "input_url": input_url,
            "output_url": output_url,
            "summary": summary,
            "record": archive_record,
            "triple_riding_detected": summary.get("triple_riding_detected", False),
            "popup_message": summary.get("popup_message", "")  
        })

    #Detection error handling, return error message
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# =========================================================
# RECENT UPLOADS API
# Used by dashboard Recent Uploads section.
# Returns latest archive records.
# =========================================================

@app.route("/api/recent-uploads", methods=["GET"])
def recent_uploads():
    records = load_archive()

    return jsonify({
        "success": True,
        "uploads": records[:5]  # Return latest 5 records
    })

# =========================================================
# ARCHIVE API -  Clear Archive 
# Clears all saved archive records.
# This route is used by the Clear Archive button in archive.html.
# =========================================================

@app.route("/api/archive/clear", methods=["POST"])
def clear_archive_route():
    clear_archive()

    # Return success message to frontend 
    return jsonify({
        "success": True,
        "message": "Archive cleared successfully." 
    })

# =========================================================
# ARCHIVE FEEDBACK API
# Stores user feedback for archive records.
# =========================================================

@app.route("/api/archive/feedback", methods=["POST"])
def save_archive_feedback():
    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "No feedback data received."
        }), 400

    archive_id = data.get("archive_id")
    filename = data.get("filename")
    feedback = data.get("feedback")
    note = data.get("note", "")

    corrected_motorcycles = data.get("corrected_motorcycles")
    corrected_helmets = data.get("corrected_helmets")
    corrected_violations = data.get("corrected_violations")

    allowed_feedback = ["correct", "needs_review", "wrong_detection"]

    if not archive_id or not filename or feedback not in allowed_feedback:
        return jsonify({
            "success": False,
            "message": "Invalid feedback data."
        }), 400

    # Save feedback to JSON file
    saved_record = add_or_update_feedback(
        archive_id=archive_id,
        filename=filename,
        feedback=feedback,
        note=note,
        corrected_motorcycles=corrected_motorcycles,
        corrected_helmets=corrected_helmets,
        corrected_violations=corrected_violations
    )

    return jsonify({
        "success": True,
        "message": "Feedback saved successfully.",
        "feedback": saved_record
    })

# =========================================================
# REVIEW CANDIDATES API
# This page shows all archive records:
# "needs_review" or "wrong_detection" 
# =========================================================
@app.route("/review-candidates")
def review_candidates():
    feedback_records = load_feedback()

    wrong_records = [
        record for record in feedback_records
        if record.get("feedback") in ["needs_review", "wrong_detection"]
    ]

    correct_records = [
        record for record in feedback_records
        if record.get("feedback") == "correct"
    ]

    return render_template(
        "review_candidates.html",
        feedback_records=feedback_records,
        wrong_records=wrong_records,
        correct_records=correct_records
    )

# =========================================================
# SYSTEM HEALTH API
# Used by dashboard system status badge.
# =========================================================

@app.route("/api/system-status", methods=["GET"])
def system_status():
    return jsonify({
        "success": True,
        "status": "ready",
        "message": "SYSTEM READY"
    })

# =========================================================
# RUN APP
# =========================================================
if __name__ == "__main__":
    app.run(debug=True)