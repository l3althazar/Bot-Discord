import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import datetime
import json
import os
import random
import google.generativeai as genai # เรียกใช้สมอง AI
from keep_alive import keep_alive

# --- ตั้งค่า Permission ---
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
ALLOWED_CHANNEL_FORTUNE = "ห้องเช็คดวง-‼️🆕"

# --- 🧠 ตั้งค่า AI (Gemini) ---
try:
    # ดึง Key ที่เราฝากไว้ใน Koyeb มาใช้
    GENAI_KEY = os.environ['GEMINI_API_KEY']
    genai.configure(api_key=GENAI_KEY)
    
    # เลือกโมเดลสมอง
    model = genai.GenerativeModel('gemini-pro')
    
    # กำหนดนิสัยบอท
    BOT_PERSONA = """
    คุณคือ "Devils DenBot" บอทประจำกิลด์เกม "Where Winds Meet" 
    นิสัยของคุณคือ: เป็นจอมยุทธ์ผู้เก่งกาจ, กวนประสาทนิดๆ, เฮฮา, รักพวกพ้อง
    คำพูดติดปาก: "ข้าคือจอมยุทธ์เด๊ะ", "ประเสริฐ", "นับถือๆ"
    เวลาตอบคำถาม: ให้ตอบสั้นๆ กระชับ ได้ใจความ และลงท้ายด้วยคำพูดสไตล์หนังจีนกำลังภายใน
    """
    print("✅ AI System: Ready")
except Exception as e:
    print(f"⚠️ Warning: AI Error ({e}) - บอทจะทำงานได้ แต่ตอบคำถามไม่ได้")

# ==========================================
# ส่วนอื่นๆ ของบอท (รับน้อง/ดูดวง/หน้าเว็บ)
# ==========================================

def load_history():
    if not os.path.exists(HISTORY_FILE): return {}
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}

def save_history(data):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f: json.dump(data, f, indent=4)

user_history = load_history()

def log(message):
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {message}")

async def refresh_setup_msg(channel):
    try:
        async for message in channel.history(limit=30):
            if message.author == bot.user and message.embeds and message.embeds[0].title == "📢 ยืนยันตัวตน / แนะนำตัว":
                await message.delete()
    except: pass
    embed = discord.Embed(title="📢 ยืนยันตัวตน / แนะนำตัว", description="กดปุ่มด้านล่างเพื่อเปิดห้องส่วนตัวสำหรับแนะนำตัวครับ 👇", color=0x00ff00)
    await channel.send(embed=embed, view=TicketButton())

# --- ปุ่มและเมนู ---
class GameSelect(discord.ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label="Where Winds Meet", emoji="⚔️"), discord.SelectOption(label="อื่นๆ", emoji="🎮")]
        super().__init__(placeholder="เลือกเกมที่คุณเล่น...", min_values=1, max_values=1, options=options)
    async def callback(self, interaction):
        self.view.selected_value = self.values[0]
        await interaction.response.defer()
        self.view.stop()

