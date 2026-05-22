let selectedMediaFile = null;

const uploadImageBtn = document.getElementById("uploadImageBtn");
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

function openUploadModal() {
  uploadModal.classList.remove("hidden");
  uploadModal.classList.add("flex");
}

function closeUploadModal() {
  uploadModal.classList.add("hidden");
  uploadModal.classList.remove("flex");
}

function showStatusModal(type, title, message) {
  statusTitle.innerText = title;
  statusMessage.innerText = message;

  if (type === "success") {
    statusIcon.className =
      "w-16 h-16 mx-auto mb-5 rounded-full bg-emerald-600 text-white flex items-center justify-center";
    statusIcon.innerHTML = '<i class="fa-solid fa-check text-2xl"></i>';
  } else if (type === "error") {
    statusIcon.className =
      "w-16 h-16 mx-auto mb-5 rounded-full bg-dashboard-accentRed text-white flex items-center justify-center";
    statusIcon.innerHTML =
      '<i class="fa-solid fa-triangle-exclamation text-2xl"></i>';
  } else {
    statusIcon.className =
      "w-16 h-16 mx-auto mb-5 rounded-full bg-dashboard-accentBlue text-white flex items-center justify-center";
    statusIcon.innerHTML = '<i class="fa-solid fa-circle-info text-2xl"></i>';
  }

  statusModal.classList.remove("hidden");
  statusModal.classList.add("flex");
}

function closeStatusModal() {
  statusModal.classList.add("hidden");
  statusModal.classList.remove("flex");
}

function resetDetectionValues() {
  motorcycleCount.innerText = "0";
  helmetCount.innerText = "0";
  violationCount.innerText = "0";
  avgConfidence.innerText = "0%";
  processingTime.innerText = "0 ms";
  resolutionText.innerText = "-";

  outputStatus.className =
    "bg-gray-200 text-gray-700 text-[10px] font-bold px-3 py-1 rounded-md flex items-center gap-1.5";

  outputStatus.innerHTML =
    '<span class="w-1.5 h-1.5 bg-gray-500 rounded-full"></span> Waiting for Detection';
}

function setInputPreview(file) {
  const fileUrl = URL.createObjectURL(file);

  originalPlaceholder.classList.add("hidden");
  outputPlaceholder.classList.add("hidden");

  originalInputImage.classList.add("hidden");
  originalInputVideo.classList.add("hidden");
  detectionOutputImage.classList.add("hidden");
  detectionOutputVideo.classList.add("hidden");

  if (file.type.startsWith("image/")) {
    originalInputImage.src = fileUrl;
    detectionOutputImage.src = fileUrl;

    originalInputImage.classList.remove("hidden");
    detectionOutputImage.classList.remove("hidden");
  } else if (file.type.startsWith("video/")) {
    originalInputVideo.src = fileUrl;
    detectionOutputVideo.src = fileUrl;

    originalInputVideo.classList.remove("hidden");
    detectionOutputVideo.classList.remove("hidden");
  }

  inputStatus.className =
    "bg-emerald-100 text-emerald-800 text-[10px] font-bold px-3 py-1 rounded-md";

  inputStatus.innerText = "Ready";

  resetDetectionValues();
}

function addRecentUpload(file) {
  const recentUploads = document.getElementById("recentUploads");

  const card = document.createElement("div");

  card.className =
    "flex-none w-[170px] bg-white rounded-xl p-1.5 shadow-sm border border-gray-200/50";

  const icon = file.type.startsWith("video/") ? "fa-video" : "fa-image";

  card.innerHTML = `
    <div class="h-20 rounded-lg overflow-hidden bg-gray-100 flex items-center justify-center text-gray-400">
      <i class="fa-solid ${icon} text-3xl"></i>
    </div>

    <div class="p-2 flex items-center justify-between">
      <span class="text-[10px] font-mono font-medium text-gray-600 truncate max-w-[120px]">
        ${file.name}
      </span>
      <span class="w-2 h-2 rounded-full bg-emerald-400"></span>
    </div>
  `;

  recentUploads.insertBefore(card, newUploadCard);
}

function simulateDetectionForNow() {
  const startTime = performance.now();

  runDetectionBtn.disabled = true;
  runDetectionBtn.innerHTML =
    '<i class="fa-solid fa-spinner fa-spin"></i> Processing Pipeline...';

  outputStatus.className =
    "bg-yellow-100 text-yellow-800 text-[10px] font-bold px-3 py-1 rounded-md flex items-center gap-1.5";

  outputStatus.innerHTML =
    '<span class="w-1.5 h-1.5 bg-yellow-600 rounded-full animate-pulse"></span> Processing';

  setTimeout(() => {
    const endTime = performance.now();
    const elapsed = Math.round(endTime - startTime);

    motorcycleCount.innerText = "1";
    helmetCount.innerText = "0";
    violationCount.innerText = "1";
    avgConfidence.innerText = "82%";
    processingTime.innerText = elapsed + " ms";

    if (selectedMediaFile && selectedMediaFile.type.startsWith("image/")) {
      const tempImg = new Image();

      tempImg.onload = function () {
        resolutionText.innerText = tempImg.width + "x" + tempImg.height;
      };

      tempImg.src = URL.createObjectURL(selectedMediaFile);
    } else {
      resolutionText.innerText = "video";
    }

    outputStatus.className =
      "bg-dashboard-accentRed text-white text-[10px] font-bold px-3 py-1 rounded-md flex items-center gap-1.5";

    outputStatus.innerHTML =
      '<span class="w-1.5 h-1.5 bg-white rounded-full animate-pulse"></span> Violation Detected';

    runDetectionBtn.disabled = false;

    runDetectionBtn.innerHTML =
      '<i class="fa-solid fa-play"></i> Run Violation Detection';

    showStatusModal(
      "success",
      "Detection Completed",
      "The UI flow is working. In the next step, this button will be connected to the Flask YOLO backend and real detection results will be displayed."
    );
  }, 1200);
}

