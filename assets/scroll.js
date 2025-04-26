document.addEventListener("scroll", function () {
    const filters = document.querySelector(".filters-container");
    const scrollPosition = window.scrollY;

    if (scrollPosition > 100) {
        filters.style.transform = `translateY(${scrollPosition - 100}px)`;
    } else {
        filters.style.transform = "translateY(0)";
    }
});