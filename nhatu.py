import discord
from discord.ext import tasks
import json
import os
import time

ROLE_TU_NHAN = 1552465079381921802
CHANNEL_NHA_TU = 1552432404730486864
ADMIN_ROLES = [1438895205012082812, 1438865272315445258]
DATA_FILE = "jail_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception: pass
    return {}

def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
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
# NÚT GIAO DIỆN KHÁNG CÁO
# ==========================================
class AppealView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📝 Gửi Kháng Cáo", style=discord.ButtonStyle.primary, custom_id="btn_khang_cao")
    async def btn_khang_cao(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = load_data()
        if str(interaction.user.id) not in data:
            try: await interaction.response.send_message("❌ Bạn không phải là tù nhân, kháng cáo gì tầm này?", ephemeral=True)
            except Exception: pass
            return
        
        try: await interaction.response.send_message("✅ Đơn kháng cáo đã được gửi tới hội đồng quản trị!", ephemeral=True)
        except Exception: pass
        
        channel = interaction.guild.get_channel(CHANNEL_NHA_TU)
        if channel:
            pings = " ".join([f"<@&{r}>" for r in ADMIN_ROLES])
            embed = discord.Embed(title="⚖️ YÊU CẦU KHÁNG CÁO", description=f"Tù nhân {interaction.user.mention} mong muốn được khoan hồng!", color=discord.Color.orange())
            try: await channel.send(content=pings, embed=embed)
            except Exception: pass

# ==========================================
# TÍCH HỢP HỆ THỐNG VÀO BOT
# ==========================================
def setup_nhatu(bot):
    jail_data = load_data()
    bot.add_view(AppealView())

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
            # Sao lưu role cũ (Bỏ qua @everyone và role Tù Nhân cũ nếu có)
            old_roles = [r.id for r in member.roles if r.name != "@everyone" and r.id != ROLE_TU_NHAN]
            
            # Gỡ tất cả role cũ của người đó
            roles_to_remove = [r for r in member.roles if r.name != "@everyone"]
            if roles_to_remove:
                await member.remove_roles(*roles_to_remove)
            
            # Gán role Tù Nhân
            tu_nhan_role = ctx.guild.get_role(ROLE_TU_NHAN)
            if tu_nhan_role:
                await member.add_roles(tu_nhan_role)
                
        except Exception as e:
            try: await ctx.send("❌ Không thể gỡ/gán role. Bot phải có Role được xếp vị trí CAO HƠN Role của phạm nhân mới có quyền lột đồ!")
            except Exception: pass
            return

        # Lưu dữ liệu vào file JSON để không bị mất khi sập bot
        end_time = time.time() + duration
        jail_data[str(member.id)] = {
            "end_time": end_time,
            "old_roles": old_roles,
            "reason": li_do
        }
        save_data(jail_data)

        # Thông báo Embed
        embed = discord.Embed(title="🚨 LỆNH BẮT GIỮ 🚨", color=discord.Color.dark_red())
        embed.add_field(name="Tội phạm", value=member.mention, inline=True)
        embed.add_field(name="Người bắt", value=ctx.author.mention, inline=True)
        embed.add_field(name="Mức án", value=thoi_gian, inline=True)
        embed.add_field(name="Lý do", value=li_do, inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="Dùng lệnh !kiemtratu để xem thời gian mãn hạn.")

        try: await ctx.send(embed=embed)
        except Exception: pass

        # Gửi thêm 1 câu vào kênh nhà tù cho không khí
        jail_channel = ctx.guild.get_channel(CHANNEL_NHA_TU)
        if jail_channel:
            try: await jail_channel.send(f"⛓️ Chào mừng {member.mention} đã đến với nhà đá! Mức án của ngươi là **{thoi_gian}**.")
            except Exception: pass

    # ==========================================
    # LỆNH ĐẶC XÁ (UNJAIL)
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
        if uid not in jail_data:
            try: await ctx.send(f"⚠️ {member.display_name} hiện đang là công dân tự do, không bị giam giữ!")
            except Exception: pass
            return

        info = jail_data[uid]
        
        try:
            # Gỡ role tù nhân
            tu_nhan_role = ctx.guild.get_role(ROLE_TU_NHAN)
            if tu_nhan_role and tu_nhan_role in member.roles:
                await member.remove_roles(tu_nhan_role)
            
            # Trả lại toàn bộ role cũ cho họ
            roles_to_add = [ctx.guild.get_role(r) for r in info.get("old_roles", []) if ctx.guild.get_role(r)]
            if roles_to_add:
                await member.add_roles(*roles_to_add)
        except Exception as e:
            try: await ctx.send(f"⚠️ Đã xảy ra lỗi hệ thống khi gỡ/trả role: {e}")
            except Exception: pass

        # Xóa hồ sơ phạm nhân khỏi hệ thống
        del jail_data[uid]
        save_data(jail_data)

        # Gửi thông báo đặc xá
        embed = discord.Embed(title="🕊️ LỆNH ĐẶC XÁ 🕊️", description=f"Quản ngục {ctx.author.mention} đã ký quyết định đặc xá cho {member.mention} trước thời hạn!", color=discord.Color.green())
        embed.set_thumbnail(url=member.display_avatar.url)
        
        try: await ctx.send(embed=embed)
        except Exception: pass
        
        jail_channel = ctx.guild.get_channel(CHANNEL_NHA_TU)
        if jail_channel:
            try: await jail_channel.send(embed=embed)
            except Exception: pass


    @bot.command()
    async def kiemtratu(ctx):
        uid = str(ctx.author.id)
        if uid not in jail_data:
            try: await ctx.send("✅ Bạn đang là công dân lương thiện, không vướng bận lao lý!")
            except Exception: pass
            return
            
        info = jail_data[uid]
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
        
        embed = discord.Embed(title="⏳ THÔNG TIN ÁN PHẠT", color=discord.Color.dark_grey())
        embed.add_field(name="Lý do phạm tội", value=info["reason"], inline=False)
        embed.add_field(name="Thời gian còn lại", value=f"**{time_str.strip()}**", inline=False)
        
        try: await ctx.send(embed=embed, view=AppealView())
        except Exception: pass


    # Tiến trình ngầm tự động quét và ân xá mỗi 15 giây
    @tasks.loop(seconds=15)
    async def check_jail_loop():
        now = time.time()
        to_remove = []
        
        for uid, info in list(jail_data.items()):
            if now >= info["end_time"]:
                to_remove.append(uid)
                try:
                    for guild in bot.guilds:
                        member = guild.get_member(int(uid))
                        if member:
                            # Gỡ role tù nhân
                            tu_nhan_role = guild.get_role(ROLE_TU_NHAN)
                            if tu_nhan_role in member.roles:
                                await member.remove_roles(tu_nhan_role)
                            
                            # Trả lại toàn bộ role cũ cho họ
                            roles_to_add = [guild.get_role(r) for r in info["old_roles"] if guild.get_role(r)]
                            if roles_to_add:
                                await member.add_roles(*roles_to_add)
                            
                            # Thông báo thả người
                            jail_channel = guild.get_channel(CHANNEL_NHA_TU)
                            if jail_channel:
                                embed = discord.Embed(title="🕊️ LỆNH ÂN XÁ 🕊️", description=f"{member.mention} đã mãn hạn tù và được trả tự do! Hãy làm lại cuộc đời.", color=discord.Color.green())
                                await jail_channel.send(embed=embed)
                            break
                except Exception as e:
                    print(f"Lỗi ân xá cho {uid}: {e}")
        
        for uid in to_remove:
            del jail_data[uid]
        if to_remove:
            save_data(jail_data)

    check_jail_loop.start()