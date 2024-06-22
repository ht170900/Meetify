import mysql.connector
from datetime import datetime, timedelta
import pytz
import time
import requests

# Database connection
def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="meetify"
    )

# Convert time to user's preferred timezone
def convert_to_timezone(time_input, timezone):
    if isinstance(time_input, str):
        utc_time = datetime.strptime(time_input, "%Y-%m-%dT%H:%M:%S%z")
    elif isinstance(time_input, datetime):
        utc_time = time_input
    else:
        raise TypeError("time_input must be a str or datetime object")
    target_tz = pytz.timezone(timezone)
    return utc_time.astimezone(target_tz)

# Convert DND times to the user's preferred timezone
def convert_dnd_to_timezone(dnd_start_input, dnd_end_input, timezone):
    dnd_start = convert_to_timezone(dnd_start_input, timezone)
    dnd_end = convert_to_timezone(dnd_end_input, timezone)
    return dnd_start, dnd_end

# Check if current time is within DND period
def is_within_dnd(dnd_start_input, dnd_end_input, current_time, timezone):
    dnd_start, dnd_end = convert_dnd_to_timezone(dnd_start_input, dnd_end_input, timezone)
    return dnd_start <= current_time <= dnd_end

# Send notification
def send_notification(meeting):
    webhook_url = "https://webhook.site/5eabab59-d7c0-4029-be1d-50d7dd6c83fa"
    data = {
        "user_id": meeting['user_id'],
        "meeting_id": meeting['id'],
        "message": f"You have a meeting scheduled at {meeting['start_time']}."
    }
    response = requests.post(webhook_url, json=data)
    print(f"Notification sent for meeting {meeting['id']} with status code {response.status_code}")

# Main function to schedule notifications
def schedule_notifications():
    db = connect_db()
    cursor = db.cursor(dictionary=True)
    
    while True:
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        
        for user in users:
            cursor.execute(f"SELECT * FROM meetings WHERE user_id = {user['id']}")
            meetings = cursor.fetchall()
            
            for meeting in meetings:
                current_time = datetime.now(pytz.timezone(user['preferred_timezone']))
                meeting_start_time = convert_to_timezone(meeting['start_time'], user['preferred_timezone'])
                meeting_end_time = convert_to_timezone(meeting['end_time'], user['preferred_timezone'])
                
                print(f"Current time: {current_time}")
                print(f"Meeting start time: {meeting_start_time}")
                
                # Ensure notifications are only sent for future meetings
                if meeting_start_time > current_time:
                    notification_time = meeting_start_time - timedelta(hours=10) # Notify 10 hours before meeting starts
                    print(f"Notification time: {notification_time}")
                    dnd_start_time, dnd_end_time = convert_dnd_to_timezone(user['dnd_start_time'], user['dnd_end_time'], user['preferred_timezone'])
                    
                    if notification_time >= current_time - timedelta(minutes=5): # Check if current time is within a 5-minute window after the notification time
                        if is_within_dnd(user['dnd_start_time'], user['dnd_end_time'], notification_time, user['preferred_timezone']):
                            # If notification time is within DND, send it before DND starts
                            if notification_time < dnd_start_time:
                                notification_time = dnd_start_time - timedelta(minutes=5) # 5 minutes before DND starts
                                print(f"Adjusted notification time due to DND: {notification_time}")
                            else:
                                # If notification time is within DND period, skip sending the notification
                                print(f"Notification time for meeting {meeting['id']} falls within DND period for user {user['id']}, skipping.")
                                continue
                        
                        if current_time >= notification_time:
                            print(f"Sending notification for meeting {meeting['id']} of user {user['id']} at {notification_time}")
                            send_notification(meeting)
                        else:
                            print(f"Notification time {notification_time} has not been reached yet for meeting {meeting['id']} of user {user['id']}")
                    
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    schedule_notifications()
