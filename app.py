from flask import Flask, request, jsonify
import requests
import time
import re
import os

app = Flask(__name__)

def get_vehicle_token(reg_no):
    url = "https://www.royalsundaram.in/car-insurance/proxy/apiproxy/eappspolicyservices/getTokenForVehicleDetails"

    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "registrationno": reg_no,
        "origin": "https://www.royalsundaram.in",
        "referer": "https://www.royalsundaram.in/car-insurance/",
        "sec-fetch-site": "same-origin",
        "sec-fetch-mode": "cors",
        "sec-fetch-dest": "empty",
    }

    try:
        response = requests.post(url, headers=headers, json={}, timeout=15)
        return response.json()
    except:
        return None


def fetch_vehicle_details(token, reg_no):
    url = "https://www.royalsundaram.in/car-insurance/proxy/apiproxy/eappspolicyservices/getVehicleDetails"

    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "origin": "https://www.royalsundaram.in",
        "referer": "https://www.royalsundaram.in/car-insurance/",
        "registrationno": reg_no,
        "token": token
    }

    data = {
        "registrationNo": reg_no,
        "token": token
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=15)
        return response.json()
    except:
        return None


@app.route('/rc', methods=['GET'])
def rc_details():
    reg_no = request.args.get('num', '').strip().upper()
    
    if not reg_no:
        return jsonify({
            "error": True,
            "message": "Registration number required",
            "usage": "/rc?num=MH02AB1234"
        }), 400
    
    # Validate format
    if not re.match(r'^[A-Z]{2}\d{1,2}[A-Z]{1,3}\d{1,4}$', reg_no):
        return jsonify({
            "error": True,
            "message": "Invalid registration format",
            "example": "MH02AB1234"
        }), 400
    
    start_time = time.time()
    
    # Step 1: Get Token
    token_data = get_vehicle_token(reg_no)
    
    if not token_data or "token" not in token_data:
        return jsonify({
            "error": True,
            "message": "Failed to get token",
            "token_response": token_data
        }), 500
    
    token = token_data["token"]
    
    # Step 2: Get Vehicle Details
    details = fetch_vehicle_details(token, reg_no)
    
    if not details:
        return jsonify({
            "error": True,
            "message": "Failed to fetch vehicle details"
        }), 500
    
    response_time = round(time.time() - start_time, 2)
    
    return jsonify({
        "success": True,
        "registration": reg_no,
        "data": details,
        "response_time_seconds": response_time,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    })


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "running",
        "service": "Royal Sundaram RC API"
    })


@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "service": "Royal Sundaram Vehicle RC API",
        "usage": "/rc?num=MH02AB1234",
        "info": "Fetches vehicle details from Royal Sundaram Insurance"
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
