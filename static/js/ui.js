/*
This file contains helper functions that update the
dashboard user interface.

Responsibilities:
- Format confidence and processing time.
- Open and close modals.
- Show status messages.
- Reset dashboard values.
- Update output status.
- Show selected image/video preview.
*/


/*
=====================================================
Formatting Helper Functions
=====================================================
*/

/*
Converts processing time into a readable format.
*/
function formatProcessingTime(ms) {
  if (!ms || ms === 0 || ms === "-") return "0 ms";

  const numeric = parseFloat(ms);

  if (Number.isNaN(numeric)) return "0 ms";

  if (numeric >= 1000) {
    return (numeric / 1000).toFixed(2) + " s";
  }

  return Math.round(numeric) + " ms";
}


/*
Converts confidence value into percentage format.
*/
function formatConfidence(val) {
  if (val === undefined || val === null || val === "-") return "0%";

  let numeric = parseFloat(val);

  if (Number.isNaN(numeric)) return "0%";

  if (numeric < 1 && numeric > 0) {
    numeric = numeric * 100;
  }

  return Math.round(numeric) + "%";
}


/*
=====================================================
Upload Modal Functions
=====================================================
*/

/*
Opens the upload modal.
*/
function openUploadModal() {
  const { uploadModal } = window.elements;

  if (!uploadModal) return;

  uploadModal.classList.remove("hidden");
  uploadModal.classList.add("flex");
}


/*
Closes the upload modal.
*/
function closeUploadModal() {
  const { uploadModal } = window.elements;

  if (!uploadModal) return;

  uploadModal.classList.add("hidden");
  uploadModal.classList.remove("flex");
}


/*
=====================================================
Status Modal Functions
=====================================================
*/

