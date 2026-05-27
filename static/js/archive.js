/*
=====================================================
archive.js
=====================================================

Handles Archive page interactions:
- Image preview modal
- Clear archive button
- Archive filtering
- Detail toggle
- Feedback and correction panel
=====================================================
*/

/*
=====================================================
Image Preview Modal
=====================================================
*/

const imageModal = document.getElementById("imageModal");
const modalImage = document.getElementById("modalImage");
const clearArchiveBtn = document.getElementById("clearArchiveBtn");

function openImageModal(imageUrl) {
  if (!imageModal || !modalImage) return;

  modalImage.src = imageUrl;
  imageModal.classList.remove("hidden");
  imageModal.classList.add("flex");
}

function closeImageModal() {
  if (!imageModal || !modalImage) return;

  imageModal.classList.add("hidden");
  imageModal.classList.remove("flex");
  modalImage.src = "";
}

window.openImageModal = openImageModal;
window.closeImageModal = closeImageModal;

if (imageModal) {
  imageModal.addEventListener("click", function (event) {
    if (event.target === imageModal) {
      closeImageModal();
    }
  });
}

/*
=====================================================
Clear Archive
=====================================================
*/

if (clearArchiveBtn) {
  clearArchiveBtn.addEventListener("click", async function () {
    const confirmed = confirm("Are you sure you want to clear the archive?");

    if (!confirmed) return;

    try {
      const response = await fetch("/api/archive/clear", {
        method: "POST"
      });

      const data = await response.json();

      if (data.success) {
        window.location.reload();
      } else {
        alert("Archive could not be cleared.");
      }
    } catch (error) {
      console.error("Archive clear error:", error);
      alert("Archive could not be cleared.");
    }
  });
}

/*
=====================================================
Archive Filter
=====================================================

Filters archive records by:
- all
- safe
- check
- violation
*/

const archiveFilterButtons = document.querySelectorAll(".archive-filter-btn");
const archiveRecordCards = document.querySelectorAll(".archive-record-card");

function resetArchiveFilterButtons() {
  archiveFilterButtons.forEach((button) => {
    button.className =
      "archive-filter-btn bg-white text-gray-600 border border-gray-200 text-[11px] font-bold px-4 py-1.5 rounded-full hover:bg-gray-50 transition";
  });
}

function setActiveArchiveFilterButton(activeButton) {
  resetArchiveFilterButtons();

  const selectedFilter = activeButton.dataset.filter;

  if (selectedFilter === "all") {
    activeButton.className =
      "archive-filter-btn bg-blue-100 text-blue-800 border border-blue-200 text-[11px] font-bold px-4 py-1.5 rounded-full transition";
  }

  else if (selectedFilter === "safe") {
    activeButton.className =
      "archive-filter-btn bg-emerald-100 text-emerald-800 border border-emerald-200 text-[11px] font-bold px-4 py-1.5 rounded-full transition";
  }

  else if (selectedFilter === "check") {
    activeButton.className =
      "archive-filter-btn bg-orange-100 text-orange-800 border border-orange-200 text-[11px] font-bold px-4 py-1.5 rounded-full transition";
  }

  else if (selectedFilter === "violation") {
    activeButton.className =
      "archive-filter-btn bg-red-100 text-red-800 border border-red-200 text-[11px] font-bold px-4 py-1.5 rounded-full transition";
  }
}

archiveFilterButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const selectedFilter = button.dataset.filter;

    setActiveArchiveFilterButton(button);

    archiveRecordCards.forEach((card) => {
      const cardStatus = card.dataset.status;

      if (selectedFilter === "all") {
        card.classList.remove("hidden");
      }

      else if (cardStatus === selectedFilter) {
        card.classList.remove("hidden");
      }

      else {
        card.classList.add("hidden");
      }
    });
  });
});

/*
=====================================================
Archive Detail Toggle
=====================================================

Shows or hides the detailed input/output/metrics area
inside each archive record card.
*/

const archiveToggleButtons = document.querySelectorAll(".archive-toggle-btn");

archiveToggleButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const card = button.closest(".archive-record-card");
    if (!card) return;

    const details = card.querySelector(".archive-details");
    if (!details) return;

    const isHidden = details.classList.contains("hidden");

    if (isHidden) {
      details.classList.remove("hidden");
      button.innerText = "Hide Details";
    } else {
      details.classList.add("hidden");
      button.innerText = "View Details";
    }
  });
});

/*
=====================================================
Archive Feedback and Correction Panel
=====================================================

Handles:
- Correct
- Needs Review
- Wrong Detection
- Correction Panel visibility
- Saving corrected values
*/

function setFeedbackButtonActive(clickedButton) {
  const feedbackPanel = clickedButton.closest(".feedback-panel");
  if (!feedbackPanel) return;

  const buttons = feedbackPanel.querySelectorAll(".feedback-btn");

  buttons.forEach((button) => {
    button.classList.remove(
      "ring-2",
      "ring-offset-1",
      "ring-emerald-300",
      "ring-orange-300",
      "ring-red-300"
    );
  });

  const feedbackType = clickedButton.dataset.feedback;

  clickedButton.classList.add("ring-2", "ring-offset-1");

  if (feedbackType === "correct") {
    clickedButton.classList.add("ring-emerald-300");
  }

  else if (feedbackType === "needs_review") {
    clickedButton.classList.add("ring-orange-300");
  }

  else if (feedbackType === "wrong_detection") {
    clickedButton.classList.add("ring-red-300");
  }
}

