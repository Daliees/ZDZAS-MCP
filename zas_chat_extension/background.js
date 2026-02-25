// background.js - NIEUW voor vast Bentley side panel.
// Zorg dat klikken op de extensie-icoon de side panel opent i.p.v. een popup.

function enableSidePanelBehavior() {
  try {
    if (chrome.sidePanel && chrome.sidePanel.setPanelBehavior) {
      chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true });
    }
  } catch (err) {
    console.error("Failed to set side panel behavior", err);
  }
}

// Bij installatie / update
chrome.runtime.onInstalled.addListener(() => {
  enableSidePanelBehavior();
});

// En ook bij opstarten van de service worker
enableSidePanelBehavior();
