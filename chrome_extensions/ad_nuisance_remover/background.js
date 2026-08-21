"use strict";

chrome.action.onClicked.addListener(async (tab) => {
  if (!tab.id) {
    return;
  }

  try {
    await chrome.scripting.executeScript({
      target: { tabId: tab.id, allFrames: false },
      files: ["unlock.js"],
      injectImmediately: true,
    });
  } catch (error) {
    console.warn("Ad Nuisance Remover could not run on this page.", error);
  }
});
