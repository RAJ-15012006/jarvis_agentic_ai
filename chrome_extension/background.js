/**
 * JARVIS Browser Extension — Background Service Worker (background.js)
 * =====================================================================
 * Maintains a persistent WebSocket connection to the local JARVIS server.
 * Routes tab-level commands from Jarvis to the correct Chrome tab.
 */

const JARVIS_WS_URL  = "ws://127.0.0.1:8000/socket.io/?EIO=4&transport=websocket&token=jarvis-local-secret";
const JARVIS_SECRET  = "jarvis-local-secret";
const RECONNECT_DELAY_MS = 3000;

let socket = null;
let reconnectTimer = null;

// ── Socket.IO handshake helpers ───────────────────────────────────────────────
function sioConnect() {
  if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
    return;
  }

  console.log("[JARVIS] Connecting to local server...");
  socket = new WebSocket(JARVIS_WS_URL);

  socket.onopen = () => {
    console.log("[JARVIS] WebSocket open — performing Socket.IO handshake...");
    // Socket.IO ENGINE.IO handshake: send "40" to connect to default namespace
    socket.send("40");
  };

  socket.onmessage = (event) => {
    const data = event.data;

    // ENGINE.IO ping → respond with pong
    if (data === "2") { socket.send("3"); return; }

    // Socket.IO namespace connected
    if (data.startsWith("40")) {
      console.log("[JARVIS] Connected to JARVIS Socket.IO namespace.");
      // Authenticate
      const authPayload = JSON.stringify({ token: JARVIS_SECRET });
      socket.send(`42["authenticate",${authPayload}]`);
      notifyIcon(true);
      return;
    }

    // Parse Socket.IO event packet "42[event, data]"
    if (data.startsWith("42")) {
      try {
        const payload = JSON.parse(data.slice(2));
        const [event, eventData] = payload;
        handleJarvisEvent(event, eventData);
      } catch (e) {
        console.warn("[JARVIS] Could not parse event:", data);
      }
    }
  };

  socket.onclose = () => {
    console.warn("[JARVIS] WebSocket closed. Reconnecting in 3s...");
    notifyIcon(false);
    scheduleReconnect();
  };

  socket.onerror = (err) => {
    console.error("[JARVIS] WebSocket error:", err);
    socket.close();
  };
}

function scheduleReconnect() {
  clearTimeout(reconnectTimer);
  reconnectTimer = setTimeout(sioConnect, RECONNECT_DELAY_MS);
}

function notifyIcon(connected) {
  chrome.action.setTitle({
    title: connected ? "JARVIS — Connected ✅" : "JARVIS — Disconnected ❌",
  });
}

// ── Tab Command Handler ───────────────────────────────────────────────────────
async function handleJarvisEvent(event, data) {
  switch (event) {

    // Open a URL in a new tab
    case "open_tab": {
      const url = data?.url;
      if (url && (url.startsWith("https://") || url.startsWith("http://"))) {
        await chrome.tabs.create({ url });
        console.log("[JARVIS] Opened tab:", url);
      }
      break;
    }

    // Close ALL tabs (in all windows)
    case "close_all_tabs": {
      const windows = await chrome.windows.getAll({ populate: true });
      for (const win of windows) {
        for (const tab of win.tabs) {
          // Don't close the Jarvis UI tab itself
          if (!tab.url.includes("127.0.0.1:8000") && !tab.url.includes("localhost:8000")) {
            await chrome.tabs.remove(tab.id).catch(() => {});
          }
        }
      }
      console.log("[JARVIS] All non-Jarvis tabs closed.");
      break;
    }

    // Search Google in a new tab
    case "search_google": {
      const query = data?.query;
      if (query) {
        const url = `https://www.google.com/search?q=${encodeURIComponent(query)}`;
        await chrome.tabs.create({ url });
      }
      break;
    }

    // Execute arbitrary JS in the active tab (for page interactions)
    case "execute_in_tab": {
      const code = data?.code;
      if (!code) break;
      const [tab] = await chrome.tabs.query({ active: true, lastFocusedWindow: true });
      if (tab?.id) {
        chrome.scripting.executeScript({
          target: { tabId: tab.id },
          func: new Function(code),
        }).catch(err => console.error("[JARVIS] Script error:", err));
      }
      break;
    }

    // Scroll active tab
    case "scroll_tab": {
      const direction = data?.direction || "down";
      const amount    = data?.amount    || 500;
      const [tab] = await chrome.tabs.query({ active: true, lastFocusedWindow: true });
      if (tab?.id) {
        chrome.scripting.executeScript({
          target: { tabId: tab.id },
          func: (dir, amt) => { window.scrollBy(0, dir === "down" ? amt : -amt); },
          args: [direction, amount],
        });
      }
      break;
    }

    // Show browser notification
    case "notify": {
      chrome.notifications.create({
        type: "basic",
        iconUrl: "icons/jarvis48.png",
        title: "JARVIS",
        message: data?.message || "Hello, Sir.",
      });
      break;
    }

    default:
      break;
  }
}

// ── Startup ───────────────────────────────────────────────────────────────────
chrome.runtime.onStartup.addListener(sioConnect);
chrome.runtime.onInstalled.addListener(sioConnect);
sioConnect();
