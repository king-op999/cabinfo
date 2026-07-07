// api/index.js - BRONX VEHICLE RC API (Attestr)
const express = require('express');
const axios = require('axios');
const app = express();

// 🔥 Attestr API Config
const ATTESTR_URL = 'https://api.attestr.com/api/v3/public/checkx/rc';
const ATTESTR_AUTH = 'Basic T1gweWJ5ZklzQlVRaXJVX25uLmNjNmIwMTg3YTMzZDQwODVmY2NiMmJjMWJlYzhlYjNiOjJhOTg4MTFiYThjODgyMWY2NWM3MjE0ZmJkMDk1ZmFlNmE1NDE5YWIyNzQ5ODA4Ng==';

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
    res.send(`<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>BRONX VEHICLE RC</title>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@400;600&display=swap" rel="stylesheet"><style>
*{margin:0;padding:0;box-sizing:border-box}body{background:#000010;color:#fff;font-family:'Rajdhani',sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;padding:20px}
.card{background:rgba(10,10,30,.9);border:1px solid rgba(0,200,255,.1);border-radius:24px;padding:30px;max-width:650px;width:100%;text-align:center}
h1{font-family:'Orbitron',sans-serif;font-size:28px;background:linear-gradient(90deg,#0096ff,#00c8ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.badge{display:inline-block;background:rgba(0,200,255,.1);color:#00c8ff;padding:4px 14px;border-radius:20px;font-size:10px;letter-spacing:2px;margin:8px 0}
.row{display:flex;gap:8px;margin:16px 0}.row input{flex:1;padding:15px;background:#000;border:1px solid #222;border-radius:14px;color:#fff;font-size:14px;outline:none;font-family:'Rajdhani',sans-serif;text-transform:uppercase}.row input:focus{border-color:#00c8ff}
.row button{padding:15px 28px;background:#00c8ff;color:#000;border:none;border-radius:14px;font-weight:700;cursor:pointer;font-family:'Orbitron',sans-serif}
.result{margin-top:16px;background:rgba(0,0,0,.5);border:1px solid rgba(0,255,136,.1);border-radius:14px;padding:16px;font-family:monospace;font-size:11px;color:#00ff88;max-height:400px;overflow:auto;white-space:pre-wrap;display:none;text-align:left;line-height:1.6}
code{display:block;background:rgba(0,0,0,.5);color:#00c8ff;padding:12px;border-radius:12px;font-size:10px;margin:8px 0;word-break:break-all}
</style></head><body><div class="card">
<h1>🚗 VEHICLE RC API</h1><p class="badge">Attestr · Official Vehicle Info</p>
<div class="row"><input type="text" id="vh" placeholder="ENTER VEHICLE NUMBER (e.g. TN12XX2345)" onkeypress="if(event.key==='Enter')search()"><button onclick="search()">🔍 SEARCH</button></div>
<div class="result" id="res"></div>
<code>GET ${url}/rc?reg=TN12XX2345</code>
<code style="margin-top:4px">POST ${url}/rc {"reg":"TN12XX2345"}</code>
</div><script>
async function search(){var v=document.getElementById('vh').value.trim();if(!v)return;var r=document.getElementById('res');r.style.display='block';r.style.color='#00c8ff';r.textContent='🔍 Searching...';try{var resp=await fetch('/rc?reg='+encodeURIComponent(v));var d=await resp.json();r.style.color=d.error?'#ff4444':'#00ff88';r.textContent=JSON.stringify(d,null,2)}catch(e){r.textContent='Error: '+e.message}}</script></body></html>`);
});

// ========== VEHICLE RC API ==========
app.get('/rc', async (req, res) => {
    try {
        const reg = req.query.reg || req.query.number || req.query.vehicle || '';
        
        if (!reg || reg.trim().length < 6) {
            return res.json({ error: 'Missing vehicle number. Use: /rc?reg=TN12XX2345' });
        }

        const vehicleNumber = reg.trim().toUpperCase().replace(/\s/g, '');
        console.log(`🚗 Looking up: ${vehicleNumber}`);

        // 🔥 Call Attestr API
        const response = await axios.post(
            ATTESTR_URL,
            {
                reg: vehicleNumber,
                consent: [{ consentId: "default" }]
            },
            {
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': ATTESTR_AUTH
                },
                timeout: 30000
            }
        );

        const data = response.data;
        console.log(`✅ Response received`);

        // Clean response
        if (data && typeof data === 'object') {
            // Remove sensitive fields if any
            delete data.api_key;
            delete data.auth_token;
            
            res.json({
                success: true,
                vehicle_number: vehicleNumber,
                data: data,
                query_time: new Date().toISOString(),
                powered_by: '@BRONX_ULTRA'
            });
        } else {
            res.json({
                success: false,
                error: 'No data returned from API',
                vehicle_number: vehicleNumber
            });
        }

    } catch (e) {
        console.error('RC Error:', e.response?.data || e.message);
        
        res.status(500).json({
            success: false,
            error: e.response?.data?.message || e.message || 'API request failed',
            vehicle_number: req.query.reg || ''
        });
    }
});

// ========== POST METHOD ==========
app.post('/rc', async (req, res) => {
    try {
        const reg = req.body.reg || req.body.number || req.body.vehicle || '';
        
        if (!reg) {
            return res.json({ error: 'Missing vehicle number. Send: {"reg": "TN12XX2345"}' });
        }

        const vehicleNumber = reg.trim().toUpperCase().replace(/\s/g, '');

        const response = await axios.post(
            ATTESTR_URL,
            {
                reg: vehicleNumber,
                consent: [{ consentId: "default" }]
            },
            {
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': ATTESTR_AUTH
                },
                timeout: 30000
            }
        );

        const data = response.data;
        delete data.api_key;
        delete data.auth_token;

        res.json({
            success: true,
            vehicle_number: vehicleNumber,
            data: data,
            powered_by: '@BRONX_ULTRA'
        });

    } catch (e) {
        res.status(500).json({
            success: false,
            error: e.response?.data?.message || e.message
        });
    }
});

// ========== TEST ==========
app.get('/test', (req, res) => {
    const url = `${req.protocol}://${req.get('host')}`;
    res.json({
        status: '✅ BRONX VEHICLE RC API ONLINE',
        provider: 'Attestr',
        endpoints: {
            get: `${url}/rc?reg=TN12XX2345`,
            post: `POST ${url}/rc`,
            home: url
        },
        test_vehicles: ['TN12XX2345', 'MH02FZ0555', 'DL1CX1234', 'KA01AB1234']
    });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, '0.0.0.0', () => {
    console.log('🚗 BRONX VEHICLE RC API ONLINE!');
    console.log(`🔗 /rc?reg=TN12XX2345`);
    console.log(`🚀 PORT: ${PORT}`);
});
module.exports = app;
