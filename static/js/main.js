/*
=====================================================
main.js
=====================================================

This is the main initializer file.

Responsibilities:
- Wait until dashboard HTML is loaded.
- Check whether current page is dashboard.
- Store selected media file.
- Connect button events.
- Initialize detection handler.
- Load Recent Uploads on page open.
*/


document.addEventListener("DOMContentLoaded", () => {
  const {
    uploadImageBtn,
    uploadVideoBtn,
    newUploadCard,
    closeModalBtn,
    cancelUploadBtn,
    closeStatusModalBtn,
    chooseFileBtn,
    confirmUploadBtn,
    mediaInput,
    selectedFileName
  } = window.elements;


  /*
  =====================================================
  Dashboard Page Guard
  =====================================================

  If uploadImageBtn does not exist, this script stops.
  This prevents errors on non-dashboard pages.
  */

  if (!uploadImageBtn) return;


  /*
  =====================================================
  Global State for Selected File
  =====================================================

  selectedMediaFile stores the current image/video selected
  by the user.
  */

  let selectedMediaFile = null;


  /*
  =====================================================
  Upload Modal Button Events
  =====================================================
  */

  uploadImageBtn.addEventListener("click", openUploadModal);

  if (uploadVideoBtn) {
    uploadVideoBtn.addEventListener("click", openUploadModal);
  }

  if (newUploadCard) {
    newUploadCard.addEventListener("click", openUploadModal);
  }

  if (closeModalBtn) {
    closeModalBtn.addEventListener("click", closeUploadModal);
  }

  if (cancelUploadBtn) {
    cancelUploadBtn.addEventListener("click", closeUploadModal);
  }

  if (closeStatusModalBtn) {
    closeStatusModalBtn.addEventListener("click", closeStatusModal);
  }


  /*
  =====================================================
  Choose File Button Event
  =====================================================

  This button opens the hidden file input.
  */

  if (chooseFileBtn && mediaInput) {
    chooseFileBtn.addEventListener("click", () => {
      mediaInput.click();
    });
  }


  /*
  =====================================================
  File Selection Event
  =====================================================

  When user selects a file:
  - selectedMediaFile is updated.
  - selected file name is shown in modal.
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


  /*
  =====================================================
  Confirm Upload Event
  =====================================================

  When user clicks "Use This File":
  - selected file is shown in Original Input area.
  - file resolution is updated.
  - upload modal is closed.
  */

  if (confirmUploadBtn) {
    confirmUploadBtn.addEventListener("click", () => {
      if (!selectedMediaFile) {
        showStatusModal(
          "error",
          "No File Selected",
          "Please choose an image or video file first."
        );

        return;
      }

      setInputPreview(selectedMediaFile);
      updateResolution(selectedMediaFile);
      closeUploadModal();
    });
  }


  /*
  =====================================================
  Detection Handler Initialization
  =====================================================

  setupDetectionHandler needs access to selectedMediaFile.
  Instead of using a global variable, we pass a getter function.
  */

  setupDetectionHandler(() => selectedMediaFile);


  /*
  =====================================================
  Initial Recent Uploads Load
  =====================================================

  When dashboard opens, archive records are loaded immediately.
  */

  setupRecentUploadsToggle();
  checkSystemStatus();
  loadRecentUploadsFromArchive();
  
});