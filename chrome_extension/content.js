/**
 * JARVIS Browser Extension — Content Script (content.js)
 * ========================================================
 * Injected into every page. Listens for messages from the background
 * service worker and executes page-level actions (click, fill, scroll).
 */

(function () {
  "use strict";

  // Prevent double-injection
  if (window.__JARVIS_INJECTED__) return;
  window.__JARVIS_INJECTED__ = true;

  console.log("[JARVIS Content] Active on:", window.location.hostname);

  // ── Listen for messages from background.js ──────────────────────────────
  chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
    switch (msg.action) {

      case "jarvis_click": {
        const el = document.querySelector(msg.selector);
        if (el) {
          el.click();
          sendResponse({ ok: true });
        } else {
          sendResponse({ ok: false, error: "Element not found: " + msg.selector });
        }
        break;
      }

      case "jarvis_fill": {
        const input = document.querySelector(msg.selector);
        if (input) {
          input.focus();
          input.value = msg.value;
          input.dispatchEvent(new Event("input", { bubbles: true }));
          input.dispatchEvent(new Event("change", { bubbles: true }));
          sendResponse({ ok: true });
        } else {
          sendResponse({ ok: false, error: "Input not found: " + msg.selector });
        }
        break;
      }

      case "jarvis_scroll": {
        const dir = msg.direction || "down";
        const amt = msg.amount   || 500;
        window.scrollBy({ top: dir === "down" ? amt : -amt, behavior: "smooth" });
        sendResponse({ ok: true });
        break;
      }

      case "jarvis_get_text": {
        const el = document.querySelector(msg.selector || "body");
        sendResponse({ ok: true, text: el ? el.innerText.slice(0, 2000) : "" });
        break;
      }

      case "jarvis_ping": {
        sendResponse({ ok: true, url: window.location.href });
        break;
      }

      default:
        sendResponse({ ok: false, error: "Unknown action: " + msg.action });
    }

    return true; // keep channel open for async
  });

  // ── Visual JARVIS indicator (subtle corner badge) ────────────────────────
  const badge = document.createElement("div");
  badge.id = "__jarvis_badge__";
  badge.title = "JARVIS Browser Agent is active on this page";
  badge.style.cssText = `
    position: fixed;
    bottom: 16px;
    right: 16px;
    z-index: 2147483647;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: radial-gradient(circle at 40% 40%, #00c6ff, #0072ff);
    box-shadow: 0 0 12px #0072ff88;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    user-select: none;
    opacity: 0.75;
    transition: opacity 0.2s;
  `;
  badge.textContent = "⚙";
  badge.addEventListener("mouseenter", () => { badge.style.opacity = "1"; });
  badge.addEventListener("mouseleave", () => { badge.style.opacity = "0.75"; });
  badge.addEventListener("click", () => {
    alert("JARVIS Browser Agent is active.\nUse your JARVIS voice assistant to control this page.");
  });

  // Inject after DOM is ready
  if (document.body) {
    document.body.appendChild(badge);
  } else {
    document.addEventListener("DOMContentLoaded", () => {
      document.body?.appendChild(badge);
    });
  }

  // Keep background service worker alive
  let port = null;
  function connectPort() {
    try {
      port = chrome.runtime.connect({ name: "jarvis-keepalive" });
      port.onDisconnect.addListener(() => {
        setTimeout(connectPort, 1000);
      });
    } catch (e) {
      // Chrome runtime might be unavailable/reloaded
      setTimeout(connectPort, 5000);
    }
  }
  connectPort();
})();
