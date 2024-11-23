from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

WRITER_URL = "http://localhost:4001"
READER_URL = "http://localhost:4003"
ANALYTICS_URL = "http://localhost:4002"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/set', methods=['POST'])
def set_value():
    data = request.json
    response = requests.post(f"{WRITER_URL}/set", json=data)
    return jsonify(response.json()), response.status_code

@app.route('/api/get/<key>')
def get_value(key):
    response = requests.get(f"{READER_URL}/get/{key}")
    return jsonify(response.json()), response.status_code

@app.route('/api/delete', methods=['DELETE'])
def delete_value():
    data = request.json
    response = requests.delete(f"{WRITER_URL}/delete", json=data)
    return jsonify(response.json()), response.status_code

@app.route('/api/stats')
def get_stats():
    response = requests.get(f"{ANALYTICS_URL}/stats")
    return jsonify(response.json()), response.status_code

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)