<?php
include 'db.php';

// ডিলিট রিকোয়েস্ট হ্যান্ডেল করার কোড (যদি কোনো রেকর্ড ডিলিট করতে চান)
if (isset($_GET['delete_id'])) {
    $delete_id = $_GET['delete_id'];
    $stmt = $pdo->prepare("DELETE FROM download_history WHERE id = ?");
    $stmt->execute([$delete_id]);
    header("Location: admin.php");
    exit();
}

// ডাটাবেজ থেকে সমস্ত ডাউনলোড হিস্ট্রি ফেচ করা
$stmt = $pdo->query("SELECT * FROM download_history ORDER BY download_time DESC");
$history_list = $stmt->fetchAll();

// মোট ডাউনলোডের সংখ্যা গণনা
$total_downloads = count($history_list);
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Dashboard - TubeGrabber Studio</title>
    <link rel="stylesheet" href="style.css">
    <style>
        .admin-container {
            max-width: 1000px;
            margin: 40px auto;
            background: #fff;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
            text-align: left;
        }
        .stats-box {
            display: flex;
            gap: 20px;
            margin-bottom: 25px;
        }
        .stat-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #e9ecef;
            flex: 1;
        }
        .stat-card h3 {
            margin-bottom: 5px;
            color: #555;
            font-size: 16px;
        }
        .stat-card p {
            font-size: 24px;
            font-weight: bold;
            color: #ff0000;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        th, td {
            padding: 12px;
            border: 1px solid #ddd;
            text-align: left;
            font-size: 14px;
        }
        th {
            background-color: #f1f3f5;
            color: #333;
        }
        .btn-delete {
            background: #dc3545;
            color: white;
            padding: 6px 12px;
            border-radius: 4px;
            text-decoration: none;
            font-size: 12px;
            font-weight: bold;
        }
        .btn-delete:hover {
            background: #c82333;
        }
    </style>
</head>
<body>

    <header>
        <h1>🛠️ TubeGrabber Admin</h1>
        <nav>
            <a href="index.php">Home</a>
            <a href="admin.php" style="color: #ff0000;">Admin Panel</a>
        </nav>
    </header>

    <div class="admin-container">
        <h2>Admin Dashboard</h2>
        <p>Manage and monitor all user link requests from the database.</p>

        <!-- স্ট্যাটিস্টিক্স কার্ড -->
        <div class="stats-box">
            <div class="stat-card">
                <h3>Total Requests / Downloads</h3>
                <p><?php echo $total_downloads; ?></p>
            </div>
        </div>

        <h3>Activity Log</h3>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Video Title</th>
                    <th>Video URL</th>
                    <th>Time</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody>
                <?php if ($total_downloads > 0): ?>
                    <?php foreach($history_list as $row): ?>
                        <tr>
                            <td><?php echo $row['id']; ?></td>
                            <td><?php echo htmlspecialchars($row['video_title']); ?></td>
                            <td>
                                <a href="<?php echo htmlspecialchars($row['video_url']); ?>" target="_blank" style="color: #007bff; text-decoration: none;">
                                    <?php echo htmlspecialchars(substr($row['video_url'], 0, 40)); ?>...
                                </a>
                            </td>
                            <td><?php echo $row['download_time']; ?></td>
                            <td>
                                <a href="admin.php?delete_id=<?php echo $row['id']; ?>" class="btn-delete" onclick="return confirm('Are you sure you want to delete this record?');">Delete</a>
                            </td>
                        </tr>
                    <?php endforeach; ?>
                <?php else: ?>
                    <tr>
                        <td colspan="5" style="text-align: center; color: #777;">No records found in the database.</td>
                    </tr>
                <?php endif; ?>
            </tbody>
        </table>
        
        <br>
        <a href="index.php" style="color: #ff0000; text-decoration: none; font-weight: bold;">← Back to Website Home</a>
    </div>

</body>
</html>