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







from http.server import BaseHTTPRequestHandler, HTTPServer
import mysql.connector
import json
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta
import pytz
import requests

def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="meetify"
    )

def parse_datetime(dt_str):
        # This function parses an ISO 8601 string, converts it to UTC (if necessary), and formats it for MySQL
        dt = datetime.strptime(dt_str[:-5], '%Y-%m-%dT%H:%M:%S')
        if dt_str[-5:] != '+0000':  # Handling non-UTC timezones if needed
            tz = pytz.timezone('UTC')
            dt = tz.localize(dt).astimezone(pytz.utc)
        return dt.strftime('%Y-%m-%d %H:%M:%S')

def parse_datetime1(dt_str):
    # Assuming the input is in the format '2024-06-21T03:49:43+0000'
    try:
        # Parse the datetime string to a datetime object without timezone
        dt = datetime.strptime(dt_str[:-5], '%Y-%m-%dT%H:%M:%S')
        # Convert to UTC if necessary, here assuming the timezone offset is always '+0000'
        if dt_str[-5:] != '+0000':
            tz_original = pytz.timezone('UTC')  # Modify as per the actual timezone, if needed
            dt = dt.replace(tzinfo=pytz.utc)
        # Format to MySQL compatible datetime string
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except ValueError as e:
        print(f"Error parsing datetime: {e}")
        return None

def parse_datetime_iso(dt_str):
    # Handles datetime string with timezone information
    if 'Z' in dt_str:
        return datetime.strptime(dt_str, '%Y-%m-%dT%H:%M:%S%z')
    else:
        return datetime.strptime(dt_str, '%Y-%m-%dT%H:%M:%S')

def format_datetime_with_tz(dt, tz_str='UTC'):
    tz = pytz.timezone(tz_str)
    dt_aware = dt.astimezone(tz)
    return dt_aware.strftime('%Y-%m-%dT%H:%M:%S%z')


def format_datetime_with_tz(dt, tz_str='UTC'):
    # Create a timezone-aware datetime object
    tz = pytz.timezone(tz_str)
    dt_aware = dt.replace(tzinfo=pytz.utc).astimezone(tz)
    return dt_aware.strftime('%Y-%m-%dT%H:%M:%S%z')

