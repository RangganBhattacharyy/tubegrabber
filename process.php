<?php
include 'db.php';

$video_title = "Sample YouTube Video Title";
$thumbnail = "https://via.placeholder.com/200x120?text=Video+Thumbnail";
$success = false;

if (isset($_POST['search']) || isset($_POST['video_url'])) {
    $video_url = trim($_POST['video_url']);
    
    if (!empty($video_url)) {
        $success = true;
        // ডাটাবেজে হিস্ট্রি সেভ করা
        $stmt = $conn->prepare("INSERT INTO download_history (video_url, video_title) VALUES (?, ?)");
        $stmt->bind_param("ss", $video_url, $video_title);
        $stmt->execute();
        $stmt->close();
    }
}
$conn->close();
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Download Options - YT Downloader Pro</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>

    <header>
        <h1>📥 YT Downloader Pro</h1>
        <nav>
            <a href="index.php">Home</a>
            <a href="history.php">Download History</a>
        </nav>
    </header>

    <div class="main-container" style="text-align: left;">
        <?php if ($success): ?>
            <h3>Video Found Successfully!</h3>
            <div class="result-box">
                <img src="<?php echo $thumbnail; ?>" alt="Thumbnail">
                <div>
                    <h4><?php echo $video_title; ?></h4>
                    <p style="margin: 5px 0; font-size: 14px; color: #777;">Quality & Format Options:</p>
                    <div class="download-options">
                        <a href="#" class="btn-download">Download MP4 (720p)</a>
                        <a href="#" class="btn-download">Download MP4 (360p)</a>
                        <a href="#" class="btn-download" style="background: #007bff;">Download MP3 (Audio)</a>
                    </div>
                </div>
            </div>
            <br>
            <a href="index.php" style="color: #ff0000; text-decoration: none; font-weight: bold;">← Convert Another Video</a>
        <?php else: ?>
            <h3 style="color: red; text-align: center;">Invalid URL or Request!</h3>
            <br>
            <div style="text-align: center;">
                <a href="index.php" class="btn-download" style="background: #ff0000;">Go Back</a>
            </div>
        <?php endif; ?>
    </div>

</body>
</html>