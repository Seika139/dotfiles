chrome.commands.onCommand.addListener((command) => {
    if (command === "toggle-media-playback") {
        chrome.tabs.query({ audible: true }, (tabs) => {
            tabs.forEach((tab) => {
                chrome.scripting.executeScript({
                    target: { tabId: tab.id },
                    func: toggleMediaPlayback
                }, (results) => {
                    if (chrome.runtime.lastError) {
                        console.error('Runtime error:', chrome.runtime.lastError.message);
                    } else {
                        console.log('Script executed successfully:', results);
                        if (results && results[0] && results[0].result) {
                            console.log('Script result:', results[0].result);
                        }
                    }
                });
            });
        });
    }
});

function toggleMediaPlayback() {
    const mediaElements = document.querySelectorAll('video, audio');
    console.log('Found media elements:', mediaElements);
    if (mediaElements.length > 0) {
        mediaElements.forEach(media => {
            console.log('Media element:', media);
            console.log('Media element current state:', media.paused ? 'paused' : 'playing');
            if (media.paused) {
                console.log('Attempting to play media:', media);
                media.play().catch(error => {
                    console.error('Error playing media:', error);
                    // Chromeには自動再生ポリシーがあり
                    // 特定の条件下では自動再生がブロックされることがある
                    // これを回避するために、ユーザー操作をシミュレートする方法を試す
                    media.muted = true;
                    media.play().then(() => {
                        media.muted = false;
                    }).catch(error => console.error('Error playing muted media:', error));
                });
            } else {
                console.log('Attempting to pause media:', media);
                media.pause();
            }
        });
    } else {
        console.log('No media elements found on this page.');
    }
    return mediaElements.length > 0;
}
