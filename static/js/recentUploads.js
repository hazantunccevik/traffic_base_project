/*
This file manages the Recent Uploads section.

Responsibilities:
- Load archive records from Flask backend.
- Create recent upload cards.
- Display selected archive record on dashboard.

Backend endpoint used:
GET /api/recent-uploads
*/

/*
Stores the currently selected Recent Upload card.
It is used to remove the selected style from the previous card
when the user selects another upload.
*/
let selectedRecentUploadCard = null;

/*
Loads recent upload records from backend archive.

Backend reads archive_data.json and returns the latest records.
*/
async function loadRecentUploadsFromArchive() {
  const {
    recentUploads,
    newUploadCard
  } = window.elements;

  if (!recentUploads || !newUploadCard) return;

  try {
    const response = await fetch("/api/recent-uploads");
    const data = await response.json();

    if (!data.success) return;

    /*
    Clear current cards to avoid duplicates.
    Then add New Upload card again.
    */
    recentUploads.innerHTML = "";
    recentUploads.appendChild(newUploadCard);

    const uploads = (data.uploads || []).slice(0, 5);

    uploads.forEach((upload) => {
      const card = createRecentUploadCard(upload);
      recentUploads.insertBefore(card, newUploadCard);
    });

  } catch (error) {
    console.error("Recent uploads could not be loaded:", error);
  }
}


/*
Creates a visual card for one archived upload.
*/
function createRecentUploadCard(upload) {
  const card = document.createElement("div");

  card.className =
    "flex-none w-[150px] bg-white rounded-xl p-1.5 shadow-sm border border-gray-200/60 cursor-pointer hover:scale-[1.02] hover:shadow-md transition-all";

  const isImage = upload.type === "image";
  const isVideo = upload.type === "video";

  let previewHtml = "";

  /*
  Image record:
  Use processed output image as card thumbnail.
  */
  if (isImage) {
    previewHtml = `
      <div class="h-20 rounded-lg overflow-hidden bg-blue-50 flex items-center justify-center">
        <img src="${upload.output_url}" alt="${upload.original_filename}" class="w-full h-full object-cover">
      </div>
    `;
  }

  /*
  Video record:
  Show video icon instead of loading video as thumbnail.
  */
  else if (isVideo) {
    previewHtml = `
      <div class="h-20 rounded-lg overflow-hidden bg-emerald-50 flex items-center justify-center text-emerald-500">
        <i class="fa-solid fa-video text-3xl"></i>
      </div>
    `;
  }

  /*
  Fallback for unexpected file types.
  */
  else {
    previewHtml = `
      <div class="h-20 rounded-lg overflow-hidden bg-gray-100 flex items-center justify-center text-gray-400">
        <i class="fa-solid fa-file text-3xl"></i>
      </div>
    `;
  }

  card.innerHTML = `
    ${previewHtml}

    <div class="p-2">
      <p class="text-[10px] font-mono font-medium text-gray-700 truncate">
        ${upload.original_filename}
      </p>

      <div class="flex items-center justify-between mt-1">
        <span class="text-[9px] font-bold ${
          upload.violations > 0 ? "text-red-700" : "text-emerald-700"
        }">
          ${upload.violations} violation
        </span>

        <span class="w-2 h-2 rounded-full ${
          isImage ? "bg-blue-400" : "bg-emerald-400"
        }"></span>
      </div>
    </div>
  `;

  /*
  When card is clicked, show this archived result
  on the dashboard.
  */
  card.addEventListener("click", () => {
  /*
  First, remove selected style from the previously selected card.
  This ensures that only one Recent Upload card appears selected.
  */
  clearSelectedRecentUploadCard();

  /*
  Then, apply selected style to the clicked card.
  The border color changes according to the violation result.
  */
  markRecentUploadCardAsSelected(card, upload);

  /*
  Finally, show this archive record on the dashboard.
  */
  showArchiveRecordOnDashboard(upload);
});
  return card;
}

