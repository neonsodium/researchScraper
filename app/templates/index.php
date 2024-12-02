<?php
session_start();

$username = "scraper";
$password = "banking_labs@123";

if ($_SERVER["REQUEST_METHOD"] == "POST") {
    if ($_POST["username"] == $username && $_POST["password"] == $password) {
        $_SESSION["authenticated"] = true;
    }
}

if (!isset($_SESSION["authenticated"])) {
    ?>
    <link rel="stylesheet" type="text/css" href="styles.css">
    <form method="post">
        <label for="Username">Username:</label>
        <input type="text" name="username"><br><br>

        <label for="Password">Password:</label>
        <input type="password" name="password"><br><br>

        <input type="submit" value="Log In">
    </form>
    <?php
    exit;
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <link rel="stylesheet" type="text/css" href="styles.css">
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Submit Data</title>
</head>
<body>
    <h1>Submit Data</h1>
    <form action="main.php" method="post" onsubmit="return checkEmptyFields();">
        <label for="Keyword">Keyword:</label>
        <input type="text" name="Keyword" id="Keyword"><br><br>

        <label for="Title">Title:</label>
        <input type="text" name="Title" id="Title"><br><br>

        <label for="Abstract">Abstract:</label>
        <!-- <textarea name="Abstract" id="Abstract" rows="4"></textarea><br><br> -->
        <input type="text" name="Abstract" id="Abstract"><br><br>

        <label for="start_year">Start Year:</label>
        <input type="text" name="start_year" id="start_year"><br><br>

        <label for="end_year">End Year:</label>
        <input type="text" name="end_year" id="end_year"><br><br>

        <label for="selectField">Select an Option:</label>
        <select name="selectField" id="selectField">
            <option value="EuroPMC">EuroPMC</option>
            <option value="PubMed">PubMed</option>
        </select><br><br>

        <input type="submit" value="Submit">
    </form>

    <script>
        function checkEmptyFields() {
            var keyword = document.getElementById("Keyword").value;
            var title = document.getElementById("Title").value;
            var abstract = document.getElementById("Abstract").value;
            var startYear = document.getElementById("start_year").value;
            var endYear = document.getElementById("end_year").value;

            if (!keyword) {
                document.getElementById("Keyword").value = '\n';
            }
            if (!title) {
                document.getElementById("Title").value = '\n';
            }
            if (!abstract) {
                document.getElementById("Abstract").value = '\n';
            }
            if (!startYear) {
                document.getElementById("start_year").value = '\n';
            }
            if (!endYear) {
                document.getElementById("end_year").value = '\n';
            }

            return true; // Continue with form submission
        }
    </script>
</body>
</html>
