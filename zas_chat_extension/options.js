// options.js

const DEFAULT_API_URL = "http://192.168.104.14:9000";

function $(id) {
  return document.getElementById(id);
}

function restoreOptions() {x
  chrome.storage.sync.get(["zas_api_url", "zas_size"], result => {
    $("api-url").value = result.zas_api_url || DEFAULT_API_URL;
    $("size").value = result.zas_size || "normal";
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

function saveOptions() {
  const url = normalizeApiUrl($("api-url").value || DEFAULT_API_URL);
  const size = $("size").value || "normal";

  chrome.storage.sync.set(
    {
      zas_api_url: url,
      zas_size: size
    },
    () => {
      const s = $("status");
      s.textContent = "Instellingen opgeslagen.";
      setTimeout(() => {
        s.textContent = "";
      }, 2000);
    }
  );
}

document.addEventListener("DOMContentLoaded", () => {
  restoreOptions();
  $("save").addEventListener("click", saveOptions);
});
