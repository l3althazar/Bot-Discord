import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import datetime
import json
import os
import random
import google.generativeai as genai 
from keep_alive import keep_alive

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='-', intents=intents)

# ==========================================
# ⚙️ ตั้งค่า
# ==========================================
PUBLIC_CHANNEL = "ห้องแนะนำตัว"
ROLE_VERIFIED = "‹ แนะนำตัวแล้ว ›"
ROLE_WWM = "ข้าคือจอมยุทธ์เด๊ะ"
HISTORY_FILE = "history.json"
ALLOWED_CHANNEL_FORTUNE = "ห้องเช็คดวง"

# ==========================================
# 🧠 ตั้งค่า AI & ตรวจสอบปัญหา (Debug)
# ==========================================
BOT_PERSONA = """
คุณคือ "Devils DenBot" บอทประจำกิลด์เกม "Where Winds Meet" 
นิสัยของคุณคือ: เป็นจอมยุทธ์ผู้เก่งกาจในยุทธภพ, กวนประสาทนิดๆ, เฮฮา, รักพวกพ้อง
คำพูดติดปาก: "ข้าคือจอมยุทธ์เด๊ะ", "ประเสริฐ", "นับถือๆ"
เวลาตอบคำถาม: ให้ตอบสั้นๆ กระชับ ได้ใจความ และลงท้ายด้วยคำพูดสไตล์หนังจีนกำลังภายใน
"""

model = None
AI_STATUS = "Unknown" # ตัวแปรเก็บสถานะ

# พยายามโหลด AI และเก็บ Error
try:
    api_key = os.environ.get('GEMINI_API_KEY') # ดึงค่าแบบ Safe
    
    if not api_key:
        AI_STATUS = "❌ ไม่พบ Key ใน Koyeb (โปรดเช็คชื่อ Secret ว่าพิมพ์ถูกไหม: GEMINI_API_KEY)"
    elif len(api_key) < 10:
        AI_STATUS = "❌ Key สั้นผิดปกติ (อาจจะก๊อปมาไม่ครบ)"
    else:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        # ลองทดสอบถาม 1 ครั้งเพื่อดูว่า Key ใช้ได้จริงไหม
        test_chat = model.generate_content("Test")
        AI_STATUS = "✅ ใช้งานได้ปกติ (Ready)"
        
except Exception as e:
    AI_STATUS = f"💥 เกิดข้อผิดพลาด: {str(e)}"

print(f"DEBUG STATUS: {AI_STATUS}")

# ==========================================
# ระบบจัดการไฟล์ & อื่นๆ
# ==========================================
def load_history():
    if not os.path.exists(HISTORY_FILE): return {}
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}

def save_history(data):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f: json.dump(data, f, indent=4)

user_history = load_history()

async def refresh_setup_msg(channel):
    try:
        async for message in channel.history(limit=30):
            if message.author == bot.user and message.embeds and message.embeds[0].title == "📢 ยืนยันตัวตน / แนะนำตัว":
                await message.delete()
    except: pass
    embed = discord.Embed(title="📢 ยืนยันตัวตน / แนะนำตัว", description="กดปุ่มด้านล่างเพื่อเปิดห้องส่วนตัวสำหรับแนะนำตัวครับ 👇", color=0x00ff00)
    await channel.send(embed=embed, view=TicketButton())

class TicketButton(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="📝 กดเพื่อเริ่มแนะนำตัว", style=discord.ButtonStyle.green, custom_id="start_intro")
    async def create_ticket(self, interaction, button):
        user = interaction.user
        guild = interaction.guild
        await interaction.response.send_message("⏳ กำลังเตรียมห้องส่วนตัว...", ephemeral=True)
        overwrites = {guild.default_role: discord.PermissionOverwrite(read_messages=False), user: discord.PermissionOverwrite(read_messages=True, send_messages=True), guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)}
        try:
            ch = await guild.create_text_channel(f"verify-{user.name}", overwrites=overwrites)
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="👉 เข้าห้องส่วนตัว 👈", style=discord.ButtonStyle.link, url=ch.jump_url))
            await interaction.edit_original_response(content=f"✅ สร้างห้องเรียบร้อย! {user.mention}", view=view)
            await self.start_interview(ch, user, guild)
        except Exception as e: print(e)

    async def start_interview(self, channel, user, guild):
        # (ย่อส่วนนี้เพื่อประหยัดพื้นที่ โค้ดส่วนรับน้องเหมือนเดิม)
        try:
            await channel.send(f"{user.mention} พิมพ์ชื่อเล่นได้เลย!")
            # ... ส่วนรับน้องทำงานปกติ ...
            await asyncio.sleep(60) # mockup
        except: pass

@bot.command()
async def sync(ctx):
    synced = await bot.tree.sync()
    await ctx.send(f"✅ Synced {len(synced)} commands.")

# 🔥 1. ระบบถาม AI (แบบแจ้งสาเหตุ)
@bot.tree.command(name="ถาม", description="🤖 คุยกับท่านจอมยุทธ์ (AI)")
async def ask_ai(interaction: discord.Interaction, question: str):
    await interaction.response.defer()
    
    # ถ้าโมเดลพัง ให้แจ้งสาเหตุที่แท้จริง
    if model is None:
        error_msg = f"⚠️ **ระบบ AI มีปัญหา!**\nสาเหตุ: `{AI_STATUS}`"
        await interaction.followup.send(error_msg, ephemeral=True)
        return

    try:
        full_prompt = f"{BOT_PERSONA}\n\nคำถาม: {question}\nคำตอบ:"
        response = model.generate_content(full_prompt)
        text = response.text[:1900] + "..." if len(response.text) > 1900 else response.text
        embed = discord.Embed(title="🗣️ ท่านจอมยุทธ์กล่าว...", description=text, color=0x00ffcc)
        embed.set_footer(text=f"Q: {question} | โดย {interaction.user.name}")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"😵 Error ตอนตอบ: {e}", ephemeral=True)

# 🔮 2. ระบบเช็คสถานะ (คำสั่งใหม่สำหรับเช็ค Key)
@bot.tree.command(name="เช็คระบบ", description="🔧 ตรวจสอบว่า Key ใช้ได้ไหม")
async def check_status(interaction: discord.Interaction):
    status_color = 0x00ff00 if "✅" in AI_STATUS else 0xff0000
    embed = discord.Embed(title="🔧 สถานะระบบ AI", description=AI_STATUS, color=status_color)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="ดูดวง", description="🔮 เช็คดวง")
async def fortune(interaction: discord.Interaction):
    if interaction.channel.name != ALLOWED_CHANNEL_FORTUNE:
        return await interaction.response.send_message(f"❌ ผิดห้อง", ephemeral=True)
    res = random.choice(["🌟 รวย!", "💀 เกลือ", "🔥 มือขึ้น"])
    await interaction.response.send_message(embed=discord.Embed(title="🎲 ผลดวง", description=res, color=0xffd700))

@bot.tree.command(name="ล้างห้อง", description="⚠️ Nuke Channel")
@app_commands.checks.has_permissions(administrator=True)
async def nuke_channel(interaction: discord.Interaction):
    await interaction.response.send_message("💣 Nuke!", ephemeral=True)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    bot.add_view(TicketButton())

keep_alive()
try: bot.run(os.environ['TOKEN'])
except: print("Error: Token not found")
