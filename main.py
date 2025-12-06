from fastapi import FastAPI, BackgroundTasks, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os, re, json, requests, time, jwt, asyncio
from datetime import datetime, timedelta
from supabase import create_client, Client
from twilio.rest import Client as TwilioClient
from passlib.context import CryptContext
import anthropic

# ==================== إعدادات النظام ====================
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
SERPER_KEYS_RAW = os.environ.get("SERPER_KEYS", "")
SERPER_KEYS = [k.strip().replace('"', '') for k in SERPER_KEYS_RAW.split(',') if k.strip()]
TWILIO_SID = os.environ.get("TWILIO_SID")
TWILIO_TOKEN = os.environ.get("TWILIO_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.environ.get("TWILIO_WHATSAPP_NUMBER")
JWT_SECRET = os.environ.get("JWT_SECRET", "change-in-production")
JWT_ALGORITHM = "HS256"
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

app = FastAPI(title="Hunter Pro CRM AI System", version="5.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

key_index = 0
request_count = 0
last_reset = time.time()

print("✅ Hunter Pro CRM AI System - Ready!")

# ==================== النماذج ====================
class LoginRequest(BaseModel):
    email: str
    password: str

class HuntRequest(BaseModel):
    intent_sentence: str
    city: str
    time_filter: str = "qdr:m"
    user_id: str = "admin"
    mode: str = "general"

class WhatsAppRequest(BaseModel):
    phone_number: str
    message: str
    user_id: str

class AIConversationRequest(BaseModel):
    phone_number: str
    user_message: str
    conversation_history: List[Dict] = []
    user_id: str

class AdminAIRequest(BaseModel):
    command: str
    context: Dict = {}

class AddLeadRequest(BaseModel):
    phone_number: str
    full_name: str = ""
    email: str = ""
    source: str = "Manual"
    quality: str = "جيد ⭐"
    notes: str = ""
    user_id: str
    status: str = "NEW"

class ShareRequest(BaseModel):
    phone: str
    shared_with: List[str] = []
    is_public: bool = False
    user_id: str

class CampaignCreate(BaseModel):
    name: str
    message: str
    user_id: str
    target_quality: List[str] = ["ممتاز 🔥", "جيد ⭐"]

class AdminCommand(BaseModel):
    command: str

class AddUserRequest(BaseModel):
    username: str
    password: str
    role: str = "user"
    can_hunt: bool = True
    can_campaign: bool = True
    can_share: bool = False
    can_see_all_data: bool = False
    is_admin: bool = False

class UpdatePermissions(BaseModel):
    username: str
    can_hunt: bool
    can_campaign: bool
    can_share: bool
    can_see_all_data: bool
    is_admin: bool

class ExtractPhonesRequest(BaseModel):
    text: str

# ==================== المحاور الذكي AI Conversational Agent ====================
class AIConversationAgent:
    def __init__(self):
        self.client = anthropic_client
        self.system_prompt = """أنت محاور ذكي ومحترف في مجال العقارات. مهمتك هي:
1. بناء علاقة ثقة مع العميل
2. فهم احتياجاته بدقة (نوع العقار، الميزانية، الموقع، التوقيت)
3. إقناعه بالعرض بطريقة ذكية وغير مباشرة
4. التعامل مع الاعتراضات بمهارة
5. دفعه نحو اتخاذ قرار (حجز معاينة، دفع عربون، إتمام صفقة)

القواعد:
- كن ودوداً ومحترماً
- استخدم اللغة العربية الفصحى المبسطة أو العامية حسب سياق المحادثة
- اطرح أسئلة ذكية لفهم الاحتياج
- قدم حلول مخصصة
- اخلق إحساس بالاستعجال دون ضغط
- استخدم الأدلة الاجتماعية (عملاء سابقين، نجاحات)
"""

    async def chat_with_customer(self, user_message: str, history: List[Dict], lead_data: Dict = None) -> str:
        """محادثة ذكية مع العميل"""
        if not self.client:
            return "عذراً، خدمة المحادثة الذكية غير متاحة حالياً"

        # بناء السياق
        context = f"\n\nمعلومات العميل:\n"
        if lead_data:
            context += f"- الجودة: {lead_data.get('quality', 'غير محدد')}\n"
            context += f"- المصدر: {lead_data.get('source', 'غير محدد')}\n"
            context += f"- الملاحظات: {lead_data.get('notes', 'لا توجد')}\n"

        messages = []
        for msg in history[-10:]:  # آخر 10 رسائل
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        messages.append({
            "role": "user",
            "content": user_message
        })

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                system=self.system_prompt + context,
                messages=messages
            )
            
            return response.content[0].text
        except Exception as e:
            print(f"AI Error: {e}")
            return "عذراً، حدث خطأ في النظام. سنتواصل معك قريباً"

    async def analyze_intent(self, message: str) -> Dict:
        """تحليل نية العميل"""
        if not self.client:
            return {"intent": "UNKNOWN", "urgency": "LOW", "sentiment": "NEUTRAL"}

        analysis_prompt = f"""حلل الرسالة التالية وأعطني:
1. النية (INTERESTED/NOT_INTERESTED/NEGOTIATING/READY_TO_BUY/NEED_INFO)
2. مستوى الاستعجال (HIGH/MEDIUM/LOW)
3. المشاعر (POSITIVE/NEUTRAL/NEGATIVE)

الرسالة: {message}

أجب بـ JSON فقط بدون نص إضافي:
{{"intent": "...", "urgency": "...", "sentiment": "..."}}"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=200,
                messages=[{"role": "user", "content": analysis_prompt}]
            )
            
            result = json.loads(response.content[0].text)
            return result
        except:
            return {"intent": "UNKNOWN", "urgency": "MEDIUM", "sentiment": "NEUTRAL"}

ai_agent = AIConversationAgent()

# ==================== شات الأدمن الذكي ====================
class AdminAIAssistant:
    def __init__(self):
        self.client = anthropic_client
        self.system_prompt = """أنت مساعد إداري ذكي لنظام Hunter Pro CRM. يمكنك:

1. إدارة النظام:
   - إضافة/حذف/تعديل المستخدمين
   - تغيير الصلاحيات
   - عرض الإحصائيات
   
2. إدارة البيانات:
   - البحث عن عملاء
   - تصدير بيانات
   - تحليل الأداء
   
3. الحملات التسويقية:
   - إنشاء حملات
   - إرسال رسائل
   - متابعة النتائج

4. التحليلات:
   - تقارير مفصلة
   - توصيات ذكية
   - رؤى تحسين الأداء

عند تنفيذ أمر، أجب بـ JSON:
{
  "action": "ACTION_NAME",
  "params": {},
  "message": "رسالة للمستخدم"
}

الأوامر المتاحة:
- ADD_USER, DELETE_USER, UPDATE_PERMISSIONS
- GET_STATS, EXPORT_DATA, SEARCH_LEADS
- CREATE_CAMPAIGN, SEND_MESSAGE
- ANALYZE_PERFORMANCE, GENERATE_REPORT
"""

    async def process_admin_command(self, command: str, context: Dict) -> Dict:
        """معالجة أوامر الأدمن"""
        if not self.client:
            return {"action": "ERROR", "message": "خدمة AI غير متاحة"}

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1500,
                system=self.system_prompt,
                messages=[{
                    "role": "user",
                    "content": f"الأمر: {command}\nالسياق: {json.dumps(context, ensure_ascii=False)}"
                }]
            )
            
            result = json.loads(response.content[0].text)
            return result
        except Exception as e:
            print(f"Admin AI Error: {e}")
            return {"action": "ERROR", "message": f"خطأ: {str(e)}"}

admin_ai = AdminAIAssistant()

# ==================== وظائف مساعدة ====================
def get_active_key():
    global key_index
    if not SERPER_KEYS: return None
    key = SERPER_KEYS[key_index]
    key_index = (key_index + 1) % len(SERPER_KEYS)
    return key

def safe_request_delay():
    global request_count, last_reset
    if time.time() - last_reset > 60:
        request_count = 0
        last_reset = time.time()
    request_count += 1
    if request_count > 30: time.sleep(3.0)
    elif request_count > 20: time.sleep(2.0)
    elif request_count > 10: time.sleep(1.5)
    else: time.sleep(1.0)

def get_sub_locations(city):
    # قائمة شاملة لجميع المحافظات والمناطق في مصر
    locations = {
        # محافظات القاهرة الكبرى
        "القاهرة": ["التجمع الخامس", "المعادي", "مدينة نصر", "مصر الجديدة", "الزمالك", "الرحاب", "مدينتي", "القاهرة الجديدة", "الشروق", "حلوان", "المقطم", "عين شمس", "مصر القديمة", "الساحل", "العبور"],
        "الجيزة": ["6 أكتوبر", "الشيخ زايد", "الهرم", "المهندسين", "الدقي", "حدائق الأهرام", "فيصل", "الحوامدية", "العمرانية", "البدرشين"],
        "القليوبية": ["شبرا الخيمة", "القناطر الخيرية", "الخانكة", "قليوب", "بنها", "شبين القناطر"],
        
        # محافظات الدلتا
        "الإسكندرية": ["سموحة", "سيدي جابر", "العجمي", "المنتزه", "ميامي", "محرم بك", "الإبراهيمية", "الرمل", "سان ستيفانو", "العصافرة"],
        "البحيرة": ["دمنهور", "كفر الدوار", "رشيد", "إيتاي البارود", "حوش عيسى", "شبراخيت"],
        "الدقهلية": ["المنصورة", "ميت غمر", "طلخا", "المنزلة", "دكرنس", "أجا"],
        "الغربية": ["طنطا", "المحلة الكبرى", "كفر الزيات", "زفتى", "السنطة", "قطور"],
        "كفر الشيخ": ["كفر الشيخ", "دسوق", "فوة", "مطوبس", "بيلا", "الرياض"],
        "المنوفية": ["شبين الكوم", "منوف", "أشمون", "الباجور", "قويسنا", "تلا"],
        "الشرقية": ["الزقازيق", "العاشر من رمضان", "بلبيس", "فاقوس", "ههيا", "منيا القمح"],
        "دمياط": ["دمياط", "رأس البر", "فارسكور", "الزرقا", "كفر سعد"],
        
        # محافظات القناة
        "بورسعيد": ["بورسعيد", "بورفؤاد", "الضواحي"],
        "السويس": ["السويس", "الأربعين", "عتاقة"],
        "الإسماعيلية": ["الإسماعيلية", "فايد", "القنطرة شرق", "القنطرة غرب", "أبو صوير"],
        "شمال سيناء": ["العريش", "رفح", "الشيخ زويد", "بئر العبد"],
        "جنوب سيناء": ["الطور", "شرم الشيخ", "دهب", "نويبع", "رأس سدر", "سانت كاترين"],
        
        # محافظات الصعيد
        "الفيوم": ["الفيوم", "طامية", "سنورس", "إطسا", "إبشواي", "يوسف الصديق"],
        "بني سويف": ["بني سويف", "الفشن", "ناصر", "ببا", "سمسطا"],
        "المنيا": ["المنيا", "ملوي", "مغاغة", "بني مزار", "سمالوط", "أبو قرقاص"],
        "أسيوط": ["أسيوط", "أبنوب", "منفلوط", "ديروط", "القوصية", "أبو تيج"],
        "سوهاج": ["سوهاج", "أخميم", "جرجا", "البلينا", "المراغة", "طما"],
        "قنا": ["قنا", "قوص", "نجع حمادي", "الوقف", "قفط", "دشنا"],
        "الأقصر": ["الأقصر", "الكرنك", "الأقصر الجديدة", "البياضية", "الطود"],
        "أسوان": ["أسوان", "كوم امبو", "إدفو", "دراو", "نصر النوبة", "أبو سمبل"],
        
        # محافظات الحدود
        "البحر الأحمر": ["الغردقة", "سفاجا", "القصير", "مرسى علم", "الشلاتين", "رأس غارب"],
        "الوادي الجديد": ["الخارجة", "الداخلة", "الفرافرة", "باريس", "بلاط"],
        "مطروح": ["مرسى مطروح", "السلوم", "سيوة", "الحمام", "النجيلة", "الضبعة"],
        
        # دول عربية (للتوسع المستقبلي)
        "السعودية": ["الرياض", "جدة", "مكة", "المدينة", "الدمام", "الخبر", "تبوك", "أبها", "الطائف"],
        "الإمارات": ["دبي", "أبوظبي", "الشارقة", "عجمان", "رأس الخيمة", "الفجيرة", "أم القيوين"],
        "الكويت": ["الكويت", "حولي", "الفروانية", "الجهراء", "الأحمدي", "مبارك الكبير"],
        "قطر": ["الدوحة", "الوكرة", "الخور", "الريان", "أم صلال"],
        "البحرين": ["المنامة", "المحرق", "الرفاع", "المحرق", "سترة"],
        "عمان": ["مسقط", "صلالة", "صحار", "نزوى", "البريمي"],
        "الأردن": ["عمان", "إربد", "الزرقاء", "العقبة", "السلط", "الكرك"],
        "لبنان": ["بيروت", "طرابلس", "صيدا", "صور", "جبيل", "زحلة"],
        "سوريا": ["دمشق", "حلب", "حمص", "حماة", "اللاذقية", "طرطوس"],
        "العراق": ["بغداد", "البصرة", "الموصل", "أربيل", "السليمانية", "كربلاء"],
        "ليبيا": ["طرابلس", "بنغازي", "مصراتة", "الزاوية", "طبرق"],
        "تونس": ["تونس", "صفاقس", "سوسة", "القيروان", "بنزرت"],
        "الجزائر": ["الجزائر", "وهران", "قسنطينة", "عنابة", "بليدة"],
        "المغرب": ["الرباط", "الدار البيضاء", "مراكش", "فاس", "طنجة", "أغادير"],
        "السودان": ["الخرطوم", "أم درمان", "بورتسودان", "كسلا", "القضارف"],
        "اليمن": ["صنعاء", "عدن", "تعز", "الحديدة", "إب", "ذمار"],
        "فلسطين": ["القدس", "رام الله", "غزة", "نابلس", "الخليل", "بيت لحم"]
    }
    
    # إذا لم تجد المدينة، أرجع المدينة نفسها كقائمة
    return locations.get(city, [city])

def analyze_quality(text):
    text = text.lower()
    blacklist = ["للبيع", "for sale", "متاح الان", "احجز الان", "تواصل معنا", "امتلك", "فرصة", "offer", "discount", "سمسار", "broker", "وكيل"]
    for word in blacklist:
        if word in text: return "TRASH"
    
    excellent = ["مطلوب", "محتاج", "عايز", "أبحث", "شراء", "كاش", "wanted", "buying", "looking for", "need", "أريد"]
    for word in excellent:
        if word in text: return "ممتاز 🔥"
    
    good = ["سعر", "تفاصيل", "price", "details", "بكام", "معلومات"]
    for word in good:
        if word in text: return "جيد ⭐"
    
    return "TRASH"

def extract_phones_from_text(text):
    phones = re.findall(r'(01[0125][0-9 \-]{8,15})', text)
    clean_phones = []
    for raw in phones:
        clean = raw.replace(" ", "").replace("-", "")
        if len(clean) == 11 and clean not in clean_phones:
            clean_phones.append(clean)
    return clean_phones

def save_lead(phone, email, keyword, link, quality, user_id):
    if quality == "TRASH":
        print(f"   🗑️ Trash Skipped: {phone}")
        return False
    if not phone or len(phone) != 11: return False
    
    try:
        data = {
            "phone_number": phone,
            "source": f"SmartHunt: {keyword}",
            "quality": quality,
            "status": "NEW",
            "notes": f"Link: {link}",
            "user_id": user_id
        }
        if email: data["email"] = email
        
        supabase.table("leads").upsert(data, on_conflict="phone_number").execute()
        print(f"   💎 SAVED: {phone} ({quality})")
        
        supabase.table("events").insert({
            "event": "new_lead",
            "details": f"New lead added: {phone}",
            "user_id": user_id
        }).execute()
        
        return True
    except Exception as e:
        print(f"   ❌ Save Error: {e}")
        return False

def create_jwt_token(email: str):
    payload = {"sub": email, "exp": datetime.utcnow() + timedelta(days=7)}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
    except:
        return None

def run_hydra_hunt(intent: str, main_city: str, time_filter: str, user_id: str, mode: str):
    if not SERPER_KEYS:
        print("❌ No Serper API keys configured")
        return
    
    search_intent = intent
    if "شقة" in intent or "فيلا" in intent or "محل" in intent:
        if "مطلوب" not in intent:
            search_intent = f'مطلوب {intent}'
    
    sub_cities = get_sub_locations(main_city)
    print(f"🌍 Quality Hunt Started: {search_intent} in {sub_cities}")
    
    total_found = 0
    domains_checked = 0
    start_time = datetime.now()
    
    for area in sub_cities:
        queries = [
            f'site:facebook.com "{search_intent}" "{area}" "010"',
            f'site:facebook.com "{search_intent}" "{area}" "011"',
            f'site:olx.com.eg "{search_intent}" "{area}" "010"',
            f'"{search_intent}" "{area}" "مطلوب" "01"'
        ]
        
        for query in queries:
            api_key = get_active_key()
            if not api_key: break
            
            safe_request_delay()
            
            payload = json.dumps({
                "q": query,
                "num": 100,
                "tbs": time_filter,
                "gl": "eg",
                "hl": "ar"
            })
            
            headers = {
                'X-API-KEY': api_key,
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            try:
                print(f"🚀 Scanning: {query[:60]}...")
                response = requests.post("https://google.serper.dev/search", headers=headers, data=payload, timeout=30)
                
                if response.status_code == 429:
                    print("⚠️ Rate limit hit - waiting 10 seconds...")
                    time.sleep(10)
                    continue
                elif response.status_code != 200:
                    print(f"❌ API Error: {response.status_code}")
                    continue
                
                results = response.json().get("organic", [])
                domains_checked += len(results)
                
                for res in results:
                    snippet = f"{res.get('title', '')} {res.get('snippet', '')}"
                    quality = analyze_quality(snippet)
                    
                    if quality != "TRASH":
                        phones = extract_phones_from_text(snippet)
                        for phone in phones:
                            if save_lead(phone, None, intent, res.get('link'), quality, user_id):
                                total_found += 1
                                
            except requests.exceptions.Timeout:
                print("⏰ Request timeout - continuing...")
                continue
            except Exception as e:
                print(f"   ⚠️ Error: {e}")
    
    duration = (datetime.now() - start_time).seconds
    
    try:
        supabase.table("hunt_logs").insert({
            "user_id": user_id,
            "intent": intent,
            "city": main_city,
            "results_count": total_found,
            "domains_checked": domains_checked,
            "duration_seconds": duration,
            "mode": mode
        }).execute()
    except:
        pass
    
    print(f"🏁 Hunt Finished! Found: {total_found} diamonds | Checked: {domains_checked} domains | Time: {duration}s")

# ==================== المسارات ====================
@app.get("/", response_class=HTMLResponse)
async def home():
    try:
        with open("dashboard.html", "r", encoding="utf-8") as f:
            return f.read()
    except:
        return "<h1>Hunter Pro CRM AI System</h1><p>Dashboard file not found</p>"

@app.get("/health")
def health_check():
    return {
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "serper_keys": len(SERPER_KEYS),
        "twilio_configured": bool(TWILIO_SID and TWILIO_TOKEN),
        "ai_enabled": bool(ANTHROPIC_API_KEY)
    }

@app.post("/api/login")
async def login(req: LoginRequest):
    try:
        if req.password == "google":
            token = create_jwt_token(req.email)
            return {"access_token": token, "token_type": "bearer"}
        
        if req.email == "admin@example.com" and req.password == "admin123":
            token = create_jwt_token(req.email)
            return {"access_token": token, "token_type": "bearer"}
        
        raise HTTPException(status_code=401, detail="Invalid credentials")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/start_hunt")
@app.post("/hunt")
async def start_hunt(req: HuntRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_hydra_hunt, req.intent_sentence, req.city, req.time_filter, req.user_id, req.mode)
    return {"status": "started", "search": req.intent_sentence, "city": req.city, "message": "بدأ البحث بنجاح"}

# ==================== AI Endpoints ====================
@app.post("/api/ai/chat")
async def ai_chat(req: AIConversationRequest):
    """محادثة ذكية مع العميل"""
    try:
        # جلب بيانات العميل
        lead_data = None
        try:
            lead_result = supabase.table("leads").select("*").eq("phone_number", req.phone_number).execute()
            if lead_result.data:
                lead_data = lead_result.data[0]
        except:
            pass
        
        # المحادثة
        response = await ai_agent.chat_with_customer(req.user_message, req.conversation_history, lead_data)
        
        # تحليل النية
        intent_analysis = await ai_agent.analyze_intent(req.user_message)
        
        # حفظ المحادثة
        try:
            supabase.table("ai_conversations").insert({
                "phone_number": req.phone_number,
                "user_message": req.user_message,
                "ai_response": response,
                "intent": intent_analysis.get("intent"),
                "urgency": intent_analysis.get("urgency"),
                "sentiment": intent_analysis.get("sentiment"),
                "user_id": req.user_id
            }).execute()
        except:
            pass
        
        return {
            "success": True,
            "response": response,
            "analysis": intent_analysis
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/admin/ai")
async def admin_ai_command(req: AdminAIRequest):
    """أوامر الأدمن الذكية"""
    try:
        result = await admin_ai.process_admin_command(req.command, req.context)
        
        # تنفيذ الأمر
        if result.get("action") == "GET_STATS":
            stats = supabase.table("leads").select("id", count="exact").execute()
            result["data"] = {"total_leads": stats.count or 0}
        
        elif result.get("action") == "ADD_USER":
            params = result.get("params", {})
            # تنفيذ إضافة مستخدم...
            
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==================== باقي المسارات ====================
@app.get("/leads")
@app.get("/api/leads")
def get_leads(user_id: str = "admin"):
    try:
        user = supabase.table("users").select("can_see_all_data, is_admin").eq("username", user_id).execute()
        if user.data and (user.data[0].get("can_see_all_data") or user.data[0].get("is_admin")):
            rows = supabase.table("leads").select("*").order("created_at", desc=True).limit(500).execute()
        else:
            rows = supabase.table("leads").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(500).execute()
        return {"success": True, "leads": rows.data}
    except Exception as e:
        return {"success": False, "error": str(e), "leads": []}

@app.post("/add-lead")
@app.post("/api/add-lead")
def add_lead(req: AddLeadRequest):
    try:
        supabase.table("leads").insert(req.dict()).execute()
        supabase.table("events").insert({
            "event": "manual_lead_added",
            "details": f"Manual lead: {req.phone_number}",
            "user_id": req.user_id
        }).execute()
        return {"success": True, "message": "تم إضافة العميل بنجاح"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/send-whatsapp")
@app.post("/api/send-whatsapp")
async def send_whatsapp(req: WhatsAppRequest):
    if not all([TWILIO_SID, TWILIO_TOKEN, TWILIO_WHATSAPP_NUMBER]):
        return {"success": False, "error": "Twilio not configured"}
    
    try:
        client = TwilioClient(TWILIO_SID, TWILIO_TOKEN)
        message = client.messages.create(
            from_=f"whatsapp:{TWILIO_WHATSAPP_NUMBER}",
            body=req.message,
            to=f"whatsapp:{req.phone_number}"
        )
        
        supabase.table("campaign_logs").insert({
            "lead_phone": req.phone_number,
            "message_sent": req.message,
            "status": "sent",
            "user_id": req.user_id
        }).execute()
        
        return {"success": True, "message": "تم إرسال الرسالة", "sid": message.sid}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/extract-phones")
def extract_phones(req: ExtractPhonesRequest):
    phones = extract_phones_from_text(req.text)
    return {"success": True, "phones": phones}

@app.get("/admin-stats")
@app.get("/api/admin-stats")
def admin_stats(user_id: str = "admin"):
    try:
        total_users = supabase.table("users").select("id", count="exact").execute().count or 0
        total_leads = supabase.table("leads").select("id", count="exact").execute().count or 0
        total_messages = supabase.table("campaign_logs").select("id", count="exact").execute().count or 0
        return {"total_users": total_users, "total_leads": total_leads, "total_messages": total_messages}
    except:
        return {"total_users": 0, "total_leads": 0, "total_messages": 0}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
