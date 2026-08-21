<?php
/**
 * Advanced Database Connection using PDO (PHP Data Objects)
 * Project: TubeGrabber Studio
 */

$host = "localhost";
$username = "root";
$password = "";
$dbname = "tubegrabber_db"; // এখানে ডাটাবেজ নাম আপডেট করা হলো

try {
    // ডিবি কানেকশন তৈরি (PDO মোডে)
    $dsn = "mysql:host=$host;dbname=$dbname;charset=utf8mb4";
    $options = [
        PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION, // এরর হ্যান্ডলিং এক্সেপশন মোডে সেট করা
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,       // ডাটা অ্যাসোসিয়েটিভ অ্যারে হিসেবে ফেচ করা
        PDO::ATTR_EMULATE_PREPARES   => false,                  // রিয়েল প্রিপেয়ার্ড স্টেটমেন্ট ব্যবহার
    ];

    $pdo = new PDO($dsn, $username, $password, $options);

    // অটো টেবিল তৈরি (যদি না থাকে) - সেফ ও সিকিউর কোয়েরি
    $tableQuery = "CREATE TABLE IF NOT EXISTS download_history (
        id INT AUTO_INCREMENT PRIMARY KEY,
        video_url TEXT NOT NULL,
        video_title VARCHAR(255) DEFAULT 'Untitled Video',
        download_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;";

    $pdo->exec($tableQuery);

} catch (PDOException $e) {
    // প্রফেশনাল এরর মেসেজ হ্যান্ডলিং
    error_log("Database Connection Error: " . $e->getMessage());
    die("⚠️ Database connection failed. Please try again later.");
}
?>