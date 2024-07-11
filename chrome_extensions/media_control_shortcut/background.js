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
                console.log('Playing media:', media);
                media.play().catch(error => console.error('Error playing media:', error));
            } else {
                console.log('Pausing media:', media);
                media.pause();
            }
        });
    } else {
        console.log('No media elements found on this page.');
    }
}
