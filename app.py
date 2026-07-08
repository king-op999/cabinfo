import os
import subprocess
import time
import requests
import base64
import json
import re
import signal
from flask import Flask, jsonify, request
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# --- AGGRESSIVE AUTO-KILL ---
os.system("fuser -k 8080/tcp > /dev/null 2>&1")
os.system("pkill -9 cloudflared > /dev/null 2>&1")

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
    except: return None

@app.route('/')
def home():
    rc_no = request.args.get('rc')
    if not rc_no:
        return jsonify({"status": "error", "message": "Use /?rc=NUMBER", "branding": BRANDING}), 400

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
        response = requests.post(url, data=payload, headers=headers, timeout=10)
        decrypted = decrypt(response.text)
        return jsonify({
            "status": "success", 
            "branding": BRANDING, 
            "support": "https://t.me/+8S4n-WRMo_00Yjll",
            "data": json.loads(decrypted)
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- SHUTDOWN ROUTE ---
@app.route('/stop')
def stop_server():
    os.system("pkill -9 cloudflared")
    os.kill(os.getpid(), signal.SIGINT)
    return "API and Tunnel Stopped Successfully."

if __name__ == "__main__":
    print("\n" + "="*50)
    print("🚀 UNLIMITED API STARTING...")
    print("="*50)
    
    tunnel_proc = subprocess.Popen(
        ["cloudflared", "tunnel", "--url", "http://127.0.0.1:8080"],
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True
    )

    url_found = False
    for i in range(15):
        line = tunnel_proc.stderr.readline()
        if "trycloudflare.com" in line:
            public_url = re.search(r'https://[a-zA-Z0-9.-]+\.trycloudflare\.com', line)
            if public_url:
                print(f"\n✅ LIVE LINK:")
                print(f"🔗 {public_url.group(0)}/?rc=YOUR_RC_NUMBER")
                print(f"📁 Source: Channel.html (Free Api Here)")
                print("\n" + "="*50)
                url_found = True
                break
        time.sleep(1)
    
    app.run(host='127.0.0.1', port=8080, debug=False)
