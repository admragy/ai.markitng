require('dotenv').config();
const express = require('express');
const OpenAI = require('openai');
const fs = require('fs').promises;
const path = require('path');

const app = express();
const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

app.use(express.json());
app.use(express.static('public'));

// شات API
app.post('/api/chat', async (req, res) => {
  try {
    const { message } = req.body;

    const response = await openai.chat.completions.create({
      model: "gpt-4",
      messages: [
        {
          role: "system",
          content: `
أنت AI Builder محترف. مهمتك:

1. إنشاء ملفات ومجلدات كاملة
2. كتابة أكواد احترافية
3. بناء المشروع تلقائياً
4. إصلاح الأخطاء

عندما يطلب المستخدم إنشاء شيء، رد باستجابة JSON بهذا الشكل:

{
  "action": "create_files",
  "files": {
    "folder/file.js": "code content here"
  },
  "message": "شرح للمستخدم"
}

أو الرد العادي:
{
  "action": "chat",
  "message": "رسالة للمستخدم"
}
`
        },
        { role: "user", content: message }
      ]
    });

    const aiResponse = response.choices[0].message.content;

    // محاولة قراءة JSON
    try {
      const parsed = JSON.parse(aiResponse);

      if (parsed.action === "create_files") {
        await createFiles(parsed.files);
        return res.json({
          message: parsed.message + "\n\n✓ تم إنشاء الملفات",
          filesCreated: Object.keys(parsed.files)
        });
      }

      return res.json({ message: parsed.message });

    } catch (e) {
      return res.json({ message: aiResponse });
    }

  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// دالة إنشاء الملفات
async function createFiles(files) {
  for (const [filepath, content] of Object.entries(files)) {
    const full = path.join(__dirname, filepath);
    await fs.mkdir(path.dirname(full), { recursive: true });
    await fs.writeFile(full, content, "utf8");
  }
}

// صفحة الواجهة
app.get('/', (req, res) => {
  res.send(`
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Builder</title>

<style>
body {
  font-family: Tahoma, sans-serif;
  margin: 0;
  padding: 0;
  direction: rtl;
  background: var(--bg);
  color: var(--text);
  transition: 0.2s;
}
:root {
  --bg: #f6f7fb;
  --text: #222;
  --chat-bg: #fff;
  --bubble-user: #0078ff;
  --bubble-bot: #e5e7eb;
}
.dark {
  --bg: #0e0e11;
  --text: #e8e8e8;
  --chat-bg: #1a1b1e;
  --bubble-user: #0059c6;
  --bubble-bot: #2a2c31;
}
#topBar {
  padding: 15px;
  font-size: 20px;
  background: var(--chat-bg);
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #4444;
}
#chat {
  height: 78vh;
  overflow-y: auto;
  padding: 20px;
  background: var(--chat-bg);
}
.msg {
  margin: 10px 0;
  padding: 12px 14px;
  border-radius: 12px;
  max-width: 75%;
  white-space: pre-wrap;
  line-height: 1.7;
  font-size: 16px;
}
.user {
  background: var(--bubble-user);
  color: white;
  margin-left: auto;
}
.bot {
  background: var(--bubble-bot);
  margin-right: auto;
}
#inputBar {
  display: flex;
  padding: 10px;
  gap: 10px;
  background: var(--chat-bg);
  border-top: 1px solid #4444;
}
textarea {
  flex: 1;
  height: 60px;
  resize: none;
  padding: 12px;
  border-radius: 10px;
  background: var(--bg);
  color: var(--text);
  border: 1px solid #4444;
}
button {
  padding: 0 22px;
  border: none;
  background: #0078ff;
  color: white;
  border-radius: 10px;
  font-size: 18px;
  cursor: pointer;
}
pre {
  margin: 0;
  white-space: pre-wrap;
}
</style>
</head>

<body>

<div id="topBar">
  <span>🤖 AI Builder</span>
  <button onclick="toggleMode()">🌙</button>
</div>

<div id="chat"></div>

<div id="inputBar">
  <textarea id="msg" placeholder="اكتب أمرك…"></textarea>
  <button onclick="send()">إرسال</button>
</div>

<script>
// markdown
function md(text) {
  return text
    .replace(/\\\`\\\`\\\`(.*?)\\\`\\\`\\\`/gs, "<pre>$1</pre>")
    .replace(/\\*\\*(.*?)\\*\\*/g, "<b>$1</b>")
    .replace(/\\*(.*?)\\*/g, "<i>$1</i>")
    .replace(/\\n/g, "<br>");
}

const chat = document.getElementById("chat");
const input = document.getElementById("msg");

// إضافة رسالة
function add(text, type) {
  const d = document.createElement("div");
  d.className = "msg " + type;
  d.innerHTML = md(text);
  chat.appendChild(d);
  chat.scrollTop = chat.scrollHeight;
}

// إرسال
async function send() {
  const message = input.value.trim();
  if (!message) return;

  add(message, "user");
  input.value = "";
  add("⏳ جاري التفكير…", "bot");

  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message })
  });

  const data = await res.json();
  chat.removeChild(chat.lastChild);

  add(data.message, "bot");
}

// Enter = إرسال
input.onkeydown = e => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    send();
  }
};

// الوضع الليلي
function toggleMode() {
  document.body.classList.toggle("dark");
}
</script>

</body>
</html>
`);
});

const PORT = process.env.PORT || 10000;
app.listen(PORT, '0.0.0.0', () => {
  console.log("AI Builder Running on http://localhost:" + PORT);
});
