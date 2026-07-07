// api/index.js - BRONX ALL-IN-ONE VEHICLE API V1.0
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
    res.send(`<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>BRONX VEHICLE API</title>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@400;600&display=swap" rel="stylesheet"><style>
*{margin:0;padding:0;box-sizing:border-box}body{background:#000010;color:#fff;font-family:'Rajdhani',sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;padding:20px}
.card{background:rgba(10,10,30,.9);border:1px solid rgba(0,200,255,.1);border-radius:24px;padding:30px;max-width:700px;width:100%;text-align:center}
h1{font-family:'Orbitron',sans-serif;font-size:28px;background:linear-gradient(90deg,#0096ff,#00c8ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.badge{display:inline-block;background:rgba(0,200,255,.1);color:#00c8ff;padding:4px 14px;border-radius:20px;font-size:10px;letter-spacing:2px;margin:8px 0}
.sources{color:#888;font-size:9px;margin:8px 0;line-height:1.6}
.row{display:flex;gap:8px;margin:16px 0}.row input{flex:1;padding:15px;background:#000;border:1px solid #222;border-radius:14px;color:#fff;font-size:14px;outline:none;font-family:'Rajdhani',sans-serif;text-transform:uppercase}.row input:focus{border-color:#00c8ff}
.row button{padding:15px 28px;background:#00c8ff;color:#000;border:none;border-radius:14px;font-weight:700;cursor:pointer;font-family:'Orbitron',sans-serif}
.result{margin-top:16px;background:rgba(0,0,0,.5);border:1px solid rgba(0,255,136,.1);border-radius:14px;padding:16px;font-family:monospace;font-size:11px;color:#00ff88;max-height:400px;overflow:auto;white-space:pre-wrap;display:none;text-align:left;line-height:1.6}
code{display:block;background:rgba(0,0,0,.5);color:#00c8ff;padding:12px;border-radius:12px;font-size:10px;margin:8px 0;word-break:break-all}
</style></head><body><div class="card">
<h1>🚗 ALL-IN-ONE VEHICLE API</h1><p class="badge">6 Sources Combined</p>
<p class="sources">🟢 VahanX · 🟢 IshanX · 🟢 Chola Insurance · 🟢 Royal Sundaram · 🟢 GTPlay · 🟢 Attestr</p>
<div class="row"><input type="text" id="vh" placeholder="ENTER VEHICLE NUMBER (e.g. MH02FZ0555)" onkeypress="if(event.key==='Enter')search()"><button onclick="search()">🔍 SEARCH</button></div>
<div class="result" id="res"></div>
<code>GET ${url}/vehicle?number=MH02FZ0555</code>
</div><script>
async function search(){var v=document.getElementById('vh').value.trim();if(!v)return;var r=document.getElementById('res');r.style.display='block';r.style.color='#00c8ff';r.textContent='🔍 Searching all sources...';try{var resp=await fetch('/vehicle?number='+encodeURIComponent(v));var d=await resp.json();r.style.color=d.error?'#ff4444':'#00ff88';r.textContent=JSON.stringify(d,null,2)}catch(e){r.textContent='Error: '+e.message}}</script></body></html>`);
});

// ========== VEHICLE API SOURCES ==========
async function trySource(name, url, options = {}) {
    try {
        const resp = await axios.get(url, { timeout: 15000, ...options });
        if (resp.data && Object.keys(resp.data).length > 0) {
            return { source: name, success: true, data: resp.data };
        }
        return { source: name, success: false, error: 'Empty response' };
    } catch (e) {
        return { source: name, success: false, error: e.message };
    }
}

