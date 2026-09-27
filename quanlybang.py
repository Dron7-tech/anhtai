import discord
from discord import app_commands
import sqlite3
import json
import os
import glob
import time

DB_FILE = "bang_thang.db"
CHANNEL_NHA_TU = 1552432404730486864 
ADMIN_ROLES = [1438895205012082812, 1438865272315445258]
DANH_SACH_QUAN_LY = [1028173204029722696, 999988887777666655]

conn = None
cursor = None
DB_CHANNEL_ID = None
DB_LOADED = False

def co_quyen_quan_ly(user):
    if user.guild_permissions.administrator: return True
    if user.id in DANH_SACH_QUAN_LY: return True
    return False

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
    return None

async def init_sqlite(bot):
    global conn, cursor, DB_LOADED
    if DB_LOADED: return
    db_channel = await get_db_channel(bot)
    
    if db_channel:
        try:
            async for msg in db_channel.history(limit=20):
                if msg.author == bot.user and "🔒 [DATABASE_BANG_THANG]" in msg.content and msg.attachments:
                    att = msg.attachments[0]
                    if att.filename == DB_FILE:
                        await att.save(DB_FILE)
                        print("✅ Đã khôi phục SQLite Bảng Duy Trì từ Discord Cloud!")
                        break
        except Exception as e: print(f"[BANG_DB] Lỗi tải DB: {e}")

    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bang_duy_tri (
            thang TEXT,
            id_hoac_ten TEXT,
            name TEXT,
            status INTEGER,
            PRIMARY KEY (thang, id_hoac_ten)
        )
    ''')
    conn.commit()

    migrated = False
    for json_file in glob.glob("bang_thang_*.json"):
        if "backup" in json_file: continue
        try:
            thang = json_file.replace("bang_thang_", "").replace(".json", "")
            with open(json_file, "r", encoding="utf-8") as f:
                old_data = json.load(f)
                for k, v in old_data.items():
                    name = v.get("name", k)
                    status = 1 if v.get("status", False) else 0
                    cursor.execute("INSERT OR IGNORE INTO bang_duy_tri VALUES (?, ?, ?, ?)", (thang, k, name, status))
            conn.commit()
            os.rename(json_file, json_file + ".backup") 
            migrated = True
        except Exception: pass
            
    if migrated:
        print("✅ Đã dọn dẹp xong file JSON rác và hút vào SQLite!")
        await backup_sqlite_to_cloud(bot)

    DB_LOADED = True

async def backup_sqlite_to_cloud(bot):
    if not conn: return
    conn.commit()
    db_channel = await get_db_channel(bot)
    if not db_channel: return
    try:
        async for msg in db_channel.history(limit=10):
            if msg.author == bot.user and "🔒 [DATABASE_BANG_THANG]" in msg.content:
                await msg.delete()
        file = discord.File(DB_FILE)
        await db_channel.send(content="🔒 [DATABASE_BANG_THANG] - Dữ liệu Lõi Bảng Duy Trì Server", file=file)
    except Exception as e: print(f"[BANG_DB] Lỗi Backup lên mây: {e}")

def get_bang_data(thang):
    cursor.execute("SELECT id_hoac_ten, name, status FROM bang_duy_tri WHERE thang = ?", (str(thang),))
    rows = cursor.fetchall()
    data = {}
    for row in rows:
        data[row[0]] = {"name": row[1], "status": bool(row[2])}
    return data

def add_user_to_bang(thang, id_hoac_ten, name, status=False):
    cursor.execute("INSERT OR REPLACE INTO bang_duy_tri (thang, id_hoac_ten, name, status) VALUES (?, ?, ?, ?)", 
                   (str(thang), str(id_hoac_ten), name, int(status)))
    conn.commit()

def remove_user_from_bang(thang, id_hoac_ten):
    cursor.execute("DELETE FROM bang_duy_tri WHERE thang = ? AND id_hoac_ten = ?", (str(thang), str(id_hoac_ten)))
    conn.commit()

def tao_embed_bang(thang, data):
    embed = discord.Embed(title=f"📊 BẢNG DUY TRÌ SERVER - THÁNG {thang}", color=discord.Color.blue())
    chuoi_hien_thi = ""
    for id_hoac_ten, info in data.items():
        trang_thai = "✅ Đã đóng" if info["status"] else "❌ Chưa đóng"
        chuoi_hien_thi += f"• {id_hoac_ten}: {trang_thai}\n"
    embed.description = chuoi_hien_thi if chuoi_hien_thi else "Danh sách đang trống."
    return embed

class BangDieuKhienBiMat(discord.ui.View):
    def __init__(self, bot, thang, data, tin_nhan_public):
        super().__init__(timeout=None)
        self.bot = bot
        self.thang = str(thang)
        self.tin_nhan_public = tin_nhan_public
        self.nguoi_chon = None
        
        options = []
        for id_hoac_ten, info in data.items():
            ten = str(info.get("name", id_hoac_ten))[:95]
            val = str(id_hoac_ten)[:95]
            if not ten.strip(): ten = "Unknown"
            if not val.strip(): val = "Unknown_Val"
            options.append(discord.SelectOption(label=ten, value=val))
                
        if not options: options.append(discord.SelectOption(label="Trống", value="none"))
        self.menu = discord.ui.Select(placeholder="1. Chọn người chơi ở đây...", options=options[:25])
        self.menu.callback = self.khi_chon_menu
        self.add_item(self.menu)

    async def khi_chon_menu(self, interaction: discord.Interaction):
        self.nguoi_chon = self.menu.values[0]
        try: await interaction.response.defer()
        except Exception: pass

    async def cap_nhat_giao_dien(self, interaction, thong_bao):
        data = get_bang_data(self.thang)
        try: await self.tin_nhan_public.edit(embed=tao_embed_bang(self.thang, data))
        except Exception: pass
        try: await interaction.edit_original_response(content=thong_bao, view=BangDieuKhienBiMat(self.bot, self.thang, data, self.tin_nhan_public))
        except Exception: pass

    @discord.ui.button(label="2. ✅ Tick", style=discord.ButtonStyle.success)
    async def nut_da_dong(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.nguoi_chon or self.nguoi_chon == "none":
            try: await interaction.response.send_message("⚠️ Vui lòng chọn 1 người từ Menu!", ephemeral=True, delete_after=3.0)
            except Exception: pass
            return
        try: await interaction.response.defer()
        except Exception: pass
        
        data = get_bang_data(self.thang)
        if self.nguoi_chon in data:
            add_user_to_bang(self.thang, self.nguoi_chon, data[self.nguoi_chon]["name"], True)
            await backup_sqlite_to_cloud(self.bot)
            await self.cap_nhat_giao_dien(interaction, "✅ Đã đánh dấu Đã Đóng!")

    @discord.ui.button(label="2. ❌ Bỏ Tick", style=discord.ButtonStyle.danger)
    async def nut_chua_dong(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.nguoi_chon or self.nguoi_chon == "none":
            try: await interaction.response.send_message("⚠️ Vui lòng chọn 1 người từ Menu!", ephemeral=True, delete_after=3.0)
            except Exception: pass
            return
        try: await interaction.response.defer()
        except Exception: pass
        
        data = get_bang_data(self.thang)
        if self.nguoi_chon in data:
            add_user_to_bang(self.thang, self.nguoi_chon, data[self.nguoi_chon]["name"], False)
            await backup_sqlite_to_cloud(self.bot)
            await self.cap_nhat_giao_dien(interaction, "❌ Đã Reset về Chưa Đóng!")

    @discord.ui.button(label="3. 🗑️ Xóa", style=discord.ButtonStyle.secondary)
    async def nut_xoa(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.nguoi_chon or self.nguoi_chon == "none":
            try: await interaction.response.send_message("⚠️ Vui lòng chọn 1 người từ Menu!", ephemeral=True, delete_after=3.0)
            except Exception: pass
            return
        try: await interaction.response.defer()
        except Exception: pass
        
        remove_user_from_bang(self.thang, self.nguoi_chon)
        await backup_sqlite_to_cloud(self.bot)
        await self.cap_nhat_giao_dien(interaction, "🗑️ Đã xóa người này khỏi danh sách!")

class NutGoiDieuKhien(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="⚙️ Mở Bảng Điều Khiển", style=discord.ButtonStyle.primary, custom_id="nut_quan_ly_vinh_vien")
    async def mo_bang_dieu_khien(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not co_quyen_quan_ly(interaction.user):
            try: await interaction.response.send_message("❌ Bạn không có quyền truy cập!", ephemeral=True, delete_after=3.0)
            except Exception: pass
            return
            
        try: 
            if not interaction.message.embeds or not interaction.message.embeds[0].title:
                await interaction.response.send_message("❌ Bảng điều khiển cũ đã hỏng hoặc không có dữ liệu!", ephemeral=True)
                return
                
            thang = interaction.message.embeds[0].title.split("THÁNG ")[-1].strip()
            data = get_bang_data(thang)
            
            await interaction.response.send_message(
                content=f"🛠️ **Khu vực quản lý (Chỉ bạn nhìn thấy) - Tháng {thang}**\nHãy chọn người cần cập nhật:", 
                view=BangDieuKhienBiMat(self.bot, thang, data, interaction.message), 
                ephemeral=True
            )
        except Exception as e: print(f"Lỗi mở bảng điều khiển: {e}", flush=True)

# ==========================================
# KHỞI TẠO SLASH COMMANDS
# ==========================================
def setup_bang(bot):
    bot.add_view(NutGoiDieuKhien(bot))

    @bot.listen("on_ready")
    async def bang_on_ready():
        await init_sqlite(bot)

    @bot.tree.command(name="taobang", description="Tạo hoặc cập nhật bảng duy trì server")
    @app_commands.describe(thang="Tháng (VD: 9)", danh_sach="Tên người hoặc Tag (cách nhau bằng dấu phẩy)")
    async def slash_taobang(interaction: discord.Interaction, thang: str, danh_sach: str = ""):
        if not co_quyen_quan_ly(interaction.user):
            await interaction.response.send_message("❌ Bạn không có quyền truy cập lệnh này!", ephemeral=True)
            return
        
        await interaction.response.defer()
        data = get_bang_data(thang)
        if danh_sach:
            cac_thanh_vien = [ten.strip() for ten in danh_sach.split(',')] if ',' in danh_sach else [ten.strip() for ten in danh_sach.split()]
            for chuoi_nhap in cac_thanh_vien:
                if chuoi_nhap:
                    ten_hien_thi = chuoi_nhap
                    # Dịch Tag <@123> thành Tên thật
                    if chuoi_nhap.startswith("<@") and chuoi_nhap.endswith(">"):
                        uid_str = chuoi_nhap.strip("<@!>")
                        try:
                            member = interaction.guild.get_member(int(uid_str))
                            if member: ten_hien_thi = member.display_name
                        except: pass

                    if chuoi_nhap not in data:
                        add_user_to_bang(thang, chuoi_nhap, ten_hien_thi, False)
                        data[chuoi_nhap] = {"name": ten_hien_thi, "status": False}
            await backup_sqlite_to_cloud(bot)

        embed_moi = tao_embed_bang(thang, data)
        da_xu_ly = False
        try:
            async for msg in interaction.channel.history(limit=100):
                if msg.author == bot.user and msg.embeds:
                    if msg.embeds[0].title == f"📊 BẢNG DUY TRÌ SERVER - THÁNG {thang}":
                        try: await msg.edit(embed=embed_moi, view=NutGoiDieuKhien(bot))
                        except: pass
                        da_xu_ly = True
                        break 
        except Exception: pass
        
        if not da_xu_ly:
            await interaction.followup.send(embed=embed_moi, view=NutGoiDieuKhien(bot))
        else:
            await interaction.followup.send("✅ Bảng đã được cập nhật thành công ở tin nhắn cũ!", ephemeral=True)

    @bot.tree.command(name="copybang", description="Sao chép dữ liệu bảng sang tháng mới")
    @app_commands.describe(thang_cu="Tháng cũ (VD: 9)", thang_moi="Tháng mới (VD: 10)")
    async def slash_copybang(interaction: discord.Interaction, thang_cu: str, thang_moi: str):
        if not co_quyen_quan_ly(interaction.user):
            await interaction.response.send_message("❌ Bạn không có quyền truy cập lệnh này!", ephemeral=True)
            return
        
        data_cu = get_bang_data(thang_cu)
        if not data_cu: 
            await interaction.response.send_message(f"⚠️ Không tìm thấy dữ liệu của tháng {thang_cu}!", ephemeral=True)
            return
            
        await interaction.response.defer()
        data_moi = get_bang_data(thang_moi)
        for id_hoac_ten, info in data_cu.items():
            if id_hoac_ten not in data_moi: 
                add_user_to_bang(thang_moi, id_hoac_ten, info["name"], False)
                data_moi[id_hoac_ten] = {"name": info["name"], "status": False}
                
        await backup_sqlite_to_cloud(bot)
        await interaction.followup.send(f"✅ Đã sao chép danh sách sang **tháng {thang_moi}**!\n", embed=tao_embed_bang(thang_moi, data_moi), view=NutGoiDieuKhien(bot))