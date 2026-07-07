from flask import Flask, request, jsonify
import requests
import json
import time
import random
import re
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

# ============================================
# SOURCE 1: 91Wheels API
# ============================================
def fetch_91wheels(reg_no):
    """Fetch data from 91Wheels API"""
    print("🔹 Fetching from 91Wheels...")
    try:
        session_id = f"{random.randint(10000,99999)}-{random.randint(10000,99999)}"
        
        payload = json.dumps({
            "regNo": reg_no,
            "sessionid": session_id
        })
        
        url = "https://api1.91wheels.com/api/v1/third/rc-detail"
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://www.91wheels.com",
            "Referer": "https://www.91wheels.com/",
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; Mobile Safari/537.36)"
        }
        
        response = requests.post(url, data=payload, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success" or "data" in data:
                return {"source": "91wheels", "success": True, "data": data}
        return {"source": "91wheels", "success": False, "error": "No data found"}
    except Exception as e:
        return {"source": "91wheels", "success": False, "error": str(e)}

# ============================================
# SOURCE 2: CarInfo App API
# ============================================
def fetch_carinfo(reg_no):
    """Fetch data from CarInfo App"""
    print("🔹 Fetching from CarInfo...")
    try:
        url = (
            "https://www.carinfo.app/_next/data/"
            "lEH1JDnqa1BNfE88p-0Q9/"
            f"rto-vehicle-registration-detail/rto-details/{reg_no}.json"
        )
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "x-nextjs-data": "1",
            "sec-ch-ua-platform": "\"Android\"",
            "sec-ch-ua": "\"Google Chrome\";v=\"143\", \"Chromium\";v=\"143\", \"Not A(Brand\";v=\"24\"",
            "sec-ch-ua-mobile": "?0",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": "https://www.carinfo.app/rto-vehicle-registration-detail",
            "accept-language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7",
            "priority": "u=1, i"
        }
        
        response = requests.get(url, headers=headers, timeout=20)
        
        if response.status_code == 200 and "application/json" in response.headers.get("Content-Type", ""):
            data = response.json()
            
            try:
                section = data["pageProps"]["rtoDetailsReponse"]["webSections"][0]
                messages = section.get("messages", [])
                vehicle_msg = section.get("message", {})
                
                info = {m["title"]: m["subtitle"] for m in messages}
                registered_rto = info.get("Registered RTO", "")
                
                result = {
                    "vehicle_number": data["pageProps"].get("vehicalNum", ""),
                    "registration_state": info.get("State", ""),
                    "owner_name": vehicle_msg.get("title", ""),
                    "model": vehicle_msg.get("subtitle", ""),
                    "rto_code": info.get("Number", ""),
                    "rto_name": registered_rto.split(",")[0] if registered_rto else "",
                    "state": info.get("State", ""),
                    "vehicle_type": "Unknown"
                }
                return {"source": "carinfo", "success": True, "data": result}
            except:
                return {"source": "carinfo", "success": False, "error": "Parse error"}
        return {"source": "carinfo", "success": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"source": "carinfo", "success": False, "error": str(e)}

