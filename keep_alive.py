from flask import Flask, render_template_string

# สร้างแอป Flask (Gunicorn จะมองหาตัวแปรชื่อ 'app' นี้)
app = Flask('')

# --- ส่วน HTML ดีไซน์ปราสาททมิฬ (ของท่าน) ---
html_code = """
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Devils DenBot | Official Site</title>
    <link rel="icon" href="https://cdn.discordapp.com/attachments/1458426304633241656/1458850160066166808/24a9109c-758b-4252-a908-a1517a93f76a.png?ex=69612396&is=695fd216&hm=a6d4db9f32110dddcd05ebffe8f7a20c607ccf183740763e922f1cdf2dcc39f1&">
    
    <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@900&family=Kanit:wght@300;400;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <style>
        :root {
            --primary: #ff0000;
            --dark-red: #8a0000;
            --bg: #050505;
            --text: #e0e0e0;
        }

        * { box-sizing: border-box; }

        body {
            background-color: var(--bg);
            color: var(--text);
            font-family: 'Kanit', sans-serif;
            margin: 0;
            padding: 0;
            overflow-x: hidden;
            
            /* พื้นหลังรูปปราสาทใหม่ */
            background: linear-gradient(rgba(0, 0, 0, 0.5), rgba(30, 0, 0, 0.9)),
                        url('https://cdn.discordapp.com/attachments/1458426304633241656/1458869203925733528/ChatGPT_Image_9_.._2569_00_05_07.png?ex=69613552&is=695fe3d2&hm=1a78d6f57b6844485fbdf163d924f056a5bbd2521828898edb7804dff48e61a0&');
            background-repeat: no-repeat;
            background-position: center center;
            background-attachment: fixed;
            background-size: cover;
        }

        .fog-container {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            overflow: hidden; z-index: -1; pointer-events: none;
        }
        .fog-img {
            position: absolute; height: 100vh; width: 300vw;
            background: url('https://raw.githubusercontent.com/danielstuart14/CSS_FOG_ANIMATION/master/fog1.png') repeat-x;
            background-size: contain; animation: fog 60s linear infinite; opacity: 0.3;
        }
        .fog-img-2 {
            background: url('https://raw.githubusercontent.com/danielstuart14/CSS_FOG_ANIMATION/master/fog2.png') repeat-x;
            background-size: contain; animation: fog 40s linear infinite;
            z-index: -1; top: 30%; opacity: 0.2;
        }
        @keyframes fog { 0% { transform: translate3d(0, 0, 0); } 100% { transform: translate3d(-200vw, 0, 0); } }

        .navbar {
            background: rgba(10, 0, 0, 0.95); padding: 15px 40px;
            display: flex; justify-content: space-between; align-items: center;
            position: fixed; top: 0; left: 0; width: 100%; z-index: 1000;
            border-bottom: 2px solid var(--primary);
            box-shadow: 0 0 20px rgba(255, 0, 0, 0.3); backdrop-filter: blur(10px);
        }

        .brand-container { display: flex; align-items: center; gap: 15px; }
        .logo-text { font-family: 'Cinzel', serif; font-size: 1.5em; color: var(--primary); font-weight: bold; letter-spacing: 2px; }

        .status-badge-nav {
            font-family: 'Kanit', sans-serif; font-size: 0.8em;
            background: rgba(0, 255, 0, 0.1); border: 1px solid #00ff00; color: #00ff00;
            padding: 2px 10px; border-radius: 10px; display: flex; align-items: center; gap: 5px;
            text-transform: uppercase; font-weight: bold;
        }
        .status-dot-nav {
            width: 8px; height: 8px; background: #00ff00; border-radius: 50%;
            box-shadow: 0 0 5px #00ff00; animation: pulse 2s infinite;
        }

        .nav-links a { color: #aaa; text-decoration: none; margin-left: 25px; font-weight: 500; transition: 0.3s; }
        .nav-links a:hover { color: white; text-shadow: 0 0 5px white; }

        .btn-invite {
            background: var(--primary); color: white !important;
            padding: 8px 20px; border-radius: 5px; font-weight: bold; border: 1px solid var(--primary);
        }
        .btn-invite:hover { background: black; color: var(--primary) !important; box-shadow: 0 0 15px var(--primary); }

        .hero {
            min-height: 90vh; display: flex; flex-direction: column;
            justify-content: center; align-items: center; text-align: center; padding-top: 100px;
        }

        .bot-img-main {
            width: 220px; height: 220px; border-radius: 50%;
            border: 4px solid #000; outline: 4px solid var(--primary);
            box-shadow: 0 0 50px rgba(255, 0, 0, 0.4); object-fit: cover;
            animation: float 4s ease-in-out infinite; margin-bottom: 20px; background-color: #000;
        }

        h1.roman-title {
            font-family: 'Cinzel', serif; font-size: 5em; margin: 0; color: #000000;
            -webkit-text-stroke: 2px var(--primary); text-shadow: 0 0 30px rgba(255, 0, 0, 0.6);
            text-transform: uppercase; letter-spacing: 5px; line-height: 1.1;
        }

        p.subtitle {
            font-size: 1.2em; color: #ccc; max-width: 700px; margin-top: 15px;
            border-left: 3px solid var(--primary); padding-left: 15px;
            background: linear-gradient(90deg, rgba(255,0,0,0.1), transparent);
            background-color: rgba(0, 0, 0, 0.5); padding: 10px 15px;
            border-radius: 0 10px 10px 0; backdrop-filter: blur(3px);
        }

        .stats-row { display: flex; gap: 40px; margin-top: 40px; }
        .stat-item { text-align: center; }
        .stat-num { font-size: 2.5em; font-weight: bold; color: white; text-shadow: 0 0 10px var(--primary); }
        .stat-label { color: #888; font-size: 0.9em; text-transform: uppercase; letter-spacing: 2px; }

        .services-section {
            padding: 210px 20px; background: rgba(5, 0, 0, 0.9);
            text-align: center; backdrop-filter: blur(5px);
        }
        .section-header {
            font-family: 'Cinzel', serif; font-size: 2.5em; color: var(--primary);
            margin-bottom: 50px; text-transform: uppercase; text-shadow: 0 0 10px var(--primary);
        }

        .services-grid {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 30px; max-width: 1100px; margin: 0 auto;
        }

        .service-card {
            background: rgba(20, 0, 0, 0.8); padding: 30px;
            border: 1px solid #333; border-radius: 10px; transition: 0.3s;
            position: relative; overflow: hidden;
        }
        .service-card::before {
            content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 3px;
            background: var(--primary); transform: scaleX(0); transition: 0.3s;
        }
        .service-card:hover { transform: translateY(-10px); box-shadow: 0 10px 30px rgba(255, 0, 0, 0.2); border-color: var(--primary); }
        .service-card:hover::before { transform: scaleX(1); }
        
        .service-icon { font-size: 2.5em; color: var(--primary); margin-bottom: 15px; }
        .service-card h3 { color: white; margin-bottom: 10px; font-family: 'Cinzel', serif; }
        .service-card p { color: #bbb; font-size: 0.95em; line-height: 1.6; }

        footer {
            padding: 30px; text-align: center; border-top: 1px solid #333; font-size: 0.9em; color: #777;
            background: #000;
        }

        @keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-15px); } }
        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }

        @media (max-width: 768px) {
            h1.roman-title { font-size: 3em; -webkit-text-stroke: 1px var(--primary); }
            .navbar { padding: 15px; } .nav-links { display: none; }
            .stats-row { flex-direction: column; gap: 20px; }
        }
    </style>
</head>
<body>

    <div class="fog-container">
        <div class="fog-img"></div>
        <div class="fog-img-2"></div>
    </div>

    <nav class="navbar">
        <div class="brand-container">
            <div class="logo-text">DEVILS DEN</div>
            <div class="status-badge-nav"><div class="status-dot-nav"></div> Online</div>
        </div>
        <div class="nav-links">
            <a href="#">Home</a>
            <a href="#services">Services</a>
            <a href="https://www.facebook.com/l3althazar.bas" target="_blank">Contact</a>
            <a href="https://discord.com/oauth2/authorize?client_id=1457301588937801739&permissions=8&integration_type=0&scope=bot" class="btn-invite" target="_blank">INVITE BOT</a>
        </div>
    </nav>

    <section class="hero">
        <img src="https://cdn.discordapp.com/attachments/1458426304633241656/1458850160066166808/24a9109c-758b-4252-a908-a1517a93f76a.png?ex=69612396&is=695fd216&hm=a6d4db9f32110dddcd05ebffe8f7a20c607ccf183740763e922f1cdf2dcc39f1&" class="bot-img-main" alt="Devils Den Bot">
        <h1 class="roman-title">DEVILS DENBOT</h1>
        <p class="subtitle">
            "ข้าคือจอมยุทธ์เด๊ะ" — ผู้พิทักษ์แห่ง Where Winds Meet<br>
            ระบบรับน้อง • เสี่ยงดวงกาชา • มินิเกม RPG
        </p>

        <div class="stats-row">
            <div class="stat-item"><div class="stat-num">1+</div><div class="stat-label">SERVERS</div></div>
            <div class="stat-item"><div class="stat-num">24/7</div><div class="stat-label">UPTIME</div></div>
            <div class="stat-item"><div class="stat-num">100%</div><div class="stat-label">FUN</div></div>
        </div>
    </section>

    <section id="services" class="services-section">
        <div class="section-header">Services</div>
        <div class="services-grid">
            <div class="service-card">
                <div class="service-icon"><i class="fas fa-dice-d20"></i></div>
                <h3>SYSTEM RPG</h3>
                <p>ระบบสุ่มดวง กาชา ตีบวก และมินิเกมต่อสู้ (Duel) เพื่อความบันเทิงในกิลด์</p>
            </div>
            <div class="service-card">
                <div class="service-icon"><i class="fas fa-user-shield"></i></div>
                <h3>VERIFY & ROLES</h3>
                <p>ระบบรับน้อง ยืนยันตัวตนอัตโนมัติ เปลี่ยนชื่อ และแจกยศสมาชิกใหม่อย่างรวดเร็ว</p>
            </div>
            <div class="service-card">
                <div class="service-icon"><i class="fas fa-music"></i></div>
                <h3>MUSIC & CHILL</h3>
                <p>หน้าเว็บมาพร้อมเพลง Gothic Theme สร้างบรรยากาศเข้มขลังให้กับการใช้งาน</p>
            </div>
        </div>
    </section>

    <footer>
        <p>© 2026 Devils DenBot. All rights reserved.</p>
        <p style="font-size: 0.8em; color: #555;">Design by ท่านจอมยุทธ์</p>
    </footer>

    <div style="position: fixed; bottom: 20px; right: 20px; z-index: 2000;">
        <button onclick="document.getElementById('bgMusic').play()" style="background:var(--primary); border:none; color:white; padding:10px 15px; border-radius:50px; cursor:pointer; box-shadow: 0 0 10px red;">
            <i class="fas fa-play"></i> MUSIC
        </button>
    </div>
    <audio id="bgMusic" loop>
        <source src="https://pixabay.com/music/download/story-epic-cinematic-trailer-115966.mp3" type="audio/mpeg">
    </audio>

</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(html_code)

# ⚠️ หมายเหตุ: เราไม่ต้องมีฟังก์ชัน run() หรือ keep_alive() แล้ว
# เพราะคำสั่ง Start Command: "gunicorn keep_alive:app ..." จะจัดการเรื่อง Port และการรัน Server ให้เองครับ
# การใส่ run() ซ้อนเข้าไปอาจทำให้ Port ตีกันและ Error ได้
