import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import datetime
import os
import random
import logging
import google.generativeai as genai
from keep_alive import keep_alive

# ==========================================
# 📝 1. ตั้งค่าระบบ Log
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%d/%m/%Y %H:%M:%S'
)
logger = logging.getLogger("DevilsBot")

# --- Permission ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='-', intents=intents)

# ==========================================
# ⚙️ 2. ตั้งค่า (แก้ไขชื่อห้อง/ยศ ตรงนี้)
# ==========================================
PUBLIC_CHANNEL = "ห้องแนะนำตัว"
ROLE_VERIFIED = "‹ แนะนำตัวแล้ว ›"
ROLE_WWM = "ข้าคือจอมยุทธ์เด๊ะ"
ALLOWED_CHANNEL_FORTUNE = "ห้องเช็คดวง"

# 🆕 รายชื่อยศสายอาชีพ (ต้องสร้างใน Discord ให้ชื่อตรงเป๊ะๆ)
ROLE_DPS = "DPS ⚔️"
ROLE_HEALER = "หมอ💉🩺"
ROLE_TANK = "แทงค์ 🛡️"
ROLE_HYBRID = "ไฮบริด 🧬"

# ==========================================
# 🧠 3. AI Setup
# ==========================================
GENAI_VERSION = genai.__version__
BOT_PERSONA = """
คุณคือ "Devils DenBot" AI ผู้ช่วยอัจฉริยะประจำกิลด์
ตัวตนของคุณ: เป็นปัญญาประดิษฐ์ที่มีความรอบรู้ แต่มีจิตวิญญาณของจอมยุทธ์แฝงอยู่
สไตล์การตอบ:
1. วิชาการ: จริงจัง ชัดเจน ถูกต้อง
2. คุยเล่น: กวนนิดๆ สไตล์หนังจีนกำลังภายใน เรียกผู้ใช้ว่า "สหาย"
"""

model = None
AI_STATUS = "Unknown"
KEY_DEBUG_INFO = "No Key"

try:
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        AI_STATUS = "❌ ไม่พบ Key"
        logger.error("API Key not found!")
    else:
        k_len = len(api_key)
        KEY_DEBUG_INFO = f"{api_key[:5]}...{api_key[-4:]} (ยาว: {k_len})"
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        AI_STATUS = "✅ พร้อมใช้งาน"
        logger.info("✅ Gemini Model loaded successfully.")
except Exception as e:
    AI_STATUS = f"💥 Error: {str(e)}"
    logger.critical(f"🔥 Critical Error loading AI: {e}")

# ==========================================
# 4. ฟังก์ชันและระบบห้อง (Intro System)
# ==========================================

async def refresh_setup_msg(channel):
    try:
        async for message in channel.history(limit=20):
            if message.author == bot.user and message.embeds and message.embeds[0].title == "📢 ยืนยันตัวตน / แนะนำตัว":
                await message.delete()
    except: pass
    
    embed = discord.Embed(title="📢 ยืนยันตัวตน / แนะนำตัว", description="กดปุ่มด้านล่างเพื่อเปิดห้องส่วนตัวสำหรับแนะนำตัวครับ 👇", color=0x00ff00)
    await channel.send(embed=embed, view=TicketButton())

# --- ตัวเลือกต่างๆ (Dropdowns) ---
class GameSelect(discord.ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label="Where Winds Meet", emoji="⚔️"), discord.SelectOption(label="อื่นๆ", emoji="🎮")]
        super().__init__(placeholder="เลือกเกมที่คุณเล่น...", min_values=1, max_values=1, options=options)
    async def callback(self, interaction):
        self.view.selected_value = self.values[0]
        await interaction.response.defer()
        self.view.stop()

