import mysql.connector
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs
from http.server import BaseHTTPRequestHandler, HTTPServer
import json

# Database configuration
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASS = 'root'
DB_NAME = 'meetify'

def connect_db():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME
    )

def fetch_meetings(user_id, start_time, end_time):
    db = connect_db()
    cursor = db.cursor(dictionary=True)
    query = """
    SELECT * FROM meetings 
    WHERE user_id = %s AND 
    ((start_time >= %s AND start_time < %s) OR 
     (end_time > %s AND end_time <= %s) OR 
     (start_time <= %s AND end_time >= %s))
    """
    cursor.execute(query, (user_id, start_time, end_time, start_time, end_time, start_time, end_time))
    meetings = cursor.fetchall()
    db.close()
    return meetings

def calculate_free_slots(meetings, start_time, end_time):
    free_slots = []
    current_time = start_time

    # Sort meetings by start time
    meetings.sort(key=lambda x: x['start_time'])

    for meeting in meetings:
        meeting_start_time = meeting['start_time']
        meeting_end_time = meeting['end_time']
        while current_time < meeting_start_time:
            next_slot_end = min(current_time + timedelta(hours=1), meeting_start_time)
            duration = (next_slot_end - current_time).seconds // 60
            if duration > 0:
                free_slots.append({
                    "start_time": current_time,
                    "end_time": next_slot_end,
                    "duration": duration
                })
            current_time = next_slot_end
        current_time = max(current_time, meeting_end_time)

    while current_time < end_time:
        next_slot_end = min(current_time + timedelta(hours=1), end_time)
        duration = (next_slot_end - current_time).seconds // 60
        if duration > 0:
            free_slots.append({
                "start_time": current_time,
                "end_time": next_slot_end,
                "duration": duration
            })
        current_time = next_slot_end

    return free_slots

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/fetch_slots':
            query = parse_qs(parsed_path.query)
            user_id = query.get('user_id', [None])[0]
            start_time = query.get('start_time', [None])[0]
            end_time = query.get('end_time', [None])[0]

            if not user_id or not start_time or not end_time:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'Missing query parameters')
                return

            start_time_dt = datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S')
            end_time_dt = datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%S')

            meetings = fetch_meetings(user_id, start_time_dt, end_time_dt)

            if not meetings:
                print("No meetings found")

            booked_meetings = [
                {
                    "start_time": meeting['start_time'].strftime('%Y-%m-%dT%H:%M:%S'),
                    "end_time": meeting['end_time'].strftime('%Y-%m-%dT%H:%M:%S'),
                    "timezone": meeting['timezone'],
                    "meeting_type": meeting['meeting_type']
                } for meeting in meetings
            ]

            free_slots = calculate_free_slots(meetings, start_time_dt, end_time_dt)

            free_slots_formatted = [
                {
                    "start_time": slot["start_time"].strftime('%Y-%m-%dT%H:%M:%S'),
                    "end_time": slot["end_time"].strftime('%Y-%m-%dT%H:%M:%S'),
                    "duration": slot["duration"]
                } for slot in free_slots if slot["duration"] > 0
            ]

            response = {
                "booked_meetings": booked_meetings,
                "free_slots": free_slots_formatted
            }

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Endpoint not found')

def run(server_class=HTTPServer, handler_class=RequestHandler, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting httpd server on port {port}...')
    httpd.serve_forever()

if __name__ == '__main__':
    run()
