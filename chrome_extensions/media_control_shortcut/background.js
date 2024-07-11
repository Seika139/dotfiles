chrome.commands.onCommand.addListener((command) => {
    if (command === "toggle-media-playback") {
        chrome.tabs.query({ audible: true }, (tabs) => {
            tabs.forEach((tab) => {
                chrome.scripting.executeScript({
                    target: { tabId: tab.id },
                    func: toggleMediaPlayback
                });
            });
        });
    }
});

function toggleMediaPlayback() {
    const mediaElements = document.querySelectorAll('video, audio');
    if (mediaElements.length > 0) {
        mediaElements.forEach(media => {
            if (media.paused) {
                media.play();
            } else {
                media.pause();
            }
        });
    } else {
        console.log('No media elements found on this page.');
    }
}