# ============================================
# SOURCE 3: ACKO API
# ============================================
def fetch_acko(reg_no):
    """Fetch data from ACKO API"""
    print("🔹 Fetching from ACKO...")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            'Origin': 'https://www.acko.com',
            'Referer': 'https://www.acko.com/',
            'Cookie': 'trackerid=9a39d1a8-c010-4f8f-a14d-01d24a31b831;'
        }
        
        # Step 1: Create proposal
        payload = {
            "registration_number": reg_no.upper(),
            "product": "car",
            "is_new": False,
            "origin": "acko",
            "trace_id": str(random.randint(1000, 5000))
        }
        
        resp = requests.post(
            "https://www.acko.com/motororchestrator/api/v2/proposals",
            json=payload,
            headers=headers,
            timeout=15
        )
        
        if resp.status_code != 200:
            return {"source": "acko", "success": False, "error": "Proposal creation failed"}
        
        data = resp.json()
        ekey = data.get("ekey")
        
        if not ekey:
            return {"source": "acko", "success": False, "error": "No ekey"}
        
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
        
        final_resp = requests.put(unlock_url, json=unlock_payload, headers=headers, timeout=15)
        
        if final_resp.status_code == 200:
            final = final_resp.json()
            vehicle = final.get("vehicle", {})
            prev_policy = final.get("previous_policy", {})
            
            result = {
                "rc_number": vehicle.get("registration_number"),
                "owner_name": vehicle.get("owner_name"),
                "make": vehicle.get("make_name"),
                "model": vehicle.get("model_name"),
                "variant": vehicle.get("variant_name"),
                "fuel_type": vehicle.get("fuel_type"),
                "color": vehicle.get("color"),
                "year_of_manufacture": vehicle.get("year_of_manufacture"),
                "engine_number": vehicle.get("engine_number_unmasked") or vehicle.get("engine_number"),
                "chassis_number": vehicle.get("chassis_number_unmasked") or vehicle.get("chassis_number"),
                "cc": vehicle.get("cc"),
                "seating_capacity": vehicle.get("seating_capacity"),
                "gvw": vehicle.get("gross_vehicle_weight"),
                "body_type": vehicle.get("body_type"),
                "rto_code": vehicle.get("rto_code"),
                "rto_name": vehicle.get("rto_display_name"),
                "rto_state": vehicle.get("rto_state"),
                "rto_city": vehicle.get("rto_city"),
                "registration_date": vehicle.get("registration_date"),
                "insurance_policy": prev_policy.get("policy_number"),
                "insurance_company": prev_policy.get("insurer_name"),
                "insurance_expiry": prev_policy.get("policy_expiry_date"),
                "insurance_type": prev_policy.get("policy_type")
            }
            return {"source": "acko", "success": True, "data": result}
        return {"source": "acko", "success": False, "error": "Unlock failed"}
    except Exception as e:
        return {"source": "acko", "success": False, "error": str(e)}

# ============================================
# SOURCE 4: Vahan Selenium Scraper
# ============================================
def fetch_vahan(reg_no, chassis_last5=""):
    """Fetch data from Vahan using Selenium"""
    print("🔹 Fetching from Vahan...")
    
    if not chassis_last5:
        return {"source": "vahan", "success": False, "error": "Chassis last 5 digits required"}
    
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    try:
        driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()),
            options=options
        )
        wait = WebDriverWait(driver, 20)
        
        # Navigate to Vahan
        driver.get("https://vahan.parivahan.gov.in/vahanservice/vahan/ui/statevalidation/homepage.xhtml")
        time.sleep(2)
        
        # Enter Registration Number
        regn_input = wait.until(EC.presence_of_element_located((By.ID, "regnid")))
        regn_input.clear()
        regn_input.send_keys(reg_no)
        
        # Handle checkbox
        try:
            checkbox = driver.find_element(By.XPATH, "//div[contains(@class,'ui-chkbox-box')]")
            driver.execute_script("arguments[0].click();", checkbox)
        except:
            pass
        
        # Click Proceed
        proceed_btn = wait.until(EC.element_to_be_clickable((By.ID, "proccedHomeButtonId")))
        driver.execute_script("arguments[0].click();", proceed_btn)
        
        time.sleep(3)
        
        # Click Fitness link
        fitness_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//a[contains(text(),'Fitness')]")
        ))
        driver.execute_script("arguments[0].click();", fitness_btn)
        
        time.sleep(3)
        
        # Enter chassis last 5
        chassis_input = wait.until(EC.presence_of_element_located(
            (By.ID, "balanceFeesFine:tf_chasis_no")
        ))
        chassis_input.send_keys(chassis_last5)
        
        # Click Validate
        validate_btn = driver.find_element(By.ID, "balanceFeesFine:validate_dtls")
        driver.execute_script("arguments[0].click();", validate_btn)
        
        time.sleep(2)
        
        # Get mobile number
        mobile_input = driver.find_element(By.ID, "balanceFeesFine:tf_mobile")
        mobile_number = mobile_input.get_attribute("value")
        
        driver.quit()
        
        if mobile_number:
            return {
                "source": "vahan",
                "success": True,
                "data": {
                    "mobile_number": mobile_number,
                    "chassis_last5_used": chassis_last5
                }
            }
        return {"source": "vahan", "success": False, "error": "Mobile not found"}
    except Exception as e:
        try:
            driver.quit()
        except:
            pass
        return {"source": "vahan", "success": False, "error": str(e)}

