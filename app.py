from flask import Flask, request, jsonify
import requests
import time
import re

app = Flask(__name__)

TARGET_URL = "https://offlinechallanapi-3yh6els5ia-uc.a.run.app/vehicle/mobile-no"

HEADERS = {
    "content-type": "application/json",
    "origin": "https://offlinechallan.com",
    "referer": "https://offlinechallan.com/",
    "user-agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36",
    "accept": "*/*"
}

def validate_reg_number(reg):
    reg = reg.upper().strip()
    # Basic Indian registration number format
    pattern = r'^[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{1,4}$'
    if re.match(pattern, reg):
        return reg
    return None

def fetch_mobile(reg_number):
    payload = {"reg_number": reg_number.upper().strip()}
    
    try:
        response = requests.post(TARGET_URL, json=payload, headers=HEADERS, timeout=10)
        
        if response.status_code == 200:
            try:
                data = response.json()
                return {
                    "success": True,
                    "registration": reg_number.upper(),
                    "data": data
                }, 200
            except:
                return {
                    "success": True,
                    "registration": reg_number.upper(),
                    "raw_response": response.text
                }, 200
        else:
            return {
                "success": False,
                "error": f"API returned status {response.status_code}",
                "registration": reg_number.upper()
            }, response.status_code
            
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Request timeout"
        }, 504
    except Exception as e:
        return {
            "success": False,
            "error": "Service unavailable"
        }, 500

@app.route("/vehicle/mobile-no", methods=["GET", "POST"])
def get_mobile():
    start_time = time.time()
    
    if request.method == "POST":
        data = request.get_json()
        if not data or "reg_number" not in data:
            return jsonify({
                "success": False,
                "error": "Missing 'reg_number' in request body"
            }), 400
        reg = data["reg_number"]
    else:
        reg = request.args.get("reg") or request.args.get("registration")
        if not reg:
            return jsonify({
                "success": False,
                "error": "Missing parameter: reg",
                "usage": "/vehicle/mobile-no?reg=MH02AB1234"
            }), 400
    
    validated_reg = validate_reg_number(reg)
    if not validated_reg:
        return jsonify({
            "success": False,
            "error": "Invalid registration number format",
            "example": "MH02AB1234"
        }), 400
    
    result, status = fetch_mobile(validated_reg)
    
    response_time = round((time.time() - start_time) * 1000, 2)
    
    if isinstance(result, dict):
        result["meta"] = {
            "response_time_ms": response_time,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    return jsonify(result), status

@app.route("/vehicle/mobile", methods=["GET"])
def get_mobile_short():
    """Short endpoint - /vehicle/mobile?reg=MH02AB1234"""
    return get_mobile()

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "running",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    })

@app.route("/")
def home():
    return jsonify({
        "service": "Vehicle to Mobile Number Lookup",
        "endpoints": {
            "GET /vehicle/mobile-no?reg=MH02AB1234": "Get mobile number by registration",
            "POST /vehicle/mobile-no": "POST with JSON body",
            "GET /vehicle/mobile?reg=MH02AB1234": "Short endpoint",
            "GET /health": "Health check"
        },
        "example": "/vehicle/mobile-no?reg=MH02AB1234"
    })

if __name__ == "__main__":
    print("=" * 50)
    print("Vehicle to Mobile API by @ftgamer2")
    print("=" * 50)
    print("GET Example:")
    print("  http://localhost:5000/vehicle/mobile-no?reg=MH02AB1234")
    print("")
    print("POST Example:")
    print("  curl -X POST http://localhost:5000/vehicle/mobile-no \\")
    print("    -H 'Content-Type: application/json' \\")
    print("    -d '{\"reg_number\": \"MH02AB1234\"}'")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=False)
