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

    # Lấy thông tin Server từ kênh nhà tù
    jail_channel = bot.get_channel(CHANNEL_NHA_TU)
    if not jail_channel: return None
    guild = jail_channel.guild

    # Tìm kênh database ẩn nếu đã có sẵn
    for channel in guild.text_channels:
        if channel.name == "database-nhatu":
            DB_CHANNEL_ID = channel.id
            return channel

    # Nếu chưa có, tự động tạo kênh ẩn mới
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
        print("Lỗi tạo kênh DB:", e)
        return None

async def load_cloud_db(bot):
    global DB_MESSAGE_ID, JAIL_DATA, DB_LOADED
    if DB_LOADED: return
    
    # Quét dữ liệu từ kênh ẩn
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

    # Nếu không có trên mạng, load bằng File Local
    if not DB_MESSAGE_ID and os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                JAIL_DATA.update(json.load(f))
        except Exception: pass
    DB_LOADED = True

async def save_cloud_db(bot):
    global DB_MESSAGE_ID
    # Lưu xuống ổ cứng local dự phòng
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(JAIL_DATA, f, indent=4)
    except Exception: pass

    # Lưu lên Discord Kênh Ẩn
    db_channel = await get_db_channel(bot)
    if not db_channel: return
    
    # Gom gọn chuỗi JSON để tiết kiệm diện tích tối đa
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

class AppealView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="📝 Gửi Kháng Cáo", style=discord.ButtonStyle.primary, custom_id="btn_khang_cao")
    async def btn_khang_cao(self, interaction: discord.Interaction, button: discord.ui.Button):
        uid_str = str(interaction.user.id)
        
        if uid_str not in JAIL_DATA:
            try: await interaction.response.send_message("❌ Bạn không phải là tù nhân, kháng cáo gì tầm này?", ephemeral=True)
            except Exception: pass
            return
            
        if JAIL_DATA[uid_str].get("appealed", False):
            try: await interaction.response.send_message("❌ Bạn đã sử dụng hết quyền kháng cáo (chỉ được 1 lần duy nhất)!", ephemeral=True)
            except Exception: pass
            return
            
        JAIL_DATA[uid_str]["appealed"] = True
        await save_cloud_db(self.bot)
        
        try: await interaction.response.send_message("✅ Đơn kháng cáo đã được gửi tới hội đồng quản trị!", ephemeral=True)
        except Exception: pass
        
        button.disabled = True
        button.label = "Đã Kháng Cáo"
        try: await interaction.message.edit(view=self)
        except Exception: pass
        
        channel = interaction.guild.get_channel(CHANNEL_NHA_TU)
        if channel:
            pings = " ".join([f"<@&{r}>" for r in ADMIN_ROLES])
            embed = discord.Embed(title="⚖️ YÊU CẦU KHÁNG CÁO", description=f"Tù nhân {interaction.user.mention} mong muốn được khoan hồng!", color=discord.Color.orange())
            try: await channel.send(content=pings, embed=embed)
            except Exception: pass

