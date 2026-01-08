from flask import Flask, render_template_string
from threading import Thread
import random

app = Flask('')

# 🎨 HTML/CSS/JS ชุดใหญ่ (ธีมปีศาจแดง-ดำ)
html_code = """
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Devils DenBot | บอทจอมยุทธ์สายเกรียน</title>
    <link rel="icon" href="https://cdn.discordapp.com/avatars/1457301588937801739/a334b0c7937402868297495034875321.png">
    
    <link href="https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;600&display=swap" rel="stylesheet">
    
    <style>
        :root {
            --primary: #ff0033; /* สีแดงปีศาจ */
            --dark: #0f0f0f;    /* สีดำพื้นหลัง */
            --gray: #1a1a1a;    /* สีดำรอง */
            --text: #ffffff;
        }

        body {
            background-color: var(--dark);
            color: var(--text);
            font-family: 'Kanit', sans-serif;
            margin: 0;
            padding: 0;
            overflow-x: hidden;
        }

        /* --- Menu Bar --- */
        .navbar {
            background-color: rgba(15, 15, 15, 0.95);
            padding: 15px 50px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: fixed;
            top: 0;
            width: 90%;
            z-index: 1000;
            border-bottom: 2px solid var(--primary);
            box-shadow: 0 0 20px rgba(255, 0, 51, 0.2);
            backdrop-filter: blur(10px);
        }

        .logo {
            font-size: 1.5em;
            font-weight: bold;
            color: var(--primary);
            text-transform: uppercase;
            letter-spacing: 2px;
            text-shadow: 0 0 10px var(--primary);
        }

        .nav-links a {
            color: #ccc;
            text-decoration: none;
            margin-left: 30px;
            font-size: 1.1em;
            transition: 0.3s;
        }

        .nav-links a:hover {
            color: var(--primary);
            text-shadow: 0 0 5px var(--primary);
        }

        .btn-invite {
            background-color: var(--primary);
            color: white !important;
            padding: 8px 20px;
            border-radius: 20px;
            font-weight: bold;
            box-shadow: 0 0 10px var(--primary);
        }
        
        .btn-invite:hover {
            background-color: #cc0029;
            transform: scale(1.05);
        }

        /* --- Hero Section (หน้าแรก) --- */
        .hero {
            height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            background: radial-gradient(circle at center, #2a0a0f 0%, #0f0f0f 70%);
            padding-top: 60px;
        }

        .bot-avatar {
            width: 180px;
            height: 180px;
            border-radius: 50%;
            border: 4px solid var(--primary);
            box-shadow: 0 0 30px var(--primary);
            animation: float 3s ease-in-out infinite;
            margin-bottom: 20px;
        }

        .status-badge {
            background-color: rgba(0, 0, 0, 0.6);
            padding: 5px 15px;
            border-radius: 20px;
            border: 1px solid #00ff00;
            color: #00ff00;
            font-size: 0.9em;
            margin-bottom: 20px;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }

        .status-dot {
            width: 10px;
            height: 10px;
            background-color: #00ff00;
            border-radius: 50%;
            box-shadow: 0 0 10px #00ff00;
            animation: pulse 2s infinite;
        }

        h1 { font-size: 3.5em; margin: 10px 0; text-shadow: 2px 2px 0px #550011; }
        p.subtitle { font-size: 1.2em; color: #aaa; max-width: 600px; line-height: 1.6; }

        /* --- Stats Section --- */
        .stats-container {
            display: flex;
            gap: 50px;
            margin-top: 40px;
        }
        .stat-box {
            background: rgba(255, 255, 255, 0.05);
            padding: 20px 40px;
            border-radius: 10px;
            border: 1px solid #333;
            text-align: center;
        }
        .stat-number { font-size: 2.5em; font-weight: bold; color: var(--primary); }
        .stat-label { font-size: 1em; color: #888; }

        /* --- Services Section --- */
        .services {
            padding: 80px 50px;
            background-color: var(--gray);
            text-align: center;
        }
        
        .section-title {
            font-size: 2.5em;
            margin-bottom: 50px;
            color: white;
            position: relative;
            display: inline-block;
        }
        .section-title::after {
            content: '';
            display: block;
            width: 60px;
            height: 4px;
            background: var(--primary);
            margin: 10px auto;
        }

        .cards-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            max-width: 1200px;
            margin: 0 auto;
        }

        .card {
            background: #222;
            padding: 30px;
            border-radius: 15px;
            border: 1px solid #333;
            transition: 0.3s;
            position: relative;
            overflow: hidden;
        }
        .card:hover {
            transform: translateY(-10px);
            border-color: var(--primary);
            box-shadow: 0 10px 30px rgba(255, 0, 51, 0.1);
        }
        .card h3 { font-size: 1.5em; color: var(--primary); margin-bottom: 15px; }
        .card p { color: #bbb; line-height: 1.6; }

        /* --- Footer --- */
        footer {
            padding: 40px;
            text-align: center;
            background-color: #0a0a0a;
            color: #666;
            border-top: 1px solid #333;
        }
        
        /* Animations */
        @keyframes float { 0% { transform: translateY(0px); } 50% { transform: translateY(-15px); } 100% { transform: translateY(0px); } }
        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }

        /* Mobile Responsive */
        @media (max-width: 768px) {
            .navbar { padding: 15px 20px; }
            .nav-links { display: none; } /* ซ่อนเมนูบนมือถือเพื่อความง่าย */
            .stats-container { flex-direction: column; gap: 20px; }
            h1 { font-size: 2.5em; }
        }
    </style>
</head>
<body>

    <nav class="navbar">
        <div class="logo">😈 DEVILS DEN</div>
        <div class="nav-links">
            <a href="#">หน้าหลัก</a>
            <a href="#services">บริการของเรา</a>
            <a href="https://www.facebook.com/l3althazar.bas" target="_blank">ติดต่อเรา</a>
            <a href="https://discord.com/oauth2/authorize?client_id=1457301588937801739&permissions=8&integration_type=0&scope=bot" class="btn-invite" target="_blank">เชิญบอท +</a>
        </div>
    </nav>

    <section class="hero">
        <img src="https://cdn.discordapp.com/avatars/1457301588937801739/a334b0c7937402868297495034875321.png?size=256" class="bot-avatar" onerror="this.src='https://cdn.discordapp.com/embed/avatars/0.png'">
        
        <div class="status-badge">
            <div class="status-dot"></div> ระบบออนไลน์ 24 ชม.
        </div>

        <h1>DEVILS DENBOT</h1>
        <p class="subtitle">
            "ข้าคือจอมยุทธ์เด๊ะ"<br>
            บอทดูแลสารพัดประโยชน์ประจำกิลด์ Where Winds Meet<br>
            ระบบรับน้องสุดเท่ • เสี่ยงดวงกาชา • มินิเกมแก้เบื่อ
        </p>

        <div class="stats-container">
            <div class="stat-box">
                <div class="stat-number">1+</div>
                <div class="stat-label">เซิร์ฟเวอร์</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">24/7</div>
                <div class="stat-label">ออนไลน์</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">10+</div>
                <div class="stat-label">ฟีเจอร์</div>
            </div>
        </div>
    </section>

    <section id="services" class="services">
        <h2 class="section-title">บริการของเรา</h2>
        
        <div class="cards-grid">
            <div class="card">
                <h3>🔮 ระบบมูเตลู</h3>
                <p>เช็คดวงกาชาประจำวัน ทำนายการตีบวก เสี่ยงเซียมซี พร้อมกราฟิกสวยงามและคำทำนายสุดกวน</p>
            </div>

            <div class="card">
                <h3>🛡️ จัดการห้อง & รับน้อง</h3>
                <p>ระบบสัมภาษณ์สมาชิกใหม่ สร้างห้องส่วนตัวอัตโนมัติ เปลี่ยนชื่อเล่นให้อัตโนมัติ พร้อมมอบยศทันที</p>
            </div>

            <div class="card">
                <h3>🎮 มินิเกมแก้เบื่อ</h3>
                <p>เป่ายิ้งฉุบวัดดวง ท้าดวล RPG กับเพื่อน หรือรูเล็ตสุ่มจับรางวัล สร้างสีสันให้คอมมูนิตี้</p>
            </div>
        </div>
    </section>

    <footer>
        <p>© 2024 Devils DenBot. Developed by ท่านจอมยุทธ์</p>
        <p style="font-size: 0.9em; margin-top: 10px;">
            <a href="https://www.facebook.com/l3althazar.bas" style="color: var(--primary); text-decoration: none;">ติดต่อผู้พัฒนา (Facebook)</a>
        </p>
    </footer>

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
