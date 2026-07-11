const animatedElements = document.querySelectorAll("[data-animate]");
const hoverAnimatedElements = document.querySelectorAll("[data-hover-animate]");

function activateAnimation(element) {
    const animationName = element.dataset.animate || "animate__fadeInUp";

    element.classList.add("animate__animated", animationName);
    element.classList.remove("animate-ready");
}

if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                if (!entry.isIntersecting) return;

                activateAnimation(entry.target);
                observer.unobserve(entry.target);
            });
        },
        {
            threshold: 0.18,
            rootMargin: "0px 0px -40px 0px",
        },
    );

    animatedElements.forEach((element, index) => {
        element.classList.add("animate-ready");
        element.style.setProperty("--animate-delay", `${Math.min(index * 0.04, 0.28)}s`);
        observer.observe(element);
    });
} else {
    animatedElements.forEach(activateAnimation);
}

hoverAnimatedElements.forEach((element) => {
    const hoverAnimation = element.dataset.hoverAnimate || "animate__pulse";

    element.addEventListener("mouseenter", () => {
        element.classList.remove("animate__animated", hoverAnimation);
        void element.offsetWidth;
        element.classList.add("animate__animated", hoverAnimation, "hover-animate-active");
    });

    element.addEventListener("animationend", () => {
        element.classList.remove("animate__animated", hoverAnimation, "hover-animate-active");
    });
});
