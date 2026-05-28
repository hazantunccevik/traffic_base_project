/*
=====================================================
detection.js
=====================================================

This file handles the detection process.

Responsibilities:
- Validate selected file.
- Decide image or video endpoint.
- Send file to Flask backend.
- Receive detection result.
- Update dashboard result panels.
- Reload Recent Uploads after successful detection.

Backend endpoints:
- POST /api/detect
- POST /api/detect-video
*/


/*
Sets up Run Detection button event listener.

getSelectedMediaFile:
A function that returns the currently selected file.
This is used because selectedMediaFile is stored in main.js.
*/
function setupDetectionHandler(getSelectedMediaFile) {
  const {
    runDetectionBtn
  } = window.elements;

  if (!runDetectionBtn) return;

  runDetectionBtn.addEventListener("click", async () => {
    const selectedMediaFile = getSelectedMediaFile();

    /*
    Stop if user did not select a file.
    */
    if (!selectedMediaFile) {
      showStatusModal(
        "error",
        "No Input File",
        "Please upload an image or video before running the detection pipeline."
      );

      return;
    }

    /*
    Check file type.
    */
    const isImage = selectedMediaFile.type.startsWith("image/");
    const isVideo = selectedMediaFile.type.startsWith("video/");

    /*
    Stop unsupported file types.
    */
    if (!isImage && !isVideo) {
      showStatusModal(
        "error",
        "Unsupported File Type",
        "Please upload a valid image or video file."
      );

      return;
    }

    /*
    FormData sends the selected file to backend.
    Flask expects request.files["file"].
    */
    const formData = new FormData();
    formData.append("file", selectedMediaFile);

    /*
    Update UI while backend is processing.
    */
    setProcessingState();

    try {
      /*
      Choose correct API endpoint.
      */
      const endpoint = isVideo ? "/api/detect-video" : "/api/detect";

      const response = await fetch(endpoint, {
        method: "POST",
        body: formData
      });

      const data = await response.json();

      /*
      Handle HTTP-level errors.
      */
      if (!response.ok) {
        throw new Error(data.error || "Server error.");
      }

      /*
      Handle backend-level errors.
      */
      if (!data.success) {
        throw new Error(data.error || "Detection failed.");
      }

      /*
      Process result according to file type.
      */
      if (isImage) {
        handleImageDetectionResult(data);
        showTripleRidingWarning(data);
      }

      if (isVideo) {
        handleVideoDetectionResult(data);
        showTripleRidingWarning(data);
      }

      /*
      Backend saves the result to archive_data.json.
      After successful detection, reload Recent Uploads.
      */
      loadRecentUploadsFromArchive();

    } catch (error) {
      setOutputStatusError();

      showStatusModal(
        "error",
        "Detection Error",
        error.message
      );

    } finally {
      /*
      Button must be reset after both success and error.
      */
      resetRunButton();
    }
  });
}


/*
Handles image detection result.
*/
function handleImageDetectionResult(data) {
  const {
    motorcycleCount,
    helmetCount,
    violationCount,
    avgConfidence,
    processingTime,
    resolutionText,
    fileTypeText,
    detectionOutputImage,
    detectionOutputVideo,
    outputPlaceholder
  } = window.elements;

  const summary = data.summary || {};

  /*
  Update summary values.
  */
  if (motorcycleCount) motorcycleCount.innerText = summary.motorcycles ?? 0;
  if (helmetCount) helmetCount.innerText = summary.helmets ?? 0;
  if (violationCount) violationCount.innerText = summary.violations ?? 0;
  if (avgConfidence) avgConfidence.innerText = formatConfidence(summary.avg_confidence ?? 0);
  if (processingTime) processingTime.innerText = formatProcessingTime(summary.processing_time ?? 0);
  if (resolutionText) resolutionText.innerText = summary.resolution ?? "-";
  if (fileTypeText) fileTypeText.innerText = "IMAGE";
  /*
  Hide video output because current result is image.
  */
  if (detectionOutputVideo) {
    detectionOutputVideo.classList.add("hidden");
    detectionOutputVideo.removeAttribute("src");
  }

  /*
  Show processed output image.
  Timestamp prevents browser cache issue.
  */
  if (detectionOutputImage) {
    detectionOutputImage.src = data.output_url + "?t=" + new Date().getTime();
    detectionOutputImage.classList.remove("hidden");
  }

  if (outputPlaceholder) {
    outputPlaceholder.classList.add("hidden");
  }

  /*
  Update status label.
  */
  if ((summary.violations ?? 0) > 0) {
    setOutputStatusViolation();
  } else {
    setOutputStatusSafe();
  }

  showStatusModal(
    "success",
    "Detection Completed",
    "The uploaded image was processed successfully by the YOLO helmet violation pipeline."
  );
}


/*
Handles video detection result.
*/
function handleVideoDetectionResult(data) {
  const {
    motorcycleCount,
    helmetCount,
    violationCount,
    avgConfidence,
    processingTime,
    resolutionText,
    fileTypeText,
    detectionOutputImage,
    detectionOutputVideo,
    outputPlaceholder
  } = window.elements;

  const summary = data.summary || {};

  /*
  Hide image output because current result is video.
  */
  if (detectionOutputImage) {
    detectionOutputImage.classList.add("hidden");
    detectionOutputImage.removeAttribute("src");
  }

  /*
  Show processed output video.
  Timestamp prevents browser cache issue.
  */
  if (detectionOutputVideo) {
    detectionOutputVideo.pause();

    detectionOutputVideo.innerHTML = `
      <source src="${data.output_url}?t=${new Date().getTime()}" type="video/mp4">
    `;

    detectionOutputVideo.classList.remove("hidden");
    detectionOutputVideo.load();
  }

  if (outputPlaceholder) {
    outputPlaceholder.classList.add("hidden");
  }

  /*
  Update summary values.
  */
  if (motorcycleCount) motorcycleCount.innerText = summary.motorcycles ?? 0;
  if (helmetCount) helmetCount.innerText = summary.helmets ?? 0;
  if (violationCount) violationCount.innerText = summary.violations ?? 0;
  if (avgConfidence) avgConfidence.innerText = formatConfidence(summary.avg_confidence ?? "-");
  if (processingTime) processingTime.innerText = formatProcessingTime(summary.processing_time ?? "-");
  if (resolutionText) resolutionText.innerText = summary.resolution ?? "video";
  if (fileTypeText) fileTypeText.innerText = "VIDEO";

  /*
  Update status label.
  */
  if ((summary.violations ?? 0) > 0) {
    setOutputStatusViolation();
  } else {
    setOutputStatusSafe();
  }

  showStatusModal(
    "success",
    "Video Detection Completed",
    "The uploaded video was processed successfully by the YOLO video pipeline."
  );
}