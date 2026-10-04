import discord
from discord import app_commands

# ==========================================
# CẤU HÌNH ID KÊNH BẪY & KÊNH THÔNG BÁO
# ==========================================
TRAP_CHANNEL_ID = 1555500092029538334  # ID kênh Trap (Honeypot)

# ID kênh gửi thông báo rời server khi bị kick
LOG_CHANNEL_ID = 1438874414186758216  


def setup_trap(bot: discord.Client):
    """
    Hàm khởi tạo module Trap Channel để gắn vào setup_hook trong bot.py
    """

    # ==========================================
    # 1. LỆNH GỬI TIN NHẮN CẢNH BÁO VÀO KÊNH TRAP
    # ==========================================
    @bot.tree.command(
        name="trap_panel",
        description="Gửi bảng cảnh báo bẫy chống bot spam/hack vào kênh Trap (Chỉ Admin)"
    )
    @app_commands.default_permissions(administrator=True)
    async def slash_trap_panel(interaction: discord.Interaction):
        # Tìm kênh trap theo ID đã cấu hình
        trap_channel = bot.get_channel(TRAP_CHANNEL_ID)
        if trap_channel is None:
            try:
                trap_channel = await bot.fetch_channel(TRAP_CHANNEL_ID)
            except Exception:
                trap_channel = None

        if trap_channel is None:
            await interaction.response.send_message(
                f"❌ Không tìm thấy kênh Trap với ID `{TRAP_CHANNEL_ID}`! Vui lòng kiểm tra lại ID hoặc quyền của Bot.",
                ephemeral=True
            )
            return

        # Tạo bảng cảnh báo (Embed) để người thật nhìn thấy và tránh nhắn nhầm
        embed = discord.Embed(
            title="⚠️ KÊNH BẪY TỰ ĐỘNG (DO NOT MESSAGE) ⚠️",
            description=(
                "🚫 **TUYỆT ĐỐI KHÔNG NHẮN TIN VÀO KÊNH NÀY!**\n\n"
                "Đây là kênh bẫy dùng để bắt các tài khoản bị hack tự động rải link độc hại.\n"
                "⚡ Bất kỳ ai gửi tin nhắn vào kênh này sẽ bị **KICK NGAY LẬP TỨC** và **xoá toàn bộ tin nhắn gần nhất**."
            ),
            color=discord.Color.red()
        )
        embed.set_footer(text="Hệ thống bảo vệ máy chủ tự động")

        try:
            # Gửi bảng cảnh báo vào kênh Trap và ghim (pin) lại để không bị xoá nhầm
            msg = await trap_channel.send(embed=embed)
            try:
                await msg.pin()
            except Exception:
                pass
            await interaction.response.send_message(
                f"✅ Đã gửi tin nhắn cảnh báo vào kênh {trap_channel.mention}!",
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Bot không có quyền gửi tin nhắn vào kênh Trap!",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Lỗi khi gửi bảng cảnh báo: `{e}`",
                ephemeral=True
            )

    # ==========================================
    # 2. SỰ KIỆN BẮT TIN NHẮN TRONG KÊNH TRAP
    # ==========================================
    # Dùng @bot.listen thay vì @bot.event để không ghi đè các sự kiện on_message của module khác
    @bot.listen("on_message")
    async def KiemTraKenhTrap(message: discord.Message):
        # 1. Bỏ qua nếu tin nhắn không nằm trong Server (ví dụ: nhắn riêng DM cho Bot)
        if message.guild is None:
            return

        # 2. Bỏ qua nếu tin nhắn gửi bởi chính Bot hoặc các Bot khác
        if message.author.bot:
            return

        # 3. Kiểm tra xem tin nhắn có nằm đúng ở kênh Trap (1555500092029538334) hay không
        if message.channel.id != TRAP_CHANNEL_ID:
            return

        # 4. (An toàn) Bỏ qua nếu người nhắn là Chủ Server hoặc có quyền Quản trị viên (Admin)
        if isinstance(message.author, discord.Member):
            if message.author.guild_permissions.administrator:
                return

        # Chuẩn bị nội dung lý do bị kick theo đúng yêu cầu
        ly_do_kick = f"User đã bị kick do nhắn vào <#{TRAP_CHANNEL_ID}> (khả năng là nó bị hack spam link độc vào kênh =]]])"

        # ==========================================
        # BƯỚC 1: XOÁ 50 TIN NHẮN GẦN NHẤT
        # ==========================================
        try:
            await message.channel.purge(
                limit=50,
                check=lambda m: not m.pinned and m.author != bot.user
            )
        except discord.Forbidden:
            print("[TRAP LỖI] Bot thiếu quyền 'Manage Messages' (Quản lý tin nhắn) để xoá 50 tin nhắn.", flush=True)
        except Exception as e:
            print(f"[TRAP LỖI] Không thể xoá tin nhắn: {e}", flush=True)

        # ==========================================
        # BƯỚC 2: KICK THÀNH VIÊN KHỎI SERVER
        # ==========================================
        da_kick = False
        try:
            await message.author.kick(reason=ly_do_kick)
            da_kick = True
        except discord.Forbidden:
            print(f"[TRAP LỖI] Bot không đủ quyền hoặc Role thấp hơn để kick {message.author}.", flush=True)
        except Exception as e:
            print(f"[TRAP LỖI] Lỗi khi kick {message.author}: {e}", flush=True)

        # ==========================================
        # BƯỚC 3: GỬI THÔNG BÁO VÀO KÊNH 1438874414186758216
        # ==========================================
        if da_kick:
            kenh_thong_bao = message.guild.get_channel(LOG_CHANNEL_ID) or bot.get_channel(LOG_CHANNEL_ID)
            if kenh_thong_bao is None:
                try:
                    kenh_thong_bao = await bot.fetch_channel(LOG_CHANNEL_ID)
                except Exception as e:
                    print(f"[TRAP LỖI] Không tìm thấy kênh thông báo {LOG_CHANNEL_ID}: {e}", flush=True)

            if kenh_thong_bao is not None:
                try:
                    embed_log = discord.Embed(
                        title="🚪 THÔNG BÁO RỜI SERVER (TRAP KICK)",
                        description=(
                            f"👤 **Thành viên:** {message.author.mention} (`{message.author.name}` - ID: `{message.author.id}`)\n"
                            f"📌 **Lý do:** {ly_do_kick}"
                        ),
                        color=discord.Color.orange()
                    )
                    await kenh_thong_bao.send(embed=embed_log)
                except Exception as e:
                    print(f"[TRAP LỖI] Không thể gửi thông báo vào kênh {LOG_CHANNEL_ID}: {e}", flush=True)