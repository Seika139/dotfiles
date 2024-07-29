chrome.commands.onCommand.addListener((command) => {
    console.log(`Command received: ${command}`);
    if (command === "increment" || command === "decrement") {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            let tab = tabs[0];
            let url = new URL(tab.url);
            let updated = false;

            // Step 1: Check if URL ends with #数字
            let hashMatch = url.hash.match(/#(\d+)$/);
            if (hashMatch) {
                let number = parseInt(hashMatch[1], 10);
                if (command === "increment") {
                    number++;
                } else if (command === "decrement") {
                    number--;
                }
                url.hash = `#${number}`;
                updated = true;
            }

            // Step 2: Check query parameters for the last numeric value
            if (!updated) {
                let queryParams = url.searchParams;
                let lastNumericParam = null;
                queryParams.forEach((value, key) => {
                    if (!isNaN(value) && value !== '') {
                        lastNumericParam = { key, value: parseInt(value, 10) };
                    }
                });

                if (lastNumericParam) {
                    let number = lastNumericParam.value;
                    if (command === "increment") {
                        number++;
                    } else if (command === "decrement") {
                        number--;
                    }
                    queryParams.set(lastNumericParam.key, number.toString());
                    url.search = queryParams.toString();
                    updated = true;
                }
            }

            // Step 3 & 4: Check URL path for number.extension or /number
            if (!updated) {
                let pathParts = url.pathname.split('/');
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
                        updated = true;
                        break;
                    }
                }

                if (updated) {
                    url.pathname = pathParts.join('/');
                }
            }

            if (updated) {
                console.log(`New URL: ${url.toString()}`);
                chrome.tabs.update(tab.id, { url: url.toString() });
            } else {
                console.log('No numeric part found to update.');
            }
        });
    }
});
