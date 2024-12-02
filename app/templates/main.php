<?php
// Check if the request is a POST request
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    // Define a directory where you want to store the file
    $uploadDir = 'inputs_files/';

    $pubmedFileName = "/var/www/html/main/Pubmed/Code/args_pubmed.py";
    $europmcFileName = "/var/www/html/main/Europmc/Code/europmc.py";
    // $pubmedFileName = "/Users/vedanths/PycharmProjects/Bankinglabs/scraping_server/main/Pubmed/Code/args_pubmed.py";
    // $europmcFileName = "/Users/vedanths/PycharmProjects/Bankinglabs/scraping_server/main/Europmc/Code/europmc.py";
    // $sigalFilepath = "/path/to/signal_file.txt";

    // Generate a unique filename
    $filename = uniqid('file_') . '.txt';

    // Define the full path to the file
    $filePath = $uploadDir . $filename;

    // Get the values from the POST data
    $keyword = $_POST['Keyword'] ?? '';
    $title = $_POST['Title'] ?? '';
    $abstract = $_POST['Abstract'] ?? '';
    $startYear = $_POST['start_year'] ?? '';
    $endYear = $_POST['end_year'] ?? '';
    $selectField = $_POST['selectField'] ?? '';

    // Create a string with the values
    // debug
    // $data = "Keyword: $keyword\nTitle: $title\nAbstract: $abstract\nStart Year: $startYear\nEnd Year: $endYear";
        $data = "$title\n$keyword\n$abstract\n$startYear\n$endYear\n";

    // Create the file and write the data to it
    if (file_put_contents($filePath, $data) !== false) {
        // Execute different commands based on the selected option
        if ($selectField === 'EuroPMC') {
            // Command to run for Option 1
            $command = "python3 $europmcFileName < $filePath | tee -a log/out.log 2>/dev/null >/dev/null &";
            // $command = "cat $filePath" ;
        } elseif ($selectField === 'PubMed') {
            // Command to run for Option 2
            $command = "python3 $pubmedFileName < $filePath | tee -a log/out.log 2>/dev/null >/dev/null &";
            // $command = "cat $filePath" ;
        } else {
            // Handle other cases or errors
            echo "Invalid option selected.";
            exit;
        }


        // Execute the command
        // Execute the command in the background
        echo shell_exec($command);


        // Output a message indicating that the command has been started
        echo "Command has been started in the background.";
        echo '<link rel="stylesheet" type="text/css" href="styles.css">';
        echo '<p><a href="index.html">Go back</a></p>';
    } else {
        echo "Error: Unable to create the file.";
    }
} else {
    echo "Error: This script only accepts POST requests.";
}
?>

