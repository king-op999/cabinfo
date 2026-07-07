from flask import Flask, request, jsonify
import requests
import json
import time
import random
import re
import os
from datetime import datetime

app = Flask(__name__)

# ============================================
# SOURCE 1: CarInfo App (BEST & FASTEST)
# ============================================
def fetch_carinfo(reg_no):
    print("🔹 Fetching from CarInfo...")
    try:
        url = f"https://www.carinfo.app/rto-vehicle-registration-detail/rto-details/{reg_no}.json"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36",
            "Accept": "application/json",
            "Referer": "https://www.carinfo.app/rto-vehicle-registration-detail",
            "x-nextjs-data": "1"
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            try:
                data = response.json()
                section = data["pageProps"]["rtoDetailsReponse"]["webSections"][0]
                messages = section.get("messages", [])
                vehicle_msg = section.get("message", {})
                
                info = {}
                for m in messages:
                    info[m["title"]] = m["subtitle"]
                
                registered_rto = info.get("Registered RTO", "")
                
                result = {
                    "rc_number": data["pageProps"].get("vehicalNum", reg_no),
                    "owner_name": vehicle_msg.get("title", ""),
                    "model": vehicle_msg.get("subtitle", ""),
                    "fuel_type": info.get("Fuel Type", ""),
                    "registration_date": info.get("Registration Date", ""),
                    "rto_name": registered_rto.split(",")[0] if registered_rto else "",
                    "rto_code": info.get("Number", ""),
                    "state": info.get("State", ""),
                    "city": registered_rto.split(",")[-1].strip() if registered_rto else "",
                    "vehicle_age": info.get("Age", ""),
                    "insurance_validity": info.get("Insurance Validity", ""),
                    "fitness_validity": info.get("Fitness Validity", ""),
                    "tax_validity": info.get("Tax Validity", ""),
                    "norms": info.get("Norms", ""),
                }
                
                # Remove empty values
                result = {k: v for k, v in result.items() if v}
                
                return {"source": "carinfo", "success": True, "data": result}
            except Exception as e:
                return {"source": "carinfo", "success": False, "error": f"Parse error: {str(e)}"}
        return {"source": "carinfo", "success": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"source": "carinfo", "success": False, "error": str(e)}

