import mysql.connector
import requests
from datetime import datetime, timedelta
import pytz
from croniter import croniter
import time

# Timezone abbreviation to pytz timezone mapping
TIMEZONE_MAPPING = {
    'IST': 'Asia/Kolkata',
    # Add more mappings as needed
}

def insert_test_data():
    # Database connection
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="meetify"
    )

    cursor = db.cursor(dictionary=True)

    # Insert user data with and without DND period active
    cursor.execute("""
    INSERT INTO users (id, name, email, preferred_timezone, dnd_start_time, dnd_end_time)
    VALUES (1, 'John Doe', 'john.doe@example.com', 'Asia/Kolkata', '2024-06-21 22:00:00', '2024-06-22 07:00:00')
    ON DUPLICATE KEY UPDATE
    name = VALUES(name), email = VALUES(email), preferred_timezone = VALUES(preferred_timezone), dnd_start_time = VALUES(dnd_start_time), dnd_end_time = VALUES(dnd_end_time);
    """)
    
    cursor.execute("""
    INSERT INTO users (id, name, email, preferred_timezone, dnd_start_time, dnd_end_time)
    VALUES (2, 'Jane Doe', 'jane.doe@example.com', 'Asia/Kolkata', '2024-06-21 13:00:00', '2024-06-21 14:00:00')
    ON DUPLICATE KEY UPDATE
    name = VALUES(name), email = VALUES(email), preferred_timezone = VALUES(preferred_timezone), dnd_start_time = VALUES(dnd_start_time), dnd_end_time = VALUES(dnd_end_time);
    """)

    # Insert meeting data
    cursor.execute("""
    INSERT INTO meetings (id, user_id, meeting_type, start_time, end_time, timezone, notification_interval)
    VALUES (1, 1, 'online', NOW() + INTERVAL 1 MINUTE, NOW() + INTERVAL 1 HOUR, 'Asia/Kolkata', '* * * * *')
    ON DUPLICATE KEY UPDATE
    user_id = VALUES(user_id), meeting_type = VALUES(meeting_type), start_time = VALUES(start_time), end_time = VALUES(end_time), timezone = VALUES(timezone), notification_interval = VALUES(notification_interval);
    """)
    
    cursor.execute("""
    INSERT INTO meetings (id, user_id, meeting_type, start_time, end_time, timezone, notification_interval)
    VALUES (2, 2, 'online', NOW() + INTERVAL 1 MINUTE, NOW() + INTERVAL 1 HOUR, 'Asia/Kolkata', '* * * * *')
    ON DUPLICATE KEY UPDATE
    user_id = VALUES(user_id), meeting_type = VALUES(meeting_type), start_time = VALUES(start_time), end_time = VALUES(end_time), timezone = VALUES(timezone), notification_interval = VALUES(notification_interval);
    """)

    db.commit()
    cursor.close()
    db.close()

def send_notifications():
    try:
        # Database connection
        db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="root",
            database="meetify"
        )
        cursor = db.cursor(dictionary=True)

        # Fetch upcoming meetings
        cursor.execute("""
        SELECT m.*, u.preferred_timezone, u.dnd_start_time, u.dnd_end_time
        FROM meetings m
        JOIN users u ON m.user_id = u.id
        WHERE m.start_time > NOW()
        """)
        meetings = cursor.fetchall()

        if not meetings:
            print("No upcoming meetings found.")

        # Timezone handling and notification logic
        for meeting in meetings:
            print(f"Processing meeting ID: {meeting['id']}")

            # Convert preferred timezone to a valid pytz timezone
            preferred_timezone = TIMEZONE_MAPPING.get(meeting['preferred_timezone'], meeting['preferred_timezone'])
            try:
                user_tz = pytz.timezone(preferred_timezone)
            except pytz.UnknownTimeZoneError:
                print(f"Unknown timezone: {preferred_timezone}")
                continue
            
            now_user_tz = datetime.now(pytz.utc).astimezone(user_tz)
            start_user_tz = meeting['start_time'].replace(tzinfo=pytz.utc).astimezone(user_tz)
            dnd_start_user_tz = meeting['dnd_start_time'].replace(tzinfo=pytz.utc).astimezone(user_tz)
            dnd_end_user_tz = meeting['dnd_end_time'].replace(tzinfo=pytz.utc).astimezone(user_tz)
            
            print(f"Current time in user timezone: {now_user_tz}")
            print(f"Meeting start time in user timezone: {start_user_tz}")
            print(f"DND period: {dnd_start_user_tz} to {dnd_end_user_tz}")
            
            # Check if current time is within DND period
            if dnd_start_user_tz <= now_user_tz <= dnd_end_user_tz:
                print(f"Skipped notification during DND period for meeting at {start_user_tz}")
                continue  # Skip notification during DND
            
            # Determine the next notification time using croniter
            cron = croniter(meeting['notification_interval'], now_user_tz)
            next_notification = cron.get_next(datetime)
            
            print(f"Next notification time: {next_notification}")
            print(f"Notification interval: {meeting['notification_interval']}")

            # Adjusted check to send the notification immediately for testing
            if now_user_tz >= next_notification:  # Corrected condition for testing
                print(f"Sending notification for meeting at {start_user_tz}")
                # Sending notification via webhook
                response = requests.post("https://webhook.site/5eabab59-d7c0-4029-be1d-50d7dd6c83fa", json={"message": f"Reminder: You have a meeting at {start_user_tz}"})
                if response.status_code == 200:
                    print(f"Notification sent successfully for meeting at {start_user_tz}")
                else:
                    print(f"Failed to send notification for meeting at {start_user_tz}. Status code: {response.status_code}")
            else:
                print(f"Not time to send notification yet for meeting at {start_user_tz}")

        print("Notifications processed.")
        cursor.close()
        db.close()
    except Exception as e:
        print(f"An error occurred: {e}")

# Insert test data
insert_test_data()

# Run the notification sender in a continuous loop
while True:
    send_notifications()
    time.sleep(60)  # Wait for 1 minute before checking again
