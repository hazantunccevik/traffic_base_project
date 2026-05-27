/*
=====================================================
systemStatus.js
=====================================================

This file checks whether the backend system is reachable.

It updates the sidebar system status badge:
- Checking
- Ready
- Error
*/

async function checkSystemStatus() {
  setSystemStatus("checking", "SYSTEM STATUS: CHECKING");

  try {
    const response = await fetch("/api/system-status");
    const data = await response.json();

    if (!response.ok || !data.success) {
      throw new Error(data.message || "System status check failed.");
    }

    setSystemStatus("ready", "SYSTEM STATUS: ACTIVE");

  } catch (error) {
    console.error("System status error:", error);
    setSystemStatus("error", "SYSTEM STATUS: ERROR");
  }
}