/*
Shows a status modal.

type:
- success
- error
- info
*/
function showStatusModal(type, title, message) {
  const {
    statusModal,
    statusIcon,
    statusTitle,
    statusMessage
  } = window.elements;

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


/*
Closes the status modal.
*/
function closeStatusModal() {
  const { statusModal } = window.elements;

  if (!statusModal) return;

  statusModal.classList.add("hidden");
  statusModal.classList.remove("flex");
}


/*
=====================================================
Dashboard Reset and Status Functions
=====================================================
*/

/*
Resets detection summary and pipeline metrics.
*/
function resetDetectionValues() {
  const {
    motorcycleCount,
    helmetCount,
    violationCount,
    avgConfidence,
    processingTime,
    resolutionText,
    fileTypeText,
    outputStatus
  } = window.elements;

  if (motorcycleCount) motorcycleCount.innerText = "0";
  if (helmetCount) helmetCount.innerText = "0";
  if (violationCount) violationCount.innerText = "0";
  if (avgConfidence) avgConfidence.innerText = "0%";
  if (processingTime) processingTime.innerText = "0 ms";
  if (resolutionText) resolutionText.innerText = "-";
  if (fileTypeText) fileTypeText.innerText = "IMAGE";
  if (outputStatus) {
    outputStatus.className =
      "bg-gray-200 text-gray-700 text-[10px] font-bold px-3 py-1 rounded-md flex items-center gap-1.5";

    outputStatus.innerHTML =
      '<span class="w-1.5 h-1.5 bg-gray-500 rounded-full"></span> Waiting for Detection';
  }
}


/*
Sets the dashboard into processing state.
*/
function setProcessingState() {
  const { runDetectionBtn, outputStatus } = window.elements;

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


/*
Resets the Run Detection button after success or error.
*/
function resetRunButton() {
  const { runDetectionBtn } = window.elements;

  if (!runDetectionBtn) return;

  runDetectionBtn.disabled = false;
  runDetectionBtn.innerHTML =
    '<i class="fa-solid fa-play"></i> Run Violation Detection';
}


/*
Shows Safe output status.
*/
function setOutputStatusSafe() {
  const { outputStatus } = window.elements;

  if (!outputStatus) return;

  outputStatus.className =
    "bg-emerald-600 text-white text-[10px] font-bold px-3 py-1 rounded-md flex items-center gap-1.5";

  outputStatus.innerHTML =
    '<span class="w-1.5 h-1.5 bg-white rounded-full animate-pulse"></span> Safe';
}


/*
Shows Violation Detected output status.
*/
function setOutputStatusViolation() {
  const { outputStatus } = window.elements;

  if (!outputStatus) return;

  outputStatus.className =
    "bg-red-600 text-white text-[10px] font-bold px-3 py-1 rounded-md flex items-center gap-1.5";

  outputStatus.innerHTML =
    '<span class="w-1.5 h-1.5 bg-white rounded-full animate-pulse"></span> Violation Detected';
}


/*
Shows Error output status.
*/
function setOutputStatusError() {
  const { outputStatus } = window.elements;

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

/*
Shows selected image or video in Original Input area.
*/
function setInputPreview(file) {
  if (!file) return;

  const {
    originalInputImage,
    originalInputVideo,
    detectionOutputImage,
    detectionOutputVideo,
    originalPlaceholder,
    outputPlaceholder,
    inputStatus,
    fileTypeText
  } = window.elements;

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

    if (fileTypeText) fileTypeText.innerText = "IMAGE";

  }

  if (file.type.startsWith("video/")) {
    if (originalInputVideo) {
      originalInputVideo.src = fileUrl;
      originalInputVideo.classList.remove("hidden");
    }

    if (fileTypeText) fileTypeText.innerText = "VIDEO";
  }

  if (inputStatus) {
    inputStatus.className =
      "bg-emerald-100 text-emerald-800 text-[10px] font-bold px-3 py-1 rounded-md";

    inputStatus.innerText = "Ready";
  }

  resetDetectionValues();
}


/*
Updates resolution text for selected media.
*/
function updateResolution(file) {
  const { resolutionText } = window.elements;

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
System Status Badge
=====================================================

Updates the system status badge in the sidebar.
*/

function setSystemStatus(type, message) {
  const {
    systemStatusBadge,
    systemStatusDot,
    systemStatusText
  } = window.elements;

  if (!systemStatusBadge || !systemStatusDot || !systemStatusText) return;

  if (type === "ready") {
    systemStatusBadge.className =
      "mt-4 flex items-center gap-2 bg-emerald-100 text-emerald-800 text-[10px] font-bold px-3 py-1.5 rounded-full w-fit";

    systemStatusDot.className =
      "w-2 h-2 rounded-full bg-emerald-500 animate-pulse";

    systemStatusText.innerText = message || "SYSTEM READY";
  }

  else if (type === "checking") {
    systemStatusBadge.className =
      "mt-4 flex items-center gap-2 bg-yellow-100 text-yellow-800 text-[10px] font-bold px-3 py-1.5 rounded-full w-fit";

    systemStatusDot.className =
      "w-2 h-2 rounded-full bg-yellow-500 animate-pulse";

    systemStatusText.innerText = message || "SYSTEM CHECKING";
  }

  else {
    systemStatusBadge.className =
      "mt-4 flex items-center gap-2 bg-red-100 text-red-800 text-[10px] font-bold px-3 py-1.5 rounded-full w-fit";

    systemStatusDot.className =
      "w-2 h-2 rounded-full bg-red-500";

    systemStatusText.innerText = message || "SYSTEM ERROR";
  }
}

/*
=====================================================
Recent Uploads Toggle
=====================================================

Shows or hides the Recent Uploads card list.
This keeps the dashboard cleaner when the user does not
need to see previous uploads.
*/

function setupRecentUploadsToggle() {
  const {
    toggleRecentUploadsBtn,
    recentUploadsWrapper
  } = window.elements;

  if (!toggleRecentUploadsBtn || !recentUploadsWrapper) return;

  toggleRecentUploadsBtn.addEventListener("click", () => {
    const isHidden = recentUploadsWrapper.classList.contains("hidden");

    if (isHidden) {
      recentUploadsWrapper.classList.remove("hidden");
      toggleRecentUploadsBtn.innerText = "HIDE";
    } else {
      recentUploadsWrapper.classList.add("hidden");
      toggleRecentUploadsBtn.innerText = "SHOW";
    }
  });
}