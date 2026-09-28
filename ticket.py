import discord
from discord import app_commands
import asyncio
import io
import random
import string

ADMIN_ROLES = [1438895205012082812, 1438865272315445258]
CATEGORY_ID = 1438870146516254903

# ==========================================
# CÁC HÀM TIỆN ÍCH DÀNH CHO TICKET
# ==========================================
def get_next_ticket_number(category, prefix):
    max_num = 0
    if not category: return 1
    for ch in category.text_channels:
        if ch.name.startswith(prefix):
            try:
                num = int(ch.name.split("-")[-1])
                if num > max_num: max_num = num
            except ValueError: pass
    return max_num + 1

def get_strict_overwrites(guild, allowed_user=None, denied_user=None):
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
    }
    
    for role in guild.roles:
        if role.id in ADMIN_ROLES:
            overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        elif role.id == guild.default_role.id or role.is_bot_managed() or role.is_integration():
            continue
        else:
            overwrites[role] = discord.PermissionOverwrite(read_messages=False)
            
    if allowed_user:
        overwrites[allowed_user] = discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True)
    if denied_user:
        overwrites[denied_user] = discord.PermissionOverwrite(read_messages=False, view_channel=False)
        
    return overwrites

# ==========================================
# 1. MENU CHỌN LOẠI TICKET
# ==========================================
class TicketTypeSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Phỏng vấn trực tiếp", description="Tạo kênh chat riêng với Ban Quản Trị", emoji="🤝", value="interview"),
            discord.SelectOption(label="Gửi thư (Hiện danh)", description="Tạo kênh để gửi thư/góp ý (Bảo mật cho BQT)", emoji="📝", value="letter_public"),
            discord.SelectOption(label="Gửi thư (Ẩn danh)", description="Gửi thư bí mật đến BQT (Ẩn danh tính)", emoji="🕵️", value="letter_anon")
        ]
        super().__init__(placeholder="Chọn loại hỗ trợ bạn cần...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        val = self.values[0]

        if val == "letter_anon":
            await interaction.response.send_modal(LetterModal(is_anon=True))
            return
        elif val == "letter_public":
            await interaction.response.send_modal(LetterModal(is_anon=False))
            return

        await interaction.response.send_message("⏳ Đang khởi tạo phòng phỏng vấn...", ephemeral=True)
        guild = interaction.guild
        user = interaction.user
        category = guild.get_channel(CATEGORY_ID)
        
        if not category:
            await interaction.edit_original_response(content="❌ Lỗi: Không tìm thấy Danh Mục Ticket!")
            await asyncio.sleep(5)
            try: await interaction.delete_original_response()
            except: pass
            return

        for ch in category.text_channels:
            if ch.topic and str(user.id) in ch.topic:
                await interaction.edit_original_response(content=f"❌ Bạn đang có một ticket chưa đóng: {ch.mention}")
                await asyncio.sleep(5)
                try: await interaction.delete_original_response()
                except: pass
                return

        overwrites = get_strict_overwrites(guild, allowed_user=user)

        try:
            num = get_next_ticket_number(category, "interview-")
            ch_name = f"interview-{num}"
            ticket_channel = await guild.create_text_channel(name=ch_name, category=category, overwrites=overwrites, topic=f"Ticket của {user.id}")
            
            embed = discord.Embed(
                title="🤝 PHÒNG PHỎNG VẤN TRỰC TIẾP",
                description=f"Xin chào {user.mention},\nBan Quản Trị sẽ có mặt và phản hồi bạn trong ít phút nữa.",
                color=discord.Color.green()
            )
            admin_pings = " ".join([f"<@&{r}>" for r in ADMIN_ROLES])
            await ticket_channel.send(content=f"{user.mention} {admin_pings}", embed=embed, view=ActiveInterviewControls())
            
            await interaction.edit_original_response(content=f"✅ Đã tạo phòng thành công: {ticket_channel.mention}")
        except Exception as e:
            await interaction.edit_original_response(content=f"❌ Có lỗi: {e}")
            
        await asyncio.sleep(5)
        try: await interaction.delete_original_response()
        except: pass

class TicketTypeSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketTypeSelect())

