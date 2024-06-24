CREATE DATABASE meetify;
USE meetify;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255),
    preferred_timezone VARCHAR(50),
    dnd_start_time DATETIME,
    dnd_end_time DATETIME
);

CREATE TABLE meetings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    meeting_type ENUM('online', 'offline') NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    timezone VARCHAR(50) NOT NULL,
    notification_interval VARCHAR(255) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

select * from users;
select * from meetings;



INSERT INTO meetings (user_id, meeting_type, start_time, end_time, timezone, notification_interval) VALUES 
(1, 'online', '2024-06-20 03:00:00', '2024-06-20 03:59:59', 'IST', '0 10 * * *'),
(1, 'offline', '2024-06-20 04:00:00', '2024-06-20 06:00:00', 'IST', '0 10 * * *');

INSERT INTO users ( name, email, preferred_timezone, dnd_start_time, dnd_end_time)
VALUES
('John Doe', 'john@gmail.com', 'Asia/Kolkata', '2024-06-22 10:00:00', '2024-06-22 12:00:00'),
('Jane Smith', 'jane@gmail.com', 'Asia/Kolkata', '2024-06-22 15:00:00', '2024-06-22 16:00:00'),
('Alice Brown', 'alice@gmail.com', 'Asia/Kolkata', '2024-06-22 08:00:00', '2024-06-22 09:00:00'),
('Bob White', 'bob@gmail.com', 'Asia/Kolkata', '2024-06-22 14:00:00', '2024-06-22 15:00:00');


INSERT INTO meetings ( meeting_type, start_time, end_time, timezone, notification_interval)
VALUES
('online', '2024-06-22 10:30:00', '2024-06-22 11:00:00', 'Asia/Kolkata', '*/1 * * * *'), -- During DND period
( 'offline', '2024-06-22 16:30:00', '2024-06-22 17:00:00', 'Asia/Kolkata', '*/1 * * * *'), -- Post DND period
('online', '2024-06-22 07:30:00', '2024-06-22 08:30:00', 'Asia/Kolkata', '*/1 * * * *'), -- Pre DND period
( 'offline', '2024-06-22 14:30:00', '2024-06-22 15:30:00', 'Asia/Kolkata', '*/1 * * * *'); -- DND overlaps meeting time

INSERT INTO meetings (id, user_id, meeting_type, start_time, end_time, timezone, notification_interval)
VALUES
(13, 7, 'online', '2024-06-23 03:29:00', '2024-06-23 03:56:00', 'Asia/Kolkata', '*/1 * * * *'); -- During DND period

-- Check the inserted data
SELECT * FROM users WHERE id = 11;
SELECT * FROM meetings WHERE id = 15;

UPDATE users SET preferred_timezone = 'Asia/Kolkata' WHERE preferred_timezone = 'IST'and id = "2";
INSERT INTO meetings (id, user_id, meeting_type, start_time, end_time, timezone, notification_interval)
VALUES (1, 1, 'online', NOW(), NOW() + INTERVAL 1 HOUR, 'Asia/Kolkata', '* * * * *')
ON DUPLICATE KEY UPDATE
user_id = VALUES(user_id), meeting_type = VALUES(meeting_type), start_time = VALUES(start_time), end_time = VALUES(end_time), timezone = VALUES(timezone), notification_interval = VALUES(notification_interval);
