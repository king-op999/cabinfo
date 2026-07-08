from flask import Flask, jsonify, request
import requests
import base64
import json
import os
import time
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

app = Flask(__name__)

# --- CONFIGURATION ---
AES_KEY = "RTO@N@1V@$U2024#"
BRANDING = "@rootxindia"

def encrypt(data):
    cipher = AES.new(AES_KEY.encode('utf-8'), AES.MODE_ECB)
    return base64.b64encode(cipher.encrypt(pad(data.encode('utf-8'), 16))).decode('utf-8')

def decrypt(data):
    try:
        cipher = AES.new(AES_KEY.encode('utf-8'), AES.MODE_ECB)
        decoded = base64.b64decode(data)
        return unpad(cipher.decrypt(decoded), 16).decode('utf-8')
    except:
        return None

@app.route('/')
def home():
    rc_no = request.args.get('rc')
    if not rc_no:
        return jsonify({
            "status": "error",
            "message": "Use /?rc=NUMBER",
            "branding": BRANDING
        }), 400

    url = "https://rcdetailsapi.vehicleinfo.app/api/vasu_rc_doc_details"
    
    payload = {
        'YLnoBJXFHWIb6n+vaU5Fqw===': 'hEetH/fxDYkaiPV1O08JXGavuWKAHB7H//KqlbPQizq1sxbHamO8edqhIcOJJybWVc4wf11tUxC1uEtwt2OHiKuzQ4fSmex9pkrf6bj/yztMQT9yb5+E3V3RttX0S1WRXRiNakRvo+pOiu6k8j8M+C6aLHvrWxqTQnP9ND0xv3EQyxcgjYt5rk2qVOWP+nf8',
        'uniDRnuJvTpCyd8qqa7bmg===': '6UcabyegT3XEmP2Mw0Jwfw==',
        'wmbVbuTELPkity3gk1FSLw===': 'hwc6sd9eQz3sd8aZ5tWtOSO9P/8c0ruHIRUDVqC4PzmK3ZgUJ5W/1ibrOgk6+bHhGaWCca3iQ6qfy5v/zhdLXw==',
        'kqvOc7zzeKL9GQi3s97hRg===': 'KOgloc/Wkh/JKFVr/Y5bZA==',
        '6itFonmUeG7GaEL8YAz1dw===': 'DHKgKTb0PD667WXK14bQxQ==',
        'gaQw08ye60GZvOaEjDxwSg===': '7Xx2UpV+mliqWirrrkrJ4A==',
        'KldjgNJiCoLPelKQK12wCg===': 'Wg4luew+ZNYaVLvuYevUwhJMt5Q0FwINOnT3ntNuXiM=',
        '8qv0XiLt71c2Mcb7A/0ETw===': '2femjV0XNiZlRIoza3rq/Q==',
        'zKMffadDKn74L6D8Erq/Ow===': 'HjCiWD0aGnOHqRk+sJhmSg==',
        'aQ1IgwRQsEsftk0pG3qVOA===': 'NDEpmB1IH3r0ZWPKlDX42g==',
        'kxBCVJqsDl1CnYYrPI+ESg===': '6UcabyegT3XEmP2Mw0Jwfw==',
        '4svShi1T5ftaZPNNHhJzig===': encrypt(rc_no.upper()),
        'lES0BMK4Gbc62W3W5/cR3Q===': '6UcabyegT3XEmP2Mw0Jwfw==',
        '5ES5V9fBsVv2zixvup+QfGUYTXf6w2Wb7rfo1vbyiZo==': '6UcabyegT3XEmP2Mw0Jwfw==',
        'w0dcvRNvk81864M2TM1R4w===': '4n04akOAWVJ7qY7ccwxckA==',
        'Qh35ea+zP5C5YndUy+/5hQ===': 'Eky3lDQXAg06dPee025eIw==',
        'zdR9T9RDHgdRB7xdozvLRNUdr4dDNKvva1aeDyqC22ASTLeUNBcCDTp0957Tbl4j=': 'zeLxdIWt2S3VdsxhpTwY1A==',
        'eMY6P1CkF0Iya2o8nxqYGpW47fJY0qkIn/5knbV9Kos==': 'zeLxdIWt2S3VdsxhpTwY1A=='
    }

    headers = {
        'User-Agent': 'okhttp/5.0.0-alpha.11',
        'Content-Type': 'application/x-www-form-urlencoded',
        'version_code': '13.39',
        'device_type': 'android'
    }

    try:
        response = requests.post(url, data=payload, headers=headers, timeout=15)
        decrypted = decrypt(response.text)
        
        if decrypted:
            return jsonify({
                "status": "success",
                "branding": BRANDING,
                "support": "https://t.me/+8S4n-WRMo_00Yjll",
                "data": json.loads(decrypted)
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Decryption failed",
                "raw": response.text[:200]
            }), 500
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/rc', methods=['GET'])
def rc_shortcut():
    """Shortcut: /rc?num=MH02AB1234"""
    rc_no = request.args.get('num', '')
    if rc_no:
        return home()
    return jsonify({
        "status": "error",
        "message": "Use /rc?num=NUMBER or /?rc=NUMBER"
    }), 400


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "running",
        "branding": BRANDING,
        "service": "RC Details API"
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"""
    🔥 RC DETAILS API STARTED
    📍 Port: {port}
    💡 Usage: /?rc=MH02AB1234
    """)
    app.run(host='0.0.0.0', port=port, debug=False)
