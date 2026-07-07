// api/index.js - BRONX ALL-IN-ONE VEHICLE API V2.0 (FIXED)
const express = require('express');
const axios = require('axios');
const app = express();

app.use(express.json({ limit: '10mb' }));
app.use((req, res, next) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    if (req.method === 'OPTIONS') return res.status(200).end();
    next();
});

// ========== HOME PAGE ==========
app.get('/', (req, res) => {
    const url = `${req.protocol}://${req.get('host')}`;
    res.send(`<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>BRONX VEHICLE V2</title>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@400;600&display=swap" rel="stylesheet"><style>
*{margin:0;padding:0;box-sizing:border-box}body{background:#000010;color:#fff;font-family:'Rajdhani',sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;padding:20px}
.card{background:rgba(10,10,30,.9);border:1px solid rgba(0,200,255,.1);border-radius:24px;padding:30px;max-width:700px;width:100%;text-align:center}
h1{font-family:'Orbitron',sans-serif;font-size:28px;background:linear-gradient(90deg,#0096ff,#00c8ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.badge{display:inline-block;background:rgba(0,255,136,.1);color:#00ff88;padding:4px 14px;border-radius:20px;font-size:10px;margin:8px 0}
.row{display:flex;gap:8px;margin:16px 0}.row input{flex:1;padding:15px;background:#000;border:1px solid #222;border-radius:14px;color:#fff;font-size:14px;outline:none;font-family:'Rajdhani',sans-serif;text-transform:uppercase}.row input:focus{border-color:#00c8ff}
.row button{padding:15px 28px;background:#00c8ff;color:#000;border:none;border-radius:14px;font-weight:700;cursor:pointer;font-family:'Orbitron',sans-serif}
.result{margin-top:16px;background:rgba(0,0,0,.5);border:1px solid rgba(0,255,136,.1);border-radius:14px;padding:16px;font-family:monospace;font-size:11px;color:#00ff88;max-height:400px;overflow:auto;white-space:pre-wrap;display:none;text-align:left;line-height:1.6}
code{display:block;background:rgba(0,0,0,.5);color:#00c8ff;padding:12px;border-radius:12px;font-size:10px;margin:8px 0;word-break:break-all}
</style></head><body><div class="card">
<h1>🚗 BRONX VEHICLE V2</h1><p class="badge">✅ Fixed Data Extraction</p>
<div class="row"><input type="text" id="vh" placeholder="MH02FZ0555" onkeypress="if(event.key==='Enter')search()"><button onclick="search()">🔍 SEARCH</button></div>
<div class="result" id="res"></div>
<code>GET ${url}/vehicle?number=MH02FZ0555</code>
</div><script>
async function search(){var v=document.getElementById('vh').value.trim();if(!v)return;var r=document.getElementById('res');r.style.display='block';r.style.color='#00c8ff';r.textContent='🔍 Searching...';try{var resp=await fetch('/vehicle?number='+encodeURIComponent(v));var d=await resp.json();r.style.color=d.error?'#ff4444':'#00ff88';r.textContent=JSON.stringify(d,null,2)}catch(e){r.textContent='Error: '+e.message}}</script></body></html>`);
});

// ========== EXTRACTION HELPERS ==========
function extractFromHTML(html, label) {
    try {
        // Pattern: <span>Label</span> ke baad <p>Value</p>
        const regex = new RegExp(`<span[^>]*>\\s*${label}\\s*<\\/span>[\\s\\S]*?<p[^>]*>([^<]+)<\\/p>`, 'i');
        const match = html.match(regex);
        return match ? match[1].trim() : null;
    } catch (e) {
        return null;
    }
}

function extractJSONValue(data, keys) {
    if (!data || typeof data !== 'object') return null;
    const flat = JSON.stringify(data);
    for (const key of keys) {
        const regex = new RegExp(`"${key}"\\s*[:=]\\s*"([^"]+)"`, 'i');
        const match = flat.match(regex);
        if (match) return match[1];
        if (data[key] && typeof data[key] === 'string' && data[key].length > 0) return data[key];
    }
    return null;
}

