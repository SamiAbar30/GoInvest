role_input = document.getElementById("role");

document.getElementById("investor-role").addEventListener("click", function () {
    updateRole("investor")
});
document.getElementById("student-role").addEventListener("click", function () {
    updateRole("student")
});

function updateRole(role) {
    role_input.value = role;
    if (role == "investor") {
        document.getElementById("investor-role").classList.add("selected-role");
        document.getElementById("student-role").classList.remove("selected-role");
    } else {
        document.getElementById("student-role").classList.add("selected-role");
        document.getElementById("investor-role").classList.remove("selected-role");
    }
}