/*
Removes selected style from the previously selected Recent Upload card.
*/
function clearSelectedRecentUploadCard() {
  if (!selectedRecentUploadCard) return;

  selectedRecentUploadCard.classList.remove(
    "ring-2",
    "ring-blue-300",
    "ring-red-300",
    "ring-emerald-300",
    "border-blue-500",
    "border-red-500",
    "border-emerald-500",
    "scale-[1.03]",
    "shadow-lg"
  );

  selectedRecentUploadCard.classList.add(
    "border-gray-200/60",
    "shadow-sm"
  );

  selectedRecentUploadCard = null;
}


/*
Applies selected style to the clicked Recent Upload card.

If violation count is greater than 0:
- red border is used.

If there is no violation:
- green border is used.
*/
function markRecentUploadCardAsSelected(card, upload) {
  if (!card || !upload) return;

  card.classList.remove(
    "border-gray-200/60",
    "shadow-sm"
  );

  card.classList.add(
    "ring-2",
    "scale-[1.03]",
    "shadow-lg"
  );

  if ((upload.violations ?? 0) > 0) {
    card.classList.add(
      "border-red-500",
      "ring-red-300"
    );
  } else {
    card.classList.add(
      "border-emerald-500",
      "ring-emerald-300"
    );
  }

  selectedRecentUploadCard = card;
}

/*
Displays selected archive record on dashboard.

This function updates:
- Original Input
- Detection Output
- Detection Summary
- Pipeline Metrics
- Status labels
*/
function showArchiveRecordOnDashboard(upload) {
  if (!upload) return;

  const {
    originalPlaceholder,
    outputPlaceholder,
    originalInputImage,
    originalInputVideo,
    detectionOutputImage,
    detectionOutputVideo,
    motorcycleCount,
    helmetCount,
    violationCount,
    avgConfidence,
    processingTime,
    resolutionText,
    fileTypeText,
    inputStatus
  } = window.elements;

  /*
  Hide placeholders because archived media will be shown.
  */
  if (originalPlaceholder) originalPlaceholder.classList.add("hidden");
  if (outputPlaceholder) outputPlaceholder.classList.add("hidden");

  /*
  Clear all previous media.
  This prevents image/video overlap.
  */
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

  /*
  Show archived image input and output.
  */
  if (upload.type === "image") {
    if (originalInputImage) {
      originalInputImage.src = upload.input_url;
      originalInputImage.classList.remove("hidden");
    }

    if (detectionOutputImage) {
      detectionOutputImage.src = upload.output_url;
      detectionOutputImage.classList.remove("hidden");
    }
  }

  /*
  Show archived video input and output.
  */
  if (upload.type === "video") {
    if (originalInputVideo) {
      originalInputVideo.src = upload.input_url;
      originalInputVideo.classList.remove("hidden");
      originalInputVideo.load();
    }

    if (detectionOutputVideo) {
      detectionOutputVideo.innerHTML = `
        <source src="${upload.output_url}" type="video/mp4">
      `;

      detectionOutputVideo.classList.remove("hidden");
      detectionOutputVideo.load();
    }
  }

  /*
  Update detection summary and pipeline metrics.
  */
  if (motorcycleCount) motorcycleCount.innerText = upload.motorcycles ?? 0;
  if (helmetCount) helmetCount.innerText = upload.helmets ?? 0;
  if (violationCount) violationCount.innerText = upload.violations ?? 0;
  if (avgConfidence) avgConfidence.innerText = formatConfidence(upload.avg_confidence ?? 0);
  if (processingTime) processingTime.innerText = formatProcessingTime(upload.processing_time ?? 0);
  if (resolutionText) resolutionText.innerText = upload.resolution ?? "-";
  if (fileTypeText) fileTypeText.innerText = upload.type.toUpperCase();
  /*
  Update input status.
  */
  if (inputStatus) {
    inputStatus.className =
      "bg-emerald-100 text-emerald-800 text-[10px] font-bold px-3 py-1 rounded-md";

    inputStatus.innerText = "Loaded from Archive";
  }

  /*
  Update output status according to violation result.
  */
  if ((upload.violations ?? 0) > 0) {
    setOutputStatusViolation();
  } else {
    setOutputStatusSafe();
  }
}