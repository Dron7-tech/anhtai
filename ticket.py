import discord
from discord import app_commands
import asyncio
import io
import random
import string

ADMIN_ROLES = [1438895205012082812, 1438865272315445258]
CATEGORY_ID = 1438870146516254903

def generate_random_id(length=4):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

# ==========================================
# 1. MENU CHỌN LOẠI TICKET
# ==========================================
class TicketTypeSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Phỏng vấn trực tiếp", description="Tạo kênh chat riêng với Ban Quản Trị", emoji="🤝", value="interview"),
            discord.SelectOption(label="Gửi thư (Hiện danh)", description="Tạo kênh riêng để gửi thư/góp ý công khai", emoji="📝", value="letter_public"),
            discord.SelectOption(label="Gửi thư (Ẩn danh)", description="Gửi thư bí mật đến BQT (Bảo mật danh tính)", emoji="🕵️", value="letter_anon")
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

        # Xử lý: Phỏng vấn trực tiếp
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

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }
        for r_id in ADMIN_ROLES:
            role = guild.get_role(r_id)
            if role: overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        try:
            ch_name = f"interview-{user.name}"
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
        
        # Chỉ bot và admin được quyền xem thư, người gửi (default role) không được xem
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }
        for r_id in ADMIN_ROLES:
            role = guild.get_role(r_id)
            if role: overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        if not self.is_anon:
            # SỬA LỖI: Không cấp quyền xem kênh cho người gửi để họ chỉ thấy kênh trả lời
            ch_name = f"thu-{interaction.user.name}"
            topic_str = f"PublicLetter của {interaction.user.id}"
            desc = f"**Người gửi:** {interaction.user.mention}\n\n**Nội dung:**\n{self.noi_dung.value}"
        else:
            ch_name = f"thu-andanh-{generate_random_id()}"
            topic_str = f"AnonLetter của {interaction.user.id}"
            desc = f"**Người gửi:** 🕵️ Vô danh\n\n**Nội dung:**\n{self.noi_dung.value}"

        try:
            channel = await guild.create_text_channel(name=ch_name, category=category, overwrites=overwrites, topic=topic_str)
            embed = discord.Embed(title=f"💌 {self.tieu_de.value}", description=desc, color=discord.Color.blue())
            admin_pings = " ".join([f"<@&{r}>" for r in ADMIN_ROLES])
            await channel.send(content=admin_pings, embed=embed, view=ActiveLetterControls())
            
            await interaction.edit_original_response(content="✅ Thư của bạn đã được gửi an toàn tới hệ thống!")
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

    def __init__(self, topic_str):
        self.topic_str = topic_str or ""
        super().__init__()

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("⏳ Đang gửi phản hồi...", ephemeral=True)
        try:
            uid_str = self.topic_str.split(" ")[-1]
            
            # SỬA LỖI: Dùng fetch_member để bắt buộc tìm cả những người không có trong cache bot
            target_user = None
            if uid_str.isdigit():
                try:
                    target_user = await interaction.guild.fetch_member(int(uid_str))
                except discord.NotFound:
                    pass
        except Exception:
            target_user = None
            
        if not target_user:
            await interaction.edit_original_response(content="❌ Lỗi: Không thể xác định được người gửi thư (Họ đã rời server hoặc tài khoản bị vô hiệu hóa).")
            await asyncio.sleep(5)
            try: await interaction.delete_original_response()
            except: pass
            return
            
        guild = interaction.guild
        category = guild.get_channel(CATEGORY_ID)
        
        # Người nhận thư (kể cả vô danh hay công khai) sẽ nhận được 1 kênh riêng để xem câu trả lời
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            target_user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }
        for r_id in ADMIN_ROLES:
            role = guild.get_role(r_id)
            if role: overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
            
        try:
            ch_name = f"phanhoi-{target_user.name}"
            ch = await guild.create_text_channel(name=ch_name, category=category, overwrites=overwrites, topic=f"Ticket của {target_user.id}")
            embed = discord.Embed(title="📬 THƯ PHẢN HỒI TỪ BAN QUẢN TRỊ", description=self.noi_dung.value, color=discord.Color.green())
            await ch.send(content=f"Chào {target_user.mention}, bạn có một phản hồi mới:", embed=embed, view=ActiveInterviewControls())
            
            await interaction.edit_original_response(content=f"✅ Đã tạo kênh phản hồi thành công: {ch.mention}")
            
            # Tùy chọn: tự động đóng/đổi tên kênh thư cũ sau khi phản hồi
            try: await interaction.channel.edit(name=f"replied-{interaction.channel.name}")
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
        # Bảng chọn sẽ tự biến mất sau 60s
        await interaction.response.send_message("👇 Vui lòng chọn định dạng Ticket bạn muốn tạo:", view=TicketTypeSelectView(), ephemeral=True, delete_after=60.0)

