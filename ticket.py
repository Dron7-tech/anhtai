import discord
from discord import app_commands
import asyncio
import io

ADMIN_ROLES = [1438895205012082812, 1438865272315445258]
CATEGORY_ID = 1438870146516254903 # ID Danh mục chứa Ticket

# ==========================================
# 1. MENU CHỌN LOẠI TICKET
# ==========================================
class TicketTypeSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Phỏng vấn trực tiếp", description="Tạo kênh chat riêng với Ban Quản Trị", emoji="🤝", value="interview"),
            discord.SelectOption(label="Gửi thư (Hiện danh)", description="Tạo kênh chat riêng để gửi thư/góp ý", emoji="📝", value="letter_public"),
            discord.SelectOption(label="Gửi thư (Ẩn danh)", description="Gửi thư bí mật đến BQT (Không ai biết bạn)", emoji="🕵️", value="letter_anon")
        ]
        super().__init__(placeholder="Chọn loại hỗ trợ bạn cần...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        val = self.values[0]
        guild = interaction.guild
        user = interaction.user

        if val == "letter_anon":
            await interaction.response.send_modal(AnonymousLetterModal())
            return

        await interaction.response.defer(ephemeral=True)
        
        category = guild.get_channel(CATEGORY_ID)
        if not category or not isinstance(category, discord.CategoryChannel):
            await interaction.followup.send("❌ Không tìm thấy Danh Mục Ticket. Vui lòng báo Admin kiểm tra lại CATEGORY_ID.", ephemeral=True)
            return

        prefix = "interview-" if val == "interview" else "thu-"
        channel_name = f"{prefix}{user.name}"

        for ch in category.text_channels:
            if ch.topic and str(user.id) in ch.topic:
                await interaction.followup.send(f"❌ Bạn đang có một ticket chưa đóng: {ch.mention}", ephemeral=True)
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
            ticket_channel = await guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                topic=f"Ticket của {user.id}"
            )
            
            embed = discord.Embed(
                title="🎫 TICKET ĐƯỢC TẠO",
                description=f"Xin chào {user.mention},\nBan Quản Trị sẽ phản hồi bạn trong thời gian sớm nhất.\n\n**Mục đích:** {'Phỏng vấn trực tiếp' if val == 'interview' else 'Gửi thư góp ý (Hiện danh)'}",
                color=discord.Color.green()
            )
            admin_pings = " ".join([f"<@&{r}>" for r in ADMIN_ROLES])
            await ticket_channel.send(content=f"{user.mention} {admin_pings}", embed=embed, view=TicketActiveControls())
            
            await interaction.followup.send(f"✅ Đã tạo ticket thành công: {ticket_channel.mention}", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Có lỗi khi tạo kênh: {e}", ephemeral=True)

class TicketTypeSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketTypeSelect())

