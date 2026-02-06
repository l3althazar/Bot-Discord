import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import datetime
import os
import random
import logging
import google.generativeai as genai
from flask import Flask
from threading import Thread

# ==========================================
# 🌐 Web Server สำหรับ Uptime (Keep Alive)
# ==========================================
app = Flask('')
@app.route('/')
def home(): return "<h1>Devils DenBot is Online!</h1>"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# ==========================================
# ⚙️ การตั้งค่าหลัก (Config)
# ==========================================
logging.basicConfig(level=logging.INFO)
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='-', intents=intents)

# ชื่อยศและห้อง (ตรงตามคำสั่งเป๊ะ)
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

# AI Setup (รุ่นเดิมที่เสถียรและไม่ติด 404)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
ai_model = genai.GenerativeModel('gemini-1.5-flash')

# ==========================================
# 📜 ระบบจัดการใบลา (Leave System)
# ==========================================
class LeaveApprovalView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    async def interaction_check(self, interaction):
        if discord.utils.get(interaction.user.roles, name=ROLE_ADMIN_CHECK): return True
        await interaction.response.send_message(f"⛔ เฉพาะ **{ROLE_ADMIN_CHECK}** เท่านั้น", ephemeral=True)
        return False

    @discord.ui.button(label="อนุมัติ", style=discord.ButtonStyle.success, custom_id="approve_l", emoji="✅")
    async def approve(self, interaction, button):
        emb = interaction.message.embeds[0].copy()
        emb.color = 0x2ecc71
        emb.set_field_at(3, name="📋 สถานะ", value=f"✅ อนุมัติแล้ว โดย {interaction.user.mention}", inline=False)
        await interaction.response.edit_message(embed=emb, view=None)

    @discord.ui.button(label="ไม่อนุมัติ", style=discord.ButtonStyle.danger, custom_id="deny_l", emoji="❌")
    async def deny(self, interaction, button):
        emb = interaction.message.embeds[0].copy()
        emb.color = 0xe74c3c
        emb.set_field_at(3, name="📋 สถานะ", value=f"❌ ไม่อนุมัติ โดย {interaction.user.mention}", inline=False)
        await interaction.response.edit_message(embed=emb, view=None)

class LeaveModal(discord.ui.Modal, title="📜 แบบฟอร์มขอลา (Leave Form)"):
    char = discord.ui.TextInput(label="ชื่อตัวละครในเกม", required=True)
    l_type = discord.ui.TextInput(label="หัวข้อการลา", required=True)
    l_date = discord.ui.TextInput(label="วันที่/เวลา", required=True)
    reason = discord.ui.TextInput(label="เหตุผล (ถ้ามี)", style=discord.TextStyle.paragraph, required=False)

    async def on_submit(self, interaction):
        embed = discord.Embed(title="📩 มีสาส์นขอลาหยุด!", color=0xf1c40f)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.add_field(name="👤 จอมยุทธ์", value=self.char.value, inline=False)
        embed.add_field(name="📌 ประเภท", value=self.l_type.value, inline=False)
        embed.add_field(name="📅 วันที่/เวลา", value=self.l_date.value, inline=False)
        embed.add_field(name="📋 สถานะ", value="⏳ **รอการตรวจสอบ**", inline=False)
        embed.set_footer(text=f"ยื่นเรื่องเมื่อ: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}")
        
        await interaction.channel.send(content=f"**ผู้ยื่นเรื่อง:** {interaction.user.mention}", embed=embed, view=LeaveApprovalView())
        await interaction.response.send_message("✅ ส่งใบลาเรียบร้อย!", ephemeral=True)

class LeaveButton(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="📝 เขียนใบลา", style=discord.ButtonStyle.danger, custom_id="write_leave_btn", emoji="📜")
    async def write(self, interaction, button): await interaction.response.send_modal(LeaveModal())

# ==========================================
# 🆕 ระบบแนะนำตัว (Intro System)
# ==========================================
class IntroModal(discord.ui.Modal, title="📝 ข้อมูลแนะนำตัว"):
    name = discord.ui.TextInput(label="ชื่อเล่น", required=True)
    age = discord.ui.TextInput(label="อายุ", required=True)
    async def on_submit(self, interaction):
        await interaction.response.send_message("🎮 **เลือกเกมที่ท่านเล่น:**", view=GameSelect({"n": self.name.value, "a": self.age.value}), ephemeral=True)