# ==========================================
# 2. MODAL GỬI THƯ (ẨN DANH / HIỆN DANH)
# ==========================================
class LetterModal(discord.ui.Modal):
    tieu_de = discord.ui.TextInput(label='Tiêu đề thư', placeholder='Nhập tiêu đề...', max_length=100)
    noi_dung = discord.ui.TextInput(label='Nội dung thư', style=discord.TextStyle.paragraph, placeholder='Nhập nội dung thư...', required=True)

    def __init__(self, is_anon: bool):
        self.is_anon = is_anon
        super().__init__(title="🕵️ Gửi Thư Ẩn Danh" if is_anon else "📝 Gửi Thư Hiện Danh")

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("⏳ Đang thiết lập và gửi thư...", ephemeral=True)
        guild = interaction.guild
        category = guild.get_channel(CATEGORY_ID)
        
        overwrites = get_strict_overwrites(guild, denied_user=interaction.user)

        prefix = "thu-an-danh-" if self.is_anon else "thu-hien-danh-"
        num = get_next_ticket_number(category, prefix)
        ch_name = f"{prefix}{num}"

        if not self.is_anon:
            topic_str = f"PublicLetter của {interaction.user.id} - ID:{num}"
            desc = f"**Người gửi:** {interaction.user.mention}\n\n**Nội dung:**\n{self.noi_dung.value}"
        else:
            topic_str = f"AnonLetter của {interaction.user.id} - ID:{num}"
            desc = f"**Người gửi:** 🕵️ Vô danh\n\n**Nội dung:**\n{self.noi_dung.value}"

        try:
            channel = await guild.create_text_channel(name=ch_name, category=category, overwrites=overwrites, topic=topic_str)
            embed = discord.Embed(title=f"💌 {self.tieu_de.value}", description=desc, color=discord.Color.blue())
            admin_pings = " ".join([f"<@&{r}>" for r in ADMIN_ROLES])
            await channel.send(content=admin_pings, embed=embed, view=DirectLetterControls())
            
            await interaction.edit_original_response(content="✅ Thư của bạn đã được gửi an toàn tới hệ thống Ban Quản Trị!")
        except Exception as e:
            await interaction.edit_original_response(content=f"❌ Lỗi gửi thư: {e}")
            
        await asyncio.sleep(5)
        try: await interaction.delete_original_response()
        except: pass

# ==========================================
# 3. MODAL ADMIN PHẢN HỒI THƯ
# ==========================================
class AdminReplyModal(discord.ui.Modal, title='Phản hồi thư của Member'):
    noi_dung = discord.ui.TextInput(label='Nội dung phản hồi', style=discord.TextStyle.paragraph, placeholder="Nhập câu trả lời của Admin...", required=True)

    def __init__(self, topic_str, origin_channel_id):
        self.topic_str = topic_str or ""
        self.origin_channel_id = origin_channel_id
        super().__init__()

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("⏳ Đang gửi phản hồi...", ephemeral=True)
        try:
            parts = self.topic_str.split(" ")
            uid_str = parts[2]
            letter_id = parts[-1].replace("ID:", "")
            target_user = None
            if uid_str.isdigit():
                try: target_user = await interaction.guild.fetch_member(int(uid_str))
                except discord.NotFound: pass
        except Exception:
            target_user = None
            
        if not target_user:
            await interaction.edit_original_response(content="❌ Lỗi: Không thể xác định được người nhận (Họ đã rời server hoặc tài khoản bị vô hiệu hóa).")
            await asyncio.sleep(5)
            try: await interaction.delete_original_response()
            except: pass
            return
            
        guild = interaction.guild
        category = guild.get_channel(CATEGORY_ID)
        
        overwrites = get_strict_overwrites(guild, allowed_user=target_user)
            
        is_anon = "AnonLetter" in self.topic_str
        prefix = "phan-hoi-an-danh-" if is_anon else "phan-hoi-hien-danh-"
        ch_name = f"{prefix}{letter_id}"
        
        try:
            ch = await guild.create_text_channel(name=ch_name, category=category, overwrites=overwrites, topic=f"ReplyTicket của {target_user.id} - Linked:{self.origin_channel_id}")
            embed = discord.Embed(title="📬 THƯ PHẢN HỒI TỪ BAN QUẢN TRỊ", description=self.noi_dung.value, color=discord.Color.green())
            await ch.send(content=f"Chào {target_user.mention}, bạn có một phản hồi mới từ BQT:", embed=embed, view=ReplyChannelControls())
            
            await interaction.edit_original_response(content=f"✅ Đã tạo kênh phản hồi thành công: {ch.mention}")
            
            new_topic = f"{self.topic_str} - ReplyLinked:{ch.id}"
            try: await interaction.channel.edit(topic=new_topic)
            except: pass
            
        except Exception as e:
            await interaction.edit_original_response(content=f"❌ Có lỗi khi tạo kênh phản hồi: {e}")
            
        await asyncio.sleep(5)
        try: await interaction.delete_original_response()
        except: pass

