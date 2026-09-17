document.addEventListener("DOMContentLoaded", function () {

    const darkModeBtn = document.getElementById("darkModeBtn");

    if (darkModeBtn) {
        darkModeBtn.addEventListener("click", function () {
            document.body.classList.toggle("dark-mode");

            if (document.body.classList.contains("dark-mode")) {
                darkModeBtn.textContent = "☀️ Light Mode";
            } else {
                darkModeBtn.textContent = "🌙 Dark Mode";
            }
        });
    }

});