# ==========================================
# 5. CONTROL: TICKET / THƯ ĐANG HOẠT ĐỘNG
# ==========================================
class ActiveInterviewControls(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Khóa Kênh", style=discord.ButtonStyle.danger, custom_id="close_interview_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        is_admin = any(role.id in ADMIN_ROLES for role in getattr(interaction.user, 'roles', []))
        topic = interaction.channel.topic or ""
        is_creator = str(interaction.user.id) in topic
        
        if not is_admin and not is_creator:
            await interaction.response.send_message("❌ Bạn không có quyền khóa kênh này!", ephemeral=True, delete_after=5.0)
            return

        await interaction.response.send_message("⏳ Đang khóa kênh...", ephemeral=True)
        
        if is_creator and not is_admin:
            try: await interaction.channel.set_permissions(interaction.user, send_messages=False, read_messages=True)
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


class ActiveLetterControls(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="💬 Phản hồi Thư", style=discord.ButtonStyle.primary, custom_id="reply_letter_btn")
    async def reply_letter(self, interaction: discord.Interaction, button: discord.ui.Button):
        is_admin = any(role.id in ADMIN_ROLES for role in getattr(interaction.user, 'roles', []))
        if not is_admin:
            await interaction.response.send_message("❌ Chỉ Ban Quản Trị mới có quyền phản hồi!", ephemeral=True, delete_after=5.0)
            return
        
        await interaction.response.send_modal(AdminReplyModal(interaction.channel.topic))

    @discord.ui.button(label="🔒 Đóng Thư", style=discord.ButtonStyle.danger, custom_id="close_letter_btn")
    async def close_letter(self, interaction: discord.Interaction, button: discord.ui.Button):
        is_admin = any(role.id in ADMIN_ROLES for role in getattr(interaction.user, 'roles', []))
        if not is_admin:
            await interaction.response.send_message("❌ Chỉ Ban Quản Trị mới có quyền đóng thư!", ephemeral=True, delete_after=5.0)
            return
            
        await interaction.response.send_message("⏳ Đang khóa kênh thư...", ephemeral=True)
        try:
            await interaction.channel.edit(name=f"closed-{interaction.channel.name}")
            
            topic = interaction.channel.topic or ""
            if "PublicLetter" in topic:
                uid = int(topic.split(" ")[-1])
                try: 
                    user = await interaction.guild.fetch_member(uid)
                    if user: await interaction.channel.set_permissions(user, read_messages=False)
                except: 
                    pass
                    
            embed = discord.Embed(title="🔒 THƯ ĐÃ ĐÓNG", description="Kênh lưu trữ thư đã bị khóa. Vui lòng chọn thao tác quản lý.", color=discord.Color.gold())
            await interaction.channel.send(embed=embed, view=ClosedTicketControls())
            
            self.clear_items()
            await interaction.message.edit(view=self)
            
            await interaction.edit_original_response(content="✅ Thư đã được khóa thành công.")
        except Exception as e:
            await interaction.edit_original_response(content=f"❌ Có lỗi: {e}")
            
        await asyncio.sleep(5)
        try: await interaction.delete_original_response()
        except: pass

# ==========================================
# 6. CONTROL: TICKET / THƯ ĐÃ ĐÓNG
# ==========================================
class ClosedTicketControls(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📝 Xuất Transcript", style=discord.ButtonStyle.primary, custom_id="transcript_btn")
    async def transcript_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        is_admin = any(role.id in ADMIN_ROLES for role in getattr(interaction.user, 'roles', []))
        if not is_admin:
            await interaction.response.send_message("❌ Chỉ Admin mới có quyền xuất Transcript!", ephemeral=True, delete_after=5.0)
            return

        await interaction.response.defer(ephemeral=True)
        messages = [msg async for msg in interaction.channel.history(limit=500, oldest_first=True)]
        
        transcript_content = f"TRANSCRIPT CHO KÊNH: {interaction.channel.name}\n"
        transcript_content += f"Thời gian xuất: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
        transcript_content += "="*50 + "\n\n"
        
        for msg in messages:
            time_str = msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
            transcript_content += f"[{time_str}] {msg.author.display_name}: {msg.clean_content}\n"
            if msg.attachments:
                for att in msg.attachments: transcript_content += f"    [Đính kèm]: {att.url}\n"

        file = discord.File(io.BytesIO(transcript_content.encode('utf-8')), filename=f"transcript-{interaction.channel.name}.txt")
        await interaction.followup.send("✅ Dữ liệu Transcript đã được trích xuất:", file=file, ephemeral=True)

    @discord.ui.button(label="🗑️ Xóa Kênh", style=discord.ButtonStyle.danger, custom_id="delete_btn")
    async def delete_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        is_admin = any(role.id in ADMIN_ROLES for role in getattr(interaction.user, 'roles', []))
        if not is_admin:
            await interaction.response.send_message("❌ Chỉ Admin mới có quyền xóa!", ephemeral=True, delete_after=5.0)
            return

        await interaction.response.send_message("🗑️ Kênh sẽ bị xóa vĩnh viễn sau 5 giây...", ephemeral=True)
        await asyncio.sleep(5)
        try: await interaction.channel.delete()
        except: pass

# ==========================================
# 7. KHỞI TẠO SLASH COMMAND
# ==========================================
def setup_ticket(bot):
    bot.add_view(TicketPanel())
    bot.add_view(ActiveInterviewControls())
    bot.add_view(ActiveLetterControls())
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
            description="Bấm vào nút để tạo đơn gửi liên hợp quốc",
            color=discord.Color.green()
        )
        embed.set_footer(text="TicketTool.xyz - Ticketing without clutter")
        
        await interaction.channel.send(embed=embed, view=TicketPanel())
        
        await interaction.response.send_message("✅ Đã tạo Ticket Panel thành công!", ephemeral=True)
        await asyncio.sleep(5)
        try: await interaction.delete_original_response()
        except: pass