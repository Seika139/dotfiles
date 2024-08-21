window.handleMouseMove = function () {
    document.body.style.opacity = "1";
};

window.handleMouseOut = function () {
    document.body.style.opacity = "0";
};

window.handleScroll = function () {
    document.body.style.opacity = "1";
};

document.addEventListener("mousemove", window.handleMouseMove);
document.addEventListener("mouseout", window.handleMouseOut);
document.addEventListener("scroll", window.handleScroll);
