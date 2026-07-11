from flask import Flask, request, jsonify
import requests
import json
import os

app = Flask(__name__)

@app.route('/rc', methods=['GET'])
def rc_details():
    rc = request.args.get('rc', '').strip()
    
    if not rc:
        return jsonify({
            "status": "error",
            "message": "No RC number"
        }), 400
    
    # Generate session ID like PHP uniqid
    import uuid
    session = f"{uuid.uuid4().hex[:13]}-{uuid.uuid4().hex[:13]}"
    
    # Payload
    payload = json.dumps({
        "regNo": rc.upper(),
        "sessionid": session
    })
    
    # API URL
    url = "https://api1.91wheels.com/api/v1/third/rc-detail"
    
    # Headers (same as PHP)
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://www.91wheels.com",
        "Referer": "https://www.91wheels.com/",
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; Mobile Safari/537.36)"
    }
    
    try:
        # Make API call
        response = requests.post(url, data=payload, headers=headers, timeout=15)
        
        # Return the JSON response
        try:
            data = response.json()
            return jsonify(data)
        except:
            return jsonify({
                "status": "error",
                "message": "Invalid JSON response",
                "raw": response.text[:500]
            }), 500
            
    except requests.exceptions.Timeout:
        return jsonify({
            "status": "error",
            "message": "Request timeout"
        }), 504
    except requests.exceptions.RequestException as err:
        return jsonify({
            "status": "error",
            "message": str(err)
        }), 500


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "running",
        "service": "91Wheels RC API"
    })


@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "service": "91Wheels RC Details API",
        "usage": "/rc?rc=MH02AB1234",
        "source": "api1.91wheels.com"
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚗 91Wheels RC API | Port: {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
