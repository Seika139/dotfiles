document.addEventListener("DOMContentLoaded", function () {
    const tabList = document.getElementById("tabList");
    chrome.storage.local.get("tabs", (data) => {
        const tabs = data.tabs || {};
        chrome.tabs.query({}, (allTabs) => {
            allTabs.forEach((tab) => {
                const listItem = document.createElement("li");
                const tabStatus = tabs[tab.id] ? "on" : "off";
                listItem.textContent = `Tab ${tab.id} (${tab.title}): ${tabStatus}`;
                const toggleButton = document.createElement("button");
                toggleButton.textContent = "Toggle";
                toggleButton.addEventListener("click", () => {
                    const isActive = !tabs[tab.id];
                    tabs[tab.id] = isActive;
                    chrome.storage.local.set({ tabs: tabs });

                    if (!tab.url.startsWith("chrome://")) {
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
                                },
                            });
                        }
                    }
                    updateIcon(tab.id, isActive);
                    listItem.textContent = `Tab ${tab.id} (${tab.title}): ${isActive ? "on" : "off"}`;
                });
                listItem.appendChild(toggleButton);
                tabList.appendChild(listItem);
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
