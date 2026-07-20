// popup.js — JARVIS Extension Popup Logic

document.getElementById("openJarvis").addEventListener("click", () => {
  chrome.tabs.create({ url: "http://localhost:8000" });
  window.close();
});

document.getElementById("closeTab").addEventListener("click", () => {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (tabs[0]) chrome.tabs.remove(tabs[0].id);
  });
});

// Check if JARVIS server is running
fetch("http://localhost:8000/api", { method: "GET" })
  .then((res) => res.json())
  .then((data) => {
    if (data.status && data.status.includes("JARVIS")) {
      document.getElementById("statusDot").classList.remove("off");
      document.getElementById("statusText").textContent = "JARVIS Online ✅";
    }
  })
  .catch(() => {
    document.getElementById("statusDot").classList.add("off");
    document.getElementById("statusText").textContent = "JARVIS Offline ❌";
  });
