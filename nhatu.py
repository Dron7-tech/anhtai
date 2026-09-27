import discord
from discord.ext import tasks
from discord import app_commands
import sqlite3
import json
import os
import time

ROLE_TU_NHAN = 1552465079381921802
CHANNEL_NHA_TU = 1552432404730486864
ADMIN_ROLES = [1438895205012082812, 1438865272315445258]
DB_FILE = "nhatu_database.db"

conn = None
cursor = None
DB_CHANNEL_ID = None
DB_LOADED = False

async def get_db_channel(bot):
    global DB_CHANNEL_ID
    if DB_CHANNEL_ID: return bot.get_channel(DB_CHANNEL_ID)

    jail_channel = bot.get_channel(CHANNEL_NHA_TU)
    if not jail_channel: return None
    guild = jail_channel.guild

    for channel in guild.text_channels:
        if channel.name == "database-nhatu":
            DB_CHANNEL_ID = channel.id
            return channel

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }
    for role_id in ADMIN_ROLES:
        role = guild.get_role(role_id)
        if role: overwrites[role] = discord.PermissionOverwrite(read_messages=True)

    try:
        new_channel = await guild.create_text_channel("database-nhatu", overwrites=overwrites, category=jail_channel.category)
        DB_CHANNEL_ID = new_channel.id
        return new_channel
    except Exception as e:
        print(f"[DB] Lỗi tạo kênh DB: {e}")
        return None

