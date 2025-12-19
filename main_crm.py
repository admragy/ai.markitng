"""
Brilliox Marketing AI + CRM المتقدم - النسخة النهائية 🚀
نظام تسويق رقمي احترافي مع CRM خطير + المحاور الذكي + WhatsApp
"""
import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates

# استيراد خدمات CRM
from app.services.crm_service import crm_service
from app.models.crm_models import LeadCreate, LeadUpdate

# تهيئة التطبيق
app = FastAPI(
    title="Brilliox Marketing AI + CRM",
    description="🚀 نظام تسويق رقمي ذكي مع CRM متقدم + المحاور الذكي + WhatsApp",
    version="6.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files & Templates
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
    templates = Jinja2Templates(directory="templates")
except:
    templates = None


# ==================== الصفحات الرئيسية ====================

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """الصفحة الرئيسية"""
    if templates:
        return templates.TemplateResponse("mobile_app.html", {"request": request})
    return HTMLResponse("<h1>Brilliox CRM API is running! 🚀</h1><p>Visit <a href='/docs'>/docs</a> for API documentation</p>")


@app.get("/crm", response_class=HTMLResponse)
async def crm_dashboard(request: Request):
    """لوحة تحكم CRM"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html dir="rtl" lang="ar">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Brilliox CRM Dashboard</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', Tahoma, sans-serif; }
            body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { background: rgba(255,255,255,0.95); backdrop-filter: blur(10px); border-radius: 20px; padding: 30px; margin-bottom: 20px; box-shadow: 0 8px 32px rgba(0,0,0,0.1); }
            .header h1 { color: #667eea; font-size: 2.5em; margin-bottom: 10px; }
            .header p { color: #666; font-size: 1.1em; }
            .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 20px; }
            .stat-card { background: rgba(255,255,255,0.95); border-radius: 15px; padding: 25px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
            .stat-card h3 { color: #667eea; font-size: 1em; margin-bottom: 10px; }
            .stat-card .number { font-size: 2.5em; font-weight: bold; color: #333; }
            .feature-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
            .feature-card { background: rgba(255,255,255,0.95); border-radius: 15px; padding: 25px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
            .feature-card h3 { color: #667eea; font-size: 1.3em; margin-bottom: 15px; }
            .feature-card ul { list-style: none; }
            .feature-card li { padding: 8px 0; color: #555; border-bottom: 1px solid #eee; }
            .feature-card li:last-child { border: none; }
            .api-link { display: inline-block; background: #667eea; color: white; padding: 15px 30px; border-radius: 10px; text-decoration: none; font-weight: bold; margin-top: 20px; }
            .api-link:hover { background: #764ba2; transform: translateY(-2px); box-shadow: 0 4px 15px rgba(0,0,0,0.2); }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 Brilliox CRM Dashboard</h1>
                <p>نظام إدارة علاقات العملاء الذكي + المحاور الذكي + WhatsApp</p>
                <a href="/docs" class="api-link">📚 توثيق API الكامل</a>
            </div>
            
            <div class="stats-grid" id="stats">
                <div class="stat-card">
                    <h3>إجمالي العملاء</h3>
                    <div class="number" id="total-leads">...</div>
                </div>
                <div class="stat-card">
                    <h3>عملاء اليوم</h3>
                    <div class="number" id="new-today">...</div>
                </div>
                <div class="stat-card">
                    <h3>Hot Leads 🔥</h3>
                    <div class="number" id="hot-leads">...</div>
                </div>
                <div class="stat-card">
                    <h3>معدل التحويل</h3>
                    <div class="number" id="conversion-rate">...</div>
                </div>
            </div>
            
            <div class="feature-grid">
                <div class="feature-card">
                    <h3>🧠 المحاور الذكي</h3>
                    <ul>
                        <li>✅ فهم النوايا والمشاعر</li>
                        <li>✅ تحليل جودة العملاء تلقائياً</li>
                        <li>✅ كشف الفرص البيعية</li>
                        <li>✅ ردود مخصصة ذكية</li>
                        <li>✅ التعلم من المحادثات</li>
                    </ul>
                </div>
                
                <div class="feature-card">
                    <h3>📱 تكامل WhatsApp</h3>
                    <ul>
                        <li>✅ إرسال/استقبال تلقائي</li>
                        <li>✅ ردود ذكية فورية</li>
                        <li>✅ رسائل ترحيب تلقائية</li>
                        <li>✅ تتبع المحادثات</li>
                        <li>✅ إشعارات الفرص الساخنة</li>
                    </ul>
                </div>
                
                <div class="feature-card">
                    <h3>📊 إدارة العملاء</h3>
                    <ul>
                        <li>✅ تصنيف ذكي (Hot/Warm/Cold)</li>
                        <li>✅ حساب نقاط تلقائي</li>
                        <li>✅ تتبع التفاعلات</li>
                        <li>✅ مهام متابعة تلقائية</li>
                        <li>✅ تحليلات متقدمة</li>
                    </ul>
                </div>
                
                <div class="feature-card">
                    <h3>⚡ أتمتة ذكية</h3>
                    <ul>
                        <li>✅ مهام تلقائية عند إضافة عميل</li>
                        <li>✅ تنبيهات الفرص الساخنة</li>
                        <li>✅ رسائل ترحيب تلقائية</li>
                        <li>✅ تحديث النقاط تلقائياً</li>
                        <li>✅ توصيات ذكية</li>
                    </ul>
                </div>
            </div>
        </div>
        
        <script>
            // جلب الإحصائيات من API
            fetch('/api/crm/dashboard')
                .then(r => r.json())
                .then(data => {
                    if (data.success && data.stats) {
                        document.getElementById('total-leads').textContent = data.stats.total_leads;
                        document.getElementById('new-today').textContent = data.stats.new_leads_today;
                        document.getElementById('hot-leads').textContent = data.stats.hot_leads;
                        document.getElementById('conversion-rate').textContent = data.stats.avg_conversion_rate + '%';
                    }
                })
                .catch(e => console.error('Error loading stats:', e));
        </script>
    </body>
    </html>
    """)