class RequestHandler(BaseHTTPRequestHandler):
    def _send_response(self, content, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(content).encode('utf-8'))

    def do_POST(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query_components = parse_qs(parsed_path.query)

        length = int(self.headers['Content-Length'])
        post_data = json.loads(self.rfile.read(length))

        if path == '/create_user':
            self.create_user(post_data)
        elif path == '/update_user':
            if 'id' in query_components:
                user_id = int(query_components['id'][0])
                self.update_user(post_data, user_id)
            else:
                self._send_response({"error": "User ID is required"}, 400)
        elif path == '/create_meeting':
            if 'id' in query_components:
                user_id = int(query_components['id'][0])
                self.create_meeting(post_data, user_id)
            else:
                self._send_response({"error": "User ID is required"}, 400)
        elif path == '/send_notification':
            if 'meeting_id' in query_components and 'user_id' in query_components:
                meeting_id = int(query_components['meeting_id'][0])
                user_id = int(query_components['user_id'][0])
                self.send_notification(meeting_id, user_id)
            else:
                self._send_response({"error": "Meeting ID and User ID are required"}, 400)
        else:
            self._send_response({"error": "Invalid request"}, 404)

    def create_user(self, data):
        conn = connect_db()
        cursor = conn.cursor()
        query = "INSERT INTO users (name, email, preferred_timezone, dnd_start_time, dnd_end_time) VALUES (%s, %s, %s, %s, %s)"
        # Convert datetime fields before inserting into the database
        dnd_start_time = parse_datetime(data['dnd_start_time'])
        dnd_end_time = parse_datetime(data['dnd_end_time'])
        cursor.execute(query, (data['name'], data['email'], data['preferred_timezone'], dnd_start_time, dnd_end_time))
        conn.commit()
        cursor.close()
        conn.close()
        self._send_response({"message": "User created successfully"})

    def update_user(self, data, user_id):
        try:
            conn = connect_db()
            cursor = conn.cursor()
            # Parse datetime fields before updating in the database
            dnd_start_time = parse_datetime1(data['dnd_start_time'])
            dnd_end_time = parse_datetime1(data['dnd_end_time'])
            if not dnd_start_time or not dnd_end_time:
                self._send_response({"error": "Invalid datetime format"}, 400)
                return
            
            query = "UPDATE users SET preferred_timezone = %s, dnd_start_time = %s, dnd_end_time = %s WHERE id = %s"
            cursor.execute(query, (data['preferred_timezone'], dnd_start_time, dnd_end_time, user_id))
            conn.commit()
            cursor.close()
            conn.close()
            self._send_response({"message": "User updated successfully"})
        except mysql.connector.Error as err:
            print(f"Error in database operation: {err}")
            self._send_response({"error": "Database error"}, 500)
        except Exception as e:
            print(f"General error: {e}")
            self._send_response({"error": "Server error"}, 500)


    def create_meeting(self, data, user_id):
        conn = connect_db()
        cursor = conn.cursor()
        try:
            # Correctly parse the datetime fields before inserting into the database
            start_time = parse_datetime1(data['start_time'])
            end_time = parse_datetime1(data['end_time'])
            if not start_time or not end_time:
                self._send_response({"error": "Invalid datetime format"}, 400)
                return

            query = "INSERT INTO meetings (user_id, meeting_type, start_time, end_time, timezone, notification_interval) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(query, (user_id, data['meeting_type'], start_time, end_time, data['timezone'], data['notification_interval']))
            conn.commit()
            self._send_response({"message": "Meeting created successfully"})
        except mysql.connector.Error as err:
            print(f"Database error: {err}")
            self._send_response({"error": "Database error"}, 500)
        except Exception as e:
            print(f"Error: {e}")
            self._send_response({"error": "Server error"}, 500)
        finally:
            cursor.close()
            conn.close()

    def do_GET(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/get_free_slots':  # Make sure this matches your curl command
            query_components = parse_qs(parsed_path.query)
            user_id = int(query_components['user_id'][0])
            start_time = query_components['start_time'][0]
            end_time = query_components['end_time'][0]
            result = self.get_free_slots(user_id, start_time, end_time)
            self._send_response(result)
        else:
            self._send_response({"error": "Invalid request"}, 404)

    
    # def get_free_slots(self, user_id, query_start, query_end):
    #     conn = connect_db()
    #     cursor = conn.cursor(dictionary=True)
    #     query_start_dt = parse_datetime_iso(query_start)
    #     query_end_dt = parse_datetime_iso(query_end)

    #     # Fetch meetings that overlap with the query time range
    #     cursor.execute("""
    #         SELECT start_time, end_time, timezone, meeting_type
    #         FROM meetings
    #         WHERE user_id = %s AND ((start_time < %s AND end_time > %s) OR (start_time >= %s AND end_time <= %s))
    #         ORDER BY start_time ASC
    #     """, (user_id, query_end_dt, query_start_dt, query_start_dt, query_end_dt))
    #     meetings = cursor.fetchall()

    #     formatted_meetings = []
    #     free_slots = []
    #     last_end_time = query_start_dt

    #     # Iterate through each meeting to calculate free time slots
    #     for meeting in meetings:
    #         start_dt = parse_datetime_iso(meeting['start_time']).astimezone(pytz.timezone(meeting['timezone']))
    #         end_dt = parse_datetime_iso(meeting['end_time']).astimezone(pytz.timezone(meeting['timezone']))

    #         # Format and append booked meetings
    #         formatted_meetings.append({
    #             "start_time": start_dt.strftime('%Y-%m-%dT%H:%M:%S%z'),
    #             "end_time": end_dt.strftime('%Y-%m-%dT%H:%M:%S%z'),
    #             "timezone": meeting['timezone'],
    #             "meeting_type": meeting['meeting_type']
    #         })

    #         # Calculate the free slots between meetings
    #         while last_end_time < start_dt:
    #             next_hour = (last_end_time + timedelta(hours=1)).replace(minute=0, second=0)
    #             if next_hour > start_dt:
    #                 next_hour = start_dt
    #             free_slots.append({
    #                 "start_time": last_end_time.strftime('%Y-%m-%dT%H:%M:%S%z'),
    #                 "end_time": (next_hour - timedelta(seconds=1)).strftime('%Y-%m-%dT%H:%M:%S%z'),
    #                 "duration": int((next_hour - last_end_time).total_seconds() / 60)
    #             })
    #             last_end_time = next_hour
    #         last_end_time = max(end_dt, last_end_time)

    #     # Calculate any remaining free time after the last meeting
    #     while last_end_time < query_end_dt:
    #         next_hour = (last_end_time + timedelta(hours=1)).replace(minute=0, second=0)
    #         if next_hour > query_end_dt:
    #             next_hour = query_end_dt
    #         free_slots.append({
    #             "start_time": last_end_time.strftime('%Y-%m-%dT%H:%M:%S%z'),
    #             "end_time": (next_hour - timedelta(seconds=1)).strftime('%Y-%m-%dT%H:%M:%S%z'),
    #             "duration": int((next_hour - last_end_time).total_seconds() / 60)
    #         })
    #         last_end_time = next_hour

    #     cursor.close()
    #     conn.close()

    #     # Return both booked meetings and free slots
    #     return json.dumps({
    #         "booked_meetings": formatted_meetings,
    #         "free_slots": free_slots
    #     }, indent=4)


    def send_notification(self, meeting_id, user_id):
        conn = connect_db()
        cursor = conn.cursor()
        try:
            # Fetch meeting and user details
            cursor.execute("SELECT start_time FROM meetings WHERE id = %s AND user_id = %s", (meeting_id, user_id))
            meeting = cursor.fetchone()
            cursor.execute("SELECT email, preferred_timezone, notification_interval, dnd_start_time, dnd_end_time FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()

            # Call the send notification function
            self.actually_send_notification(meeting, user)
            self._send_response({"message": "Notification triggered successfully"})
        except mysql.connector.Error as err:
            print(f"Database error: {err}")
            self._send_response({"error": "Database error"}, 500)
        except Exception as e:
            print(f"Error: {e}")
            self._send_response({"error": "Server error"}, 500)
        finally:
            cursor.close()
            conn.close()


def run(server_class=HTTPServer, handler_class=RequestHandler, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting server at http://localhost:{port}')
    httpd.serve_forever()

if __name__ == '__main__':
    run()
