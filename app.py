import os
import uuid
from flask import Flask, render_template, request, jsonify, url_for
from werkzeug.utils import secure_filename

from pipeline2 import process_image


app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
OUTPUT_FOLDER = "static/outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "bmp", "webp"}


def allowed_image(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS
    )


@app.route("/")
def home():
    return render_template("index.html")


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

    original_filename = secure_filename(file.filename)
    extension = original_filename.rsplit(".", 1)[1].lower()

    file_id = str(uuid.uuid4())

    input_filename = f"{file_id}.{extension}"
    output_filename = f"{file_id}_result.jpg"

    input_path = os.path.join(UPLOAD_FOLDER, input_filename)
    output_path = os.path.join(OUTPUT_FOLDER, output_filename)

    file.save(input_path)

    try:
        summary = process_image(input_path, output_path)

        return jsonify({
            "success": True,
            "input_url": url_for("static", filename=f"uploads/{input_filename}"),
            "output_url": url_for("static", filename=f"outputs/{output_filename}"),
            "summary": summary
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


if __name__ == "__main__":
    app.run(debug=True)