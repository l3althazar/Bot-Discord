from flask import Flask, render_template
from threading import Thread

app = Flask(__name__)

@app.route('/')
def home():
    # โหลดหน้าแรก
    return render_template('index.html')

@app.route('/draw')
def draw():
    # โหลดหน้าสุ่ม
    return render_template('draw.html')

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