function showOrHideCorrectionPanel(feedbackPanel, feedbackType) {
  const correctionPanel = feedbackPanel.querySelector(".correction-panel");

  if (!correctionPanel) {
    console.error("Correction panel not found.");
    return;
  }

  if (feedbackType === "needs_review" || feedbackType === "wrong_detection") {
    correctionPanel.classList.remove("hidden");
  } else {
    correctionPanel.classList.add("hidden");
  }
}

function getCorrectionValues(feedbackPanel) {
  const motorcyclesInput = feedbackPanel.querySelector(".corrected-motorcycles");
  const helmetsInput = feedbackPanel.querySelector(".corrected-helmets");
  const violationsInput = feedbackPanel.querySelector(".corrected-violations");
  const noteInput = feedbackPanel.querySelector(".correction-note");

  return {
    corrected_motorcycles: motorcyclesInput ? Number(motorcyclesInput.value) : null,
    corrected_helmets: helmetsInput ? Number(helmetsInput.value) : null,
    corrected_violations: violationsInput ? Number(violationsInput.value) : null,
    note: noteInput ? noteInput.value.trim() : ""
  };
}

async function sendArchiveFeedback(feedbackPanel, feedbackType, includeCorrections) {
  const archiveId = feedbackPanel.dataset.archiveId;
  const filename = feedbackPanel.dataset.filename;
  const feedbackStatus = feedbackPanel.querySelector(".feedback-status");

  let payload = {
    archive_id: archiveId,
    filename: filename,
    feedback: feedbackType,
    note: ""
  };

  if (includeCorrections) {
    payload = {
      ...payload,
      ...getCorrectionValues(feedbackPanel)
    };
  }

  try {
    const response = await fetch("/api/archive/feedback", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });

    const data = await response.json();

    if (!response.ok || !data.success) {
      throw new Error(data.message || "Feedback could not be saved.");
    }

    if (feedbackStatus) {
      feedbackStatus.classList.remove("hidden");
      feedbackStatus.className =
        "feedback-status text-[10px] text-emerald-700 mt-2";

      feedbackStatus.innerText = includeCorrections
        ? "Correction saved successfully."
        : "Feedback saved: " + feedbackType.replace("_", " ");
    }
  } catch (error) {
    console.error("Feedback error:", error);

    if (feedbackStatus) {
      feedbackStatus.classList.remove("hidden");
      feedbackStatus.className =
        "feedback-status text-[10px] text-red-700 mt-2";
      feedbackStatus.innerText = "Feedback could not be saved.";
    }
  }
}

document.querySelectorAll(".feedback-btn").forEach((button) => {
  button.addEventListener("click", async () => {
    const feedbackPanel = button.closest(".feedback-panel");
    if (!feedbackPanel) return;

    const feedbackType = button.dataset.feedback;

    setFeedbackButtonActive(button);
    showOrHideCorrectionPanel(feedbackPanel, feedbackType);

    if (feedbackType === "correct") {
      await sendArchiveFeedback(feedbackPanel, feedbackType, false);
    }
  });
});

document.querySelectorAll(".save-correction-btn").forEach((button) => {
  button.addEventListener("click", async () => {
    const feedbackPanel = button.closest(".feedback-panel");
    if (!feedbackPanel) return;

    const activeButton = feedbackPanel.querySelector(".feedback-btn.ring-2");

    if (!activeButton) {
      alert("Please select Needs Review or Wrong Detection first.");
      return;
    }

    const feedbackType = activeButton.dataset.feedback;

    if (feedbackType === "correct") {
      alert("Correction values are only needed for Needs Review or Wrong Detection.");
      return;
    }

    await sendArchiveFeedback(feedbackPanel, feedbackType, true);
  });
});

/*
=====================================================
Open Archive Record From URL Hash
=====================================================

If the page is opened with a URL such as:
/archive#record-abc123

This function scrolls to the record, opens its details,
and highlights it temporarily.
*/

function openRecordFromUrlHash() {
  const hash = window.location.hash;

  if (!hash) return;

  const targetRecord = document.querySelector(hash);

  if (!targetRecord) return;

  targetRecord.scrollIntoView({
    behavior: "smooth",
    block: "start"
  });

  const details = targetRecord.querySelector(".archive-details");
  const toggleButton = targetRecord.querySelector(".archive-toggle-btn");

  if (details && details.classList.contains("hidden")) {
    details.classList.remove("hidden");

    if (toggleButton) {
      toggleButton.innerText = "Hide Details";
    }
  }

  targetRecord.classList.add(
    "ring-2",
    "ring-blue-300",
    "shadow-lg"
  );

  setTimeout(() => {
    targetRecord.classList.remove(
      "ring-2",
      "ring-blue-300",
      "shadow-lg"
    );
  }, 2500);
}

openRecordFromUrlHash();