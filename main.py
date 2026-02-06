import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import datetime
import json
import os
import random
import logging
import google.generativeai as genai
from flask import Flask
from threading import Thread

# ==========================================
# 🌐 1. KEEP ALIVE (Web Server สำหรับ Railway)
# ==========================================
app = Flask('')
@app.route('/')
def home(): return "Devils DenBot is Online!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# ==========================================
# 📝 2. LOGGING & CONFIG
# ==========================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("DevilsBot")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='-', intents=intents)

# Config - ห้องและยศ (ตามที่คุณตั้งไว้)
PUBLIC_CHANNEL = "ห้องแนะนำตัว"
CHANNEL_LEAVE = "ห้องแจ้งลา"        
ALLOWED_CHANNEL_FORTUNE = "ห้องเช็คดวง"
ROLE_ADMIN_CHECK = "‹ 𝑆𝑦𝑠𝑡𝑒𝑚 𝐴𝑑𝑚𝑖𝑛 ⚖️ ›" 
ROLE_VERIFIED = "‹ แนะนำตัวแล้ว ›"
ROLE_WWM = "ข้าคือจอมยุทธ์เด๊ะ"
ROLE_DPS = "DPS ⚔️"
ROLE_HEALER = "หมอ💉🩺"
ROLE_TANK = "แทงค์ 🛡️"
ROLE_HYBRID = "ไฮบริด 🧬"
LEAVE_FILE = "leaves.json"

# ==========================================
# 🧠 3. AI SETUP (แก้ไขรุ่นให้ถูกต้อง)
# ==========================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
model = None
AI_STATUS = "❌ ไม่พร้อมใช้งาน"

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # แก้ไขจาก 2.5 เป็น 1.5-flash เพื่อความเสถียร
        model = genai.GenerativeModel('gemini-2.5-flash')
        AI_STATUS = "✅ พร้อมใช้งาน (1.5-Flash)"
    except Exception as e:
        AI_STATUS = f"💥 Error: {e}"

# ==========================================
# 📂 4. JSON MANAGER
# ==========================================
def load_leaves():
    if os.path.exists(LEAVE_FILE):
        with open(LEAVE_FILE, "r", encoding="utf-8") as f: return json.load(f)
    return []

def save_leaves(data):
    with open(LEAVE_FILE, "w", encoding="utf-8") as f: json.dump(data, f, indent=4, ensure_ascii=False)

# ==========================================
# 📜 5. ระบบใบลา (แก้ไข Logic การลบข้อความ)
# ==========================================
class LeaveApprovalView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    
    async def interaction_check(self, interaction):
        if any(role.name == ROLE_ADMIN_CHECK for role in interaction.user.roles): return True
        await interaction.response.send_message("⛔ เจ้าไม่มีสิทธิ์สั่งการ!", ephemeral=True)
        return False

    @discord.ui.button(label="อนุมัติ", style=discord.ButtonStyle.success, custom_id="l_app", emoji="✅")
    async def app(self, interaction, button):
        emb = interaction.message.embeds[0].copy()
        emb.color = 0x2ecc71
        emb.set_field_at(3, name="📋 สถานะ", value=f"✅ อนุมัติโดย {interaction.user.mention}", inline=False)
        await interaction.response.edit_message(embed=emb, view=None)

    @discord.ui.button(label="ไม่อนุมัติ", style=discord.ButtonStyle.danger, custom_id="l_den", emoji="❌")
    async def den(self, interaction, button):
        emb = interaction.message.embeds[0].copy()
        emb.color = 0xe74c3c
        emb.set_field_at(3, name="📋 สถานะ", value=f"❌ ไม่อนุมัติโดย {interaction.user.mention}", inline=False)
        await interaction.response.edit_message(embed=emb, view=None)

class LeaveModal(discord.ui.Modal, title="📜 แบบฟอร์มขอลา"):
    char = discord.ui.TextInput(label="ชื่อตัวละคร", required=True)
    l_type = discord.ui.TextInput(label="หัวข้อการลา", required=True)
    l_date = discord.ui.TextInput(label="วันที่/เวลา", required=True)
    reason = discord.ui.TextInput(label="เหตุผล", style=discord.TextStyle.paragraph, required=False)

    async def on_submit(self, interaction):
        tz = datetime.timezone(datetime.timedelta(hours=7))
        now = datetime.datetime.now(tz).strftime("%d/%m/%Y %H:%M")
        
        # บันทึกข้อมูล
        data = load_leaves()
        data.append({"user": interaction.user.name, "char": self.char.value, "date": self.l_date.value})
        save_leaves(data)

        embed = discord.Embed(title="📩 มีสาส์นขอลาหยุด!", color=0xf1c40f)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.add_field(name="👤 จอมยุทธ์", value=self.char.value, inline=False)
        embed.add_field(name="📌 ประเภท", value=self.l_type.value, inline=False)
        embed.add_field(name="📅 วันที่/เวลา", value=self.l_date.value, inline=False)
        embed.add_field(name="📋 สถานะ", value="⏳ **รอการตรวจสอบ**", inline=False)
        embed.set_footer(text=f"ยื่นเมื่อ: {now}")

        await interaction.channel.send(content=f"**ผู้ยื่นเรื่อง:** {interaction.user.mention}", embed=embed, view=LeaveApprovalView())
        # แจ้งเตือนแล้วลบออกเอง
        resp = await interaction.response.send_message("✅ ส่งใบลาแล้ว (ข้อความนี้จะถูกลบใน 5 วิ)", ephemeral=False)
        await asyncio.sleep(5)
        await interaction.delete_original_response()

