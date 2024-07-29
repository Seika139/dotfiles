chrome.commands.onCommand.addListener((command) => {
    console.log(`Command received: ${command}`);
    if (command === "increment" || command === "decrement") {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            let tab = tabs[0];
            let url = new URL(tab.url);
            let pathParts = url.pathname.split('/');

            let found = false;
            for (let i = pathParts.length - 1; i >= 0; i--) {
                let match = pathParts[i].match(/(\d+)(\.\w+)?$/);
                if (match) {
                    let number = parseInt(match[1], 10);
                    let extension = match[2] || '';
                    if (command === "increment") {
                        number++;
                    } else if (command === "decrement") {
                        number--;
                    }
                    pathParts[i] = number + extension;
                    found = true;
                    break;
                }
            }

            if (found) {
                url.pathname = pathParts.join('/');
                console.log(`New URL: ${url.toString()}`);
                chrome.tabs.update(tab.id, { url: url.toString() });
            } else {
                console.log('No numeric part found in the URL path.');
            }
        });
    }
});
