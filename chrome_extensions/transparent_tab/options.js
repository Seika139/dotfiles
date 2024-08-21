document.addEventListener("DOMContentLoaded", function () {
    const tabList = document.getElementById("tabList");
    const sortToggleSwitch = document.getElementById("sort-toggle-switch");
    let sortByOn = false;

    function renderTabs(tabs, allTabs) {
        tabList.innerHTML = "";
        const sortedTabs = allTabs.sort((a, b) => {
            if (sortByOn) {
                return (tabs[b.id] ? 1 : 0) - (tabs[a.id] ? 1 : 0);
            } else {
                return a.id - b.id;
            }
        });

        sortedTabs.forEach((tab) => {
            const row = document.createElement("tr");
            const tabStatus = tabs[tab.id] ? "on" : "off";
            row.className = tabs[tab.id] ? "on" : "";
            row.innerHTML = `
                <td>${tab.id}</td>
                <td><a href="#" class="tab-title" data-tab-id="${tab.id}">${tab.title}</a></td>
                <td>${tabStatus}</td>
                <td><button class="toggle-button">Toggle</button></td>
            `;

            const toggleButton = row.querySelector(".toggle-button");
            const tabTitle = row.querySelector(".tab-title");
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
                                document.removeEventListener("scroll", window.handleScroll);
                            },
                        });
                    }
                }

                updateIcon(tab.id, isActive);
                renderTabs(tabs, allTabs);
            });

            tabTitle.addEventListener("click", (e) => {
                e.preventDefault();
                const tabId = parseInt(e.target.getAttribute("data-tab-id"), 10);
                chrome.tabs.update(tabId, { active: true });
            });

            tabList.appendChild(row);
        });
    }

    chrome.storage.local.get("tabs", (data) => {
        const tabs = data.tabs || {};
        chrome.tabs.query({}, (allTabs) => {
            renderTabs(tabs, allTabs);
        });
    });

    sortToggleSwitch.addEventListener("change", () => {
        sortByOn = sortToggleSwitch.checked;
        chrome.storage.local.get("tabs", (data) => {
            const tabs = data.tabs || {};
            chrome.tabs.query({}, (allTabs) => {
                renderTabs(tabs, allTabs);
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