async def init_sqlite(bot):
    global conn, cursor, DB_LOADED
    if DB_LOADED: return
    
    db_channel = await get_db_channel(bot)
    
    if db_channel:
        try:
            async for msg in db_channel.history(limit=10):
                if msg.author == bot.user and msg.attachments:
                    att = msg.attachments[0]
                    if att.filename == DB_FILE:
                        await att.save(DB_FILE)
                        print("✅ Đã khôi phục SQLite Database từ Discord Cloud!")
                        break
        except Exception as e:
            print(f"[DB] Lỗi tải DB từ Discord: {e}")

    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jail (
            user_id TEXT PRIMARY KEY,
            end_time REAL,
            old_roles TEXT,
            reason TEXT,
            appealed INTEGER
        )
    ''')
    conn.commit()

    old_json = "jail_data.json"
    if os.path.exists(old_json):
        try:
            with open(old_json, "r", encoding="utf-8") as f:
                old_data = json.load(f)
                for uid, info in old_data.items():
                    if not get_jail_data(uid):
                        add_jail_data(uid, info["end_time"], info.get("old_roles", []), info.get("reason", "Không rõ"), info.get("appealed", False))
            os.rename(old_json, "jail_data_backup.json")
            await backup_sqlite_to_cloud(bot)
        except Exception: pass
            
    DB_LOADED = True

async def backup_sqlite_to_cloud(bot):
    if not conn: return
    conn.commit() 
    db_channel = await get_db_channel(bot)
    if not db_channel: return
    
    try:
        async for msg in db_channel.history(limit=5):
            if msg.author == bot.user and msg.attachments:
                await msg.delete()
        file = discord.File(DB_FILE)
        await db_channel.send(content="💾 [SQLITE BACKUP] - Dữ liệu Lõi Nhà Tù", file=file)
    except Exception as e:
        print(f"[DB] Lỗi Backup SQLite: {e}")

def get_jail_data(user_id):
    cursor.execute("SELECT end_time, old_roles, reason, appealed FROM jail WHERE user_id = ?", (str(user_id),))
    row = cursor.fetchone()
    if row:
        return {
            "end_time": row[0],
            "old_roles": json.loads(row[1]),
            "reason": row[2],
            "appealed": bool(row[3])
        }
    return None

def get_all_jail_data():
    cursor.execute("SELECT user_id, end_time, old_roles, reason, appealed FROM jail")
    rows = cursor.fetchall()
    data = {}
    for row in rows:
        data[row[0]] = {"end_time": row[1], "old_roles": json.loads(row[2]), "reason": row[3], "appealed": bool(row[4])}
    return data

def add_jail_data(user_id, end_time, old_roles, reason, appealed=False):
    cursor.execute('''
        INSERT OR REPLACE INTO jail (user_id, end_time, old_roles, reason, appealed)
        VALUES (?, ?, ?, ?, ?)
    ''', (str(user_id), end_time, json.dumps(old_roles), reason, int(appealed)))
    conn.commit()

def remove_jail_data(user_id):
    cursor.execute("DELETE FROM jail WHERE user_id = ?", (str(user_id),))
    conn.commit()

def update_appeal_status(user_id):
    cursor.execute("UPDATE jail SET appealed = 1 WHERE user_id = ?", (str(user_id),))
    conn.commit()

def parse_time(time_str):
    if not time_str: return None
    unit = time_str[-1].lower()
    try:
        val = int(time_str[:-1])
        if unit == 'm': return val * 60
        if unit == 'h': return val * 3600
        if unit == 'd': return val * 86400
    except Exception: pass
    return None

def is_admin(member):
    for role in member.roles:
        if role.id in ADMIN_ROLES: return True
    return False

class AppealView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="📝 Gửi Kháng Cáo", style=discord.ButtonStyle.primary, custom_id="btn_khang_cao")
    async def btn_khang_cao(self, interaction: discord.Interaction, button: discord.ui.Button):
        uid_str = str(interaction.user.id)
        try:
            info = get_jail_data(uid_str)
            if not info:
                await interaction.response.send_message("❌ Bạn không phải là tù nhân, kháng cáo gì tầm này?", ephemeral=True)
                return
                
            if info.get("appealed", False):
                await interaction.response.send_message("❌ Bạn đã dùng hết quyền kháng cáo (1 lần duy nhất)!", ephemeral=True)
                return
                
            update_appeal_status(uid_str)
            await backup_sqlite_to_cloud(self.bot)
            
            await interaction.response.send_message("✅ Đơn kháng cáo đã được gửi tới hội đồng quản trị!", ephemeral=True)
            button.disabled = True
            button.label = "Đã Kháng Cáo"
            await interaction.message.edit(view=self)
            
            channel = interaction.guild.get_channel(CHANNEL_NHA_TU)
            if channel:
                pings = " ".join([f"<@&{r}>" for r in ADMIN_ROLES])
                embed = discord.Embed(title="⚖️ ĐƠN XIN KHOAN HỒNG", description=f"Phạm nhân {interaction.user.mention} đã đệ đơn xin giảm án/đặc xá!", color=discord.Color.orange())
                embed.add_field(name="Tội danh hiện tại", value=info.get("reason", "Không rõ"), inline=False)
                embed.set_thumbnail(url=interaction.user.display_avatar.url)
                embed.set_footer(text="Admin dùng lệnh /unjail để duyệt đặc xá.")
                await channel.send(content=pings, embed=embed)
        except Exception as e: print(f"[APPEAL] Lỗi: {e}")

# ==========================================
# KHỞI TẠO SLASH COMMANDS
# ==========================================
def setup_nhatu(bot):
    bot.add_view(AppealView(bot))

    @bot.listen("on_ready")
    async def jail_on_ready():
        await init_sqlite(bot)
        if not check_jail_loop.is_running():
            check_jail_loop.start()
            print("✅ Vòng lặp Nhà Tù & SQLite DB đã khởi động an toàn!")

    @bot.tree.command(name="jail", description="Bắt giam một tội phạm vào nhà đá")
    @app_commands.describe(member="Chọn người cần bắt", thoi_gian="Nhập thời gian (VD: 10m, 2h, 1d)", li_do="Lý do bắt giữ")
    async def slash_jail(interaction: discord.Interaction, member: discord.Member, thoi_gian: str, li_do: str = "Không có lý do"):
        if not is_admin(interaction.user):
            await interaction.response.send_message("❌ Bạn không có quyền bỏ tù người khác!", ephemeral=True)
            return

        if is_admin(member):
            await interaction.response.send_message("❌ Luật pháp không áp dụng lên các vị thần! Không thể bỏ tù Quản trị viên.", ephemeral=True)
            return
            
        duration = parse_time(thoi_gian)
        if not duration:
            await interaction.response.send_message("❌ Định dạng thời gian sai. Dùng `m` (phút), `h` (giờ), `d` (ngày). Ví dụ: `10m`.", ephemeral=True)
            return

        await interaction.response.defer() 
        bot_top_role = interaction.guild.me.top_role.position
        old_roles = []
        roles_to_remove = []
        unremovable_roles = []

        for role in member.roles:
            if role.name == "@everyone" or role.id == ROLE_TU_NHAN: continue
            old_roles.append(role.id)
            if role.position < bot_top_role: roles_to_remove.append(role)
            else: unremovable_roles.append(role)

        try:
            if roles_to_remove: await member.remove_roles(*roles_to_remove)
            tu_nhan_role = interaction.guild.get_role(ROLE_TU_NHAN)
            if tu_nhan_role and tu_nhan_role.position < bot_top_role: await member.add_roles(tu_nhan_role)
        except Exception as e:
            print(f"[JAIL] Lỗi gỡ/gán role cho {member.display_name}: {e}")

        end_time = time.time() + duration
        add_jail_data(member.id, end_time, old_roles, li_do, False)
        await backup_sqlite_to_cloud(bot)

        embed = discord.Embed(title="🚨 LỆNH BẮT GIỮ 🚨", color=discord.Color.dark_red())
        embed.add_field(name="Tội phạm", value=member.mention, inline=True)
        embed.add_field(name="Người bắt", value=interaction.user.mention, inline=True)
        embed.add_field(name="Mức án", value=thoi_gian, inline=True)
        embed.add_field(name="Lý do", value=li_do, inline=False)
        if unremovable_roles:
            embed.add_field(name="⚠️ Báo cáo ngục tốt", value=f"Phạm nhân có chức sắc quá lớn, không thể lột các role: {', '.join([r.name for r in unremovable_roles])}", inline=False)
            
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="Dùng lệnh /kiemtratu để xem thời gian mãn hạn.")
        await interaction.followup.send(embed=embed)

        jail_channel = interaction.guild.get_channel(CHANNEL_NHA_TU)
        if jail_channel and interaction.channel.id != CHANNEL_NHA_TU:
            try: await jail_channel.send(f"⛓️ Chào mừng {member.mention} đã đến với nhà đá! Mức án của ngươi là **{thoi_gian}**.")
            except Exception: pass

    @bot.tree.command(name="unjail", description="Đặc xá, ân xá cho một tù nhân")
    @app_commands.describe(member="Người cần ân xá")
    async def slash_unjail(interaction: discord.Interaction, member: discord.Member):
        if not is_admin(interaction.user):
            await interaction.response.send_message("❌ Bạn không có quyền ân xá người khác!", ephemeral=True)
            return

        uid_str = str(member.id)
        info = get_jail_data(uid_str)
        if not info:
            await interaction.response.send_message(f"⚠️ {member.display_name} hiện không bị giam giữ!", ephemeral=True)
            return

        await interaction.response.defer()
        bot_top_role = interaction.guild.me.top_role.position
        
        try:
            tu_nhan_role = interaction.guild.get_role(ROLE_TU_NHAN)
            if tu_nhan_role and tu_nhan_role in member.roles and tu_nhan_role.position < bot_top_role:
                await member.remove_roles(tu_nhan_role)
            
            roles_to_add = []
            for r_id in info.get("old_roles", []):
                r = interaction.guild.get_role(r_id)
                if r and r not in member.roles and r.position < bot_top_role: roles_to_add.append(r)
            if roles_to_add: await member.add_roles(*roles_to_add)
        except Exception as e: print(f"[UNJAIL] Lỗi: {e}")

        remove_jail_data(uid_str)
        await backup_sqlite_to_cloud(bot)

        embed = discord.Embed(title="🕊️ LỆNH ĐẶC XÁ 🕊️", description=f"Quản ngục {interaction.user.mention} đã ký quyết định đặc xá cho {member.mention} trước thời hạn!", color=discord.Color.green())
        embed.set_thumbnail(url=member.display_avatar.url)
        await interaction.followup.send(embed=embed)

    @bot.tree.command(name="kiemtratu", description="Kiểm tra thông tin án phạt")
    @app_commands.describe(member="Người cần kiểm tra (Dành cho Admin)")
    async def slash_kiemtratu(interaction: discord.Interaction, member: discord.Member = None):
        target_id = member.id if member else interaction.user.id
        is_self = target_id == interaction.user.id

        if not is_self and not is_admin(interaction.user):
            await interaction.response.send_message("❌ Bạn không có quyền kiểm tra hồ sơ tù nhân của người khác!", ephemeral=True)
            return

        uid_str = str(target_id)
        info = get_jail_data(uid_str)
        
        if not info:
            msg = "✅ Bạn đang là công dân tự do!" if is_self else f"✅ {member.display_name} không có trong danh sách đen!"
            await interaction.response.send_message(msg, ephemeral=True)
            return

        remaining = int(info["end_time"] - time.time())
        if remaining <= 0:
            msg = "🕊️ Mức án của bạn đã hết! Đang chờ thả..." if is_self else f"🕊️ Mức án của {member.display_name} đã hết! Chuẩn bị thả."
            await interaction.response.send_message(msg, ephemeral=True)
            return
            
        m, s = divmod(remaining, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        
        time_str = f"{d} ngày " if d > 0 else ""
        time_str += f"{h} giờ " if h > 0 else ""
        time_str += f"{m} phút " if m > 0 else ""
        time_str += f"{s} giây" if s > 0 else ""
        
        da_khang_cao = info.get("appealed", False)
        appealed_status = "Đã dùng (Hết quyền)" if da_khang_cao else "Còn 1 lần"
        
        target_obj = interaction.guild.get_member(target_id)
        embed = discord.Embed(title=f"⏳ HỒ SƠ ÁN PHẠT: {target_obj.display_name if target_obj else 'Phạm nhân'}", color=discord.Color.dark_grey())
        embed.add_field(name="Lý do phạm tội", value=info.get("reason", "Không rõ"), inline=False)
        embed.add_field(name="Thời gian còn lại", value=f"**{time_str.strip()}**", inline=False)
        embed.add_field(name="Trạng thái kháng cáo", value=appealed_status, inline=False)
        
        view_to_send = None if (da_khang_cao or not is_self) else AppealView(bot)
        await interaction.response.send_message(embed=embed, view=view_to_send, ephemeral=(not is_self))

    @tasks.loop(seconds=15)
    async def check_jail_loop():
        now = time.time()
        to_remove = []
        jail_channel = bot.get_channel(CHANNEL_NHA_TU)
        if not jail_channel: return
        guild = jail_channel.guild
        bot_top_role = guild.me.top_role.position 
        
        all_jail_data = get_all_jail_data()
        for uid_str, info in all_jail_data.items():
            if now >= info.get("end_time", 0):
                to_remove.append((uid_str, info))

        if not to_remove: return

        for uid_str, _ in to_remove: remove_jail_data(uid_str)
        await backup_sqlite_to_cloud(bot)

        for uid_str, info in to_remove:
            uid_int = int(uid_str)
            member = guild.get_member(uid_int)
            if not member:
                try: member = await guild.fetch_member(uid_int)
                except: continue

            try:
                tu_nhan_role = guild.get_role(ROLE_TU_NHAN)
                if tu_nhan_role and tu_nhan_role in member.roles and tu_nhan_role.position < bot_top_role:
                    await member.remove_roles(tu_nhan_role)
            except Exception as e: print(f"[LOOP] Lỗi tháo còng: {e}")

            try:
                roles_to_add = [guild.get_role(r_id) for r_id in info.get("old_roles", []) if guild.get_role(r_id) and guild.get_role(r_id) not in member.roles and guild.get_role(r_id).position < bot_top_role]
                if roles_to_add: await member.add_roles(*roles_to_add)
            except Exception as e: print(f"[LOOP] Lỗi trả quần áo: {e}")

            try:
                embed = discord.Embed(title="🕊️ LỆNH MÃN HẠN TÙ 🕊️", description=f"{member.mention} đã thụ án xong và được trả tự do! Hãy làm lại cuộc đời.", color=discord.Color.green())
                await jail_channel.send(embed=embed)
            except Exception: pass