class LeaveButtonView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="📝 เขียนใบลา", style=discord.ButtonStyle.danger, custom_id="btn_l", emoji="📜")
    async def open_l(self, interaction, button): await interaction.response.send_modal(LeaveModal())

# ==========================================
# 🆕 6. ระบบแนะนำตัว (พร้อม Logic ยศและรูปภาพ)
# ==========================================
class IntroModal(discord.ui.Modal, title="📝 ข้อมูลแนะนำตัว"):
    name = discord.ui.TextInput(label="ชื่อเล่น", required=True)
    age = discord.ui.TextInput(label="อายุ", required=True)
    async def on_submit(self, interaction):
        await interaction.response.send_message("🎮 **โปรดเลือกเกมที่คุณเล่น:**", view=GameSelectView({"n": self.name.value, "a": self.age.value}), ephemeral=True)

class GameSelectView(discord.ui.View):
    def __init__(self, data):
        super().__init__()
        self.data = data
    @discord.ui.select(placeholder="เลือกเกม...", options=[discord.SelectOption(label="Where Winds Meet", emoji="⚔️"), discord.SelectOption(label="อื่นๆ", emoji="🎮")])
    async def select_game(self, interaction, select):
        self.data["g"] = select.values[0]
        if self.data["g"] == "Where Winds Meet":
            modal = discord.ui.Modal(title="⚔️ ข้อมูล WWM")
            ign = discord.ui.TextInput(label="ชื่อในเกม (IGN)")
            modal.add_item(ign)
            async def wwm_sub(it):
                self.data["ign"] = ign.value
                await it.response.edit_message(content="🛡️ **เลือกสายอาชีพ:**", view=ClassSelectView(self.data))
            modal.on_submit = wwm_sub
            await interaction.response.send_modal(modal)
        else: await finalize_intro(interaction, self.data)

class ClassSelectView(discord.ui.View):
    def __init__(self, data):
        super().__init__()
        self.data = data
    @discord.ui.select(placeholder="อาชีพหลัก...", options=[discord.SelectOption(label="ดาเมจ", emoji="⚔️"), discord.SelectOption(label="หมอ", emoji="🩺"), discord.SelectOption(label="แทงค์", emoji="🛡️"), discord.SelectOption(label="ไฮบริด", emoji="🧬")])
    async def select_cls(self, interaction, select):
        self.data["c"] = select.values[0]
        await finalize_intro(interaction, self.data)

async def finalize_intro(interaction, data):
    guild = interaction.guild
    user = interaction.user
    pub_ch = discord.utils.get(guild.text_channels, name=PUBLIC_CHANNEL)
    
    # ลบข้อความเก่า
    if pub_ch:
        async for m in pub_ch.history(limit=50):
            if m.author == bot.user and m.embeds and user.name in str(m.embeds[0].footer.text):
                await m.delete()

    # ยศและชื่อ
    roles = [discord.utils.get(guild.roles, name=ROLE_VERIFIED)]
    icon = ""
    if data.get("g") == "Where Winds Meet":
        roles.append(discord.utils.get(guild.roles, name=ROLE_WWM))
        cls_map = {"ดาเมจ": (ROLE_DPS, "⚔️"), "หมอ": (ROLE_HEALER, "💉"), "แทงค์": (ROLE_TANK, "🛡️"), "ไฮบริด": (ROLE_HYBRID, "🧬")}
        rn, icon = cls_map.get(data["c"], (None, ""))
        roles.append(discord.utils.get(guild.roles, name=rn))

    await user.add_roles(*[r for r in roles if r])
    try: await user.edit(nick=f"{icon} {user.name} ({data['n']})")
    except: pass

    embed = discord.Embed(title="✅ สมาชิกใหม่รายงานตัว!", color=0xffd700)
    embed.set_thumbnail(url=user.display_avatar.url)
    embed.description = f"**ชื่อเล่น :** {data['n']}\n**อายุ :** {data['a']}\n**เกม :** {data['g']}"
    if "ign" in data: embed.description += f"\n**IGN :** {data['ign']}\n**สายอาชีพ :** {data['c']}"
    embed.set_footer(text=f"แนะนำตัวโดย {user.name}")

    await pub_ch.send(embed=embed)
    await interaction.response.edit_message(content="✅ สำเร็จ!", view=None, embed=None)

