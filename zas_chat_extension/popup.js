// popup.js

const DEFAULT_API_URL = "http://192.168.104.14:9000";

let sessionId = null;
let conversationId = null;
let apiUrl = DEFAULT_API_URL;
let isSending = false;

let localHistory = [];

function $(id) {
  return document.getElementById(id);
}

// ---------- Link rendering helpers ----------

// HTML escapen om XSS te voorkomen
function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// Markdown-achtige [text](url) + platte URLs → klikbare links
function renderTextWithLinks(text) {
  if (!text) return "";

  // Eerst HTML escapen
  let safe = escapeHtml(text);

  // [label](https://link)
  const mdLinkRegex = /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g;
  safe = safe.replace(
    mdLinkRegex,
    (_, label, url) =>
      `<a href="${url}" target="_blank" rel="noopener noreferrer">${escapeHtml(
        label
      )}</a>`
  );

  // Platte URLs (https://... of http://...)
  const urlRegex = /(https?:\/\/[^\s]+)/g;
  safe = safe.replace(
    urlRegex,
    url =>
      `<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`
  );

  return safe;
}

// ---------- Status / state helpers ----------

function generateSessionId() {
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, c => {
    const r = (crypto.getRandomValues(new Uint8Array(1))[0] & 0xf) >> 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

function setStatus(text) {
  const statusEl = $("status");
  if (!text) {
    statusEl.classList.add("hidden");
    statusEl.textContent = "";
  } else {
    statusEl.textContent = text;
    statusEl.classList.remove("hidden");
  }
}

function setSendingState(sending) {
  isSending = sending;
  $("send-button").disabled = sending;
}

// ---------- Rendering van berichten ----------

function appendMessage(role, text, options = {}) {
  const messagesEl = $("messages");
  const historyBefore = options.historyBefore || localHistory;

  const row = document.createElement("div");
  row.className = `message-row ${role}`;

  const inner = document.createElement("div");
  inner.className = "message-inner";

  const bubble = document.createElement("div");
  bubble.className = "bubble";

  // HIER: HTML met linkjes i.p.v. pure text
  bubble.innerHTML = renderTextWithLinks(text);

  inner.appendChild(bubble);

  if (role === "agent") {
    const ratingBar = document.createElement("div");
    ratingBar.className = "rating-bar";

    const lastUser = [...historyBefore].reverse().find(m => m.role === "user");
    const userMessageForThisReply = lastUser ? lastUser.text : null;
    ratingBar.dataset.userMessage = userMessageForThisReply || "";

    ratingBar.innerHTML = `
      <button class="rating-btn" data-rating="bad" title="Slecht / hallucinatie">✖</button>
      <button class="rating-btn" data-rating="neutral" title="Neutraal / geen nuttige info">≃</button>
      <button class="rating-btn" data-rating="good" title="Goed antwoord">✔</button>
    `;

    ratingBar.addEventListener("click", e => {
      const btn = e.target.closest(".rating-btn");
      if (!btn) return;
      const rating = btn.dataset.rating;

      ratingBar.querySelectorAll(".rating-btn").forEach(b =>
        b.classList.remove("selected")
      );
      btn.classList.add("selected");

      const userMessage = ratingBar.dataset.userMessage || null;
      sendFeedback(rating, text, userMessage).catch(err =>
        console.error("Feedback send failed", err)
      );
    });

    inner.appendChild(ratingBar);
  }

  row.appendChild(inner);
  messagesEl.appendChild(row);

  if (!options.skipScroll) {
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }
}

function saveHistory() {
  const trimmed = localHistory.slice(-100);
  chrome.storage.local.set({ zas_history: trimmed });
}

function loadState() {
  return new Promise(resolve => {
    chrome.storage.local.get(
      ["zas_session_id", "zas_history", "zas_conversation_id"],
      result => {
        sessionId = result.zas_session_id || generateSessionId();
        conversationId = result.zas_conversation_id || null;

        if (!result.zas_session_id) {
          chrome.storage.local.set({ zas_session_id: sessionId });
        }

        const storedHistory = result.zas_history || [];
        localHistory = [];
        storedHistory.forEach(item => {
          appendMessage(item.role, item.text, {
            skipScroll: true,
            historyBefore: localHistory
          });
          localHistory.push({ role: item.role, text: item.text });
        });

        $("messages").scrollTop = $("messages").scrollHeight;
        resolve();
      }
    );
  });
}

function loadApiUrl() {
  return new Promise(resolve => {
    chrome.storage.sync.get(["zas_api_url"], result => {
      apiUrl = normalizeApiUrl(result.zas_api_url || DEFAULT_API_URL);
      resolve();
    });
  });
}

function normalizeApiUrl(rawUrl) {
  if (!rawUrl) return DEFAULT_API_URL + "/chat";
  let url = rawUrl.trim();
  if (url.endsWith("/")) {
    url = url.slice(0, -1);
  }
  if (!url.endsWith("/chat")) {
    url = url + "/chat";
  }
  return url;
}

// ---------- Backend calls ----------

async function sendMessageToBackend(text) {
  await loadApiUrl();

  const payload = {
    message: text,
    conversationId: conversationId || null
  };

  const headers = {
    "Content-Type": "application/json",
    "X-Session-Id": sessionId
  };

  const res = await fetch(apiUrl, {
    method: "POST",
    headers,
    body: JSON.stringify(payload)
  });

  if (!res.ok) {
    const errText = await res.text().catch(() => "");
    throw new Error(
      `HTTP ${res.status} ${res.statusText || ""} - ${errText.slice(0, 200)}`
    );
  }

  const data = await res.json().catch(() => ({}));

  if (typeof data.conversationId === "string") {
    conversationId = data.conversationId;
    chrome.storage.local.set({ zas_conversation_id: conversationId });
  }

  let replyText = "";
  if (typeof data.reply === "string") {
    replyText = data.reply;
  } else if (Array.isArray(data.messages)) {
    const lastAgent = [...data.messages]
      .reverse()
      .find(
        m =>
          m.role === "assistant" ||
          m.role === "agent" ||
          m.role === "zas_agent"
      );
    if (lastAgent && typeof lastAgent.content === "string") {
      replyText = lastAgent.content;
    }
  }

  if (!replyText) {
    replyText = "[Geen leesbare reply ontvangen van ZAS agent]";
  }

  return replyText;
}

async function sendFeedback(rating, agentReply, userMessage) {
  await loadApiUrl();
  const urlObj = new URL(apiUrl);
  urlObj.pathname = "/feedback";

  const payload = {
    conversationId: conversationId || sessionId || "unknown",
    sessionId: sessionId || null,
    userMessage: userMessage,
    agentReply,
    rating,
    createdAt: new Date().toISOString()
  };

  await fetch(urlObj.toString(), {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });
}

async function resetChat() {
  $("messages").innerHTML = "";
  setStatus("");

  localHistory = [];
  conversationId = null;

  await new Promise(resolve =>
    chrome.storage.local.set(
      { zas_history: [], zas_conversation_id: null },
      resolve
    )
  );

  try {
    await loadApiUrl();
    const urlObj = new URL(apiUrl);
    urlObj.pathname = "/reset";

    const payload = {
      conversationId: null
    };

    await fetch(urlObj.toString(), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Session-Id": sessionId
      },
      body: JSON.stringify(payload)
    });
  } catch (err) {
    console.error("Backend reset error", err);
  }
}

