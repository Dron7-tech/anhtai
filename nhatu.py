import discord
from discord.ext import tasks
import json
import os
import time

ROLE_TU_NHAN = 1552465079381921802
CHANNEL_NHA_TU = 1552432404730486864
ADMIN_ROLES = [1438895205012082812, 1438865272315445258]
DATA_FILE = "jail_data.json"

# Biến bộ nhớ lưu trữ Cloud Database
JAIL_DATA = {}
DB_MESSAGE_ID = None
DB_CHANNEL_ID = None
DB_LOADED = False

async def get_db_channel(bot):
    global DB_CHANNEL_ID
    if DB_CHANNEL_ID:
        return bot.get_channel(DB_CHANNEL_ID)

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
        if role:
            overwrites[role] = discord.PermissionOverwrite(read_messages=True)

    try:
        new_channel = await guild.create_text_channel("database-nhatu", overwrites=overwrites, category=jail_channel.category)
        DB_CHANNEL_ID = new_channel.id
        return new_channel
    except Exception as e:
        print(f"[DB] Lỗi tạo kênh DB: {e}")
        return None

async def load_cloud_db(bot):
    global DB_MESSAGE_ID, JAIL_DATA, DB_LOADED
    if DB_LOADED: return
    
    db_channel = await get_db_channel(bot)
    if db_channel:
        try:
            async for msg in db_channel.history(limit=20):
                if msg.author == bot.user and "🔒 [DATABASE_NHA_TU]" in msg.content:
                    DB_MESSAGE_ID = msg.id
                    try:
                        json_str = msg.content.split("```json\n")[1].split("\n```")[0]
                        JAIL_DATA.update(json.loads(json_str))
                        print("✅ Đã khôi phục dữ liệu Nhà tù từ Kênh Database Ẩn!")
                    except Exception: pass
                    break
        except Exception: pass

    if not DB_MESSAGE_ID and os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                JAIL_DATA.update(json.load(f))
        except Exception: pass
    DB_LOADED = True

async def save_cloud_db(bot):
    global DB_MESSAGE_ID
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(JAIL_DATA, f, indent=4)
    except Exception: pass

    db_channel = await get_db_channel(bot)
    if not db_channel: return
    
    content = f"🔒 [DATABASE_NHA_TU] - Dữ liệu chống mất trí nhớ của hệ thống. KHÔNG XÓA!\n```json\n{json.dumps(JAIL_DATA)}\n```"
    
    if DB_MESSAGE_ID:
        try:
            msg = await db_channel.fetch_message(DB_MESSAGE_ID)
            await msg.edit(content=content)
            return
        except Exception:
            DB_MESSAGE_ID = None
    
    try:
        async for msg in db_channel.history(limit=20):
            if msg.author == bot.user and "🔒 [DATABASE_NHA_TU]" in msg.content:
                await msg.edit(content=content)
                DB_MESSAGE_ID = msg.id
                return
        msg = await db_channel.send(content)
        DB_MESSAGE_ID = msg.id
    except Exception: pass

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
        if role.id in ADMIN_ROLES:
            return True
    return False

# ==========================================
# LỚP GIAO DIỆN KHÁNG CÁO
# ==========================================
class AppealView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="📝 Gửi Kháng Cáo", style=discord.ButtonStyle.primary, custom_id="btn_khang_cao")
    async def btn_khang_cao(self, interaction: discord.Interaction, button: discord.ui.Button):
        uid_str = str(interaction.user.id)
        
        try:
            info = JAIL_DATA.get(uid_str)
            if not info:
                await interaction.response.send_message("❌ Bạn không phải là tù nhân, kháng cáo gì tầm này?", ephemeral=True)
                return
                
            if info.get("appealed", False):
                await interaction.response.send_message("❌ Bạn đã sử dụng hết quyền kháng cáo (chỉ được 1 lần duy nhất)!", ephemeral=True)
                return
                
            JAIL_DATA[uid_str]["appealed"] = True
            await save_cloud_db(self.bot)
            
            await interaction.response.send_message("✅ Đơn kháng cáo đã được gửi tới hội đồng quản trị!", ephemeral=True)
            
            button.disabled = True
            button.label = "Đã Kháng Cáo"
            await interaction.message.edit(view=self)
            
            channel = interaction.guild.get_channel(CHANNEL_NHA_TU)
            if channel:
                pings = " ".join([f"<@&{r}>" for r in ADMIN_ROLES])
                embed = discord.Embed(
                    title="⚖️ ĐƠN XIN KHOAN HỒNG", 
                    description=f"Phạm nhân {interaction.user.mention} đã đệ đơn xin giảm án/đặc xá!", 
                    color=discord.Color.orange()
                )
                embed.add_field(name="Tội danh hiện tại", value=info.get("reason", "Không rõ"), inline=False)
                embed.set_thumbnail(url=interaction.user.display_avatar.url)
                embed.set_footer(text="Admin dùng lệnh !unjail @tên để duyệt đặc xá.")
                
                await channel.send(content=pings, embed=embed)
                
        except Exception as e:
            print(f"[APPEAL] Lỗi trong quá trình kháng cáo: {e}")