def setup_nhatu(bot):
    bot.add_view(AppealView(bot))

    @bot.listen("on_ready")
    async def jail_on_ready():
        await load_cloud_db(bot)
        if not check_jail_loop.is_running():
            check_jail_loop.start()
            print("✅ Vòng lặp Nhà Tù đã khởi động an toàn!")

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

        try:
            old_roles = [r.id for r in member.roles if r.name != "@everyone" and r.id != ROLE_TU_NHAN]
            roles_to_remove = [r for r in member.roles if r.name != "@everyone"]
            if roles_to_remove:
                await member.remove_roles(*roles_to_remove)
            
            tu_nhan_role = ctx.guild.get_role(ROLE_TU_NHAN)
            if tu_nhan_role:
                await member.add_roles(tu_nhan_role)
                
        except Exception as e:
            try: await ctx.send("❌ Không thể gỡ/gán role. Bot phải có Role được xếp vị trí CAO HƠN Role của phạm nhân mới có quyền lột đồ!")
            except Exception: pass
            return

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
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="Dùng lệnh !kiemtratu để xem thời gian mãn hạn.")

        try: await ctx.send(embed=embed)
        except Exception: pass

        jail_channel = ctx.guild.get_channel(CHANNEL_NHA_TU)
        if jail_channel and ctx.channel.id != CHANNEL_NHA_TU:
            try: await jail_channel.send(f"⛓️ Chào mừng {member.mention} đã đến với nhà đá! Mức án của ngươi là **{thoi_gian}**.")
            except Exception: pass

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
        if uid not in JAIL_DATA:
            try: await ctx.send(f"⚠️ {member.display_name} hiện đang là công dân tự do, không bị giam giữ!")
            except Exception: pass
            return

        info = JAIL_DATA[uid]
        
        try:
            tu_nhan_role = ctx.guild.get_role(ROLE_TU_NHAN)
            if tu_nhan_role and tu_nhan_role in member.roles:
                await member.remove_roles(tu_nhan_role)
            
            roles_to_add = [ctx.guild.get_role(r) for r in info.get("old_roles", []) if ctx.guild.get_role(r)]
            if roles_to_add:
                await member.add_roles(*roles_to_add)
        except Exception as e:
            try: await ctx.send(f"⚠️ Đã xảy ra lỗi hệ thống khi gỡ/trả role: {e}")
            except Exception: pass

        del JAIL_DATA[uid]
        await save_cloud_db(bot)

        embed = discord.Embed(title="🕊️ LỆNH ĐẶC XÁ 🕊️", description=f"Quản ngục {ctx.author.mention} đã ký quyết định đặc xá cho {member.mention} trước thời hạn!", color=discord.Color.green())
        embed.set_thumbnail(url=member.display_avatar.url)
        
        # Chỉ gửi 1 lần vào kênh gõ lệnh hiện tại
        try: await ctx.send(embed=embed)
        except Exception: pass

    @bot.command()
    async def kiemtratu(ctx, member: discord.Member = None):
        if member and member.id != ctx.author.id:
            if not is_admin(ctx.author):
                try: await ctx.send("❌ Bạn không có quyền kiểm tra hồ sơ tù nhân của người khác!")
                except Exception: pass
                return
                
            uid = str(member.id)
            if uid not in JAIL_DATA:
                try: await ctx.send(f"✅ {member.display_name} hiện không có trong danh sách đen!")
                except Exception: pass
                return
                
            info = JAIL_DATA[uid]
            remaining = int(info["end_time"] - time.time())
            
            if remaining <= 0:
                try: await ctx.send(f"🕊️ Mức án của {member.display_name} đã hết! Hệ thống đang chuẩn bị thả người.")
                except Exception: pass
                return
                
            m, s = divmod(remaining, 60)
            h, m = divmod(m, 60)
            d, h = divmod(h, 24)
            
            time_str = ""
            if d > 0: time_str += f"{d} ngày "
            if h > 0: time_str += f"{h} giờ "
            if m > 0: time_str += f"{m} phút "
            if s > 0: time_str += f"{s} giây"
            
            appealed_status = "Đã sử dụng" if info.get("appealed", False) else "Chưa sử dụng"
            
            embed = discord.Embed(title=f"⏳ HỒ SƠ ÁN PHẠT: {member.display_name}", color=discord.Color.dark_grey())
            embed.add_field(name="Lý do phạm tội", value=info["reason"], inline=False)
            embed.add_field(name="Thời gian còn lại", value=f"**{time_str.strip()}**", inline=False)
            embed.add_field(name="Quyền kháng cáo", value=appealed_status, inline=False)
            
            try: await ctx.send(embed=embed)
            except Exception: pass
            return

        uid = str(ctx.author.id)
        if uid not in JAIL_DATA:
            try: await ctx.send("✅ Bạn đang là công dân lương thiện, không vướng bận lao lý!")
            except Exception: pass
            return
            
        info = JAIL_DATA[uid]
        remaining = int(info["end_time"] - time.time())
        
        if remaining <= 0:
            try: await ctx.send("🕊️ Mức án của bạn đã hết! Đang chờ lính canh mở cửa...")
            except Exception: pass
            return
            
        m, s = divmod(remaining, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        
        time_str = ""
        if d > 0: time_str += f"{d} ngày "
        if h > 0: time_str += f"{h} giờ "
        if m > 0: time_str += f"{m} phút "
        if s > 0: time_str += f"{s} giây"
        
        da_khang_cao = info.get("appealed", False)
        appealed_status = "Đã dùng (Hết quyền)" if da_khang_cao else "Còn 1 lần"
        
        embed = discord.Embed(title="⏳ THÔNG TIN ÁN PHẠT", color=discord.Color.dark_grey())
        embed.add_field(name="Lý do phạm tội", value=info["reason"], inline=False)
        embed.add_field(name="Thời gian còn lại", value=f"**{time_str.strip()}**", inline=False)
        embed.add_field(name="Trạng thái kháng cáo", value=appealed_status, inline=False)
        
        view_to_send = None if da_khang_cao else AppealView(bot)
        
        try: await ctx.send(embed=embed, view=view_to_send)
        except Exception: pass

    @tasks.loop(seconds=15)
    async def check_jail_loop():
        now = time.time()
        to_remove = []
        
        for uid, info in list(JAIL_DATA.items()):
            if now >= info["end_time"]:
                to_remove.append(uid)
                try:
                    for guild in bot.guilds:
                        member = guild.get_member(int(uid))
                        if member:
                            tu_nhan_role = guild.get_role(ROLE_TU_NHAN)
                            if tu_nhan_role in member.roles:
                                await member.remove_roles(tu_nhan_role)
                            
                            roles_to_add = [guild.get_role(r) for r in info["old_roles"] if guild.get_role(r)]
                            if roles_to_add:
                                await member.add_roles(*roles_to_add)
                            
                            jail_channel = guild.get_channel(CHANNEL_NHA_TU)
                            if jail_channel:
                                embed = discord.Embed(title="🕊️ LỆNH ÂN XÁ 🕊️", description=f"{member.mention} đã mãn hạn tù và được trả tự do! Hãy làm lại cuộc đời.", color=discord.Color.green())
                                await jail_channel.send(embed=embed)
                            break
                except Exception as e:
                    print(f"Lỗi ân xá cho {uid}: {e}")
        
        for uid in to_remove:
            del JAIL_DATA[uid]
        if to_remove:
            await save_cloud_db(bot)