// ========== MAIN API ==========
app.get('/vehicle', async (req, res) => {
    try {
        const number = req.query.number || req.query.vh || '';
        if (!number || number.trim().length < 6) {
            return res.json({ error: 'Missing vehicle number. Use: /vehicle?number=MH02FZ0555' });
        }

        const vh = number.trim().toUpperCase().replace(/\s/g, '');
        console.log(`\n🚗 Looking up: ${vh}`);

        let htmlData = null;
        let jsonData = null;
        const sources = [];

        // 🔥 SOURCE 1: VahanX (HTML Scraping)
        try {
            console.log('[1] VahanX...');
            const resp = await axios.get(`https://vahanx.in/rc-search/${vh}`, {
                headers: {
                    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml',
                    'Accept-Language': 'en-US,en;q=0.9'
                },
                timeout: 20000
            });
            htmlData = resp.data;
            
            // Extract all fields from HTML
            const fields = {};
            const labels = [
                'Owner Name', 'Father\'s Name', 'Owner Serial No', 'Model Name', 'Maker Model',
                'Vehicle Class', 'Fuel Type', 'Fuel Norms', 'Registration Date', 'Insurance Company',
                'Insurance No', 'Insurance Expiry', 'Insurance Upto', 'Fitness Upto', 'Tax Upto',
                'PUC No', 'PUC Upto', 'Financier Name', 'Registered RTO', 'Address', 'City Name', 'Phone',
                'Chassis Number', 'Engine Number', 'Cubic Capacity', 'Seating Capacity', 'Permit Type',
                'Blacklist Status', 'NOC Details'
            ];
            
            labels.forEach(label => {
                const val = extractFromHTML(htmlData, label);
                if (val && val !== 'N/A' && val !== '') {
                    fields[label] = val;
                }
            });
            
            const hasData = Object.keys(fields).length > 2;
            sources.push({ name: 'VahanX', status: hasData ? '✅' : '⚠️', fields: Object.keys(fields).length });
            if (hasData) jsonData = fields;
            console.log(`[1] VahanX: ${Object.keys(fields).length} fields`);
            
        } catch (e) {
            console.log(`[1] VahanX Error: ${e.message}`);
            sources.push({ name: 'VahanX', status: '❌' });
        }

        // 🔥 SOURCE 2: IshanX Studio (JSON API)
        if (!jsonData || Object.keys(jsonData).length < 5) {
            try {
                console.log('[2] IshanX...');
                const resp = await axios.get(`https://ishanxstudio.space/rc?query=${vh}`, {
                    headers: { 'User-Agent': 'Mozilla/5.0' },
                    timeout: 20000
                });
                const data = resp.data;
                
                if (data?.rc_chudai?.data?.[0]) {
                    const vehicle = data.rc_chudai.data[0];
                    const fields = {};
                    
                    const mapping = {
                        'owner_name': 'Owner Name', 'father_name': "Father's Name",
                        'reg_no': 'Registration Number', 'regn_dt': 'Registration Date',
                        'fuel_type': 'Fuel Type', 'vehicle_model': 'Model Name',
                        'maker_modal': 'Maker Model', 'vh_class': 'Vehicle Class',
                        'chasi_no': 'Chassis Number', 'engine_no': 'Engine Number',
                        'insurance_comp': 'Insurance Company', 'insUpto': 'Insurance Upto',
                        'rto': 'Registered RTO', 'address': 'Address',
                        'mobile_no': 'Phone', 'puc_no': 'PUC No', 'puc_upto': 'PUC Upto',
                        'financer_details': 'Financier Name', 'cubic_cap': 'Cubic Capacity',
                        'no_of_seats': 'Seating Capacity', 'permit_type': 'Permit Type',
                        'blacklist_status': 'Blacklist Status', 'noc_details': 'NOC Details'
                    };
                    
                    Object.entries(mapping).forEach(([apiKey, label]) => {
                        if (vehicle[apiKey] && vehicle[apiKey] !== '' && vehicle[apiKey] !== 'N/A') {
                            fields[label] = vehicle[apiKey];
                        }
                    });
                    
                    sources.push({ name: 'IshanX', status: '✅', fields: Object.keys(fields).length });
                    if (Object.keys(fields).length > (jsonData ? Object.keys(jsonData).length : 0)) {
                        jsonData = fields;
                    }
                    console.log(`[2] IshanX: ${Object.keys(fields).length} fields`);
                } else {
                    sources.push({ name: 'IshanX', status: '❌' });
                }
            } catch (e) {
                console.log(`[2] IshanX Error: ${e.message}`);
                sources.push({ name: 'IshanX', status: '❌' });
            }
        }

        // 🔥 SOURCE 3: Attestr (Auth API)
        if (!jsonData || Object.keys(jsonData).length < 5) {
            try {
                console.log('[3] Attestr...');
                const resp = await axios.post(
                    'https://api.attestr.com/api/v3/public/checkx/rc',
                    { reg: vh, consent: [{ consentId: 'default' }] },
                    {
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': 'Basic T1gweWJ5ZklzQlVRaXJVX25uLmNjNmIwMTg3YTMzZDQwODVmY2NiMmJjMWJlYzhlYjNiOjJhOTg4MTFiYThjODgyMWY2NWM3MjE0ZmJkMDk1ZmFlNmE1NDE5YWIyNzQ5ODA4Ng=='
                        },
                        timeout: 20000
                    }
                );
                const data = resp.data;
                
                if (data && Object.keys(data).length > 1) {
                    const fields = {};
                    const labels = [
                        'owner_name', 'father_name', 'registration_date', 'fuel_type',
                        'maker_model', 'vehicle_class', 'chassis_number', 'engine_number',
                        'insurance_company', 'insurance_valid', 'rto_name', 'state'
                    ];
                    labels.forEach(l => {
                        const val = extractJSONValue(data, [l]);
                        if (val) fields[l.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())] = val;
                    });
                    
                    sources.push({ name: 'Attestr', status: '✅', fields: Object.keys(fields).length });
                    if (Object.keys(fields).length > (jsonData ? Object.keys(jsonData).length : 0)) {
                        jsonData = fields;
                    }
                    console.log(`[3] Attestr: ${Object.keys(fields).length} fields`);
                } else {
                    sources.push({ name: 'Attestr', status: '❌' });
                }
            } catch (e) {
                console.log(`[3] Attestr Error: ${e.message}`);
                sources.push({ name: 'Attestr', status: '❌' });
            }
        }

        // ========== BUILD RESPONSE ==========
        const info = jsonData || {};
        
        const response = {
            success: Object.keys(info).length > 0,
            vehicle_number: vh,
            owner_name: info['Owner Name'] || info['owner_name'] || 'N/A',
            father_name: info["Father's Name"] || info['father_name'] || 'N/A',
            registration_date: info['Registration Date'] || info['registration_date'] || 'N/A',
            fuel_type: info['Fuel Type'] || info['fuel_type'] || 'N/A',
            maker_model: info['Maker Model'] || info['Model Name'] || info['maker_model'] || 'N/A',
            vehicle_class: info['Vehicle Class'] || info['vehicle_class'] || 'N/A',
            chassis_number: info['Chassis Number'] || info['chassis_number'] || 'N/A',
            engine_number: info['Engine Number'] || info['engine_number'] || 'N/A',
            insurance_company: info['Insurance Company'] || info['insurance_company'] || 'N/A',
            insurance_valid: info['Insurance Upto'] || info['Insurance Expiry'] || info['insurance_valid'] || 'N/A',
            rto: info['Registered RTO'] || info['rto'] || 'N/A',
            phone: info['Phone'] || info['mobile_no'] || 'N/A',
            address: info['Address'] || info['address'] || 'N/A',
            all_details: info,
            sources: sources,
            query_time: new Date().toISOString(),
            powered_by: '@BRONX_ULTRA'
        };

        console.log(`✅ Done! ${Object.keys(info).length} fields from ${sources.filter(s=>s.status==='✅').length} sources\n`);
        res.json(response);

    } catch (e) {
        console.error('Error:', e.message);
        res.status(500).json({ error: 'Server error', message: e.message });
    }
});

// ========== TEST ==========
app.get('/test', (req, res) => {
    res.json({
        status: '✅ BRONX VEHICLE API V2 ONLINE',
        test: '/vehicle?number=MH02FZ0555'
    });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, '0.0.0.0', () => {
    console.log('🚗 BRONX VEHICLE API V2 ONLINE!');
    console.log(`🔗 /vehicle?number=MH02FZ0555`);
    console.log(`🚀 PORT: ${PORT}`);
});
module.exports = app;
