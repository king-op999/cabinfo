from flask import Flask, request, jsonify
import requests
import json
import time
import re
import random
import os
import tempfile
import shutil
import string
from datetime import datetime
from dateutil.relativedelta import relativedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

app = Flask(__name__)

# --- CONFIGURATION ---
ACKO_COOKIE = "trackerid=9a39d1a8-c010-4f8f-a14d-01d24a31b831;"

class VahanIntelligence:
    def __init__(self):
        self.data = {
            "status": "FAILED",
            "rc_number": None,
            "owner_details": {"name": None, "ownership_serial": None},
            "vehicle_details": {},
            "registration_details": {},
            "insurance_details": {},
            "technical_specs": {}
        }
        self.session = requests.Session()

    def _get_headers(self):
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ]
        
        return {
            'User-Agent': random.choice(user_agents),
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Content-Type': 'application/json',
            'Origin': 'https://www.acko.com',
            'Referer': 'https://www.acko.com/',
            'Sec-Ch-Ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Cookie': ACKO_COOKIE
        }

    def _calculate_validity(self, reg_date_str):
        try:
            for fmt in ('%d-%m-%Y', '%Y-%m-%d', '%d/%m/%Y'):
                try:
                    reg_dt = datetime.strptime(reg_date_str, fmt)
                    break
                except:
                    continue
            else:
                return {}

            fitness_exp = reg_dt + relativedelta(years=15)
            
            return {
                "fitness_valid_upto": fitness_exp.strftime('%d-%m-%Y'),
                "tax_valid_upto": "Lifetime (15 Years)",
                "vehicle_age": f"{(datetime.now() - reg_dt).days // 365} Years"
            }
        except:
            return {}

    # ========== ACKO API ==========
    def fetch_from_acko(self, reg_no):
        print(f"🔹 Fetching from ACKO API...")
        try:
            headers = self._get_headers()
            
            # Step 1: Create proposal
            payload = {
                "registration_number": reg_no.upper(),
                "product": "car",
                "is_new": False,
                "origin": "acko",
                "trace_id": str(random.randint(1000, 5000))
            }
            
            for attempt in range(3):
                try:
                    resp = self.session.post(
                        "https://www.acko.com/motororchestrator/api/v2/proposals",
                        json=payload,
                        headers=headers,
                        timeout=15
                    )
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        ekey = data.get("ekey")
                        
                        if not ekey:
                            if attempt < 2:
                                time.sleep(2)
                                continue
                            return False
                        
                        # Step 2: Unlock proposal
                        time.sleep(0.5)
                        
                        unlock_url = f"https://www.acko.com/motororchestrator/api/v2/proposals/{ekey}"
                        unlock_payload = {
                            "product": "car",
                            "origin": "acko",
                            "vehicle": {
                                "is_commercial": False,
                                "registration_number": reg_no.upper()
                            },
                            "user": {
                                "pincode": str(random.randint(110000, 110099)),
                                "phone": f"9{random.randint(100000000, 999999999)}",
                                "email": f"user{random.randint(1000, 9999)}@example.com"
                            },
                            "session_id": f"session_{int(time.time())}"
                        }
                        
                        final_resp = self.session.put(
                            unlock_url,
                            json=unlock_payload,
                            headers=headers,
                            timeout=15
                        )
                        
                        if final_resp.status_code == 200:
                            final = final_resp.json()
                            v = final.get("vehicle", {})
                            pp = final.get("previous_policy", {})

                            self.data["status"] = "SUCCESS"
                            self.data["rc_number"] = v.get("registration_number")
                            self.data["owner_details"]["name"] = v.get("owner_name")
                            
                            self.data["vehicle_details"] = {
                                "make": v.get("make_name"),
                                "model": v.get("model_name"),
                                "variant": v.get("variant_name"),
                                "fuel_type": v.get("fuel_type"),
                                "color": v.get("color"),
                                "year": v.get("year_of_manufacture"),
                                "body_type": v.get("body_type")
                            }
                            
                            self.data["technical_specs"] = {
                                "engine_number": v.get("engine_number_unmasked") or v.get("engine_number"),
                                "chassis_number": v.get("chassis_number_unmasked") or v.get("chassis_number"),
                                "cc": v.get("cc"),
                                "seating_capacity": v.get("seating_capacity"),
                                "gvw": v.get("gross_vehicle_weight")
                            }
                            
                            # Registration date
                            reg_date = None
                            if v.get("registration_date"):
                                ts = v.get("registration_date")
                                if isinstance(ts, (int, float)) and ts > 1000000000:
                                    reg_date = datetime.fromtimestamp(ts/1000).strftime('%d-%m-%Y')
                            
                            self.data["registration_details"] = {
                                "reg_date": reg_date,
                                "rto_code": v.get("rto_code"),
                                "rto_name": v.get("rto_display_name"),
                                "rto_state": v.get("rto_state"),
                                "rto_city": v.get("rto_city")
                            }
                            
                            # Calculate validity
                            if reg_date:
                                validity = self._calculate_validity(reg_date)
                                self.data["registration_details"].update(validity)
                            
                            self.data["insurance_details"] = {
                                "policy_number": pp.get("policy_number"),
                                "insurer": pp.get("insurer_name"),
                                "expiry_date": pp.get("policy_expiry_date"),
                                "is_expired": pp.get("is_expired"),
                                "policy_type": pp.get("policy_type")
                            }
                            
                            return True
                        else:
                            print(f"⚠️ Unlock failed: {final_resp.status_code}")
                            
                except requests.exceptions.Timeout:
                    print(f"⏰ Timeout attempt {attempt + 1}")
                    if attempt < 2:
                        time.sleep(3)
                except Exception as e:
                    print(f"❌ Error attempt {attempt + 1}: {e}")
                    if attempt < 2:
                        time.sleep(2)
                        
            return False
        except Exception as e:
            print(f"❌ ACKO Error: {e}")
            return False

    # ========== SELENIUM SCRAPER ==========
    def fetch_from_scraper(self, reg_no):
        print(f"🌐 Fetching from Web Scraper...")
        driver = None
        temp_dir = None
        
        try:
            # Create temp directory for Chrome
            temp_dir = tempfile.mkdtemp(prefix="chrome_")
            
            options = Options()
            options.add_argument('--headless=new')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument(f"--user-data-dir={temp_dir}")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            
            # Auto-install ChromeDriver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            
            # Remove automation traces
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            sources = [
                "https://www.spinny.com/rto-details/",
                "https://www.carinfo.app/rto-vehicle-registration-detail"
            ]
            
            for source in sources:
                try:
                    print(f"🔄 Trying: {source}")
                    driver.get(source)
                    time.sleep(3)
                    
                    # Find input field
                    input_selectors = [
                        "input[name='registrationNumber']",
                        "input[name='rcNumber']",
                        "input[placeholder*='RC']",
                        "input[placeholder*='registration']",
                        "#rcNumber",
                        "#registrationNumber"
                    ]
                    
                    inp = None
                    for selector in input_selectors:
                        try:
                            inp = WebDriverWait(driver, 5).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                            )
                            break
                        except:
                            continue
                    
                    if not inp:
                        continue
                    
                    # Type registration number
                    inp.click()
                    time.sleep(0.3)
                    inp.clear()
                    for char in reg_no:
                        inp.send_keys(char)
                        time.sleep(random.uniform(0.05, 0.1))
                    
                    # Click search button
                    buttons = driver.find_elements(By.TAG_NAME, "button")
                    for btn in buttons:
                        btn_text = btn.text.lower()
                        if any(kw in btn_text for kw in ['search', 'submit', 'get details', 'check']):
                            driver.execute_script("arguments[0].click();", btn)
                            break
                    
                    time.sleep(5)
                    
                    # Parse with BeautifulSoup
                    soup = BeautifulSoup(driver.page_source, "html.parser")
                    page_text = soup.get_text()
                    
                    # Extract Owner Name
                    owner_patterns = ["Owner Name", "Registered Owner", "Owner", "owner name"]
                    for pattern in owner_patterns:
                        if pattern.lower() in page_text.lower():
                            lines = page_text.split('\n')
                            for i, line in enumerate(lines):
                                if pattern.lower() in line.lower():
                                    for j in range(i+1, min(i+4, len(lines))):
                                        candidate = lines[j].strip()
                                        if candidate and len(candidate) > 2 and len(candidate) < 60:
                                            if not self.data["owner_details"]["name"]:
                                                self.data["owner_details"]["name"] = candidate
                                            break
                                    break
                    
                    # Extract Model
                    h1_tags = soup.find_all('h1')
                    for h1 in h1_tags:
                        text = h1.text.strip()
                        if text and len(text) > 3 and len(text) < 80:
                            if not self.data["vehicle_details"].get("model"):
                                self.data["vehicle_details"]["model"] = text
                                break
                    
                    # Extract Registration Date
                    if "Registration Date" in page_text or "Reg Date" in page_text:
                        lines = page_text.split('\n')
                        for i, line in enumerate(lines):
                            if 'registration date' in line.lower() or 'reg date' in line.lower():
                                for j in range(i+1, min(i+4, len(lines))):
                                    candidate = lines[j].strip()
                                    if re.search(r'\d{2}[-/]\d{2}[-/]\d{4}', candidate):
                                        if not self.data["registration_details"].get("reg_date"):
                                            self.data["registration_details"]["reg_date"] = candidate
                                            validity = self._calculate_validity(candidate)
                                            self.data["registration_details"].update(validity)
                                        break
                                break
                    
                    # Extract Fuel Type
                    if "Fuel" in page_text:
                        lines = page_text.split('\n')
                        for i, line in enumerate(lines):
                            if 'fuel' in line.lower():
                                for j in range(i+1, min(i+4, len(lines))):
                                    candidate = lines[j].strip().upper()
                                    if candidate in ["PETROL", "DIESEL", "CNG", "ELECTRIC", "HYBRID"]:
                                        if not self.data["vehicle_details"].get("fuel_type"):
                                            self.data["vehicle_details"]["fuel_type"] = candidate
                                        break
                                break
                    
                    self.data["status"] = "SUCCESS"
                    driver.quit()
                    return True
                    
                except Exception as e:
                    print(f"⚠️ Source failed: {e}")
                    continue
            
            driver.quit()
            return False
            
        except Exception as e:
            print(f"❌ Scraper Error: {e}")
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            return False
        finally:
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except:
                    pass

    def get_full_profile(self, reg_no):
        print(f"🚀 Fetching details for: {reg_no}")
        
        # Try ACKO API first
        acko_success = self.fetch_from_acko(reg_no)
        
        if acko_success:
            print("✅ ACKO API successful")
            # Check if we got all data
            has_model = bool(self.data["vehicle_details"].get("model"))
            has_reg_date = bool(self.data["registration_details"].get("reg_date"))
            
            if not has_model or not has_reg_date:
                print("🔄 Missing some data, trying scraper...")
                self.fetch_from_scraper(reg_no)
        else:
            print("🔄 ACKO failed, trying scraper...")
            self.fetch_from_scraper(reg_no)
        
        # Clean up None values
        for section in self.data:
            if isinstance(self.data[section], dict):
                self.data[section] = {k: v for k, v in self.data[section].items() if v is not None}
        
        return self.data