# ==========================================
# 2. FORM ĐIỀN THƯ ẨN DANH (MODAL)
# ==========================================
class AnonymousLetterModal(discord.ui.Modal, title='Gửi Thư Ẩn Danh'):
    tieu_de = discord.ui.TextInput(label='Tiêu đề thư', placeholder='Nhập tiêu đề ngắn gọn...', max_length=100)
    noi_dung = discord.ui.TextInput(label='Nội dung thư', style=discord.TextStyle.paragraph, placeholder='Nhập nội dung bạn muốn gửi ẩn danh đến BQT...', required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        admin_channel = discord.utils.get(interaction.guild.text_channels, name="thư-ẩn-danh")
        
        if not admin_channel:
            try:
                overwrites = {
                    interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
                }
                for r_id in ADMIN_ROLES:
                    role = interaction.guild.get_role(r_id)
                    if role: overwrites[role] = discord.PermissionOverwrite(read_messages=True)
                admin_channel = await interaction.guild.create_text_channel("thư-ẩn-danh", overwrites=overwrites)
            except: pass
        
        if admin_channel:
            embed = discord.Embed(title=f"🕵️ THƯ ẨN DANH: {self.tieu_de.value}", description=self.noi_dung.value, color=discord.Color.dark_grey())
            embed.set_footer(text="Người gửi hoàn toàn ẩn danh. BQT không thể biết người gửi là ai.")
            await admin_channel.send(embed=embed)
            await interaction.followup.send("✅ Thư ẩn danh của bạn đã được gửi an toàn tới BQT!", ephemeral=True)
        else:
            await interaction.followup.send("❌ Không tìm thấy kênh nhận thư ẩn danh. Vui lòng báo Admin thiết lập lại.", ephemeral=True)

# ==========================================
# 3. GIAO DIỆN NÚT "CREATE TICKET" CHÍNH
# ==========================================
class TicketPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Create ticket", emoji="📩", style=discord.ButtonStyle.secondary, custom_id="create_ticket_btn_main")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("👇 Vui lòng chọn định dạng Ticket bạn muốn tạo:", view=TicketTypeSelectView(), ephemeral=True)

# ==========================================
# 4. TRẠNG THÁI: TICKET ĐANG MỞ
# ==========================================
class TicketActiveControls(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Đóng Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket_btn_action")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        is_admin = False
        if hasattr(interaction.user, 'roles'):
            is_admin = any(role.id in ADMIN_ROLES for role in interaction.user.roles)
        
        topic = interaction.channel.topic or ""
        user_id_str = topic.replace("Ticket của ", "")
        is_creator = str(interaction.user.id) == user_id_str
        
        if not is_admin and not is_creator:
            await interaction.response.send_message("❌ Bạn không có quyền đóng ticket này!", ephemeral=True)
            return

        await interaction.response.defer()
        
        # Khóa quyền gửi tin nhắn của người tạo Ticket
        if user_id_str.isdigit():
            creator = interaction.guild.get_member(int(user_id_str))
            if creator:
                try: await interaction.channel.set_permissions(creator, send_messages=False, read_messages=True)
                except: pass

        # Đổi tên kênh thêm tiền tố closed
        try: await interaction.channel.edit(name=f"closed-{interaction.channel.name}")
        except: pass

        embed = discord.Embed(title="🔒 TICKET ĐÃ ĐÓNG", description=f"Ticket này đã được đóng bởi {interaction.user.mention}.\nKênh hiện tại đã bị khóa chức năng trò chuyện.\n\nVui lòng chọn các thao tác quản lý bên dưới.", color=discord.Color.gold())
        await interaction.followup.send(embed=embed, view=TicketClosedControls())

        # Xóa các nút cũ để tránh bấm lại
        self.clear_items()
        try: await interaction.message.edit(view=self)
        except: pass

# ==========================================
# 5. TRẠNG THÁI: TICKET ĐÃ ĐÓNG (TRANSCRIPT & XÓA)
# ==========================================
class TicketClosedControls(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📝 Xuất Transcript", style=discord.ButtonStyle.primary, custom_id="transcript_ticket_btn")
    async def transcript_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        is_admin = False
        if hasattr(interaction.user, 'roles'):
            is_admin = any(role.id in ADMIN_ROLES for role in interaction.user.roles)
        if not is_admin:
            await interaction.response.send_message("❌ Chỉ Admin mới có quyền xuất Transcript!", ephemeral=True)
            return

        await interaction.response.defer()
        messages = [msg async for msg in interaction.channel.history(limit=500, oldest_first=True)]
        
        transcript_content = f"TRANSCRIPT CHO KÊNH: {interaction.channel.name}\n"
        transcript_content += f"Thời gian xuất: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
        transcript_content += "="*50 + "\n\n"
        
        for msg in messages:
            time_str = msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
            transcript_content += f"[{time_str}] {msg.author.display_name}: {msg.clean_content}\n"
            if msg.attachments:
                for att in msg.attachments:
                    transcript_content += f"    [Đính kèm]: {att.url}\n"

        file = discord.File(io.BytesIO(transcript_content.encode('utf-8')), filename=f"transcript-{interaction.channel.name}.txt")
        await interaction.followup.send("✅ Dữ liệu Transcript đã được trích xuất thành công:", file=file)

    @discord.ui.button(label="🗑️ Xóa Ticket", style=discord.ButtonStyle.danger, custom_id="delete_ticket_btn")
    async def delete_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        is_admin = False
        if hasattr(interaction.user, 'roles'):
            is_admin = any(role.id in ADMIN_ROLES for role in interaction.user.roles)
        if not is_admin:
            await interaction.response.send_message("❌ Chỉ Admin mới có quyền xóa ticket!", ephemeral=True)
            return

        await interaction.response.send_message("🗑️ Kênh sẽ bị xóa vĩnh viễn sau 5 giây...")
        await asyncio.sleep(5)
        try: await interaction.channel.delete()
        except: pass

# ==========================================
# 6. KHỞI TẠO SLASH COMMAND
# ==========================================
def setup_ticket(bot):
    bot.add_view(TicketPanel())
    bot.add_view(TicketActiveControls())
    bot.add_view(TicketClosedControls())

    @bot.tree.command(name="ticket_panel", description="Tạo bảng điều khiển Mở Ticket (Dành cho Admin)")
    @app_commands.default_permissions(administrator=True)
    async def slash_ticket_panel(interaction: discord.Interaction):
        is_admin = interaction.user.guild_permissions.administrator or any(role.id in ADMIN_ROLES for role in getattr(interaction.user, 'roles', []))
        if not is_admin:
            await interaction.response.send_message("❌ Bạn không có quyền sử dụng lệnh này!", ephemeral=True)
            return
            
        embed = discord.Embed(
            title="Đơn liên hợp quốc", 
            description="Bấm vào nút để tạo đơn gửi liên hợp quốc",
            color=discord.Color.green()
        )
        embed.set_footer(text="AnhTai Bot - Hệ thống Ticket chuyên nghiệp")
        
        await interaction.channel.send(embed=embed, view=TicketPanel())
        await interaction.response.send_message("✅ Đã tạo Ticket Panel thành công!", ephemeral=True)