import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import datetime
import json
import os
import random
import logging # ✅ เพิ่มไลบรารีสำหรับ Log
import google.generativeai as genai
from keep_alive import keep_alive

# ==========================================
# 📝 ตั้งค่าระบบ Log (บันทึกการทำงาน)
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%d/%m/%Y %H:%M:%S'
)
logger = logging.getLogger("DevilsBot")

# --- ตั้งค่า Permission ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='-', intents=intents)

# ==========================================
# ⚙️ ตั้งค่า (แก้ไขชื่อห้อง/ยศ ตรงนี้)
# ==========================================
PUBLIC_CHANNEL = "ห้องแนะนำตัว"
ROLE_VERIFIED = "‹ แนะนำตัวแล้ว ›"
ROLE_WWM = "ข้าคือจอมยุทธ์เด๊ะ"
HISTORY_FILE = "history.json"
ALLOWED_CHANNEL_FORTUNE = "ห้องเช็คดวง"

# ==========================================
# 🧠 ตั้งค่า AI & ตรวจสอบกุญแจ
# ==========================================
GENAI_VERSION = genai.__version__

BOT_PERSONA = """
คุณคือ "Devils DenBot" AI ผู้ช่วยอัจฉริยะที่มีความรู้กว้างขวาง
ตัวตนของคุณ: เป็นปัญญาประดิษฐ์ที่มีความรอบรู้ระดับสูง (เหมือน Gemini/GPT) แต่มีจิตวิญญาณของจอมยุทธ์แฝงอยู่

สไตล์การตอบ:
1. **เมื่อถูกถามเรื่องความรู้/วิชาการ/โค้ด:** ให้ตอบแบบ "จริงจัง ชัดเจน และถูกต้อง 100%" อธิบายให้ละเอียด เข้าใจง่าย ไม่ต้องติดเล่น
2. **เมื่อคุยเล่นทั่วไป:** ให้มีลูกเล่น กวนนิดๆ หรือใช้คำเรียกผู้ใช้ว่า "ท่านจอมยุทธ์" หรือ "สหาย" ได้ตามความเหมาะสม
3. **สำคัญ:** ความถูกต้องของข้อมูลต้องมาก่อนบทบาทเสมอ ถ้าเรื่องไหนซับซ้อน ให้เน้นอธิบายให้รู้เรื่องที่สุด
สรุปสั้นๆ: "บทเรียนแน่น แม่นยำ ดั่งกระบี่ไร้ใจ แต่คุยสนุกเหมือนเพื่อนร่วมสำนัก"

📢 **ข้อมูลล่าสุดของเกม Where Winds Meet (อัปเดต):**
- **วันเปิดตัว Global (PC & PS5):** 14 พฤศจิกายน 2025
- **วันเปิดตัว Global (Mobile iOS/Android):** 12 ธันวาคม 2025
- **แพลตฟอร์ม:** Steam, Epic Games Store, PlayStation Store
- **แนวเกม:** Action RPG Wuxia (กำลังภายใน) Open World
- **ระบบ:** รองรับ Cross-play ระหว่าง PC และ PS5
"""

model = None
AI_STATUS = "Unknown"
KEY_DEBUG_INFO = "No Key"

try:
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        AI_STATUS = "❌ ไม่พบ Key"
        KEY_DEBUG_INFO = "None"
        logger.error("API Key not found in environment variables!")
    else:
        k_len = len(api_key)
        start_char = api_key[:5]
        end_char = api_key[-4:]
        KEY_DEBUG_INFO = f"{start_char}...{end_char} (ยาว: {k_len})"
        
        genai.configure(api_key=api_key)
        
        # เรียกใช้ผ่าน genai.protos โดยตรง เพื่อความชัวร์ครับ
        model = genai.GenerativeModel(
            'gemini-2.5-flash',
            tools=[genai.protos.Tool(google_search=genai.protos.GoogleSearch())]
        )
        
        AI_STATUS = "✅ พร้อมใช้งาน (Google Search Enabled)"
        logger.info("✅ Gemini Model loaded successfully with Google Search tool.")
except Exception as e:
    AI_STATUS = f"💥 Error: {str(e)}"
    logger.critical(f"🔥 Critical Error loading AI: {e}")

# ==========================================
# ระบบจัดการไฟล์ & Setup
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
    logger.info(f"Refreshed setup message in channel: {channel.name}")