# 🆕 ตัวเลือกสายอาชีพ
class ClassSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="ดาเมจ", emoji="⚔️", description="สายโจมตี DPS"),
            discord.SelectOption(label="หมอ", emoji="🩺", description="สายรักษา Healer"),
            discord.SelectOption(label="แทงค์", emoji="🛡️", description="สายป้องกัน Tank"),
            discord.SelectOption(label="ไฮบริด", emoji="🧬", description="สายผสม Hybrid")
        ]
        super().__init__(placeholder="เลือกสายอาชีพหลัก...", min_values=1, max_values=1, options=options)
    async def callback(self, interaction):
        self.view.selected_value = self.values[0]
        await interaction.response.defer()
        self.view.stop()

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
        except Exception as e: logger.error(f"Failed to create ticket: {e}")

    async def start_interview(self, channel, user, guild):
        def check(m): return m.author == user and m.channel == channel
        data = {}
        icon_prefix = "" # เก็บไอคอนนำหน้าชื่อ (เช่น ⚔️)

        try:
            await channel.send(f"{user.mention} **ยินดีต้อนรับครับ!**")
            
            # 1. ชื่อ
            await channel.send(embed=discord.Embed(title="1. ชื่อเล่นของคุณคือ?", color=0x3498db))
            data["name"] = (await bot.wait_for("message", check=check, timeout=300)).content

            # 2. อายุ
            await channel.send(embed=discord.Embed(title="2. อายุเท่าไหร่?", color=0x3498db))
            data["age"] = (await bot.wait_for("message", check=check, timeout=300)).content

            # 3. เกม
            view_game = discord.ui.View()
            select_game = GameSelect()
            view_game.add_item(select_game)
            await channel.send(embed=discord.Embed(title="3. เลือกเกมที่คุณเล่น", color=0x3498db), view=view_game)
            await view_game.wait()
            data["game"] = select_game.selected_value if hasattr(select_game, 'selected_value') else "อื่นๆ"

            data["char_name"] = "-"
            data["class"] = "-"

            # ถ้าเลือกเกม WWM
            if data["game"] == "Where Winds Meet":
                # 3.1 ถามชื่อตัวละคร
                await channel.send(embed=discord.Embed(title="⚔️ ชื่อตัวละครของคุณคือ?", color=0xe74c3c))
                data["char_name"] = (await bot.wait_for("message", check=check, timeout=300)).content
                
                # ให้ยศเกม WWM
                role_wwm = discord.utils.get(guild.roles, name=ROLE_WWM)
                if role_wwm: await user.add_roles(role_wwm)

                # 🆕 3.2 ถามสายอาชีพ (Class)
                view_class = discord.ui.View()
                select_class = ClassSelect()
                view_class.add_item(select_class)
                await channel.send(embed=discord.Embed(title="🛡️ เล่นสายอาชีพไหน?", color=0xe74c3c), view=view_class)
                await view_class.wait()
                
                if hasattr(select_class, 'selected_value'):
                    cls = select_class.selected_value
                    data["class"] = cls
                    
                    # Logic ให้ยศและไอคอนตามสาย
                    role_name_to_add = None
                    
                    if cls == "ดาเมจ":
                        role_name_to_add = ROLE_DPS
                        icon_prefix = "⚔️"
                    elif cls == "หมอ":
                        role_name_to_add = ROLE_HEALER
                        icon_prefix = "💉"
                    elif cls == "แทงค์":
                        role_name_to_add = ROLE_TANK
                        icon_prefix = "🛡️"
                    elif cls == "ไฮบริด":
                        role_name_to_add = ROLE_HYBRID
                        icon_prefix = "🧬"
                    
                    # เพิ่มยศสายอาชีพ
                    if role_name_to_add:
                        r = discord.utils.get(guild.roles, name=role_name_to_add)
                        if r: await user.add_roles(r)

            # สรุปและส่ง
            embed = discord.Embed(title="✅ สมาชิกใหม่รายงานตัว!", color=0xffd700)
            desc = f"**ชื่อเล่น :** {data['name']}\n**อายุ :** {data['age']}\n**เกมที่เล่น :** {data['game']}"
            if data["char_name"] != "-": 
                desc += f"\n**ชื่อในเกม :** {data['char_name']}"
                desc += f"\n**สายอาชีพ :** {data['class']}" # โชว์สายอาชีพด้วย
            
            embed.description = desc
            if user.avatar: embed.set_thumbnail(url=user.avatar.url)
            embed.set_footer(text=f"แนะนำตัวโดย {user.name}")

            pub_ch = discord.utils.get(guild.text_channels, name=PUBLIC_CHANNEL)
            sent_msg = None
            if pub_ch:
                # สแกนลบอันเก่า
                async for msg in pub_ch.history(limit=50):
                    if msg.author == bot.user and msg.embeds and msg.embeds[0].footer.text == f"แนะนำตัวโดย {user.name}":
                        try: await msg.delete()
                        except: pass
                        break
                sent_msg = await pub_ch.send(embed=embed)
                await refresh_setup_msg(pub_ch)

            # ให้ยศแนะนำตัวแล้ว
            role_ver = discord.utils.get(guild.roles, name=ROLE_VERIFIED)
            if role_ver: await user.add_roles(role_ver)
            
            # 🆕 เปลี่ยนชื่อดิสคอร์ด (ใส่ไอคอน + ชื่อเดิม + ชื่อเล่น)
            try:
                # ถ้ามีไอคอน (เล่น WWM) ให้ใส่ ถ้าไม่มีก็ใส่แค่ชื่อเล่น
                new_nick = ""
                if icon_prefix:
                    new_nick = f"{icon_prefix} {user.name} ({data['name']})"
                else:
                    new_nick = f"{user.name} ({data['name']})"
                
                await user.edit(nick=new_nick)
            except Exception as e:
                logger.warning(f"เปลี่ยนชื่อไม่ได้ (อาจเพราะยศบอทต่ำกว่าคนนี้): {e}")
                await channel.send(f"⚠️ บอทเปลี่ยนชื่อให้ไม่ได้ (ยศบอทต่ำกว่าท่าน) แต่บันทึกข้อมูลแล้วครับ")

            view_back = discord.ui.View()
            if sent_msg:
                view_back.add_item(discord.ui.Button(label="🔙 ไปดูผลลัพธ์", style=discord.ButtonStyle.link, url=sent_msg.jump_url))
            
            await channel.send(embed=discord.Embed(title="✅ เรียบร้อย!", description="ห้องจะลบใน 10 วินาที", color=0x00ff00), view=view_back)
            await asyncio.sleep(10)
            await channel.delete()
        except: await channel.delete()