# ========== FLASK ENDPOINTS ==========

@app.route('/vahan/search', methods=['GET'])
def search_vahan():
    reg_no = request.args.get('number', '').strip().upper()
    
    if not reg_no:
        return jsonify({
            "error": "Registration number required",
            "example": "/vahan/search?number=MH14KK9159"
        }), 400
    
    if not re.match(r'^[A-Z]{2}\d{1,2}[A-Z]{1,3}\d{1,4}$', reg_no):
        return jsonify({
            "error": "Invalid format",
            "example": "MH14KK9159, DL1CAA1111"
        }), 400
    
    start = time.time()
    engine = VahanIntelligence()
    result = engine.get_full_profile(reg_no)
    
    # Add metadata
    result["meta"] = {
        "version": "4.0",
        "response_time": f"{round(time.time() - start, 2)}s",
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "request_id": f"VH{int(time.time())}{random.randint(100, 999)}"
    }
    
    return jsonify(result)

@app.route('/rc', methods=['GET'])
def rc_shortcut():
    """Shortcut endpoint: /rc?num=MH14KK9159"""
    reg_no = request.args.get('num', '').strip().upper()
    
    if not reg_no:
        return jsonify({"error": "Use /rc?num=REG_NUMBER"}), 400
    
    start = time.time()
    engine = VahanIntelligence()
    result = engine.get_full_profile(reg_no)
    
    result["meta"] = {
        "version": "4.0",
        "response_time": f"{round(time.time() - start, 2)}s",
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    return jsonify(result)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "operational",
        "service": "Vahan Intelligence API v4.0",
        "endpoints": ["/vahan/search?number=REG", "/rc?num=REG", "/health"]
    })

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "service": "Vahan RC Intelligence API",
        "version": "4.0",
        "endpoints": {
            "search": "/vahan/search?number=MH14KK9159",
            "shortcut": "/rc?num=MH14KK9159",
            "health": "/health"
        },
        "features": [
            "Owner Name",
            "Vehicle Model & Make",
            "Engine & Chassis Number",
            "Registration Date & RTO",
            "Insurance Details",
            "Fitness & Tax Validity"
        ]
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"""
    🔥 VAHAN INTELLIGENCE API v4.0
    📍 Running on: http://0.0.0.0:{port}
    
    📋 Endpoints:
    • /vahan/search?number=MH14KK9159
    • /rc?num=MH14KK9159
    • /health
    """)
    app.run(host='0.0.0.0', port=port, debug=False)
