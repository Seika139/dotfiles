window.handleMouseMove = function () {
    document.body.style.opacity = "1";
};

window.handleMouseOut = function () {
    document.body.style.opacity = "0.5"; // 透明度を調整
};

document.addEventListener("mousemove", window.handleMouseMove);
document.addEventListener("mouseout", window.handleMouseOut);