# ==========================================
# 4. GIAO DIỆN CHÍNH "CREATE TICKET"
# ==========================================
class TicketPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Create ticket", emoji="📩", style=discord.ButtonStyle.secondary, custom_id="create_ticket_btn_main")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("👇 Vui lòng chọn định dạng Ticket bạn muốn tạo:", view=TicketTypeSelectView(), ephemeral=True, delete_after=60.0)

# ==========================================
# 5. CONTROL: TICKET PHỎNG VẤN ĐANG MỞ
# ==========================================
class ActiveInterviewControls(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Khóa Kênh", style=discord.ButtonStyle.danger, custom_id="close_interview_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        is_admin = any(role.id in ADMIN_ROLES for role in getattr(interaction.user, 'roles', []))
        
        if not is_admin:
            await interaction.response.send_message("❌ Chỉ Ban Quản Trị mới có quyền khóa kênh này!", ephemeral=True, delete_after=5.0)
            return

        await interaction.response.send_message("⏳ Đang khóa kênh...", ephemeral=True)
        
        # Admin bấm nút -> Bot tự động tìm người gửi để tước quyền chat
        topic = interaction.channel.topic or ""
        try:
            creator_id = int(topic.split()[-1])
            creator = interaction.guild.get_member(creator_id)
            if creator:
                await interaction.channel.set_permissions(creator, send_messages=False, read_messages=True)
        except: pass

        try:
            await interaction.channel.edit(name=f"closed-{interaction.channel.name}")
            embed = discord.Embed(title="🔒 KÊNH ĐÃ KHÓA", description=f"Kênh này đã được khóa bởi {interaction.user.mention}.\nVui lòng chọn các thao tác quản lý bên dưới.", color=discord.Color.gold())
            await interaction.channel.send(embed=embed, view=ClosedTicketControls())
            
            self.clear_items()
            await interaction.message.edit(view=self)
            
            await interaction.edit_original_response(content="✅ Đã khóa kênh thành công.")
        except Exception as e:
            await interaction.edit_original_response(content=f"❌ Có lỗi: {e}")
            
        await asyncio.sleep(5)
        try: await interaction.delete_original_response()
        except: pass

# ==========================================
# 6. CONTROL: KÊNH THƯ GỐC (Bên Admin)
# ==========================================
class DirectLetterControls(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="💬 Phản hồi", style=discord.ButtonStyle.primary, custom_id="reply_direct_btn")
    async def reply_letter(self, interaction: discord.Interaction, button: discord.ui.Button):
        is_admin = any(role.id in ADMIN_ROLES for role in getattr(interaction.user, 'roles', []))
        if not is_admin:
            await interaction.response.send_message("❌ Chỉ Ban Quản Trị mới có quyền phản hồi!", ephemeral=True, delete_after=5.0)
            return
        
        if "ReplyLinked:" in str(interaction.channel.topic):
            await interaction.response.send_message("⚠️ Thư này đã được phản hồi rồi. Bạn có thể xóa nếu đã giải quyết xong.", ephemeral=True, delete_after=5.0)
            return
            
        await interaction.response.send_modal(AdminReplyModal(interaction.channel.topic, interaction.channel.id))

    @discord.ui.button(label="📝 Transcript", style=discord.ButtonStyle.secondary, custom_id="transcript_direct_btn")
    async def transcript_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        is_admin = any(role.id in ADMIN_ROLES for role in getattr(interaction.user, 'roles', []))
        if not is_admin:
            await interaction.response.send_message("❌ Chỉ Admin mới có quyền xuất Transcript!", ephemeral=True, delete_after=5.0)
            return

        await interaction.response.defer(ephemeral=True)
        messages = [msg async for msg in interaction.channel.history(limit=500, oldest_first=True)]
        
        transcript_content = f"TRANSCRIPT THƯ: {interaction.channel.name}\n"
        transcript_content += f"Thời gian xuất: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
        transcript_content += "="*50 + "\n\n"
        
        for msg in messages:
            time_str = msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
            transcript_content += f"[{time_str}] {msg.author.display_name}: {msg.clean_content}\n"
            if msg.attachments:
                for att in msg.attachments: transcript_content += f"    [Đính kèm]: {att.url}\n"

        file = discord.File(io.BytesIO(transcript_content.encode('utf-8')), filename=f"transcript-{interaction.channel.name}.txt")
        await interaction.followup.send("✅ Dữ liệu Transcript đã được trích xuất:", file=file, ephemeral=True)

    @discord.ui.button(label="🗑️ Xóa Kênh", style=discord.ButtonStyle.danger, custom_id="delete_direct_btn")
    async def delete_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        is_admin = any(role.id in ADMIN_ROLES for role in getattr(interaction.user, 'roles', []))
        if not is_admin:
            await interaction.response.send_message("❌ Chỉ Admin mới có quyền xóa kênh!", ephemeral=True, delete_after=5.0)
            return

        await interaction.response.send_message("🗑️ Kênh này (và kênh phản hồi liên quan) sẽ bị xóa vĩnh viễn sau 5 giây...", ephemeral=True)
        
        topic = str(interaction.channel.topic)
        if "ReplyLinked:" in topic:
            try:
                reply_ch_id = int(topic.split("ReplyLinked:")[-1])
                reply_ch = interaction.guild.get_channel(reply_ch_id)
                if reply_ch: await reply_ch.delete()
            except: pass
            
        await asyncio.sleep(5)
        try: await interaction.channel.delete()
        except: pass

# ==========================================
# 7. CONTROL: KÊNH PHẢN HỒI (Bên Người Gửi)
# ==========================================
class ReplyChannelControls(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📝 Xuất Transcript", style=discord.ButtonStyle.primary, custom_id="transcript_reply_btn")
    async def transcript_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        is_admin = any(role.id in ADMIN_ROLES for role in getattr(interaction.user, 'roles', []))
        if not is_admin:
            await interaction.response.send_message("❌ Chỉ Admin mới có quyền xuất Transcript!", ephemeral=True, delete_after=5.0)
            return

        await interaction.response.defer(ephemeral=True)
        messages = [msg async for msg in interaction.channel.history(limit=500, oldest_first=True)]
        
        transcript_content = f"TRANSCRIPT PHẢN HỒI: {interaction.channel.name}\n"
        transcript_content += f"Thời gian xuất: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
        transcript_content += "="*50 + "\n\n"
        
        for msg in messages:
            time_str = msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
            transcript_content += f"[{time_str}] {msg.author.display_name}: {msg.clean_content}\n"
            if msg.attachments:
                for att in msg.attachments: transcript_content += f"    [Đính kèm]: {att.url}\n"

        file = discord.File(io.BytesIO(transcript_content.encode('utf-8')), filename=f"transcript-{interaction.channel.name}.txt")
        await interaction.followup.send("✅ Dữ liệu Transcript đã được trích xuất:", file=file, ephemeral=True)

    @discord.ui.button(label="🗑️ Xóa Kênh", style=discord.ButtonStyle.danger, custom_id="delete_reply_btn")
    async def delete_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        is_admin = any(role.id in ADMIN_ROLES for role in getattr(interaction.user, 'roles', []))
        if not is_admin:
            await interaction.response.send_message("❌ Chỉ Ban Quản Trị mới có quyền xóa kênh!", ephemeral=True, delete_after=5.0)
            return

        await interaction.response.send_message("🗑️ Kênh này (và Thư gốc bên phía Admin) sẽ bị xóa vĩnh viễn sau 5 giây...", ephemeral=True)
        
        topic = str(interaction.channel.topic)
        if "Linked:" in topic:
            try:
                origin_ch_id = int(topic.split("Linked:")[-1])
                origin_ch = interaction.guild.get_channel(origin_ch_id)
                if origin_ch: await origin_ch.delete()
            except: pass

        await asyncio.sleep(5)
        try: await interaction.channel.delete()
        except: pass

# ==========================================
# 8. CONTROL: TICKET PHỎNG VẤN ĐÃ ĐÓNG
# ==========================================
class ClosedTicketControls(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📝 Xuất Transcript", style=discord.ButtonStyle.primary, custom_id="transcript_closed_btn")
    async def transcript_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        is_admin = any(role.id in ADMIN_ROLES for role in getattr(interaction.user, 'roles', []))
        if not is_admin:
            await interaction.response.send_message("❌ Chỉ Admin mới có quyền xuất Transcript!", ephemeral=True, delete_after=5.0)
            return

        await interaction.response.defer(ephemeral=True)
        messages = [msg async for msg in interaction.channel.history(limit=500, oldest_first=True)]
        
        transcript_content = f"TRANSCRIPT KÊNH: {interaction.channel.name}\n"
        transcript_content += f"Thời gian xuất: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
        transcript_content += "="*50 + "\n\n"
        
        for msg in messages:
            time_str = msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
            transcript_content += f"[{time_str}] {msg.author.display_name}: {msg.clean_content}\n"
            if msg.attachments:
                for att in msg.attachments: transcript_content += f"    [Đính kèm]: {att.url}\n"

        file = discord.File(io.BytesIO(transcript_content.encode('utf-8')), filename=f"transcript-{interaction.channel.name}.txt")
        await interaction.followup.send("✅ Dữ liệu Transcript đã được trích xuất:", file=file, ephemeral=True)

    @discord.ui.button(label="🗑️ Xóa Kênh", style=discord.ButtonStyle.danger, custom_id="delete_closed_btn")
    async def delete_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        is_admin = any(role.id in ADMIN_ROLES for role in getattr(interaction.user, 'roles', []))
        if not is_admin:
            await interaction.response.send_message("❌ Chỉ Ban Quản Trị mới có quyền xóa kênh!", ephemeral=True, delete_after=5.0)
            return

        await interaction.response.send_message("🗑️ Kênh sẽ bị xóa vĩnh viễn sau 5 giây...", ephemeral=True)
        await asyncio.sleep(5)
        try: await interaction.channel.delete()
        except: pass

# ==========================================
# 9. KHỞI TẠO SLASH COMMAND
# ==========================================
def setup_ticket(bot):
    bot.add_view(TicketPanel())
    bot.add_view(ActiveInterviewControls())
    bot.add_view(DirectLetterControls())
    bot.add_view(ReplyChannelControls())
    bot.add_view(ClosedTicketControls())

    @bot.tree.command(name="ticket_panel", description="Tạo bảng điều khiển Mở Ticket (Dành cho Admin)")
    @app_commands.default_permissions(administrator=True)
    async def slash_ticket_panel(interaction: discord.Interaction):
        is_admin = interaction.user.guild_permissions.administrator or any(role.id in ADMIN_ROLES for role in getattr(interaction.user, 'roles', []))
        if not is_admin:
            await interaction.response.send_message("❌ Bạn không có quyền sử dụng lệnh này!", ephemeral=True, delete_after=5.0)
            return
            
        embed = discord.Embed(
            title="Đơn liên hợp quốc", 
            description="""Nếu muốn report, góp ý, gửi đơn khoan hồng xoá tội, mách lẻo, hay đơn giản chỉ là muốn tâm sự với Admin,... thì hãy ghé ⁠┍《🎟️》liên-hợp-quốc.

**CÁC TÙY CHỌN HỖ TRỢ:**
🤝 **Phỏng vấn:** Mở kênh chat 1-1 trực tiếp với Ban Quản Trị.
📝 **Gửi thư (Hiện danh):** Góp ý công khai tên tuổi.
🕵️ **Gửi thư (Ẩn danh):** Thông tin người gửi hoàn toàn được bảo mật.

*Vui lòng bấm nút bên dưới để tạo đơn.*""",
            color=0x2b2d31
        )
        embed.set_footer(text="ĐẠI ANH TÀI BOT - CÔNG - MINH - LIÊM - CHÍNH")
        
        await interaction.channel.send(embed=embed, view=TicketPanel())
        
        await interaction.response.send_message("✅ Đã tạo Ticket Panel thành công!", ephemeral=True)
        await asyncio.sleep(5)
        try: await interaction.delete_original_response()
        except: pass