# --- ตัวเลือกเกม (Game Select) ---
class GameSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Where Winds Meet", emoji="⚔️", description="จอมยุทธ์"),
            discord.SelectOption(label="อื่นๆ", emoji="🎮", description="เกมทั่วไป")
        ]
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

# --- ระบบสร้างห้อง & สัมภาษณ์ ---
class TicketButton(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="📝 กดเพื่อเริ่มแนะนำตัว", style=discord.ButtonStyle.green, custom_id="start_intro")
    async def create_ticket(self, interaction, button):
        user = interaction.user
        guild = interaction.guild
        logger.info(f"🎫 User {user.name} requested verification ticket.")
        
        await interaction.response.send_message("⏳ กำลังเตรียมห้องส่วนตัว...", ephemeral=True)
        overwrites = {guild.default_role: discord.PermissionOverwrite(read_messages=False), user: discord.PermissionOverwrite(read_messages=True, send_messages=True), guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)}
        try:
            ch = await guild.create_text_channel(f"verify-{user.name}", overwrites=overwrites)
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="👉 เข้าห้องส่วนตัว 👈", style=discord.ButtonStyle.link, url=ch.jump_url))
            await interaction.edit_original_response(content=f"✅ สร้างห้องเรียบร้อย! {user.mention}", view=view)
            await self.start_interview(ch, user, guild)
        except Exception as e:
            logger.error(f"Failed to create ticket: {e}")
            print(e)

    async def start_interview(self, channel, user, guild):
        logger.info(f"▶️ Starting interview for {user.name} in {channel.name}")
        data = {"name": "", "age": "", "game": "", "char_name": "-"}
        def check(m): return m.author == user and m.channel == channel

        try:
            await channel.send(f"{user.mention} **ยินดีต้อนรับครับ!** (ตอบคำถามในห้องนี้ได้เลย)")

            # 1. ชื่อ
            await channel.send(embed=discord.Embed(title="1. ชื่อเล่นของคุณคือ?", description="ชื่อนี้จะถูกนำไปต่อท้ายชื่อเดิม (เช่น: Ball)", color=0x3498db))
            data["name"] = (await bot.wait_for("message", check=check, timeout=300)).content

            # 2. อายุ
            await channel.send(embed=discord.Embed(title="2. อายุเท่าไหร่?", color=0x3498db))
            data["age"] = (await bot.wait_for("message", check=check, timeout=300)).content

            # 3. เกม
            view = GameView()
            await channel.send(embed=discord.Embed(title="3. เลือกเกมที่คุณเล่น", color=0x3498db), view=view)
            await view.wait()
            if not view.selected_value: return
            data["game"] = view.selected_value

            if data["game"] == "Where Winds Meet":
                await channel.send(embed=discord.Embed(title="⚔️ ชื่อตัวละครของคุณคือ?", color=0xe74c3c))
                data["char_name"] = (await bot.wait_for("message", check=check, timeout=300)).content
                role_wwm = discord.utils.get(guild.roles, name=ROLE_WWM)
                if role_wwm: await user.add_roles(role_wwm)

            # สรุปและส่งข้อมูล
            await channel.send("⏳ **กำลังบันทึกข้อมูล...**")
            embed = discord.Embed(title="✅ สมาชิกใหม่รายงานตัว!", color=0xffd700)
            desc = f"**ชื่อเล่น :** {data['name']}\n**อายุ :** {data['age']}\n**เกมที่เล่น :** {data['game']}"
            if data["char_name"] != "-": desc += f"\n**ชื่อในเกม :** {data['char_name']}"
            embed.description = desc
            if user.avatar: embed.set_thumbnail(url=user.avatar.url)
            embed.set_footer(text=f"แนะนำตัวโดย {user.name}")

            pub_ch = discord.utils.get(guild.text_channels, name=PUBLIC_CHANNEL)
            sent_msg = None
            if pub_ch:
                if str(user.id) in user_history:
                    try: (await pub_ch.fetch_message(user_history[str(user.id)])).delete()
                    except: pass
                sent_msg = await pub_ch.send(embed=embed)
                user_history[str(user.id)] = sent_msg.id
                save_history(user_history)
                await refresh_setup_msg(pub_ch)

            role_ver = discord.utils.get(guild.roles, name=ROLE_VERIFIED)
            if role_ver: await user.add_roles(role_ver)
            try: await user.edit(nick=f"{user.display_name} ({data['name']})")
            except: pass

            logger.info(f"✅ Verified user {user.name} successfully.")

            # ปุ่มย้อนกลับ
            if sent_msg:
                view_back = discord.ui.View()
                btn_back = discord.ui.Button(label="🔙 กดเพื่อไปดูผลลัพธ์", style=discord.ButtonStyle.link, url=sent_msg.jump_url, emoji="✨")
                view_back.add_item(btn_back)
                await channel.send(embed=discord.Embed(title="✅ เรียบร้อย!", description="ห้องจะลบใน 10 วินาที", color=0x00ff00), view=view_back)
            
            await asyncio.sleep(10)
            await channel.delete()
        except Exception as e: 
            logger.error(f"Error during interview with {user.name}: {e}")
            await channel.delete()

