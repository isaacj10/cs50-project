document.addEventListener('DOMContentLoaded', function() {
    document.getElementById("menuButton").addEventListener("click", function() {
    var dropdownMenu = document.getElementById("dropdownMenu");
    dropdownMenu.style.display = (dropdownMenu.style.display == "block") ? "none" : "block";
    });
});