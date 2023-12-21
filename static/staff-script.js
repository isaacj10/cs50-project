function toggleFormFields() {
    var action = document.getElementById("action").value;
    var newUserFields = document.getElementById("new_user_fields");
    var deleteUserFields = document.getElementById("delete_user_fields");

    if (action === "enter_user") {
        newUserFields.style.display = "block";
        deleteUserFields.style.display = "none";
    } else if (action === "delete_user") {
        newUserFields.style.display = "none";
        deleteUserFields.style.display = "block";
    }
}