class GameSelect(discord.ui.View):
    def __init__(self, data): super().__init__(); self.data = data
    @discord.ui.select(placeholder="เลือกเกม...", options=[discord.SelectOption(label="Where Winds Meet", emoji="⚔️"), discord.SelectOption(label="อื่นๆ", emoji="🎮")])
    async def select(self, interaction, select):
        self.data["g"] = select.values[0]
        if self.data["g"] == "Where Winds Meet":
            modal = discord.ui.Modal(title="⚔️ ข้อมูลตัวละคร WWM")
            ign = discord.ui.TextInput(label="ชื่อในเกม WWM", required=True)
            modal.add_item(ign)
            async def wwm_sub(it):
                self.data["ign"] = ign.value
                await it.response.edit_message(content="🛡️ **เลือกสายอาชีพ:**", view=ClassSelect(self.data))
            modal.on_submit = wwm_sub
            await interaction.response.send_modal(modal)
        else: await finalize_intro(interaction, self.data)

class ClassSelect(discord.ui.View):
    def __init__(self, data): super().__init__(); self.data = data
    @discord.ui.select(placeholder="เลือกอาชีพ...", options=[
        discord.SelectOption(label="ดาเมจ", emoji="⚔️"), discord.SelectOption(label="หมอ", emoji="🩺"),
        discord.SelectOption(label="แทงค์", emoji="🛡️"), discord.SelectOption(label="ไฮบริด", emoji="🧬")
    ])
    async def callback(self, interaction, select):
        self.data["c"] = select.values[0]
        await finalize_intro(interaction, self.data)

async def finalize_intro(interaction, data):
    user, guild = interaction.user, interaction.guild
    pub_ch = discord.utils.get(guild.text_channels, name=PUBLIC_CHANNEL)
    
    # ลบข้อความเก่าของผู้ใช้ และปุ่มแนะนำตัวเก่า
    if pub_ch:
        async for m in pub_ch.history(limit=50):
            if m.author == bot.user and m.embeds:
                if user.name in str(m.embeds[0].footer.text if m.embeds[0].footer else "") or "ยืนยันตัวตน" in str(m.embeds[0].title):
                    await m.delete()

    # จัดการยศ
    roles = [discord.utils.get(guild.roles, name=ROLE_VERIFIED)]
    icon = ""
    if data.get("g") == "Where Winds Meet":
        roles.append(discord.utils.get(guild.roles, name=ROLE_WWM))
        cls_map = {"ดาเมจ": (ROLE_DPS, "⚔️"), "หมอ": (ROLE_HEALER, "💉"), "แทงค์": (ROLE_TANK, "🛡️"), "ไฮบริด": (ROLE_HYBRID, "🧬")}
        rn, icon = cls_map.get(data.get("c"), (None, ""))
        roles.append(discord.utils.get(guild.roles, name=rn))
    
    await user.add_roles(*[r for r in roles if r])
    try: await user.edit(nick=f"{icon} {user.name} ({data['n']})")
    except: pass

    # ส่ง Embed แนะนำตัว และส่งปุ่มใหม่ไว้ล่างสุด
    embed = discord.Embed(title="✅ สมาชิกใหม่รายงานตัว!", color=0xffd700)
    embed.set_thumbnail(url=user.display_avatar.url)
    embed.description = f"**ชื่อเล่น :** {data['n']}\n**อายุ :** {data['a']}\n**เกมที่เล่น :** {data['g']}"
    if "ign" in data: embed.description += f"\n**ชื่อในเกม :** {data['ign']}\n**สายอาชีพ :** {data['c']}"
    embed.set_footer(text=f"แนะนำตัวโดย {user.name}")
    
    await pub_ch.send(embed=embed)
    await pub_ch.send(embed=discord.Embed(title="📢 ยืนยันตัวตน / แนะนำตัว", description="กดปุ่มด้านล่างเพื่อเปิดแบบฟอร์มลงทะเบียนครับ 👇", color=0x00ff00), view=IntroButton())
    await interaction.response.edit_message(content="✅ บันทึกเรียบร้อย!", view=None)

class IntroButton(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="📝 กดเพื่อเริ่มแนะนำตัว", style=discord.ButtonStyle.green, custom_id="start_intro_btn")
    async def start(self, interaction, button): await interaction.response.send_modal(IntroModal())

