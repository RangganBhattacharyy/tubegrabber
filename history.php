<?php
include 'db.php';

$result = $conn->query("SELECT * FROM download_history ORDER BY download_time DESC");
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Download History - YT Downloader Pro</title>
    <link rel="stylesheet" href="style.css">
    <style>
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th, td {
            padding: 12px;
            border: 1px solid #ddd;
            text-align: left;
        }
        th {
            background-color: #f8f9fa;
        }
    </style>
</head>
<body>

    <header>
        <h1>📥 YT Downloader Pro</h1>
        <nav>
            <a href="index.php">Home</a>
            <a href="history.php">Download History</a>
        </nav>
    </header>

    <div class="main-container" style="max-width: 900px; text-align: left;">
        <h2>Download History</h2>
        <p>List of all processed video links stored in the database.</p>

        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Video Title</th>
                    <th>URL</th>
                    <th>Time</th>
                </tr>
            </thead>
            <tbody>
                <?php if ($result->num_rows > 0): ?>
                    <?php while($row = $result->fetch_assoc()): ?>
                        <tr>
                            <td><?php echo $row['id']; ?></td>
                            <td><?php echo htmlspecialchars($row['video_title']); ?></td>
                            <td><a href="<?php echo htmlspecialchars($row['video_url']); ?>" target="_blank" style="color: #007bff;"><?php echo substr($row['video_url'], 0, 30); ?>...</a></td>
                            <td><?php echo $row['download_time']; ?></td>
                        </tr>
                    <?php endwhile; ?>
                <?php else: ?>
                    <tr>
                        <td colspan="4" style="text-align: center; color: #777;">No history found.</td>
                    </tr>
                <?php endif; ?>
            </tbody>
        </table>
        <br>
        <a href="index.php" style="color: #ff0000; text-decoration: none; font-weight: bold;">← Back to Home</a>
    </div>

</body>
</html>