// ========== MAIN API ==========
app.get('/vehicle', async (req, res) => {
    try {
        const number = req.query.number || req.query.vh || req.query.rc || '';
        if (!number || number.trim().length < 6) {
            return res.json({ error: 'Missing vehicle number. Use: /vehicle?number=MH02FZ0555' });
        }

        const vh = number.trim().toUpperCase().replace(/\s/g, '');
        console.log(`🚗 Looking up: ${vh}`);

        const results = [];
        let bestData = null;

        // 🔥 Source 1: VahanX
        const vahanx = await trySource('VahanX', `https://vahanx.in/rc-search/${vh}`, {
            headers: { 'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'en-US' }
        });
        results.push(vahanx);
        if (vahanx.success) bestData = bestData || vahanx.data;

        // 🔥 Source 2: IshanX Studio
        const ishanx = await trySource('IshanX', `https://ishanxstudio.space/rc?query=${vh}`, {
            headers: { 'User-Agent': 'Mozilla/5.0' }
        });
        results.push(ishanx);
        if (ishanx.success) {
            const d = ishanx.data;
            if (d.rc_chudai?.data?.[0]) bestData = bestData || d.rc_chudai.data[0];
        }

        // 🔥 Source 3: Chola Insurance
        try {
            const cholaResp = await axios.post(
                'https://digital.cholainsurance.com/api/v1/masterdata/vehicle_class_validation',
                { vehicleNumber: vh, journeyChannel: 'CSC', productName: 'Private Car', signzySelPolicytype: 'Comprehensive' },
                {
                    headers: {
                        'Content-Type': 'application/json',
                        'Origin': 'https://digital.cholainsurance.com',
                        'Referer': 'https://digital.cholainsurance.com/',
                        'User-Agent': 'Mozilla/5.0'
                    },
                    timeout: 15000
                }
            );
            results.push({ source: 'Chola Insurance', success: true, data: cholaResp.data });
            if (cholaResp.data?.data) bestData = bestData || cholaResp.data.data;
        } catch (e) {
            results.push({ source: 'Chola Insurance', success: false, error: e.message });
        }

        // 🔥 Source 4: Royal Sundaram
        try {
            const tokenResp = await axios.post(
                'https://www.royalsundaram.in/car-insurance/proxy/apiproxy/eappspolicyservices/getTokenForVehicleDetails',
                {},
                {
                    headers: {
                        'Content-Type': 'application/json',
                        'registrationno': vh,
                        'User-Agent': 'Mozilla/5.0'
                    },
                    timeout: 15000
                }
            );
            if (tokenResp.data?.token) {
                const detailResp = await axios.post(
                    'https://www.royalsundaram.in/car-insurance/proxy/apiproxy/eappspolicyservices/getVehicleDetails',
                    { registrationNo: vh, token: tokenResp.data.token },
                    {
                        headers: {
                            'Content-Type': 'application/json',
                            'registrationno': vh,
                            'token': tokenResp.data.token,
                            'User-Agent': 'Mozilla/5.0'
                        },
                        timeout: 15000
                    }
                );
                results.push({ source: 'Royal Sundaram', success: true, data: detailResp.data });
                if (detailResp.data?.data) bestData = bestData || detailResp.data.data;
            } else {
                results.push({ source: 'Royal Sundaram', success: false, error: 'No token' });
            }
        } catch (e) {
            results.push({ source: 'Royal Sundaram', success: false, error: e.message });
        }

        // 🔥 Source 5: GTPlay
        try {
            const gtplayResp = await axios.post(
                'https://gtplay.in/API/vehicle_challan_info/puc_info.php',
                `vehicle_no=${vh}`,
                {
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'User-Agent': 'Dalvik/2.1.0'
                    },
                    timeout: 15000
                }
            );
            results.push({ source: 'GTPlay', success: true, data: gtplayResp.data });
        } catch (e) {
            results.push({ source: 'GTPlay', success: false, error: e.message });
        }

        // 🔥 Source 6: Attestr (POST)
        try {
            const attestrResp = await axios.post(
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
            results.push({ source: 'Attestr', success: true, data: attestrResp.data });
            if (attestrResp.data) bestData = bestData || attestrResp.data;
        } catch (e) {
            results.push({ source: 'Attestr', success: false, error: e.message });
        }

        // 🔥 Extract best info from all sources
        const info = {
            vehicle_number: vh,
            owner_name: extractValue(bestData, ['owner_name', 'ownerName', 'owner', 'Owner Name']),
            father_name: extractValue(bestData, ['father_name', 'fatherName', 'Father\'s Name']),
            registration_date: extractValue(bestData, ['registration_date', 'regDate', 'Registration Date', 'regn_dt']),
            fuel_type: extractValue(bestData, ['fuel_type', 'fuelType', 'Fuel Type', 'fuel']),
            maker_model: extractValue(bestData, ['maker_model', 'makerModel', 'Model Name', 'model', 'vehicle_model']),
            vehicle_class: extractValue(bestData, ['vehicle_class', 'vehicleClass', 'Vehicle Class', 'vh_class']),
            chassis_number: extractValue(bestData, ['chassis_number', 'chassisNo', 'Chassis Number', 'chasi_no']),
            engine_number: extractValue(bestData, ['engine_number', 'engineNo', 'Engine Number', 'engine_no']),
            insurance_company: extractValue(bestData, ['insurance_company', 'insuranceCompany', 'Insurance Company']),
            insurance_valid: extractValue(bestData, ['insurance_valid', 'insuranceExpiry', 'Insurance Expiry', 'insUpto']),
            rto: extractValue(bestData, ['rto', 'rto_name', 'Registered RTO']),
            state: extractValue(bestData, ['state', 'stateName']),
            sources: results.map(r => ({ name: r.source, status: r.success ? '✅' : '❌' })),
            query_time: new Date().toISOString(),
            powered_by: '@BRONX_ULTRA'
        };

        console.log(`✅ Vehicle info fetched from ${results.filter(r => r.success).length} sources`);
        res.json({ success: true, ...info });

    } catch (e) {
        console.error('Error:', e.message);
        res.status(500).json({ error: 'Server error', message: e.message });
    }
});

// ========== HELPER ==========
function extractValue(data, keys) {
    if (!data || typeof data !== 'object') return 'N/A';
    for (const key of keys) {
        if (data[key] && data[key] !== '') return data[key];
        // Check nested
        const flat = JSON.stringify(data);
        const match = flat.match(new RegExp(`"${key}"\\s*:\\s*"([^"]+)"`));
        if (match) return match[1];
    }
    return 'N/A';
}

// ========== TEST ==========
app.get('/test', (req, res) => {
    res.json({
        status: '✅ ALL-IN-ONE VEHICLE API ONLINE',
        sources: ['VahanX', 'IshanX', 'Chola Insurance', 'Royal Sundaram', 'GTPlay', 'Attestr'],
        usage: '/vehicle?number=MH02FZ0555'
    });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, '0.0.0.0', () => {
    console.log('🚗 ALL-IN-ONE VEHICLE API ONLINE!');
    console.log(`🔗 /vehicle?number=MH02FZ0555`);
    console.log(`🚀 PORT: ${PORT}`);
});
module.exports = app;