# ==========================================
# 🔮 ระบบดูดวง (10 รูปแบบ พร้อม GIF)
# ==========================================
@bot.tree.command(name="ดูดวง", description="🔮 เช็คดวงประจำวันของท่าน (10 รูปแบบ)")
async def fortune(interaction: discord.Interaction):
    if interaction.channel.name != ALLOWED_CHANNEL_FORTUNE:
        return await interaction.response.send_message(f"❌ กรุณาใช้ในห้อง `{ALLOWED_CHANNEL_FORTUNE}`", ephemeral=True)
    
    fortunes_data = [
        {"text": "🌟 RNG ประทับร่าง! ออฟทองมาแน่!", "color": 0xffd700, "img": "https://media.giphy.com/media/l0Ex6kAKAoFRsFh6M/giphy.gif"},
        {"text": "🔥 มือร้อน(เงิน)! ระวังหมดตัวนะเพื่อน", "color": 0xff4500, "img": "https://media.giphy.com/media/Lopx9eUi34rbq/giphy.gif"},
        {"text": "✨ แสงสีทองรออยู่! การันตีของแรร์!", "color": 0xffff00, "img": "https://media.giphy.com/media/3o7TKSjRrfIPjeiVyM/giphy.gif"},
        {"text": "🟢 สีเขียวเหนี่ยวทรัพย์ วันนี้ได้แต่ของพอถูไถ", "color": 0x2ecc71, "img": "https://media.giphy.com/media/13HgwGsXF0aiGY/giphy.gif"},
        {"text": "📈 ดวงกลางๆ พอไหว ไม่ดีไม่ร้าย", "color": 0x3498db, "img": "https://media.giphy.com/media/l2Je66zG6mAAZxgqI/giphy.gif"},
        {"text": "🧘 ไปทำบุญ 9 วัดก่อน แล้วค่อยมาสุ่มใหม่", "color": 0x9b59b6, "img": "https://media.giphy.com/media/xT5LMHxhOfscxPfIfm/giphy.gif"},
        {"text": "💀 ดวง All Bamboocut (ไผ่ล้วนๆ)", "color": 0x000000, "img": "https://media.giphy.com/media/26tP3M3iA3EBIfXy0/giphy.gif"},
        {"text": "💎 เกลือล้วนๆ ไม่มีวัวปน", "color": 0x95a5a6, "img": "https://media.giphy.com/media/3o6UB5RrlQuMfZp82Y/giphy.gif"},
        {"text": "⚔️ จอมยุทธ์ถังแตก... วันนี้พักก่อน", "color": 0x7f8c8d, "img": "https://media.giphy.com/media/l2JdZOv5901Q6Q7Ek/giphy.gif"},
        {"text": "🧧 GM รักคุณ (รักที่จะกินตังค์คุณนะ)", "color": 0xe74c3c, "img": "https://media.giphy.com/media/3o7TKRBB3E7IdVNLm8/giphy.gif"}
    ]
    res = random.choice(fortunes_data)
    emb = discord.Embed(title="🔮 ผลทำนายดวงประจำวัน", description=f"# {res['text']}", color=res['color'])
    emb.set_image(url=res['img'])
    emb.set_footer(text=f"จอมยุทธ์: {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
    await interaction.response.send_message(embed=emb)

# ==========================================
# 🧹 คำสั่งจัดการห้องแชท
# ==========================================
@bot.tree.command(name="ล้าง", description="🧹 ลบข้อความตามจำนวน")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"🧹 ลบแล้ว {len(deleted)} ข้อความ", ephemeral=True)

@bot.tree.command(name="ล้างห้อง", description="🔥 ลบข้อความทั้งหมดในห้องนี้")
@app_commands.checks.has_permissions(administrator=True)
async def clear_all(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    await interaction.channel.purge()
    await interaction.followup.send("🔥 ล้างห้องเรียบร้อย!", ephemeral=True)

# ==========================================
# 🤖 ระบบถาม AI และ Sync
# ==========================================
@bot.tree.command(name="ถาม", description="🤖 คุยกับ AI จอมยุทธ์")
async def ask(interaction: discord.Interaction, คำถาม: str):
    await interaction.response.defer()
    try:
        response = ai_model.generate_content(คำถาม)
        await interaction.followup.send(embed=discord.Embed(title="🗣️ ท่านจอมยุทธ์กล่าว...", description=response.text[:1900], color=0x00ffcc))
    except Exception as e: await interaction.followup.send(f"❌ AI Error: {e}")

@bot.tree.command(name="เช็ครุ่นไอเอ", description="🔍 ตรวจสอบรุ่น AI")
async def check_ai(interaction: discord.Interaction):
    txt = "- gemini-1.5-flash 🟢 (Active)\n- gemini-1.5-pro ⚪\n- gemini-2.0-flash-exp ⚪"
    await interaction.response.send_message(embed=discord.Embed(title="🤖 AI Support", description=txt), ephemeral=True)

@bot.command()
async def sync(ctx):
    synced = await bot.tree.sync()
    await ctx.send(f"✅ Sync สำเร็จ! ตรวจพบและอัปเดตคำสั่งทั้งหมด **{len(synced)}** คำสั่ง")

@bot.event
async def on_ready():
    bot.add_view(IntroButton())
    bot.add_view(LeaveButton())
    bot.add_view(LeaveApprovalView())
    await bot.tree.sync()
    print(f"🚀 {bot.user} พร้อมรับใช้!")

# ==========================================
# 🚀 รันระบบ
# ==========================================
keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))