uploadImageBtn.addEventListener("click", openUploadModal);
uploadVideoBtn.addEventListener("click", openUploadModal);
newUploadCard.addEventListener("click", openUploadModal);

closeModalBtn.addEventListener("click", closeUploadModal);
cancelUploadBtn.addEventListener("click", closeUploadModal);
closeStatusModalBtn.addEventListener("click", closeStatusModal);

chooseFileBtn.addEventListener("click", () => {
  mediaInput.click();
});

mediaInput.addEventListener("change", () => {
  selectedMediaFile = mediaInput.files[0];

  if (!selectedMediaFile) {
    selectedFileName.innerText = "No file selected";
    return;
  }

  selectedFileName.innerText = selectedMediaFile.name;
});

confirmUploadBtn.addEventListener("click", () => {
  if (!selectedMediaFile) {
    showStatusModal(
      "error",
      "No File Selected",
      "Please choose an image or video first."
    );
    return;
  }

  setInputPreview(selectedMediaFile);
  addRecentUpload(selectedMediaFile);
  closeUploadModal();
});

runDetectionBtn.addEventListener("click", async () => {
  if (!selectedMediaFile) {
    showStatusModal(
      "error",
      "No Input File",
      "Please upload an image before running the detection pipeline."
    );
    return;
  }

  if (!selectedMediaFile.type.startsWith("image/")) {
    showStatusModal(
      "error",
      "Video Not Supported Yet",
      "For now, the backend supports image detection only. Video detection will be added later."
    );
    return;
  }

  const formData = new FormData();
  formData.append("file", selectedMediaFile);

  runDetectionBtn.disabled = true;
  runDetectionBtn.innerHTML =
    '<i class="fa-solid fa-spinner fa-spin"></i> Running YOLO Pipeline...';

  outputStatus.className =
    "bg-yellow-100 text-yellow-800 text-[10px] font-bold px-3 py-1 rounded-md flex items-center gap-1.5";

  outputStatus.innerHTML =
    '<span class="w-1.5 h-1.5 bg-yellow-600 rounded-full animate-pulse"></span> Processing';

  try {
    const response = await fetch("/api/detect", {
      method: "POST",
      body: formData
    });

    const data = await response.json();

    if (!data.success) {
      throw new Error(data.error || "Detection failed.");
    }

    const summary = data.summary;

    motorcycleCount.innerText = summary.motorcycles;
    helmetCount.innerText = summary.helmets;
    violationCount.innerText = summary.violations;
    avgConfidence.innerText = summary.avg_confidence + "%";
    processingTime.innerText = summary.processing_time + " ms";
    resolutionText.innerText = summary.resolution;

    detectionOutputVideo.classList.add("hidden");
    detectionOutputImage.src = data.output_url + "?t=" + new Date().getTime();
    detectionOutputImage.classList.remove("hidden");
    outputPlaceholder.classList.add("hidden");

    if (summary.violations > 0) {
      outputStatus.className =
        "bg-dashboard-accentRed text-white text-[10px] font-bold px-3 py-1 rounded-md flex items-center gap-1.5";

      outputStatus.innerHTML =
        '<span class="w-1.5 h-1.5 bg-white rounded-full animate-pulse"></span> Violation Detected';
    } else {
      outputStatus.className =
        "bg-emerald-600 text-white text-[10px] font-bold px-3 py-1 rounded-md flex items-center gap-1.5";

      outputStatus.innerHTML =
        '<span class="w-1.5 h-1.5 bg-white rounded-full animate-pulse"></span> Safe';
    }

    showStatusModal(
      "success",
      "Detection Completed",
      "The uploaded image was processed successfully by the YOLO helmet violation pipeline."
    );

  } catch (error) {
    outputStatus.className =
      "bg-red-100 text-red-800 text-[10px] font-bold px-3 py-1 rounded-md flex items-center gap-1.5";

    outputStatus.innerHTML =
      '<span class="w-1.5 h-1.5 bg-red-600 rounded-full"></span> Error';

    showStatusModal(
      "error",
      "Detection Error",
      error.message
    );

  } finally {
    runDetectionBtn.disabled = false;
    runDetectionBtn.innerHTML =
      '<i class="fa-solid fa-play"></i> Run Violation Detection';
  }
});