# ============================================
# SOURCE 5: Spinny Web Scraper
# ============================================
def fetch_spinny(reg_no):
    """Fetch data from Spinny using Selenium"""
    print("🔹 Fetching from Spinny...")
    
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    try:
        driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()),
            options=options
        )
        
        driver.get("https://www.spinny.com/rto-details/")
        time.sleep(3)
        
        # Find input and enter RC number
        input_field = driver.find_element(By.CSS_SELECTOR, "input[name='registrationNumber']")
        input_field.clear()
        for char in reg_no:
            input_field.send_keys(char)
            time.sleep(0.1)
        
        # Find and click search button
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for btn in buttons:
            if 'get details' in btn.text.lower() or 'search' in btn.text.lower():
                driver.execute_script("arguments[0].click();", btn)
                break
        
        time.sleep(5)
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        driver.quit()
        
        result = {}
        
        # Extract model
        h1_tags = soup.find_all('h1')
        for h1 in h1_tags:
            if h1.text.strip():
                result["model"] = h1.text.strip()[:100]
                break
        
        # Extract other details
        text = soup.get_text()
        
        if "Owner Name" in text or "owner" in text.lower():
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if 'owner' in line.lower():
                    if i+1 < len(lines):
                        result["owner_name"] = lines[i+1].strip()[:50]
                        break
        
        if "Registration Date" in text:
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if 'registration date' in line.lower():
                    if i+1 < len(lines):
                        result["registration_date"] = lines[i+1].strip()
                        break
        
        if "Fuel Type" in text:
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if 'fuel' in line.lower():
                    if i+1 < len(lines):
                        result["fuel_type"] = lines[i+1].strip()
                        break
        
        if result:
            return {"source": "spinny", "success": True, "data": result}
        return {"source": "spinny", "success": False, "error": "No data extracted"}
    except Exception as e:
        try:
            driver.quit()
        except:
            pass
        return {"source": "spinny", "success": False, "error": str(e)}

# ============================================
# MERGE ALL RESULTS
# ============================================
def merge_all_results(all_results):
    """Merge results from all sources into one unified response"""
    
    merged = {
        "rc_number": "",
        "owner_name": "",
        "vehicle_details": {},
        "registration_details": {},
        "technical_specs": {},
        "insurance_details": {},
        "contact_info": {},
        "sources_used": []
    }
    
    for result in all_results:
        if not result.get("success"):
            continue
        
        source = result.get("source", "unknown")
        merged["sources_used"].append(source)
        data = result.get("data", {})
        
        # Merge based on source
        if source == "acko":
            if data.get("rc_number"):
                merged["rc_number"] = data["rc_number"]
            if data.get("owner_name"):
                merged["owner_name"] = data["owner_name"]
            
            merged["vehicle_details"].update({
                "make": data.get("make") or merged["vehicle_details"].get("make"),
                "model": data.get("model") or merged["vehicle_details"].get("model"),
                "variant": data.get("variant") or merged["vehicle_details"].get("variant"),
                "fuel_type": data.get("fuel_type") or merged["vehicle_details"].get("fuel_type"),
                "color": data.get("color") or merged["vehicle_details"].get("color"),
                "year": data.get("year_of_manufacture") or merged["vehicle_details"].get("year"),
                "body_type": data.get("body_type") or merged["vehicle_details"].get("body_type")
            })
            
            merged["technical_specs"].update({
                "engine_number": data.get("engine_number") or merged["technical_specs"].get("engine_number"),
                "chassis_number": data.get("chassis_number") or merged["technical_specs"].get("chassis_number"),
                "cc": data.get("cc") or merged["technical_specs"].get("cc"),
                "seating_capacity": data.get("seating_capacity") or merged["technical_specs"].get("seating_capacity"),
                "gvw": data.get("gvw") or merged["technical_specs"].get("gvw")
            })
            
            merged["registration_details"].update({
                "rto_code": data.get("rto_code") or merged["registration_details"].get("rto_code"),
                "rto_name": data.get("rto_name") or merged["registration_details"].get("rto_name"),
                "rto_state": data.get("rto_state") or merged["registration_details"].get("rto_state"),
                "rto_city": data.get("rto_city") or merged["registration_details"].get("rto_city"),
                "registration_date": data.get("registration_date") or merged["registration_details"].get("registration_date")
            })
            
            merged["insurance_details"].update({
                "policy_number": data.get("insurance_policy") or merged["insurance_details"].get("policy_number"),
                "company": data.get("insurance_company") or merged["insurance_details"].get("company"),
                "expiry": data.get("insurance_expiry") or merged["insurance_details"].get("expiry"),
                "type": data.get("insurance_type") or merged["insurance_details"].get("type")
            })
        
        elif source == "carinfo":
            if data.get("vehicle_number"):
                merged["rc_number"] = data["vehicle_number"]
            if data.get("owner_name"):
                merged["owner_name"] = data["owner_name"]
            
            merged["vehicle_details"].update({
                "model": data.get("model") or merged["vehicle_details"].get("model")
            })
            
            merged["registration_details"].update({
                "rto_code": data.get("rto_code") or merged["registration_details"].get("rto_code"),
                "rto_name": data.get("rto_name") or merged["registration_details"].get("rto_name"),
                "state": data.get("registration_state") or merged["registration_details"].get("state")
            })
        
        elif source == "vahan":
            merged["contact_info"]["mobile_number"] = data.get("mobile_number")
        
        elif source == "spinny":
            if data.get("owner_name"):
                merged["owner_name"] = data["owner_name"]
            merged["vehicle_details"].update({
                "model": data.get("model") or merged["vehicle_details"].get("model"),
                "fuel_type": data.get("fuel_type") or merged["vehicle_details"].get("fuel_type")
            })
            merged["registration_details"].update({
                "registration_date": data.get("registration_date") or merged["registration_details"].get("registration_date")
            })
    
    return merged

