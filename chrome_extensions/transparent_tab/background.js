chrome.runtime.onInstalled.addListener(() => {
    chrome.storage.local.set({ tabs: {} });
    setDefaultIcon();
});

chrome.action.onClicked.addListener((tab) => {
    chrome.storage.local.get("tabs", (data) => {
        const tabs = data.tabs || {};
        const isActive = !tabs[tab.id];
        tabs[tab.id] = isActive;
        chrome.storage.local.set({ tabs: tabs });

        if (!tab.url.startsWith("chrome://") && !tab.url.startsWith("chrome-extension://")) {
            if (isActive) {
                chrome.scripting.executeScript({
                    target: { tabId: tab.id },
                    files: ["content.js"],
                });
            } else {
                chrome.scripting.executeScript({
                    target: { tabId: tab.id },
                    func: () => {
                        document.body.style.opacity = "1";
                        document.removeEventListener("mousemove", window.handleMouseMove);
                        document.removeEventListener("mouseout", window.handleMouseOut);
                        document.removeEventListener("scroll", window.handleScroll);
                    },
                });
            }
        }
        updateIcon(tab.id, isActive);
    });
});

chrome.tabs.onRemoved.addListener((tabId) => {
    chrome.storage.local.get("tabs", (data) => {
        const tabs = data.tabs || {};
        delete tabs[tabId];
        chrome.storage.local.set({ tabs: tabs });
    });
});

chrome.tabs.onCreated.addListener((tab) => {
    // 新しいタブが作成されたときに、そのタブの状態を初期化
    chrome.storage.local.get("tabs", (data) => {
        const tabs = data.tabs || {};
        tabs[tab.id] = false; // デフォルトで透明化をオフに設定
        chrome.storage.local.set({ tabs: tabs });
        updateIcon(tab.id, false);
    });
});

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === "complete") {
        chrome.storage.local.get("tabs", (data) => {
            const tabs = data.tabs || {};
            if (tabs[tabId] && !tab.url.startsWith("chrome://") && !tab.url.startsWith("chrome-extension://")) {
                chrome.scripting.executeScript({
                    target: { tabId: tabId },
                    files: ["content.js"],
                });
            } else if (!tab.url.startsWith("chrome://") && !tab.url.startsWith("chrome-extension://")) {
                chrome.scripting.executeScript({
                    target: { tabId: tabId },
                    func: () => {
                        document.body.style.opacity = "1";
                        document.removeEventListener("mousemove", window.handleMouseMove);
                        document.removeEventListener("mouseout", window.handleMouseOut);
                        document.removeEventListener("scroll", window.handleScroll);
                    },
                });
            }
            updateIcon(tabId, tabs[tabId]);
        });
    }
});

function updateIcon(tabId, isActive) {
    const color = isActive ? "on" : "off";
    chrome.action.setIcon({
        tabId: tabId,
        path: {
            16: `icons/icon-${color}-16.png`,
            48: `icons/icon-${color}-48.png`,
            128: `icons/icon-${color}-128.png`,
        },
    });
}

function setDefaultIcon() {
    chrome.action.setIcon({
        path: {
            16: `icons/icon-off-16.png`,
            48: `icons/icon-off-48.png`,
            128: `icons/icon-off-128.png`,
        },
    });
}
