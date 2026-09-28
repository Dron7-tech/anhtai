import discord
from discord import app_commands
import asyncio

ADMIN_ROLES = [1438895205012082812, 1438865272315445258]

# ==========================================
# 1. MENU CHỌN LOẠI TICKET (Hiện ẩn sau khi bấm nút)
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

        # Xử lý Gửi Thư Ẩn Danh (Dùng Modal Form)
        if val == "letter_anon":
            await interaction.response.send_modal(AnonymousLetterModal())
            return

        # Xử lý Phỏng Vấn / Gửi Thư Hiện Danh (Tạo Kênh riêng)
        await interaction.response.defer(ephemeral=True)
        
        category = discord.utils.get(guild.categories, name="TICKETS")
        if not category:
            try:
                category = await guild.create_category("TICKETS")
            except Exception as e:
                await interaction.followup.send(f"❌ Lỗi tạo danh mục TICKETS: {e}", ephemeral=True)
                return

        prefix = "interview-" if val == "interview" else "thu-"
        channel_name = f"{prefix}{user.name}"

        # Kiểm tra nếu User đã có Ticket chưa đóng
        for ch in category.text_channels:
            if ch.topic and str(user.id) in ch.topic:
                await interaction.followup.send(f"❌ Bạn đang có một ticket chưa đóng: {ch.mention}", ephemeral=True)
                return

        # Phân quyền kênh Ticket
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }
        for r_id in ADMIN_ROLES:
            role = guild.get_role(r_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

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
            await ticket_channel.send(content=f"{user.mention} {admin_pings}", embed=embed, view=TicketControls())
            
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
    tieu_de = discord.ui.TextInput(
        label='Tiêu đề thư',
        placeholder='Nhập tiêu đề ngắn gọn...',
        max_length=100
    )
    noi_dung = discord.ui.TextInput(
        label='Nội dung thư',
        style=discord.TextStyle.paragraph,
        placeholder='Nhập nội dung bạn muốn gửi ẩn danh đến BQT...',
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        admin_channel = discord.utils.get(interaction.guild.text_channels, name="thư-ẩn-danh")
        
        # Tự động tạo kênh thư ẩn danh cho BQT nếu chưa có
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

    # Nút bấm được thiết kế giống hệt Ticket Tool
    @discord.ui.button(label="Create ticket", emoji="📩", style=discord.ButtonStyle.secondary, custom_id="create_ticket_btn_main")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = TicketTypeSelectView()
        # Hiện menu chọn loại Ticket dưới dạng tin nhắn ẩn (ephemeral)
        await interaction.response.send_message("👇 Vui lòng chọn định dạng Ticket bạn muốn tạo:", view=view, ephemeral=True)

# ==========================================
# 4. NÚT ĐÓNG TICKET TRONG KÊNH ĐÃ TẠO
# ==========================================
class TicketControls(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Đóng Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket_btn_action")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        is_admin = False
        if hasattr(interaction.user, 'roles'):
            is_admin = any(role.id in ADMIN_ROLES for role in interaction.user.roles)
        is_creator = str(interaction.user.id) in (interaction.channel.topic or "")
        
        if not is_admin and not is_creator:
            await interaction.response.send_message("❌ Bạn không có quyền đóng ticket này!", ephemeral=True)
            return
            
        await interaction.response.send_message("🔒 Kênh sẽ bị xóa sau 5 giây...")
        await asyncio.sleep(5)
        try:
            await interaction.channel.delete()
        except: pass

# ==========================================
# 5. KHỞI TẠO SLASH COMMAND
# ==========================================
def setup_ticket(bot):
    # Đăng ký view tĩnh để nút bấm không bị liệt khi Bot khởi động lại
    bot.add_view(TicketPanel())
    bot.add_view(TicketControls())

    @bot.tree.command(name="ticket_panel", description="Tạo bảng điều khiển Mở Ticket (Dành cho Admin)")
    @app_commands.default_permissions(administrator=True) # Chỉ người có quyền Admin mới nhìn thấy lệnh này
    async def slash_ticket_panel(interaction: discord.Interaction):
        # Lớp bảo vệ thứ 2: Kiểm tra Role thủ công
        is_admin = interaction.user.guild_permissions.administrator or any(role.id in ADMIN_ROLES for role in getattr(interaction.user, 'roles', []))
        if not is_admin:
            await interaction.response.send_message("❌ Bạn không có quyền sử dụng lệnh này!", ephemeral=True)
            return
            
        # Bảng Embed thiết kế giống Ticket Tool
        embed = discord.Embed(
            title="Đơn liên hợp quốc", # Bạn có thể sửa tiêu đề tại đây
            description="Bấm vào nút để tạo đơn gửi liên hợp quốc",
            color=discord.Color.green() # Viền xanh lá giống Ticket Tool
        )
        embed.set_footer(text="AnhTai Bot - Hệ thống Ticket chuyên nghiệp")
        
        await interaction.channel.send(embed=embed, view=TicketPanel())
        await interaction.response.send_message("✅ Đã tạo Ticket Panel thành công!", ephemeral=True)