class IntroButtonView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="📝 กดเพื่อแนะนำตัว", style=discord.ButtonStyle.green, custom_id="btn_i", emoji="👋")
    async def start_i(self, interaction, button): await interaction.response.send_modal(IntroModal())

# ==========================================
# 🛠️ 7. COMMANDS & EVENTS
# ==========================================
@bot.tree.command(name="ดูดวง", description="🔮 ดูดวงประจำวัน 10 แบบ")
async def fortune(interaction):
    if interaction.channel.name != ALLOWED_CHANNEL_FORTUNE:
        return await interaction.response.send_message("❌ ผิดห้อง!", ephemeral=True)
    
    data = [
        {"t": "🌟 RNG ประทับร่าง! ออฟทองมาแน่!", "c": 0xffd700, "g": "https://media.giphy.com/media/l0Ex6kAKAoFRsFh6M/giphy.gif"},
        {"t": "🔥 มือร้อน(เงิน)! ระวังหมดตัว!", "c": 0xff4500, "g": "https://media.giphy.com/media/Lopx9eUi34rbq/giphy.gif"},
        {"t": "✨ แสงสีทองรออยู่! การันตีของแรร์!", "c": 0xffff00, "g": "https://media.giphy.com/media/3o7TKSjRrfIPjeiVyM/giphy.gif"},
        {"t": "🟢 สีเขียวเหนี่ยวทรัพย์ ได้ของถูไถ", "c": 0x2ecc71, "g": "https://media.giphy.com/media/13HgwGsXF0aiGY/giphy.gif"},
        {"t": "📈 ดวงกลางๆ พอไหว", "c": 0x3498db, "g": "https://media.giphy.com/media/l2Je66zG6mAAZxgqI/giphy.gif"},
        {"t": "🧘 ไปทำบุญก่อนนะ ดวงยังนิ่ง", "c": 0x9b59b6, "g": "https://media.giphy.com/media/xT5LMHxhOfscxPfIfm/giphy.gif"},
        {"text": "💀 ดวงเกลือ All Bamboocut", "color": 0x000000, "img": "https://media.giphy.com/media/26tP3M3iA3EBIfXy0/giphy.gif"},
        {"t": "💎 เกลือล้วนๆ 99.99%", "c": 0x95a5a6, "g": "https://media.giphy.com/media/3o6UB5RrlQuMfZp82Y/giphy.gif"},
        {"t": "⚔️ จอมยุทธ์ถังแตก พักก่อน", "c": 0x7f8c8d, "g": "https://media.giphy.com/media/l2JdZOv5901Q6Q7Ek/giphy.gif"},
        {"t": "🧧 GM รักคุณ (เตรียมเติมตังค์)", "c": 0xe74c3c, "g": "https://media.giphy.com/media/3o7TKRBB3E7IdVNLm8/giphy.gif"}
    ]
    res = random.choice(data)
    emb = discord.Embed(title="🔮 ผลทำนาย", description=f"# {res.get('t', res.get('text'))}", color=res.get('c', res.get('color')))
    emb.set_image(url=res.get('g', res.get('img')))
    await interaction.response.send_message(embed=emb)

@bot.command()
async def sync(ctx):
    synced = await bot.tree.sync()
    await ctx.send(f"✅ Sync สำเร็จ! ทั้งหมด {len(synced)} คำสั่ง")

@bot.command()
async def setup(ctx):
    pub = discord.utils.get(ctx.guild.channels, name=PUBLIC_CHANNEL)
    if pub: await pub.send(embed=discord.Embed(title="📢 ลงทะเบียน", description="กดปุ่มเพื่อเริ่มแนะนำตัว", color=0x00ff00), view=IntroButtonView())
    
    leave = discord.utils.get(ctx.guild.channels, name=CHANNEL_LEAVE)
    if leave: await leave.send(embed=discord.Embed(title="📢 แจ้งลา", description="กดปุ่มเพื่อเขียนใบลา", color=0xe74c3c), view=LeaveButtonView())
    await ctx.send("✅ ตั้งค่าปุ่มเรียบร้อย!")

@bot.tree.command(name="ถาม", description="🤖 คุยกับ AI")
async def ask(interaction, คำถาม: str):
    await interaction.response.defer()
    if not model: return await interaction.followup.send("❌ AI ไม่พร้อม")
    try:
        resp = model.generate_content(คำถาม)
        await interaction.followup.send(embed=discord.Embed(title="🗣️ AI ตอบว่า:", description=resp.text[:1900], color=0x00ffcc))
    except Exception as e: await interaction.followup.send(f"❌ Error: {e}")

@bot.event
async def on_ready():
    bot.add_view(IntroButtonView())
    bot.add_view(LeaveButtonView())
    bot.add_view(LeaveApprovalView())
    await bot.tree.sync()
    keep_alive()
    print(f"🚀 {bot.user} พร้อมใช้งาน!")

bot.run(os.getenv("DISCORD_TOKEN"))
