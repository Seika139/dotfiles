chrome.commands.onCommand.addListener((command) => {
    console.log(`Command received: ${command}`);
    if (command === "increment" || command === "decrement") {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            let tab = tabs[0];
            let url = new URL(tab.url);
            let pathParts = url.pathname.split('/');
            let increase = (command === "increment");

            // Function to handle increment/decrement
            function updateNumber(match) {
                let number = parseInt(match[1], 10);
                let extension = match[2] || '';
                if (increase) {
                    number++;
                } else {
                    number--;
                }
                return number + extension;
            }

            // Search and update the pathname part
            let updated = pathParts.some((part, index) => {
                let match = part.match(/(\d+)(\.\w+)?$/);
                if (match) {
                    pathParts[index] = updateNumber(match);
                    url.pathname = pathParts.join('/');
                    return true;
                }
                return false;
            });

            // If pathname part is not found, search and update the hash part
            if (!updated) {
                let hashMatch = url.hash.match(/#(\d+)$/);
                if (hashMatch) {
                    url.hash = `#${updateNumber(hashMatch)}`;
                    updated = true;
                }
            }

            if (updated) {
                console.log(`New URL: ${url.toString()}`);
                chrome.tabs.update(tab.id, { url: url.toString() });
            } else {
                console.log('No numeric part found in the URL path or hash.');
            }
        });
    }
});