# ============================================
# SOURCE 2: 91Wheels API
# ============================================
def fetch_91wheels(reg_no):
    print("🔹 Fetching from 91Wheels...")
    try:
        session_id = f"{random.randint(10000,99999)}-{random.randint(10000,99999)}"
        
        payload = json.dumps({
            "regNo": reg_no.upper(),
            "sessionid": session_id
        })
        
        url = "https://api1.91wheels.com/api/v1/third/rc-detail"
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Origin": "https://www.91wheels.com",
            "Referer": "https://www.91wheels.com/",
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; Mobile Safari/537.36)"
        }
        
        response = requests.post(url, data=payload, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract actual vehicle data
            vehicle_data = {}
            
            if "data" in data:
                d = data["data"]
                vehicle_data = {
                    "rc_number": d.get("regNo") or reg_no,
                    "owner_name": d.get("ownerName", ""),
                    "model": d.get("model", ""),
                    "make": d.get("make", ""),
                    "fuel_type": d.get("fuelType", ""),
                    "registration_date": d.get("regDate", ""),
                    "chassis_number": d.get("chassisNo", ""),
                    "engine_number": d.get("engineNo", ""),
                    "rto_name": d.get("rtoName", ""),
                    "insurance_expiry": d.get("insuranceValidTill", ""),
                    "fitness_expiry": d.get("fitnessValidTill", ""),
                }
            elif "result" in data:
                d = data["result"]
                vehicle_data = {
                    "rc_number": d.get("registration_no") or reg_no,
                    "owner_name": d.get("owner_name", ""),
                    "model": d.get("model", ""),
                    "fuel_type": d.get("fuel", ""),
                    "registration_date": d.get("reg_date", ""),
                }
            
            vehicle_data = {k: v for k, v in vehicle_data.items() if v}
            
            if vehicle_data:
                return {"source": "91wheels", "success": True, "data": vehicle_data}
        
        return {"source": "91wheels", "success": False, "error": "No data found"}
    except Exception as e:
        return {"source": "91wheels", "success": False, "error": str(e)}

# ============================================
# SOURCE 3: Vehicle RC Info API (New Source)
# ============================================
def fetch_rcinfo(reg_no):
    print("🔹 Fetching from RC Info API...")
    try:
        # Multiple API attempts
        apis = [
            {
                "url": f"https://rto-vehicle-information-verification-india.p.rapidapi.com/vehicle-info",
                "headers": {
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0"
                },
                "method": "POST",
                "body": {"registrationNumber": reg_no}
            },
            {
                "url": f"https://vehicle-rc-information.p.rapidapi.com/vehicle-info",
                "headers": {
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0"
                },
                "method": "POST",
                "body": {"regNo": reg_no}
            }
        ]
        
        for api in apis:
            try:
                if api["method"] == "POST":
                    resp = requests.post(api["url"], json=api["body"], headers=api["headers"], timeout=10)
                else:
                    resp = requests.get(api["url"], headers=api["headers"], timeout=10)
                
                if resp.status_code == 200:
                    data = resp.json()
                    if data:
                        return {"source": "rcinfo", "success": True, "data": data}
            except:
                continue
        
        return {"source": "rcinfo", "success": False, "error": "All APIs failed"}
    except Exception as e:
        return {"source": "rcinfo", "success": False, "error": str(e)}

# ============================================
# SOURCE 4: Spinny Scraper (Simple HTTP)
# ============================================
def fetch_spinny_simple(reg_no):
    print("🔹 Fetching from Spinny...")
    try:
        url = f"https://www.spinny.com/api/v1/vehicle-info/{reg_no}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Referer": "https://www.spinny.com/rto-details/"
        }
        
        resp = requests.get(url, headers=headers, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            if data:
                return {"source": "spinny", "success": True, "data": data}
        
        return {"source": "spinny", "success": False, "error": "No data"}
    except Exception as e:
        return {"source": "spinny", "success": False, "error": str(e)}

# ============================================
# MERGE FUNCTION
# ============================================
def merge_all_results(all_results):
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
        
        # Set RC Number
        if data.get("rc_number") and not merged["rc_number"]:
            merged["rc_number"] = data["rc_number"]
        
        # Set Owner Name
        if data.get("owner_name") and not merged["owner_name"]:
            merged["owner_name"] = data["owner_name"]
        
        # Vehicle Details
        for key in ["model", "make", "fuel_type", "color", "vehicle_age", "norms"]:
            if data.get(key) and not merged["vehicle_details"].get(key):
                merged["vehicle_details"][key] = data[key]
        
        # Registration Details
        for key in ["registration_date", "rto_name", "rto_code", "state", "city"]:
            if data.get(key) and not merged["registration_details"].get(key):
                merged["registration_details"][key] = data[key]
        
        # Technical Specs
        for key in ["chassis_number", "engine_number", "cc", "seating_capacity"]:
            if data.get(key) and not merged["technical_specs"].get(key):
                merged["technical_specs"][key] = data[key]
        
        # Insurance Details
        for key in ["insurance_validity", "insurance_expiry", "fitness_validity", "fitness_expiry", "tax_validity"]:
            if data.get(key):
                if "insurance" in key and not merged["insurance_details"].get("validity"):
                    merged["insurance_details"]["validity"] = data[key]
                elif "fitness" in key and not merged["insurance_details"].get("fitness"):
                    merged["insurance_details"]["fitness"] = data[key]
                elif "tax" in key and not merged["insurance_details"].get("tax"):
                    merged["insurance_details"]["tax"] = data[key]
        
        # Contact Info
        for key in ["mobile_number", "email", "phone"]:
            if data.get(key) and not merged["contact_info"].get(key):
                merged["contact_info"][key] = data[key]
    
    return merged

# ============================================
# MAIN API ENDPOINT
# ============================================
@app.route('/rc', methods=['GET'])
def rc_details():
    reg_no = request.args.get('num', '').strip().upper()
    
    if not reg_no:
        return jsonify({
            "error": True,
            "message": "Registration number required",
            "usage": "/rc?num=MH14KK9159"
        }), 400
    
    if not re.match(r'^[A-Z]{2}\d{1,2}[A-Z]{1,3}\d{1,4}$', reg_no):
        return jsonify({
            "error": True,
            "message": "Invalid format. Example: MH14KK9159"
        }), 400
    
    start_time = time.time()
    all_results = []
    
    # Fetch from all sources
    result = fetch_carinfo(reg_no)
    all_results.append(result)
    
    result = fetch_91wheels(reg_no)
    all_results.append(result)
    
    # Merge results
    merged_data = merge_all_results(all_results)
    
    response_time = round(time.time() - start_time, 2)
    
    # Check if we got any useful data
    has_data = bool(merged_data.get("rc_number") or 
                   merged_data.get("owner_name") or 
                   merged_data.get("vehicle_details"))
    
    final_response = {
        "status": "SUCCESS" if has_data else "FAILED",
        "response_time_seconds": response_time,
        "data": merged_data,
        "meta": {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "sources_used": merged_data["sources_used"],
            "total_sources_checked": len(all_results),
            "successful_sources": len([r for r in all_results if r.get("success")])
        }
    }
    
    return jsonify(final_response)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "Vehicle RC API v2.0"})

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "service": "Vehicle RC Information API",
        "version": "2.0",
        "usage": "/rc?num=MH14KK9159",
        "sources": ["CarInfo", "91Wheels"]
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