# ==========================================
# KHỞI TẠO MODULE
# ==========================================
def setup_nhatu(bot):
    bot.add_view(AppealView(bot))

    @bot.listen("on_ready")
    async def jail_on_ready():
        await load_cloud_db(bot)
        if not check_jail_loop.is_running():
            check_jail_loop.start()
            print("✅ Vòng lặp Nhà Tù đã khởi động an toàn!")

    # ==========================================
    # LỆNH BỎ TÙ (!jail)
    # ==========================================
    @bot.command()
    async def jail(ctx, member: discord.Member = None, thoi_gian: str = None, *, li_do: str = "Không có lý do"):
        if not is_admin(ctx.author):
            try: await ctx.send("❌ Bạn không có quyền bỏ tù người khác!")
            except Exception: pass
            return
            
        if not member or not thoi_gian:
            try: await ctx.send("⚠️ Sai cú pháp! Hãy dùng: `!jail [@người_dùng] [thời_gian: 10m/2h/1d] [lý do]`")
            except Exception: pass
            return

        if is_admin(member):
            try: await ctx.send("❌ Luật pháp không áp dụng lên các vị thần! Không thể bỏ tù người quản lý khác.")
            except Exception: pass
            return
            
        duration = parse_time(thoi_gian)
        if not duration:
            try: await ctx.send("❌ Định dạng thời gian sai. Dùng `m` (phút), `h` (giờ), `d` (ngày). Ví dụ: `10m`.")
            except Exception: pass
            return

        bot_top_role = ctx.guild.me.top_role.position
        old_roles = []
        roles_to_remove = []
        unremovable_roles = []

        for role in member.roles:
            if role.name == "@everyone" or role.id == ROLE_TU_NHAN:
                continue
                
            old_roles.append(role.id)
            
            if role.position < bot_top_role:
                roles_to_remove.append(role)
            else:
                unremovable_roles.append(role)

        try:
            if roles_to_remove:
                await member.remove_roles(*roles_to_remove)
                
            tu_nhan_role = ctx.guild.get_role(ROLE_TU_NHAN)
            if tu_nhan_role and tu_nhan_role.position < bot_top_role:
                await member.add_roles(tu_nhan_role)
                
        except Exception as e:
            print(f"[JAIL] Lỗi gỡ/gán role cho {member.display_name}: {e}")
            try: await ctx.send("⚠️ Có lỗi khi lột đồ phạm nhân, có thể do lỗi API hoặc Bot chưa đủ quyền cao nhất. Vẫn sẽ tiến hành giam giữ logic!")
            except Exception: pass

        end_time = time.time() + duration
        JAIL_DATA[str(member.id)] = {
            "end_time": end_time,
            "old_roles": old_roles,
            "reason": li_do,
            "appealed": False
        }
        await save_cloud_db(bot)

        embed = discord.Embed(title="🚨 LỆNH BẮT GIỮ 🚨", color=discord.Color.dark_red())
        embed.add_field(name="Tội phạm", value=member.mention, inline=True)
        embed.add_field(name="Người bắt", value=ctx.author.mention, inline=True)
        embed.add_field(name="Mức án", value=thoi_gian, inline=True)
        embed.add_field(name="Lý do", value=li_do, inline=False)
        if unremovable_roles:
            unremovable_names = ", ".join([r.name for r in unremovable_roles])
            embed.add_field(name="⚠️ Báo cáo ngục tốt", value=f"Phạm nhân có chức sắc quá lớn, không thể lột các role: {unremovable_names}", inline=False)
            
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="Dùng lệnh !kiemtratu để xem thời gian mãn hạn.")

        try: await ctx.send(embed=embed)
        except Exception as e: print(f"Lỗi gửi thông báo jail: {e}")

        jail_channel = ctx.guild.get_channel(CHANNEL_NHA_TU)
        if jail_channel and ctx.channel.id != CHANNEL_NHA_TU:
            try: await jail_channel.send(f"⛓️ Chào mừng {member.mention} đã đến với nhà đá! Mức án của ngươi là **{thoi_gian}**.")
            except Exception: pass

    # ==========================================
    # LỆNH ĐẶC XÁ (!unjail)
    # ==========================================
    @bot.command()
    async def unjail(ctx, member: discord.Member = None):
        if not is_admin(ctx.author):
            try: await ctx.send("❌ Bạn không có quyền ân xá người khác!")
            except Exception: pass
            return
            
        if not member:
            try: await ctx.send("⚠️ Hãy tag người cần ân xá! Cú pháp: `!unjail [@người_dùng]`")
            except Exception: pass
            return

        uid = str(member.id)
        info = JAIL_DATA.get(uid)
        if not info:
            try: await ctx.send(f"⚠️ {member.display_name} hiện đang là công dân tự do, không bị giam giữ!")
            except Exception: pass
            return

        bot_top_role = ctx.guild.me.top_role.position
        
        try:
            tu_nhan_role = ctx.guild.get_role(ROLE_TU_NHAN)
            if tu_nhan_role and tu_nhan_role in member.roles and tu_nhan_role.position < bot_top_role:
                await member.remove_roles(tu_nhan_role)
            
            roles_to_add = []
            for r_id in info.get("old_roles", []):
                r = ctx.guild.get_role(r_id)
                if r and r not in member.roles and r.position < bot_top_role:
                    roles_to_add.append(r)
                    
            if roles_to_add:
                await member.add_roles(*roles_to_add)
                
        except Exception as e:
            print(f"[UNJAIL] Lỗi gỡ/trả role cho {member.display_name}: {e}")
            try: await ctx.send("⚠️ Đã xảy ra lỗi hệ thống khi trả lại quần áo cho phạm nhân (Hierarchy Limit).")
            except Exception: pass

        del JAIL_DATA[uid]
        await save_cloud_db(bot)

        embed = discord.Embed(title="🕊️ LỆNH ĐẶC XÁ 🕊️", description=f"Quản ngục {ctx.author.mention} đã ký quyết định đặc xá cho {member.mention} trước thời hạn!", color=discord.Color.green())
        embed.set_thumbnail(url=member.display_avatar.url)
        
        try: await ctx.send(embed=embed)
        except Exception: pass

    # ==========================================
    # LỆNH KIỂM TRA THÔNG TIN (!kiemtratu)
    # ==========================================
    @bot.command()
    async def kiemtratu(ctx, member: discord.Member = None):
        if member and member.id != ctx.author.id:
            if not is_admin(ctx.author):
                try: await ctx.send("❌ Bạn không có quyền kiểm tra hồ sơ tù nhân của người khác!")
                except Exception: pass
                return
                
            uid = str(member.id)
            info = JAIL_DATA.get(uid)
            if not info:
                try: await ctx.send(f"✅ {member.display_name} hiện không có trong danh sách đen!")
                except Exception: pass
                return
                
            remaining = int(info["end_time"] - time.time())
            if remaining <= 0:
                try: await ctx.send(f"🕊️ Mức án của {member.display_name} đã hết! Hệ thống đang chuẩn bị thả người.")
                except Exception: pass
                return
                
            m, s = divmod(remaining, 60)
            h, m = divmod(m, 60)
            d, h = divmod(h, 24)
            
            time_str = f"{d} ngày " if d > 0 else ""
            time_str += f"{h} giờ " if h > 0 else ""
            time_str += f"{m} phút " if m > 0 else ""
            time_str += f"{s} giây" if s > 0 else ""
            
            appealed_status = "Đã sử dụng" if info.get("appealed", False) else "Chưa sử dụng"
            
            embed = discord.Embed(title=f"⏳ HỒ SƠ ÁN PHẠT: {member.display_name}", color=discord.Color.dark_grey())
            embed.add_field(name="Lý do phạm tội", value=info.get("reason", "Không rõ"), inline=False)
            embed.add_field(name="Thời gian còn lại", value=f"**{time_str.strip()}**", inline=False)
            embed.add_field(name="Quyền kháng cáo", value=appealed_status, inline=False)
            
            try: await ctx.send(embed=embed)
            except Exception: pass
            return

        uid = str(ctx.author.id)
        info = JAIL_DATA.get(uid)
        
        if not info:
            try: await ctx.send("✅ Bạn đang là công dân lương thiện, không vướng bận lao lý!")
            except Exception: pass
            return
            
        remaining = int(info["end_time"] - time.time())
        if remaining <= 0:
            try: await ctx.send("🕊️ Mức án của bạn đã hết! Đang chờ lính canh mở cửa...")
            except Exception: pass
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
        
        embed = discord.Embed(title="⏳ THÔNG TIN ÁN PHẠT", color=discord.Color.dark_grey())
        embed.add_field(name="Lý do phạm tội", value=info.get("reason", "Không rõ"), inline=False)
        embed.add_field(name="Thời gian còn lại", value=f"**{time_str.strip()}**", inline=False)
        embed.add_field(name="Trạng thái kháng cáo", value=appealed_status, inline=False)
        
        view_to_send = None if da_khang_cao else AppealView(bot)
        
        try: await ctx.send(embed=embed, view=view_to_send)
        except Exception: pass

    # ==========================================
    # VÒNG LẶP KIỂM TRA THỜI HẠN VÀ TỰ ĐỘNG THẢ
    # ==========================================
    @tasks.loop(seconds=60)
    async def check_jail_loop():
        now = time.time()
        to_remove = []
        
        # 1. Tìm Guild chứa kênh nhà tù
        jail_channel = bot.get_channel(CHANNEL_NHA_TU)
        if not jail_channel: return
        guild = jail_channel.guild
        bot_top_role = guild.me.top_role.position 
        
        # 2. Lọc ra những người ĐÃ HẾT HẠN TÙ
        for uid, info in list(JAIL_DATA.items()):
            if now >= info.get("end_time", 0):
                to_remove.append((uid, info))

        if not to_remove: return

        # 3. XÓA NGAY LẬP TỨC khỏi JAIL_DATA và Cloud DB để tránh Đệ Quy
        for uid, _ in to_remove:
            if uid in JAIL_DATA:
                del JAIL_DATA[uid]
        await save_cloud_db(bot)

        # 4. Bắt đầu tiến trình Thả Người (Đã an toàn cách ly)
        for uid_str, info in to_remove:
            uid_int = int(uid_str)
            member = guild.get_member(uid_int)
            
            # GIẢI QUYẾT LỖI CACHE: Nếu get_member thất bại, fetch trực tiếp
            if not member:
                try:
                    member = await guild.fetch_member(uid_int)
                except discord.NotFound:
                    print(f"[LOOP] Phạm nhân {uid_str} đã rời khỏi Server. Đã xóa hồ sơ.")
                    continue 
                except Exception as e:
                    print(f"[LOOP] Lỗi Fetch Member {uid_str}: {e}")
                    continue

            # ISOLATION 1: Tháo còng (Gỡ Role Tù)
            try:
                tu_nhan_role = guild.get_role(ROLE_TU_NHAN)
                if tu_nhan_role and tu_nhan_role in member.roles and tu_nhan_role.position < bot_top_role:
                    await member.remove_roles(tu_nhan_role)
            except Exception as e:
                print(f"[LOOP] Lỗi tháo còng cho {member.display_name}: {e}")

            # ISOLATION 2: Trả lại đồ đạc (Trả Role Cũ)
            try:
                roles_to_add = []
                for r_id in info.get("old_roles", []):
                    r = guild.get_role(r_id)
                    if r and r not in member.roles and r.position < bot_top_role:
                        roles_to_add.append(r)
                        
                if roles_to_add:
                    await member.add_roles(*roles_to_add)
            except Exception as e:
                print(f"[LOOP] Lỗi trả quần áo cho {member.display_name}: {e}")

            # ISOLATION 3: Gửi giấy ra trại (Thông báo)
            try:
                embed = discord.Embed(
                    title="🕊️ LỆNH MÃN HẠN TÙ 🕊️", 
                    description=f"{member.mention} đã thụ án xong và được trả tự do! Hãy làm lại cuộc đời.", 
                    color=discord.Color.green()
                )
                await jail_channel.send(embed=embed)
            except Exception as e:
                print(f"[LOOP] Lỗi gửi thông báo thả {member.display_name}: {e}")