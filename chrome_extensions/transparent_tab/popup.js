document.addEventListener("DOMContentLoaded", function () {
    const toggleSwitch = document.getElementById("toggle-switch");
    const toggleContainer = document.getElementById("toggle-container");

    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        const tab = tabs[0];
        // URLが"chrome://"や"chrome-extension://"から始まる場合は表示しない
        if (tab.url.startsWith("chrome://") || tab.url.startsWith("chrome-extension://")) {
            toggleContainer.style.display = "none";
            return;
        }
        chrome.storage.local.get("tabs", (data) => {
            const tabs = data.tabs || {};
            toggleSwitch.checked = tabs[tab.id] || false;
        });

        toggleContainer.addEventListener("click", () => {
            toggleSwitch.checked = !toggleSwitch.checked;
            chrome.storage.local.get("tabs", (data) => {
                const tabs = data.tabs || {};
                const isActive = toggleSwitch.checked;
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
    });
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