@bot.command()
async def sync(ctx):
    synced = await bot.tree.sync()
    logger.info(f"🔄 Commands synced: {len(synced)} commands.")
    await ctx.send(f"✅ Synced {len(synced)} commands.")

# ==========================================
# 🔥 5 Slash Commands
# ==========================================

# 1. เช็คระบบ
@bot.tree.command(name="เช็คระบบ", description="🔧 ดูว่าบอทใช้ Key ตัวไหนอยู่")
async def check_status(interaction: discord.Interaction):
    logger.info(f"🔍 [System Check] requested by {interaction.user.name}")
    color = 0x00ff00 if "✅" in AI_STATUS else 0xff0000
    embed = discord.Embed(title="🔧 ข้อมูลระบบ AI", color=color)
    embed.add_field(name="สถานะ", value=AI_STATUS, inline=False)
    embed.add_field(name="📦 GenAI Version", value=f"`v{GENAI_VERSION}`", inline=True)
    embed.add_field(name="🔑 กุญแจที่บอทเห็น", value=f"`{KEY_DEBUG_INFO}`", inline=False)
    embed.set_footer(text="ถ้ากุญแจยาวเกิน 39 หรือตัวหน้า/หลังไม่ตรงกับ Google แปลว่าผิด!")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# 2. ถาม AI
@bot.tree.command(name="ถาม", description="🤖 คุยกับท่านจอมยุทธ์ (AI)")
async def ask_ai(interaction: discord.Interaction, question: str):
    logger.info(f"❓ [Ask AI] User: {interaction.user.name} | Q: {question}")
    
    await interaction.response.defer()
    if model is None:
        logger.warning("⚠️ AI model is not ready.")
        return await interaction.followup.send(f"⚠️ AI ยังไม่พร้อม: {AI_STATUS}", ephemeral=True)
    try:
        now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        context_time = f"(ข้อมูลเวลาปัจจุบัน: {now})"

        response = model.generate_content(f"{BOT_PERSONA}\n{context_time}\n\nQ: {question}\nA:")
        
        text = response.text[:1900] + "..." if len(response.text) > 1900 else response.text
        embed = discord.Embed(title="🗣️ ท่านจอมยุทธ์กล่าว...", description=text, color=0x00ffcc)
        embed.set_footer(text=f"Q: {question} | โดย {interaction.user.name}")
        await interaction.followup.send(embed=embed)
        logger.info("✅ [Ask AI] Answered successfully.")
    except Exception as e:
        logger.error(f"🔥 [Ask AI] Error: {e}")
        await interaction.followup.send(f"😵 Error: {e}", ephemeral=True)