@bot.command()
async def sync(ctx):
    synced = await bot.tree.sync()
    await ctx.send(f"✅ Synced {len(synced)} commands.")

@bot.command()
async def setup(ctx):
    await ctx.message.delete()
    await refresh_setup_msg(ctx.channel)

# ==========================================
# 🔥 5. Slash Commands
# ==========================================

# 1. เช็คระบบ
@bot.tree.command(name="เช็คระบบ", description="🔧 ดูสถานะบอท")
async def check_status(interaction: discord.Interaction):
    color = 0x00ff00 if "✅" in AI_STATUS else 0xff0000
    embed = discord.Embed(title="🔧 ข้อมูลระบบ AI", color=color)
    embed.add_field(name="สถานะ", value=AI_STATUS, inline=False)
    embed.add_field(name="📦 Version", value=f"`v{GENAI_VERSION}`", inline=True)
    embed.add_field(name="🔑 Key", value=f"`{KEY_DEBUG_INFO}`", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# 2. เช็คโมเดล
@bot.tree.command(name="เช็คโมเดล", description="📂 ดูโมเดลที่ใช้ได้")
async def list_models(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    try:
        msg = "**Models:**\n" + "\n".join([f"- `{m.name}`" for m in genai.list_models() if 'generateContent' in m.supported_generation_methods])
        await interaction.followup.send(msg[:1900])
    except: await interaction.followup.send("❌ เช็คไม่ได้")

# 3. ถาม AI (เวลาไทย)
@bot.tree.command(name="ถาม", description="🤖 คุยกับท่านจอมยุทธ์ (AI)")
async def ask_ai(interaction: discord.Interaction, question: str):
    await interaction.response.defer()
    if model is None: return await interaction.followup.send(f"⚠️ AI ยังไม่พร้อม: {AI_STATUS}", ephemeral=True)
    try:
        tz_thai = datetime.timezone(datetime.timedelta(hours=7))
        now = datetime.datetime.now(tz_thai).strftime("%d/%m/%Y %H:%M:%S")
        response = model.generate_content(f"{BOT_PERSONA}\n(เวลาไทย: {now})\n\nQ: {question}\nA:")
        text = response.text[:1900] + "..." if len(response.text) > 1900 else response.text
        embed = discord.Embed(title="🗣️ ท่านจอมยุทธ์กล่าว...", description=text, color=0x00ffcc)
        embed.set_footer(text=f"Q: {question} | โดย {interaction.user.name}")
        await interaction.followup.send(embed=embed)
    except Exception as e: await interaction.followup.send(f"😵 Error: {e}", ephemeral=True)

# 4. ดูดวง (Full Option)
@bot.tree.command(name="ดูดวง", description="🔮 เช็คดวงกาชา/Tune")
async def fortune(interaction: discord.Interaction):
    if interaction.channel.name != ALLOWED_CHANNEL_FORTUNE:
        return await interaction.response.send_message(f"❌ ผิดห้อง! ไปห้อง `{ALLOWED_CHANNEL_FORTUNE}` ครับ", ephemeral=True)
    
    fortunes = [
        "🌟 **เทพเจ้า RNG ประทับร่าง!** ออฟชั่นทองมาแน่!", 
        "💀 **เกลือเค็มปี๋...** อย่าหาทำ Tune ออฟชั่นกาก", 
        "🔥 **มือร้อน(เงิน)!** ระวังหมดตัวนะเพื่อน", 
        "🟢 **สีเขียวเหนี่ยวทรัพย์** วันนี้ได้แต่ของกากๆ", 
        "📈 **ดวงกลางๆ** พอถูไถ แต่อย่าหวังของแรร์", 
        "💎 **มีแววเสียตังค์ฟรี** 99% = เกลือ", 
        "✨ **แสงสีทองรออยู่!** (ในฝันนะ) ของจริงเกลือ", 
        "🧘 **ไปทำบุญ 9 วัดก่อน** ดวงมืดมนมากวันนี้", 
        "⚔️ **จอมยุทธ์ถังแตก** เก็บตังค์กินข้าวเถอะ", 
        "🧧 **GM รักคุณ** (รักที่จะกินตังค์คุณ)"
    ]
    result = random.choice(fortunes)
    if "เทพเจ้า" in result or "แสง" in result: color = 0xffd700
    elif "เกลือ" in result or "ถังแตก" in result: color = 0x000000
    else: color = 0x3498db
    
    embed = discord.Embed(title="🎲 ผลการเสี่ยงทาย", description=f"ผลลัพธ์ของ {interaction.user.mention}:\n\n{result}", color=color)
    await interaction.response.send_message(embed=embed)

# 5. ล้างแชท
@bot.tree.command(name="ล้าง", description="🧹 ลบข้อความ")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear_chat(interaction: discord.Interaction, amount: int):
    if amount > 100: return await interaction.response.send_message("❌ สูงสุด 100", ephemeral=True)
    await interaction.response.defer(ephemeral=True)
    await interaction.channel.purge(limit=amount)
    await interaction.followup.send("🧹 เรียบร้อย!", ephemeral=True)

# 6. ล้างห้อง
@bot.tree.command(name="ล้างห้อง", description="⚠️ Nuke Channel")
@app_commands.checks.has_permissions(administrator=True)
async def nuke_channel(interaction: discord.Interaction):
    view = discord.ui.View()
    async def confirm(i):
        if i.user != interaction.user: return
        await i.response.send_message("💣 บึ้มมมม...", ephemeral=True)
        new_ch = await interaction.channel.clone(reason="Nuke")
        await interaction.channel.delete()
        await new_ch.send(f"✨ ห้องใหม่! (ล้างโดย {interaction.user.mention})")
    
    btn = discord.ui.Button(label="ยืนยัน?", style=discord.ButtonStyle.danger, emoji="💣")
    btn.callback = confirm
    view.add_item(btn)
    await interaction.response.send_message("⚠️ ยืนยันที่จะล้างห้อง?", view=view, ephemeral=True)

@bot.event
async def on_ready():
    logger.info(f"🚀 Logged in as {bot.user}")
    bot.add_view(TicketButton())

keep_alive()
bot.run(os.environ['TOKEN'])
