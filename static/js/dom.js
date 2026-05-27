/*
This file stores all HTML element references used by
the dashboard JavaScript files.

Purpose:
- Keep document.getElementById calls in one place.
- Make other JS files cleaner and easier to read.
- If an HTML id changes, it can be updated here only.
*/

window.elements = {
  // Upload Buttons
  uploadImageBtn: document.getElementById("uploadImageBtn"),
  uploadVideoBtn: document.getElementById("uploadVideoBtn"),

  //Upload Modal Elements
  uploadModal: document.getElementById("uploadModal"),
  closeModalBtn: document.getElementById("closeModalBtn"),
  cancelUploadBtn: document.getElementById("cancelUploadBtn"),
  chooseFileBtn: document.getElementById("chooseFileBtn"),
  confirmUploadBtn: document.getElementById("confirmUploadBtn"),
  mediaInput: document.getElementById("mediaInput"),
  selectedFileName: document.getElementById("selectedFileName"),

  // Original Input and Detection Output Preview Elements
  originalInputImage: document.getElementById("originalInputImage"),
  originalInputVideo: document.getElementById("originalInputVideo"),
  detectionOutputImage: document.getElementById("detectionOutputImage"),
  detectionOutputVideo: document.getElementById("detectionOutputVideo"),

  originalPlaceholder: document.getElementById("originalPlaceholder"),
  outputPlaceholder: document.getElementById("outputPlaceholder"),

  // Status Labels
  inputStatus: document.getElementById("inputStatus"),
  outputStatus: document.getElementById("outputStatus"),
  
  systemStatusBadge: document.getElementById("systemStatusBadge"),
  systemStatusDot: document.getElementById("systemStatusDot"),
  systemStatusText: document.getElementById("systemStatusText"),

  // Main Detection Button
  runDetectionBtn: document.getElementById("runDetectionBtn"),

  // Detection Summary and Pipeline Metrics
  motorcycleCount: document.getElementById("motorcycleCount"),
  helmetCount: document.getElementById("helmetCount"),
  violationCount: document.getElementById("violationCount"),
  avgConfidence: document.getElementById("avgConfidence"),
  processingTime: document.getElementById("processingTime"),
  resolutionText: document.getElementById("resolutionText"),
  fileTypeText: document.getElementById("fileTypeText"),

  // Status Modal Elements
  statusModal: document.getElementById("statusModal"),
  statusIcon: document.getElementById("statusIcon"),
  statusTitle: document.getElementById("statusTitle"),
  statusMessage: document.getElementById("statusMessage"),
  closeStatusModalBtn: document.getElementById("closeStatusModalBtn"),

  // Recent Uploads Container
  recentUploads: document.getElementById("recentUploads"),
  newUploadCard: document.getElementById("newUploadCard"),
  toggleRecentUploadsBtn: document.getElementById("toggleRecentUploadsBtn"),
  recentUploadsWrapper: document.getElementById("recentUploadsWrapper"),
};