# 3. ดูดวง (Tune)
@bot.tree.command(name="ดูดวง", description="🔮 เช็คดวงกาชา/Tune")
async def fortune(interaction: discord.Interaction):
    if interaction.channel.name != ALLOWED_CHANNEL_FORTUNE:
        return await interaction.response.send_message(f"❌ **ผิดห้องครับ!**\nเล่นได้เฉพาะห้อง `{ALLOWED_CHANNEL_FORTUNE}` เท่านั้นครับ", ephemeral=True)
    
    fortunes = [
        "🌟 **เทพเจ้า RNG ประทับร่าง!** วันนี้กดอะไรก็ติด ออฟชั่นทองมาแน่!",
        "💀 **เกลือเค็มปี๋...** อย่าหาทำ Tune ออฟชั่นกาก พักก่อนโยม",
        "🔥 **มือร้อน(เงิน)!** ระวังหมดตัวนะเพื่อน เรท 0.98% มันไม่มีจริงหรอก",
        "🟢 **สีเขียวเหนี่ยวทรัพย์** วันนี้ได้แต่ของกากๆ แน่นอน ทำใจซะ",
        "📈 **ดวงกลางๆ** พอถูไถ แต่อย่าหวังของแรร์เลย แค่ได้ของปลอบใจก็ดีแล้ว",
        "💎 **มีแววเสียตังค์ฟรี** เปอร์เซ็นต์สำเร็จ 99% = เกลือ (ตามสูตรเกม)",
        "✨ **แสงสีทองรออยู่!** (ในฝันนะ) ของจริงน่าจะได้แค่เกลือ",
        "🧘 **ไปทำบุญ 9 วัดก่อน** ค่อยมาสุ่ม ดวงมืดมนมากวันนี้ ราหูอมกาชา",
        "⚔️ **จอมยุทธ์ถังแตก** วันนี้ดวงการเงินรั่วไหล อย่าเสี่ยงดวงเลย เก็บตังค์กินข้าวเถอะ",
        "🧧 **GM รักคุณ** (รักที่จะกินตังค์คุณ) กดกาชาทีไร น้ำตาไหลพรากทุกที"
    ]
    result = random.choice(fortunes)
    if "เทพเจ้า" in result or "แสง" in result: color = 0xffd700
    elif "เกลือ" in result or "ถังแตก" in result: color = 0x000000
    else: color = 0x3498db
    embed = discord.Embed(title="🎲 ผลการเสี่ยงทายดวงชะตา", description=f"ผลลัพธ์ของ {interaction.user.mention} คือ...\n\n{result}", color=color)
    await interaction.response.send_message(embed=embed)
    logger.info(f"🎲 Fortune checked for {interaction.user.name}")

# 4. ล้างแชท
@bot.tree.command(name="ล้าง", description="🧹 ลบข้อความล่าสุด")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear_chat(interaction: discord.Interaction, amount: int):
    if amount > 100: return await interaction.response.send_message("❌ สูงสุด 100", ephemeral=True)
    
    await interaction.response.defer(ephemeral=True) 
    await interaction.channel.purge(limit=amount)
    await interaction.followup.send("🧹 เรียบร้อย!", ephemeral=True)
    logger.info(f"🧹 Cleared {amount} messages in channel {interaction.channel.name} by {interaction.user.name}")

# 5. ล้างห้อง
@bot.tree.command(name="ล้างห้อง", description="⚠️ Nuke Channel")
@app_commands.checks.has_permissions(administrator=True)
async def nuke_channel(interaction: discord.Interaction):
    view = discord.ui.View()
    async def confirm(i):
        if i.user != interaction.user: return
        await i.response.send_message("💣 บึ้มมมม...", ephemeral=True)
        new_ch = await interaction.channel.clone(reason="Nuke by Bot")
        await interaction.channel.delete()
        await new_ch.send(f"✨ **ห้องใหม่ไฉไลกว่าเดิม!** (ล้างโดย {interaction.user.mention})")
        logger.warning(f"💣 Channel Nuked: {interaction.channel.name} by {interaction.user.name}")
    
    btn = discord.ui.Button(label="ยืนยันที่จะล้างห้อง?", style=discord.ButtonStyle.danger, emoji="💣")
    btn.callback = confirm
    view.add_item(btn)
    await interaction.response.send_message("⚠️ **คำเตือน:** ห้องนี้จะถูกลบและสร้างใหม่ ข้อความทั้งหมดจะหายไป!", view=view, ephemeral=True)

# 6. เช็คโมเดลที่มี (Add-on)
@bot.tree.command(name="เช็คโมเดล", description="📂 ดูว่าบัญชีนี้ใช้โมเดลอะไรได้บ้าง")
async def list_models(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    try:
        msg = "**รายชื่อโมเดลที่ใช้ได้:**\n"
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                msg += f"- `{m.name}`\n"
        await interaction.followup.send(msg)
    except Exception as e:
        await interaction.followup.send(f"❌ เช็คไม่ได้: {e}")

@bot.event
async def on_ready():
    logger.info(f"🚀 Logged in as {bot.user} (ID: {bot.user.id})")
    logger.info("✅ Bot is online and ready!")
    bot.add_view(TicketButton())

@bot.command()
async def setup(ctx):
    await ctx.message.delete()
    await refresh_setup_msg(ctx.channel)
    logger.info(f"🛠️ Setup command used in {ctx.channel.name}")

keep_alive()

# ✅ ใช้คำสั่งปกติ ไม่ต้องมี try...except ครอบ เพื่อให้เห็น Error เต็มๆ
bot.run(os.environ['TOKEN'])
