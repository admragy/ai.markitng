# 🚀 دليل النشر - Brilliox CRM

## 🌐 نشر على مختلف المنصات

### 1. Railway

```bash
# تثبيت Railway CLI
npm i -g @railway/cli

# تسجيل الدخول والنشر
railway login
railway init
railway up
```

أضف Environment Variables في Railway Dashboard:
- `OPENAI_API_KEY`
- `GOOGLE_API_KEY`
- `WHATSAPP_API_KEY`

### 2. Render

1. أنشئ حساب على [Render.com](https://render.com)
2. اربط GitHub repository
3. اختر "Web Service"
4. أضف Environment Variables
5. Deploy!

### 3. Fly.io

```bash
# تثبيت Fly CLI
curl -L https://fly.io/install.sh | sh

# تسجيل الدخول والنشر
fly auth login
fly launch
fly deploy
```

### 4. VPS (Ubuntu/Debian)

```bash
# تثبيت Python والمكتبات
sudo apt update
sudo apt install python3 python3-pip nginx
pip3 install -r requirements.txt

# تشغيل كخدمة
sudo nano /etc/systemd/system/brilliox.service
```

محتوى `brilliox.service`:
```ini
[Unit]
Description=Brilliox CRM
After=network.target

[Service]
User=your-user
WorkingDirectory=/path/to/brilliox
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/python3 main_crm.py

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable brilliox
sudo systemctl start brilliox
```

### 5. Docker

```bash
# بناء الصورة
docker build -t brilliox-crm .

# تشغيل Container
docker run -d \
  -p 5000:5000 \
  -e OPENAI_API_KEY=your-key \
  --name brilliox \
  brilliox-crm
```

## 📝 ملاحظات مهمة

- ✅ تأكد من إضافة جميع Environment Variables
- ✅ استخدم PostgreSQL للإنتاج بدلاً من SQLite
- ✅ فعّل HTTPS
- ✅ احفظ نسخة احتياطية من قاعدة البيانات