# ==================== CRM API ROUTES ====================

@app.get("/api/crm/dashboard")
async def get_crm_dashboard():
    """لوحة تحكم CRM - الإحصائيات الرئيسية"""
    return await crm_service.get_dashboard()


@app.post("/api/crm/leads")
async def create_lead(lead: LeadCreate):
    """إنشاء عميل محتمل جديد"""
    return await crm_service.create_lead(lead)


@app.get("/api/crm/leads/{lead_id}")
async def get_lead(lead_id: int):
    """الحصول على بيانات عميل محدد"""
    return await crm_service.get_lead(lead_id)


@app.put("/api/crm/leads/{lead_id}")
async def update_lead(lead_id: int, updates: LeadUpdate):
    """تحديث بيانات عميل"""
    return await crm_service.update_lead(lead_id, updates)


@app.get("/api/crm/leads")
async def search_leads(
    status: str = None,
    source: str = None,
    search: str = None,
    limit: int = 50,
    offset: int = 0
):
    """البحث والتصفية في العملاء"""
    filters = {}
    if status:
        filters['status'] = [status]
    if source:
        filters['source'] = [source]
    if search:
        filters['search'] = search
    
    return await crm_service.search_leads(filters, limit, offset)


@app.post("/api/crm/leads/{lead_id}/message")
async def handle_lead_message(lead_id: int, request: Request):
    """معالجة رسالة واردة من عميل (المحاور الذكي)"""
    data = await request.json()
    message = data.get('message', '')
    channel = data.get('channel', 'whatsapp')
    
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    return await crm_service.handle_incoming_message(lead_id, message, channel)


@app.post("/api/crm/leads/{lead_id}/send")
async def send_message_to_lead(lead_id: int, request: Request):
    """إرسال رسالة لعميل"""
    data = await request.json()
    message = data.get('message', '')
    channel = data.get('channel', 'whatsapp')
    
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    return await crm_service.send_message_to_lead(lead_id, message, channel)


@app.get("/api/crm/tasks")
async def get_tasks(user_id: int = None):
    """الحصول على المهام"""
    return await crm_service.get_my_tasks(user_id)


# ==================== WhatsApp Webhook ====================

@app.get("/api/whatsapp/webhook")
async def whatsapp_webhook_verify(request: Request):
    """التحقق من WhatsApp webhook"""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    
    if mode == "subscribe" and token == os.getenv("WHATSAPP_WEBHOOK_TOKEN", "brilliox_token"):
        return HTMLResponse(content=challenge)
    
    raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/api/whatsapp/webhook")
async def whatsapp_webhook(request: Request):
    """استقبال رسائل WhatsApp الواردة"""
    try:
        data = await request.json()
        # معالجة الرسالة الواردة هنا
        # يمكن ربطها مع CRM لاحقاً
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"WhatsApp webhook error: {e}")
        return {"status": "error"}


# ==================== API الأصلي (التسويق) ====================

@app.post("/api/chat")
async def chat(request: Request):
    """API للمحادثة مع الذكاء الاصطناعي"""
    try:
        data = await request.json()
        message = data.get('message', '')
        
        from app.services.ai_service_clean import AIMarketingService
        ai_service = AIMarketingService()
        response = await ai_service.chat(message)
        
        return JSONResponse(response)
        
    except Exception as e:
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=500)


@app.get("/api/facebook-ads/guide")
async def facebook_ads_guide():
    """دليل إنشاء إعلانات Facebook"""
    from app.services.facebook_boost_service import FacebookBoostService
    
    service = FacebookBoostService()
    guide = service.get_setup_guide()
    
    return JSONResponse(guide)


@app.get("/api/health")
async def health_check():
    """فحص صحة التطبيق"""
    return {
        'status': 'healthy',
        'version': '6.0.0',
        'features': [
            '🚀 Brilliox Marketing AI',
            '🧠 المحاور الذكي (Smart Conversational AI)',
            '📱 WhatsApp Integration',
            '💼 CRM المتقدم',
            '⚡ أتمتة ذكية',
            '📊 تحليلات متقدمة',
            '🔥 كشف الفرص الساخنة تلقائياً'
        ]
    }


# ==================== Startup ====================

@app.on_event("startup")
async def startup_event():
    """عند بدء التشغيل"""
    print("=" * 70)
    print("🚀 Brilliox Marketing AI + CRM - Starting...")
    print("=" * 70)
    print("✅ Clean Marketing Code")
    print("✅ Facebook Ads Solution")
    print("✅ Mobile App PWA")
    print("✅ 🧠 المحاور الذكي (Smart Conversational AI)")
    print("✅ 📱 WhatsApp Integration")
    print("✅ 💼 CRM المتقدم + Database")
    print("✅ ⚡ أتمتة ذكية شاملة")
    print("=" * 70)
    print("📱 Main App: http://localhost:5000")
    print("💼 CRM Dashboard: http://localhost:5000/crm")
    print("📚 API Docs: http://localhost:5000/docs")
    print("=" * 70)


# ==================== Run ====================

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 5000))
    
    uvicorn.run(
        "main_crm:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