class GameView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.selected_value = None
        self.add_item(GameSelect())

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
            await interaction.edit_original_response(content=f"✅ สร้างห้องแล้ว! {user.mention}", view=view)
            await self.start_interview(ch, user, guild)
        except Exception as e: log(f"Error creating ticket: {e}")

    async def start_interview(self, channel, user, guild):
        data = {"name": "", "age": "", "game": "", "char_name": "-"}
        def check(m): return m.author == user and m.channel == channel
        try:
            await channel.send(f"{user.mention} **ยินดีต้อนรับครับ!**")
            await channel.send(embed=discord.Embed(title="1. ชื่อเล่นของคุณคือ?", color=0x3498db))
            data["name"] = (await bot.wait_for("message", check=check, timeout=300)).content
            
            await channel.send(embed=discord.Embed(title="2. อายุเท่าไหร่?", color=0x3498db))
            data["age"] = (await bot.wait_for("message", check=check, timeout=300)).content
            
            view = GameView()
            await channel.send(embed=discord.Embed(title="3. เลือกเกมที่คุณเล่น", color=0x3498db), view=view)
            await view.wait()
            data["game"] = view.selected_value if view.selected_value else "Unknown"

            if data["game"] == "Where Winds Meet":
                await channel.send(embed=discord.Embed(title="⚔️ ชื่อตัวละครของคุณคือ?", color=0xe74c3c))
                data["char_name"] = (await bot.wait_for("message", check=check, timeout=300)).content
                role = discord.utils.get(guild.roles, name=ROLE_WWM)
                if role: await user.add_roles(role)

            embed = discord.Embed(title="✅ สมาชิกใหม่รายงานตัว!", description=f"**ชื่อ:** {data['name']}\n**อายุ:** {data['age']}\n**เกม:** {data['game']}", color=0xffd700)
            if data["char_name"] != "-": embed.description += f"\n**ชื่อในเกม:** {data['char_name']}"
            if user.avatar: embed.set_thumbnail(url=user.avatar.url)
            
            pub_ch = discord.utils.get(guild.text_channels, name=PUBLIC_CHANNEL)
            if pub_ch:
                if str(user.id) in user_history:
                    try: (await pub_ch.fetch_message(user_history[str(user.id)])).delete()
                    except: pass
                msg = await pub_ch.send(embed=embed)
                user_history[str(user.id)] = msg.id
                save_history(user_history)
                await refresh_setup_msg(pub_ch)

            role_ver = discord.utils.get(guild.roles, name=ROLE_VERIFIED)
            if role_ver: await user.add_roles(role_ver)
            try: await user.edit(nick=f"{user.display_name} ({data['name']})")
            except: pass
            
            await channel.send("✅ เรียบร้อย! ห้องจะลบใน 10 วินาที")
            await asyncio.sleep(10)
            await channel.delete()
        except: await channel.delete()

# --- Slash Commands ---
@bot.command()
async def sync(ctx):
    synced = await bot.tree.sync()
    await ctx.send(f"✅ Synced {len(synced)} commands.")

# 🔥 คำสั่งถาม AI (สำคัญ!) 🔥
@bot.tree.command(name="ถาม", description="🤖 คุยกับท่านจอมยุทธ์ (AI)")
@app_commands.describe(question="อยากถามอะไร")
async def ask_ai(interaction: discord.Interaction, question: str):
    await interaction.response.defer()
    try:
        full_prompt = f"{BOT_PERSONA}\n\nคำถาม: {question}\nคำตอบ:"
        response = model.generate_content(full_prompt)
        text = response.text[:1900] + "..." if len(response.text) > 1900 else response.text
        embed = discord.Embed(title="🗣️ ท่านจอมยุทธ์กล่าว...", description=text, color=0x00ffcc)
        embed.set_footer(text=f"Q: {question} | โดย {interaction.user.name}")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"😵 ลมปราณแตกซ่าน (Error): {e}", ephemeral=True)

@bot.tree.command(name="ดูดวง", description="🔮 เช็คดวง")
async def fortune(interaction: discord.Interaction):
    if interaction.channel.name != ALLOWED_CHANNEL_FORTUNE:
        return await interaction.response.send_message(f"❌ ไปเล่นห้อง {ALLOWED_CHANNEL_FORTUNE} นะ!", ephemeral=True)
    res = random.choice(["🌟 รวยเละ!", "💀 เกลือ!", "🔥 ตีบวกติด!", "💎 กลางๆ", "🧘 ไปทำบุญนะ"])
    await interaction.response.send_message(embed=discord.Embed(title="🎲 ผลดวง", description=res, color=0xffd700))

@bot.tree.command(name="ล้าง", description="🧹 ลบข้อความ")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    if amount > 100: return await interaction.response.send_message("❌ เยอะไป", ephemeral=True)
    await interaction.channel.purge(limit=amount)
    await interaction.response.send_message("🧹 เรียบร้อย", ephemeral=True)

@bot.event
async def on_ready():
    log(f"✅ Logged in as {bot.user}")
    bot.add_view(TicketButton())

@bot.command()
async def setup(ctx):
    await ctx.message.delete()
    await refresh_setup_msg(ctx.channel)

keep_alive()
try: bot.run(os.environ['TOKEN'])
except: print("Error: Token not found")
