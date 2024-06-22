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


-- Insert users
INSERT INTO users (id, name, email, preferred_timezone, dnd_start_time, dnd_end_time)
VALUES
(7, 'John Doe', 'john@gmail.com', 'Asia/Kolkata', '2024-06-22 10:00:00', '2024-06-22 12:00:00'),
(8, 'Jane Smith', 'jane@gmail.com', 'Asia/Kolkata', '2024-06-22 15:00:00', '2024-06-22 16:00:00'),
(9, 'Alice Brown', 'alice@gmail.com', 'Asia/Kolkata', '2024-06-22 08:00:00', '2024-06-22 09:00:00'),
(10, 'Bob White', 'bob@gmail.com', 'Asia/Kolkata', '2024-06-22 14:00:00', '2024-06-22 15:00:00');

-- Insert meetings
INSERT INTO meetings (id, user_id, meeting_type, start_time, end_time, timezone, notification_interval)
VALUES
(7, 7, 'online', '2024-06-22 10:30:00', '2024-06-22 11:00:00', 'Asia/Kolkata', '*/1 * * * *'), -- During DND period
(8, 8, 'offline', '2024-06-22 16:30:00', '2024-06-22 17:00:00', 'Asia/Kolkata', '*/1 * * * *'), -- Post DND period
(9, 9, 'online', '2024-06-22 07:30:00', '2024-06-22 08:30:00', 'Asia/Kolkata', '*/1 * * * *'), -- Pre DND period
(10, 10, 'offline', '2024-06-22 14:30:00', '2024-06-22 15:30:00', 'Asia/Kolkata', '*/1 * * * *'); -- DND overlaps meeting time

-- Insert meetings
INSERT INTO meetings (id, user_id, meeting_type, start_time, end_time, timezone, notification_interval)
VALUES
(13, 7, 'online', '2024-06-23 03:29:00', '2024-06-23 03:56:00', 'Asia/Kolkata', '*/1 * * * *'); -- During DND period

-- Calculate meeting time 10 hours from now
SET @meeting_start_time = NOW() + INTERVAL 10 HOUR;
SET @meeting_end_time = @meeting_start_time + INTERVAL 1 HOUR;

-- Insert meetings
INSERT INTO meetings (id, user_id, meeting_type, start_time, end_time, timezone, notification_interval)
VALUES
(14, 1, 'online', @meeting_start_time, @meeting_end_time, 'Asia/Kolkata', '*/1 * * * *');

-- Check the inserted data
SELECT * FROM users;
-- Insert user
INSERT INTO users (id, name, email, preferred_timezone, dnd_start_time, dnd_end_time)
VALUES
(11, 'Test User', 'testuser@gmail.com', 'Asia/Kolkata', '2024-06-22 22:00:00', '2024-06-23 06:00:00');

-- Insert meeting
INSERT INTO meetings (id, user_id, meeting_type, start_time, end_time, timezone, notification_interval)
VALUES
(15, 11, 'online', '2024-06-23 02:30:00', '2024-06-23 03:30:00', 'Asia/Kolkata', '*/1 * * * *');

-- Check the inserted data
SELECT * FROM users WHERE id = 11;
SELECT * FROM meetings WHERE id = 15;

UPDATE users SET preferred_timezone = 'Asia/Kolkata' WHERE preferred_timezone = 'IST'and id = "2";
INSERT INTO meetings (id, user_id, meeting_type, start_time, end_time, timezone, notification_interval)
VALUES (1, 1, 'online', NOW(), NOW() + INTERVAL 1 HOUR, 'Asia/Kolkata', '* * * * *')
ON DUPLICATE KEY UPDATE
user_id = VALUES(user_id), meeting_type = VALUES(meeting_type), start_time = VALUES(start_time), end_time = VALUES(end_time), timezone = VALUES(timezone), notification_interval = VALUES(notification_interval);

SELECT start_time, end_time, timezone, meeting_type 
FROM meetings 
WHERE user_id = '%s' 
  AND (
    (start_time < '%s' AND end_time > '%s') OR 
    (start_time < '%s' AND end_time > '%s') OR 
    (start_time >= '%s' AND end_time <= '%s')
  );

INSERT INTO users (id, name, email, preferred_timezone, dnd_start_time, dnd_end_time)
VALUES (1, 'John Doe', 'john.doe@example.com', 'Asia/Kolkata', '2024-06-21 22:00:00', '2024-06-22 07:00:00')
ON DUPLICATE KEY UPDATE
name = VALUES(name), email = VALUES(email), preferred_timezone = VALUES(preferred_timezone), dnd_start_time = VALUES(dnd_start_time), dnd_end_time = VALUES(dnd_end_time);


-- Insert user data with DND period active
INSERT INTO users (id, name, email, preferred_timezone, dnd_start_time, dnd_end_time)
VALUES (1, 'John Doe', 'john.doe@example.com', 'Asia/Kolkata', '2024-06-21 14:00:00', '2024-06-21 16:00:00')
ON DUPLICATE KEY UPDATE
name = VALUES(name), email = VALUES(email), preferred_timezone = VALUES(preferred_timezone), dnd_start_time = VALUES(dnd_start_time), dnd_end_time = VALUES(dnd_end_time);

-- Insert meeting data
INSERT INTO meetings (id, user_id, meeting_type, start_time, end_time, timezone, notification_interval)
VALUES (1, 1, 'online', '2024-06-21 15:30:00', '2024-06-21 16:30:00', 'Asia/Kolkata', '* * * * *')
ON DUPLICATE KEY UPDATE
user_id = VALUES(user_id), meeting_type = VALUES(meeting_type), start_time = VALUES(start_time), end_time = VALUES(end_time), timezone = VALUES(timezone), notification_interval = VALUES(notification_interval);

