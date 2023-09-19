import os
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import re
from dotenv import load_dotenv

# import mysql.connector
# from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
load_dotenv()

# mysql_config = {
#     'user': os.environ.get("MYSQL_USER"),
#     'password': os.environ.get("MYSQL_PASSWORD"),
#     'host': os.environ.get("MYSQL_HOST"),
#     'database': os.environ.get("MYSQL_DATABASE"),
# }

# conn = mysql.connector.connect(**mysql_config)
# cursor = conn.cursor()

def parse_log_line(line):
    pattern = r'(\S+) - - \[([^\]]+)\] "(.+)" (\d+) \d+ ".+" ".+"'
    match = re.match(pattern, line)
    if match:
        ip_address, timestamp, request, http_response_code = match.groups()
        return ip_address, timestamp, request, int(http_response_code)
    return None

def read_log_file(file_path):
    log_entries = []
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line:
                parsed_info = parse_log_line(line)
                if parsed_info:
                    ip_address, _, _, http_response_code = parsed_info
                    entry_type = 'secure' if http_response_code == 200 else 'error'
                    log_entry = {'ip_address': ip_address, 'timestamp': _, 'request': _, 'http_response_code': http_response_code, 'type': entry_type}
                    log_entries.append(log_entry)
    return log_entries

def add_log_entry(ip, timestamp, request, http_response_code):
    log_entry = f'{ip} - - [{timestamp}] "{request}" {http_response_code} 0 "-" "-" "-"'
    with open('error.txt', 'a') as file:
        file.write('\n' + log_entry)
    # input_format = '%d/%b/%Y:%H:%M:%S +0000'
    # parsed_timestamp = datetime.strptime(timestamp, input_format)
    # mysql_datetime = parsed_timestamp.strftime('%Y-%m-%d %H:%M:%S')
    # entry_type = 'secure' if http_response_code == 200 else 'error'
    # query = "INSERT INTO temp_log_entries (ip_address, timestamp, request, http_response_code, type) VALUES (%s, %s, %s, %s, %s)"
    # values = (ip, mysql_datetime, request, http_response_code, entry_type)
    # cursor.execute(query, values)
    # conn.commit()


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_log', methods=['POST'])
def add_log():
    data = request.get_json()
    ip = data.get('ip', '')
    timestamp = data.get('timestamp', '')
    request_str = data.get('request', '')
    http_response_code = data.get('http_response_code', 0)

    add_log_entry(ip, timestamp, request_str, http_response_code)

    log_entries = read_log_file('error.txt')
    print('Updated entries:', len(log_entries)) 

    socketio.emit('log_data', {'logs': log_entries}, namespace='/') 
    
    return jsonify({'message': 'Log entry added successfully'})

@socketio.on('connect')
def on_connect():
    print('Client connected')
    log_file_path = 'error.txt'
    log_entries = read_log_file(log_file_path)
    socketio.emit('log_data', {'logs': log_entries})

@socketio.on('disconnect')
def on_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    socketio.run(app, debug=True)
