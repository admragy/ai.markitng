# ⚡ دليل البدء السريع - Brilliox CRM

## 🎯 خطوات التشغيل (3 دقائق)

### 1️⃣ التثبيت
```bash
git clone https://github.com/admragy/brilliox.git
cd brilliox
pip install -r requirements.txt
```

### 2️⃣ الإعداد
```bash
cp .env.example .env
# أضف مفتاح AI واحد على الأقل في .env:
# OPENAI_API_KEY=sk-xxx  أو  GOOGLE_API_KEY=xxx
```

### 3️⃣ التشغيل
```bash
python main_crm.py
```

### 4️⃣ الوصول
- 🌐 التطبيق: http://localhost:5000
- 💼 CRM: http://localhost:5000/crm
- 📚 API: http://localhost:5000/docs

## 🧪 اختبار سريع

### إنشاء عميل:
```bash
curl -X POST http://localhost:5000/api/crm/leads \
  -H "Content-Type: application/json" \
  -d '{
    "name": "أحمد محمد",
    "phone": "+201234567890",
    "email": "ahmed@test.com",
    "source": "facebook_ad"
  }'
```

### معالجة رسالة (المحاور الذكي):
```bash
curl -X POST http://localhost:5000/api/crm/leads/1/message \
  -H "Content-Type: application/json" \
  -d '{"message": "مرحباً، عايز أعرف أسعاركم"}'
```

## 📱 WhatsApp (اختياري)

أضف في `.env`:
```
WHATSAPP_API_KEY=your-key
WHATSAPP_PHONE_NUMBER_ID=your-id
```

## ✅ تم!
الآن لديك CRM كامل + المحاور الذكي + WhatsApp Integration! 🎉

للمزيد: اقرأ `README_CRM.md`
