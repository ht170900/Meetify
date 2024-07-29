from http.server import BaseHTTPRequestHandler, HTTPServer
import mysql.connector
import json
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta
import pytz
import requests

class RequestHandler(BaseHTTPRequestHandler):

    def connect_db(self):
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="root",
            database="meetify"
        )

    def parse_datetime(self, dt_str):
        try:
            dt = datetime.strptime(dt_str[:-5], '%Y-%m-%dT%H:%M:%S')
            if dt_str[-5:] != '+0000':
                tz = pytz.timezone('UTC')
                dt = tz.localize(dt).astimezone(pytz.utc)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError as e:
            print(f"Error parsing datetime: {e}")
            return None

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
        else:
            self._send_response({"error": "Invalid request"}, 404)

    def create_user(self, data):
        conn = self.connect_db()
        cursor = conn.cursor()
        query = "INSERT INTO users (name, email, preferred_timezone, dnd_start_time, dnd_end_time) VALUES (%s, %s, %s, %s, %s)"
        dnd_start_time = self.parse_datetime(data['dnd_start_time'])
        dnd_end_time = self.parse_datetime(data['dnd_end_time'])
        cursor.execute(query, (data['name'], data['email'], data['preferred_timezone'], dnd_start_time, dnd_end_time))
        conn.commit()
        cursor.close()
        conn.close()
        self._send_response({"message": "User created successfully"})

    def update_user(self, data, user_id):
        conn = self.connect_db()
        cursor = conn.cursor()
        dnd_start_time = self.parse_datetime(data['dnd_start_time'])
        dnd_end_time = self.parse_datetime(data['dnd_end_time'])
        if not dnd_start_time or not dnd_end_time:
            self._send_response({"error": "Invalid datetime format"}, 400)
            return
        query = "UPDATE users SET preferred_timezone = %s, dnd_start_time = %s, dnd_end_time = %s WHERE id = %s"
        cursor.execute(query, (data['preferred_timezone'], dnd_start_time, dnd_end_time, user_id))
        conn.commit()
        cursor.close()
        conn.close()
        self._send_response({"message": "User updated successfully"})

    def create_meeting(self, data, user_id):
        conn = self.connect_db()
        cursor = conn.cursor()
        try:
            start_time = self.parse_datetime(data['start_time'])
            end_time = self.parse_datetime(data['end_time'])
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


def run(server_class=HTTPServer, handler_class=RequestHandler, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting server at http://localhost:{port}')
    httpd.serve_forever()

if __name__ == '__main__':
    run()
