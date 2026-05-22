document.addEventListener("DOMContentLoaded", () => {
  /*
    =====================================================
    Dashboard Page Guard
    =====================================================
  */
  const uploadImageBtn = document.getElementById("uploadImageBtn");
  if (!uploadImageBtn) return;

  /*
    =====================================================
    Global State
    =====================================================
  */

  let selectedMediaFile = null;

  // Prevent adding the same file multiple times to Recent Uploads
  const recentUploadKeys = new Set();

  /*
    =====================================================
    Element Selectors
    =====================================================
  */

  const uploadVideoBtn = document.getElementById("uploadVideoBtn");
  const newUploadCard = document.getElementById("newUploadCard");

  const uploadModal = document.getElementById("uploadModal");
  const closeModalBtn = document.getElementById("closeModalBtn");
  const cancelUploadBtn = document.getElementById("cancelUploadBtn");
  const chooseFileBtn = document.getElementById("chooseFileBtn");
  const confirmUploadBtn = document.getElementById("confirmUploadBtn");
  const mediaInput = document.getElementById("mediaInput");
  const selectedFileName = document.getElementById("selectedFileName");

  const originalInputImage = document.getElementById("originalInputImage");
  const originalInputVideo = document.getElementById("originalInputVideo");
  const detectionOutputImage = document.getElementById("detectionOutputImage");
  const detectionOutputVideo = document.getElementById("detectionOutputVideo");

  const originalPlaceholder = document.getElementById("originalPlaceholder");
  const outputPlaceholder = document.getElementById("outputPlaceholder");

  const inputStatus = document.getElementById("inputStatus");
  const outputStatus = document.getElementById("outputStatus");

  const runDetectionBtn = document.getElementById("runDetectionBtn");

  const motorcycleCount = document.getElementById("motorcycleCount");
  const helmetCount = document.getElementById("helmetCount");
  const violationCount = document.getElementById("violationCount");
  const avgConfidence = document.getElementById("avgConfidence");
  const processingTime = document.getElementById("processingTime");
  const resolutionText = document.getElementById("resolutionText");

  const statusModal = document.getElementById("statusModal");
  const statusIcon = document.getElementById("statusIcon");
  const statusTitle = document.getElementById("statusTitle");
  const statusMessage = document.getElementById("statusMessage");
  const closeStatusModalBtn = document.getElementById("closeStatusModalBtn");
 
  /*
    =====================================================
    Formatting Helpers (The Precision Update)
    =====================================================
  */
  function formatProcessingTime(ms) {
    if (!ms || ms === 0) return "0 ms";
    if (ms >= 1000) {
      return (ms / 1000).toFixed(2) + " s";
    }
    return ms + " ms";
  }

  function formatConfidence(val) {
    if (val === undefined || val === null || val === "-") return "0%";
    // If the backend sends 0.85 instead of 85, convert it
    let numeric = parseFloat(val);
    if (numeric < 1 && numeric > 0) numeric = numeric * 100;
    return Math.round(numeric) + "%";
  }

  
  /*
    =====================================================
    Modal & UI Functions
    =====================================================
  */

  function openUploadModal() {
    if (!uploadModal) return;

    uploadModal.classList.remove("hidden");
    uploadModal.classList.add("flex");
  }

  function closeUploadModal() {
    if (!uploadModal) return;

    uploadModal.classList.add("hidden");
    uploadModal.classList.remove("flex");
  }

  function showStatusModal(type, title, message) {
    if (!statusModal || !statusIcon || !statusTitle || !statusMessage) {
      alert(message);
      return;
    }

    statusTitle.innerText = title;
    statusMessage.innerText = message;

    if (type === "success") {
      statusIcon.className =
        "w-16 h-16 mx-auto mb-5 rounded-full bg-emerald-600 text-white flex items-center justify-center";

      statusIcon.innerHTML =
        '<i class="fa-solid fa-check text-2xl"></i>';
    } else if (type === "error") {
      statusIcon.className =
        "w-16 h-16 mx-auto mb-5 rounded-full bg-dashboard-accentRed text-white flex items-center justify-center";

      statusIcon.innerHTML =
        '<i class="fa-solid fa-triangle-exclamation text-2xl"></i>';
    } else {
      statusIcon.className =
        "w-16 h-16 mx-auto mb-5 rounded-full bg-dashboard-accentBlue text-white flex items-center justify-center";

      statusIcon.innerHTML =
        '<i class="fa-solid fa-circle-info text-2xl"></i>';
    }

    statusModal.classList.remove("hidden");
    statusModal.classList.add("flex");
  }

  function closeStatusModal() {
    if (!statusModal) return;

    statusModal.classList.add("hidden");
    statusModal.classList.remove("flex");
  }

  /*
    =====================================================
    Reset / Status Helpers
    =====================================================
  */

  function resetDetectionValues() {
    if (motorcycleCount) motorcycleCount.innerText = "0";
    if (helmetCount) helmetCount.innerText = "0";
    if (violationCount) violationCount.innerText = "0";
    if (avgConfidence) avgConfidence.innerText = "0%";
    if (processingTime) processingTime.innerText = "0 ms";
    if (resolutionText) resolutionText.innerText = "-";

    if (outputStatus) {
      outputStatus.className =
        "bg-gray-200 text-gray-700 text-[10px] font-bold px-3 py-1 rounded-md flex items-center gap-1.5";

      outputStatus.innerHTML =
        '<span class="w-1.5 h-1.5 bg-gray-500 rounded-full"></span> Waiting for Detection';
    }
  }

  function setProcessingState() {
    if (runDetectionBtn) {
      runDetectionBtn.disabled = true;
      runDetectionBtn.innerHTML =
        '<i class="fa-solid fa-spinner fa-spin"></i> Running YOLO Pipeline...';
    }

    if (outputStatus) {
      outputStatus.className =
        "bg-yellow-100 text-yellow-800 text-[10px] font-bold px-3 py-1 rounded-md flex items-center gap-1.5";
      outputStatus.innerHTML =
        '<span class="w-1.5 h-1.5 bg-yellow-600 rounded-full animate-pulse"></span> Processing';
    }
  }

  function resetRunButton() {
    if (!runDetectionBtn) return;
    runDetectionBtn.disabled = false;
    runDetectionBtn.innerHTML =
      '<i class="fa-solid fa-play"></i> Run Violation Detection';
  }

  function setOutputStatusSafe() {
    if (!outputStatus) return;
    outputStatus.className =
      "bg-emerald-600 text-white text-[10px] font-bold px-3 py-1 rounded-md flex items-center gap-1.5";
    outputStatus.innerHTML =
      '<span class="w-1.5 h-1.5 bg-white rounded-full animate-pulse"></span> Safe';
  }

  function setOutputStatusViolation() {
    if (!outputStatus) return;
    outputStatus.className =
      "bg-dashboard-accentRed text-white text-[10px] font-bold px-3 py-1 rounded-md flex items-center gap-1.5";
    outputStatus.innerHTML =
      '<span class="w-1.5 h-1.5 bg-white rounded-full animate-pulse"></span> Violation Detected';
  }

  function setOutputStatusError() {
    if (!outputStatus) return;
    outputStatus.className =
      "bg-red-100 text-red-800 text-[10px] font-bold px-3 py-1 rounded-md flex items-center gap-1.5";
    outputStatus.innerHTML =
      '<span class="w-1.5 h-1.5 bg-red-600 rounded-full"></span> Error';
  }

  /*
    =====================================================
    File Preview Functions
    =====================================================
  */

  function setInputPreview(file) {
    if (!file) return;
    const fileUrl = URL.createObjectURL(file);

    if (originalPlaceholder) {
      originalPlaceholder.classList.add("hidden");
    }

    if (outputPlaceholder) {
      outputPlaceholder.classList.remove("hidden");
    }

    if (originalInputImage) {
      originalInputImage.classList.add("hidden");
      originalInputImage.removeAttribute("src");
    }

    if (originalInputVideo) {
      originalInputVideo.classList.add("hidden");
      originalInputVideo.removeAttribute("src");
    }

    if (detectionOutputImage) {
      detectionOutputImage.classList.add("hidden");
      detectionOutputImage.removeAttribute("src");
    }

    if (detectionOutputVideo) {
      detectionOutputVideo.classList.add("hidden");
      detectionOutputVideo.removeAttribute("src");
    }

    if (file.type.startsWith("image/")) {
      if (originalInputImage) {
        originalInputImage.src = fileUrl;
        originalInputImage.classList.remove("hidden");
      }
    } else if (file.type.startsWith("video/")) {
      if (originalInputVideo) {
        originalInputVideo.src = fileUrl;
        originalInputVideo.classList.remove("hidden");
      }
    }

    if (inputStatus) {
      inputStatus.className =
        "bg-emerald-100 text-emerald-800 text-[10px] font-bold px-3 py-1 rounded-md";

      inputStatus.innerText = "Ready";
    }

    resetDetectionValues();
  }

  function updateResolution(file) {
    if (!resolutionText || !file) return;

    if (file.type.startsWith("image/")) {
      const tempImg = new Image();
      const objectUrl = URL.createObjectURL(file);

      tempImg.onload = function () {
        resolutionText.innerText = tempImg.width + "x" + tempImg.height;
        URL.revokeObjectURL(objectUrl);
      };

      tempImg.src = objectUrl;
    } else {
      resolutionText.innerText = "video";
    }
  }

  /*
    =====================================================
    Recent Uploads
    =====================================================
  */

  function getFileKey(file) {
    return `${file.name}-${file.size}-${file.lastModified}`;
  }

  function addRecentUpload(file) {
    const recentUploads = document.getElementById("recentUploads");

    if (!recentUploads || !newUploadCard || !file) {
      return;
    }

    const fileKey = getFileKey(file);

    if (recentUploadKeys.has(fileKey)) {
      showStatusModal(
        "info",
        "Already Uploaded",
        "This file is already listed in Recent Uploads."
      );
      return;
    }

    recentUploadKeys.add(fileKey);

    const fileUrl = URL.createObjectURL(file);
    const isImage = file.type.startsWith("image/");
    const isVideo = file.type.startsWith("video/");

    const card = document.createElement("div");

    card.className =
      "flex-none w-[150px] bg-white rounded-xl p-1.5 shadow-sm border border-gray-200/60 cursor-pointer hover:scale-[1.02] hover:shadow-md transition-all";

    let previewHtml = "";

    if (isImage) {
      previewHtml = `
        <div class="h-20 rounded-lg overflow-hidden bg-blue-50 flex items-center justify-center">
          <img src="${fileUrl}" alt="${file.name}" class="w-full h-full object-cover">
        </div>
      `;
    } else if (isVideo) {
      previewHtml = `
        <div class="h-20 rounded-lg overflow-hidden bg-emerald-50 flex items-center justify-center text-emerald-500">
          <i class="fa-solid fa-video text-3xl"></i>
        </div>
      `;
    } else {
      previewHtml = `
        <div class="h-20 rounded-lg overflow-hidden bg-gray-100 flex items-center justify-center text-gray-400">
          <i class="fa-solid fa-file text-3xl"></i>
        </div>
      `;
    }

    card.innerHTML = `
      ${previewHtml}

      <div class="p-2 flex items-center justify-between gap-2">
        <span class="text-[10px] font-mono font-medium text-gray-600 truncate max-w-[105px]">
          ${file.name}
        </span>

        <span class="w-2 h-2 rounded-full ${
          isImage ? "bg-blue-400" : "bg-emerald-400"
        }"></span>
      </div>
    `;

    card.addEventListener("click", () => {
      selectedMediaFile = file;

      setInputPreview(file);

      if (selectedFileName) {
        selectedFileName.innerText = file.name;
      }

      showStatusModal(
        "success",
        "Upload Selected",
        "The selected recent upload is ready for detection."
      );
    });

    recentUploads.insertBefore(card, newUploadCard);
  }

  function simulateDetectionForNow() {
    const startTime = performance.now();

    setProcessingState();

    setTimeout(() => {
      const endTime = performance.now();
      const elapsed = Math.round(endTime - startTime);

      if (motorcycleCount) motorcycleCount.innerText = "1";
      if (helmetCount) helmetCount.innerText = "0";
      if (violationCount) violationCount.innerText = "1";
      if (avgConfidence) avgConfidence.innerText = "82%";
      if (processingTime) processingTime.innerText = elapsed + " ms";

      updateResolution(selectedMediaFile);

      setOutputStatusViolation();
      resetRunButton();

      showStatusModal(
        "success",
        "Detection Completed",
        "The UI flow is working. This is a frontend-only simulation."
      );
    }, 1200);
  }

  /*
    =====================================================
    Event Listeners - Upload Modal
    =====================================================
  */

  uploadImageBtn.addEventListener("click", openUploadModal);

  if (uploadVideoBtn) uploadVideoBtn.addEventListener("click", openUploadModal);
  if (newUploadCard) newUploadCard.addEventListener("click", openUploadModal);
  if (closeModalBtn) closeModalBtn.addEventListener("click", closeUploadModal);
  if (cancelUploadBtn) cancelUploadBtn.addEventListener("click", closeUploadModal);
  if (closeStatusModalBtn) closeStatusModalBtn.addEventListener("click", closeStatusModal);
  if (chooseFileBtn && mediaInput) {
    chooseFileBtn.addEventListener("click", () => {
      mediaInput.click();
    });
  }

  /*
    =====================================================
    Event Listeners - File Selection
    =====================================================
  */

  if (mediaInput && selectedFileName) {
    mediaInput.addEventListener("change", () => {
      selectedMediaFile = mediaInput.files[0];

      if (!selectedMediaFile) {
        selectedFileName.innerText = "No file selected";
        return;
      }

      selectedFileName.innerText = selectedMediaFile.name;
    });
  }

  if (confirmUploadBtn) {
    confirmUploadBtn.addEventListener("click", () => {
      if (!selectedMediaFile) return;
      const fileUrl = URL.createObjectURL(selectedMediaFile);
      if (originalPlaceholder) originalPlaceholder.classList.add("hidden");

      // Setup Preview
      if (selectedMediaFile.type.startsWith("image/")) {
        originalInputImage.src = fileUrl;
        originalInputImage.classList.remove("hidden");
        originalInputVideo.classList.add("hidden");
      } else {
        originalInputVideo.src = fileUrl;
        originalInputVideo.classList.remove("hidden");
        originalInputImage.classList.add("hidden");
      }
      closeUploadModal();
    });
  }

  /*
  =====================================================
  Event Listener - Run Detection
  =====================================================
*/

if (runDetectionBtn) {
  runDetectionBtn.addEventListener("click", async () => {
    if (!selectedMediaFile) {
      showStatusModal(
        "error",
        "No Input File",
        "Please upload an image or video before running the detection pipeline."
      );
      return;
    }

    const isImage = selectedMediaFile.type.startsWith("image/");
    const isVideo = selectedMediaFile.type.startsWith("video/");

    if (!isImage && !isVideo) {
      showStatusModal(
        "error",
        "Unsupported File Type",
        "Please upload a valid image or video file."
      );
      return;
    }

    const formData = new FormData();
    formData.append("file", selectedMediaFile);

    setProcessingState();

    try {
      const endpoint = isVideo ? "/api/detect-video" : "/api/detect";

      const response = await fetch(endpoint, {
        method: "POST",
        body: formData
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Server error.");
      }

      if (!data.success) {
        throw new Error(data.error || "Detection failed.");
      }

      if (isImage) {
        const summary = data.summary || {};

        if (motorcycleCount) motorcycleCount.innerText = summary.motorcycles ?? 0;
        if (helmetCount) helmetCount.innerText = summary.helmets ?? 0;
        if (violationCount) violationCount.innerText = summary.violations ?? 0;
        if (avgConfidence) avgConfidence.innerText = (summary.avg_confidence ?? 0) + "%";
        if (processingTime) processingTime.innerText = (summary.processing_time ?? 0) + " ms";
        if (resolutionText) resolutionText.innerText = summary.resolution ?? "-";

        if (detectionOutputVideo) {
          detectionOutputVideo.classList.add("hidden");
          detectionOutputVideo.removeAttribute("src");
        }

        if (detectionOutputImage) {
          detectionOutputImage.src = data.output_url + "?t=" + new Date().getTime();
          detectionOutputImage.classList.remove("hidden");
        }

        if (outputPlaceholder) {
          outputPlaceholder.classList.add("hidden");
        }

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

      if (isVideo) {
         const summary = data.summary || {};
         
        if (detectionOutputImage) {
          detectionOutputImage.classList.add("hidden");
          detectionOutputImage.removeAttribute("src");
        }

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

        if (motorcycleCount) motorcycleCount.innerText =  summary.motorcycles ?? 0;
        if (helmetCount) helmetCount.innerText = summary.helmets ?? 0;
        if (violationCount) violationCount.innerText = summary.violations ?? 0;
        if (avgConfidence) avgConfidence.innerText = formatConfidence(summary.avg_confidence ?? "-");
        if (processingTime) processingTime.innerText = formatProcessingTime(summary.processing_time ?? "-");
        if (resolutionText) resolutionText.innerText = summary.resolution ?? "video";

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
    } catch (error) {
      setOutputStatusError();

      showStatusModal(
        "error",
        "Detection Error",
        error.message
      );
    } finally {
      resetRunButton();
    }
  });
}

});