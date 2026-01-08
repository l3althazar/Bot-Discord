from flask import Flask, render_template_string
from threading import Thread

app = Flask('')

# 🎨 หน้าเว็บ HTML สวยๆ
html_code = """
<!DOCTYPE html>
<html>
<head>
    <title>Devils DenBot - Official</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta property="og:title" content="Devils DenBot">
    <meta property="og:description" content="บอทจอมยุทธ์สุดเกรียน ระบบรับน้อง/ดูดวง/จัดการห้อง ครบวงจร">
    <style>
        body {
            background-color: #2c2f33;
            color: white;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            text-align: center;
            padding-top: 50px;
            margin: 0;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 { font-size: 2.5em; color: #ff4757; text-shadow: 2px 2px #000; margin-bottom: 10px; }
        p { font-size: 1.1em; color: #b9bbbe; line-height: 1.6; }
        
        /* รูปโปรไฟล์บอท (ดึงมาจาก Discord โดยตรง) */
        .bot-img {
            width: 150px;
            height: 150px;
            border-radius: 50%;
            border: 5px solid #ff4757;
            margin-bottom: 20px;
            animation: float 3s ease-in-out infinite;
            box-shadow: 0 0 20px rgba(255, 71, 87, 0.5);
        }
        
        /* ปุ่มกด Invite */
        .btn {
            background-color: #5865F2;
            color: white;
            padding: 15px 32px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 18px;
            margin: 20px 0;
            cursor: pointer;
            border-radius: 5px;
            transition: 0.3s;
            border: none;
            font-weight: bold;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        .btn:hover { 
            background-color: #4752c4; 
            transform: translateY(-2px);
            box-shadow: 0 6px 8px rgba(0,0,0,0.4);
        }
        
        .footer {
            margin-top: 50px;
            font-size: 0.8em;
            color: #72767d;
        }

        /* อนิเมชั่นรูปลอย */
        @keyframes float {
            0% { transform: translatey(0px); }
            50% { transform: translatey(-15px); }
            100% { transform: translatey(0px); }
        }
    </style>
</head>
<body>
    <div class="container">
        <img src="https://cdn.discordapp.com/avatars/1457301588937801739/a334b0c7937402868297495034875321.png?size=256" onerror="this.src='https://cdn.discordapp.com/embed/avatars/0.png'" class="bot-img">

        <h1>Devils DenBot 😈</h1>
        
        <p>
            <b>"ข้าคือจอมยุทธ์เด๊ะ"</b><br>
            บอทดูแลประจำกิลด์ Where Winds Meet<br>
            ระบบยืนยันตัวตน | เสี่ยงดวงกาชา | จัดการห้อง
        </p>

        <a href="https://discord.com/oauth2/authorize?client_id=1457301588937801739&permissions=8&integration_type=0&scope=bot" class="btn" target="_blank">
            ➕ เชิญบอทเข้าเซิร์ฟเวอร์
        </a>
        
        <div class="footer">
            Status: <span style="color: #43b581;">● Online</span><br>
            Developed by ท่านจอมยุทธ์
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(html_code)

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