// ---------- Event handlers ----------

async function handleSubmit(event) {
  event.preventDefault();
  if (isSending) return;

  const inputEl = $("message-input");
  const text = (inputEl.value || "").trim();
  if (!text) return;

  setSendingState(true);
  setStatus("ZAS agent is aan het nadenken…");

  appendMessage("user", text);
  localHistory.push({ role: "user", text });
  saveHistory();
  inputEl.value = "";

  try {
    const reply = await sendMessageToBackend(text);

    appendMessage("agent", reply, { historyBefore: localHistory });
    localHistory.push({ role: "agent", text: reply });
    saveHistory();

    setStatus("");
  } catch (err) {
    console.error(err);
    setStatus("Fout bij contact met ZAS agent. Check API URL / server.");
    const errorText =
      "Er ging iets mis bij het verbinden met de ZAS backend. " +
      "Controleer of de chat_api server draait en de URL correct is.";
    appendMessage("agent", errorText, { historyBefore: localHistory });
    localHistory.push({ role: "agent", text: errorText });
    saveHistory();
  } finally {
    setSendingState(false);
  }
}

async function openBentleyView() {
  try {
    if (chrome.sidePanel && chrome.sidePanel.open) {
      const [tab] = await chrome.tabs.query({
        active: true,
        currentWindow: true
      });
      await chrome.sidePanel.open({ tabId: tab.id });
    } else {
      console.warn("Side panel API niet beschikbaar.");
    }
  } catch (err) {
    console.error("Bentley View failed", err);
  }
}

// ---------- Init ----------

document.addEventListener("DOMContentLoaded", async () => {
  await loadState();
  await loadApiUrl();

  $("input-form").addEventListener("submit", handleSubmit);

  $("message-input").addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      $("input-form").requestSubmit();
    }
  });

  $("open-options").addEventListener("click", () => {
    chrome.runtime.openOptionsPage();
  });

  $("reset-chat").addEventListener("click", () => {
    resetChat().catch(err => console.error("Reset failed", err));
  });

  $("bentley-view").addEventListener("click", () => {
    openBentleyView().catch(err => console.error(err));
  });
});
