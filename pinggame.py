import discord
from discord import app_commands

# ==========================================
# CLASS GIAO DIỆN NÚT BẤM VÀO VOICE
# ==========================================
class GamePingView(discord.ui.View):
    def __init__(self, invite_url=None):
        super().__init__(timeout=None)
        # Nút Link cực kỳ an toàn: Discord sẽ tự mở phòng Voice khi người dùng click vào
        if invite_url:
            self.add_item(discord.ui.Button(label="🔊 Tham Gia Voice Cùng Chủ Phòng", style=discord.ButtonStyle.link, url=invite_url))

# ==========================================
# KHỞI TẠO LỆNH SLASH CHO GAME
# ==========================================
def setup_pinggame(bot):
    @bot.tree.command(name="pingvalorant", description="Tìm đồng đội chiến Valorant")
    @app_commands.describe(
        ma_phong="Mã phòng hoặc Riot ID của bạn",
        rank="Rank yêu cầu (VD: Đồng, Bạc, Kim Cương...)",
        so_luong="Số lượng người đang thiếu",
        che_do="Chế độ chơi (Bỏ trống nếu không cần)"
    )
    # Tạo lựa chọn sẵn cho chế độ, user không bắt buộc phải chọn
    @app_commands.choices(che_do=[
        app_commands.Choice(name="Vui vẻ / Giải trí", value="Vui Vẻ"),
        app_commands.Choice(name="Tryhard / Cày Rank", value="Tryhard")
    ])
    async def slash_pingvalorant(interaction: discord.Interaction, ma_phong: str, rank: str, so_luong: int, che_do: app_commands.Choice[str] = None):
        await interaction.response.defer()
        
        # Xử lý phần chế độ chơi (Nếu user bỏ trống thì mặc định là tùy hứng)
        che_do_str = che_do.value if che_do else "Bắn tùy hứng (Không yêu cầu)"
        
        # Thiết kế Bảng thông tin (Embed) với màu Đỏ đặc trưng của Valorant
        embed = discord.Embed(title="🎮 TÌM ĐỒNG ĐỘI VALORANT", color=0xFA4454) 
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        
        embed.add_field(name="👑 Chủ phòng", value=interaction.user.mention, inline=False)
        embed.add_field(name="🆔 Riot ID / Code", value=f"`{ma_phong}`", inline=True)
        embed.add_field(name="🏆 Rank yêu cầu", value=f"**{rank}**", inline=True)
        embed.add_field(name="👥 Thiếu", value=f"**{so_luong} người**", inline=True)
        embed.add_field(name="🎯 Chế độ", value=f"**{che_do_str}**", inline=False)
        
        invite_url = None
        view = discord.ui.View() # Mặc định là không có nút
        
        # LÔ-GÍC THÔNG MINH: Kiểm tra xem người gõ lệnh có đang ở trong Voice không (bao gồm cả đang Live)
        if interaction.user.voice and interaction.user.voice.channel:
            voice_channel = interaction.user.voice.channel
            try:
                # Tự động tạo một vé mời (invite) vào thẳng kênh Voice đó. Hạn sử dụng 2 tiếng để chống rác server.
                invite = await voice_channel.create_invite(max_age=7200, max_uses=0, reason="Lệnh Ping Valorant")
                invite_url = invite.url
                embed.add_field(name="🔊 Kênh đàm thoại", value=voice_channel.mention, inline=False)
                
                # Cập nhật lại giao diện, nhúng nút bấm vào
                view = GamePingView(invite_url=invite_url)
            except Exception as e:
                print(f"Lỗi tạo link Voice: {e}")
        else:
            embed.set_footer(text="Chủ phòng hiện không có mặt trong kênh Voice nào.")
            
        # Đẩy thông báo lên kênh
        await interaction.followup.send(content="🚀 Có anh em nào lên rank Valorant không, vào việc luôn!", embed=embed, view=view)