# ============================================
# MAIN API ENDPOINT
# ============================================
@app.route('/rc', methods=['GET'])
def rc_details():
    """
    Main endpoint: /rc?num=REG_NUMBER
    Fetches from all sources and returns unified response
    """
    reg_no = request.args.get('num', '').strip().upper()
    
    if not reg_no:
        return jsonify({
            "error": True,
            "message": "Registration number required",
            "usage": "/rc?num=MH14KK9159"
        }), 400
    
    # Validate basic format
    if not re.match(r'^[A-Z]{2}\d{1,2}[A-Z]{1,3}\d{1,4}$', reg_no):
        return jsonify({
            "error": True,
            "message": "Invalid registration number format",
            "valid_examples": ["MH14KK9159", "DL1CAA1111", "KA01AB1234"]
        }), 400
    
    start_time = time.time()
    all_results = []
    
    # Fetch from all sources in sequence
    # Source 1: 91Wheels
    result = fetch_91wheels(reg_no)
    all_results.append(result)
    time.sleep(0.5)
    
    # Source 2: CarInfo
    result = fetch_carinfo(reg_no)
    all_results.append(result)
    time.sleep(0.5)
    
    # Source 3: ACKO (best source)
    result = fetch_acko(reg_no)
    all_results.append(result)
    time.sleep(0.5)
    
    # Source 4: Spinny Scraper
    result = fetch_spinny(reg_no)
    all_results.append(result)
    
    # Merge all results
    merged_data = merge_all_results(all_results)
    
    # Get chassis for Vahan if available
    chassis = merged_data.get("technical_specs", {}).get("chassis_number", "")
    if chassis and len(chassis) >= 5:
        chassis_last5 = chassis[-5:]
        result = fetch_vahan(reg_no, chassis_last5)
        all_results.append(result)
        # Update merged data with mobile if found
        if result.get("success"):
            merged_data["contact_info"]["mobile_number"] = result.get("data", {}).get("mobile_number")
            merged_data["sources_used"].append("vahan")
    
    # Calculate response time
    response_time = round(time.time() - start_time, 2)
    
    # Final response
    final_response = {
        "status": "SUCCESS" if merged_data.get("rc_number") or merged_data.get("owner_name") else "PARTIAL",
        "response_time_seconds": response_time,
        "data": merged_data,
        "meta": {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "total_sources_checked": len(all_results),
            "successful_sources": len([r for r in all_results if r.get("success")]),
            "sources_used": merged_data["sources_used"]
        }
    }
    
    return jsonify(final_response)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Unified Vehicle RC API",
        "version": "1.0",
        "endpoints": ["/rc?num=REG_NUMBER", "/health"]
    })

@app.route('/', methods=['GET'])
def home():
    """Home page"""
    return jsonify({
        "service": "Unified Vehicle RC Information API",
        "version": "1.0",
        "usage": "/rc?num=REG_NUMBER",
        "examples": [
            "/rc?num=MH14KK9159",
            "/rc?num=DL1CAA1111",
            "/rc?num=KA01AB1234"
        ],
        "sources": [
            "91Wheels API",
            "CarInfo App",
            "ACKO Insurance",
            "Spinny",
            "Vahan Parivahan"
        ]
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"""
    🚀 Unified Vehicle RC API Server
    📍 Running on: http://0.0.0.0:{port}
    
    📋 Endpoints:
    • GET /rc?num=REG_NUMBER - Get complete vehicle details
    • GET /health - Health check
    
    💡 Example: http://localhost:{port}/rc?num=MH14KK9159
    """)
    app.run(host='0.0.0.0', port=port, debug=False)
