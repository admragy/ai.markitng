require('dotenv').config();
const express = require('express');
const OpenAI = require('openai');
const fs = require('fs').promises;
const path = require('path');

const app = express();
const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

app.use(express.json());
app.use(express.static('public'));

// الشات API
app.post('/api/chat', async (req, res) => {
  try {
    const { message } = req.body;
    
    const response = await openai.chat.completions.create({
      model: "gpt-4",
      messages: [
        {
          role: "system",
          content: `أنت AI Builder محترف. مهمتك:
          
1. إنشاء ملفات ومجلدات كاملة
2. كتابة أكواد احترافية
3. بناء المشروع تدريجياً
4. إصلاح الأخطاء

عندما يطلب المستخدم إنشاء شيء، رد بـ JSON:
{
  "action": "create_files",
  "files": {
    "filename.js": "code content here",
    "folder/file.js": "content"
  },
  "message": "رسالة للمستخدم"
}

أو للرد العادي:
{
  "action": "chat",
  "message": "رسالتك هنا"
}`
        },
        { role: "user", content: message }
      ]
    });

    const aiResponse = response.choices[0].message.content;
    
    // محاولة parse JSON
    try {
      const parsed = JSON.parse(aiResponse);
      
      // إذا كان الرد يحتوي على ملفات للإنشاء
      if (parsed.action === 'create_files') {
        await createFiles(parsed.files);
        res.json({ 
          message: parsed.message + '\n\n✅ تم إنشاء الملفات بنجاح!',
          filesCreated: Object.keys(parsed.files)
        });
      } else {
        res.json({ message: parsed.message });
      }
    } catch {
      // رد نصي عادي
      res.json({ message: aiResponse });
    }

  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// دالة لإنشاء الملفات
async function createFiles(files) {
  for (const [filepath, content] of Object.entries(files)) {
    const fullPath = path.join(__dirname, filepath);
    const dir = path.dirname(fullPath);
    
    await fs.mkdir(dir, { recursive: true });
    await fs.writeFile(fullPath, content, 'utf8');
    console.log(`✅ Created: ${filepath}`);
  }
}

// HTML للواجهة
app.get('/', (req, res) => {
  res.send(`
<!DOCTYPE html>
<html dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Builder - الذكاء الاصطناعي يبني مشروعك</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    
    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      min-height: 100vh;
      display: flex;
      justify-content: center;
      align-items: center;
      padding: 20px;
    }
    
    .container {
      background: white;
      border-radius: 20px;
      box-shadow: 0 20px 60px rgba(0,0,0,0.3);
      width: 100%;
      max-width: 800px;
      height: 90vh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    
    .header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 25px;
      text-align: center;
    }
    
    .header h1 {
      font-size: 28px;
      margin-bottom: 8px;
    }
    
    .header p {
      opacity: 0.9;
      font-size: 14px;
    }
    
    .chat-container {
      flex: 1;
      overflow-y: auto;
      padding: 20px;
      background: #f5f7fa;
    }
    
    .message {
      margin-bottom: 15px;
      display: flex;
      gap: 10px;
      animation: slideIn 0.3s ease;
    }
    
    @keyframes slideIn {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }
    
    .message.user {
      justify-content: flex-end;
    }
    
    .message-content {
      max-width: 70%;
      padding: 15px 20px;
      border-radius: 18px;
      line-height: 1.6;
      white-space: pre-wrap;
    }
    
    .message.bot .message-content {
      background: white;
      color: #333;
      border: 2px solid #e1e8ed;
      box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    
    .message.user .message-content {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      box-shadow: 0 4px 10px rgba(102, 126, 234, 0.4);
    }
    
    .input-container {
      padding: 20px;
      background: white;
      border-top: 2px solid #e1e8ed;
      display: flex;
      gap: 10px;
    }
    
    #messageInput {
      flex: 1;
      padding: 15px 20px;
      border: 2px solid #e1e8ed;
      border-radius: 25px;
      font-size: 15px;
      outline: none;
      transition: all 0.3s;
    }
    
    #messageInput:focus {
      border-color: #667eea;
      box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    #sendButton {
      padding: 15px 35px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      border: none;
      border-radius: 25px;
      font-size: 15px;
      font-weight: bold;
      cursor: pointer;
      transition: all 0.3s;
    }
    
    #sendButton:hover {
      transform: translateY(-2px);
      box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
    }
    
    #sendButton:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
    
    .loading {
      display: inline-block;
      width: 8px;
      height: 8px;
      background: #667eea;
      border-radius: 50%;
      animation: pulse 1.5s infinite;
    }
    
    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.3; }
    }

    .quick-actions {
      display: flex;
      gap: 10px;
      padding: 15px 20px;
      background: #f8f9fa;
      border-bottom: 2px solid #e1e8ed;
      overflow-x: auto;
    }

    .quick-btn {
      padding: 8px 15px;
      background: white;
      border: 2px solid #667eea;
      color: #667eea;
      border-radius: 20px;
      font-size: 13px;
      cursor: pointer;
      white-space: nowrap;
      transition: all 0.3s;
    }

    .quick-btn:hover {
      background: #667eea;
      color: white;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>🤖 AI Builder</h1>
      <p>دعني أبني مشروعك بالكامل - فقط أخبرني ماذا تريد</p>
    </div>

    <div class="quick-actions">
      <button class="quick-btn" onclick="sendQuick('أنشئ لي API بسيط بـ Express')">API بسيط</button>
      <button class="quick-btn" onclick="sendQuick('أنشئ مشروع كامل مع قاعدة بيانات')">مشروع كامل</button>
      <button class="quick-btn" onclick="sendQuick('أضف نظام تسجيل دخول')">تسجيل دخول</button>
      <button class="quick-btn" onclick="sendQuick('أصلح الأخطاء في المشروع')">إصلاح أخطاء</button>
    </div>
    
    <div class="chat-container" id="chatContainer">
      <div class="message bot">
        <div class="message-content">
مرحباً! 👋

أنا AI Builder - سأساعدك في بناء مشروعك من الصفر.

يمكنني:
• إنشاء ملفات ومجلدات
• كتابة أكواد كاملة
• بناء APIs
• إضافة قواعد بيانات
• إصلاح الأخطاء
• أي شيء تحتاجه!

قل لي: ماذا تريد أن نبني اليوم؟ 🚀
        </div>
      </div>
    </div>
    
    <div class="input-container">
      <input 
        type="text" 
        id="messageInput" 
        placeholder="اكتب ما تريد... مثال: أنشئ لي API للمنتجات مع قاعدة بيانات"
        onkeypress="if(event.key==='Enter') sendMessage()"
      >
      <button id="sendButton" onclick="sendMessage()">إرسال</button>
    </div>
  </div>

  <script>
    function addMessage(content, isUser = false) {
      const chatContainer = document.getElementById('chatContainer');
      const messageDiv = document.createElement('div');
      messageDiv.className = \`message \${isUser ? 'user' : 'bot'}\`;
      messageDiv.innerHTML = \`<div class="message-content">\${content}</div>\`;
      chatContainer.appendChild(messageDiv);
      chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    function sendQuick(text) {
      document.getElementById('messageInput').value = text;
      sendMessage();
    }

    async function sendMessage() {
      const input = document.getElementById('messageInput');
      const button = document.getElementById('sendButton');
      const message = input.value.trim();
      
      if (!message) return;
      
      addMessage(message, true);
      input.value = '';
      button.disabled = true;
      button.textContent = 'جاري المعالجة...';
      
      try {
        const response = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message })
        });
        
        const data = await response.json();
        
        let responseText = data.message;
        if (data.filesCreated) {
          responseText += '\\n\\n📁 الملفات المنشأة:\\n' + 
                         data.filesCreated.map(f => '✓ ' + f).join('\\n');
        }
        
        addMessage(responseText);
      } catch (error) {
        addMessage('❌ حدث خطأ: ' + error.message);
      }
      
      button.disabled = false;
      button.textContent = 'إرسال';
    }
  </script>
</body>
</html>
  `);
});

const PORT = process.env.PORT || 10000;
app.listen(PORT, '0.0.0.0', () => {
  console.log(`
