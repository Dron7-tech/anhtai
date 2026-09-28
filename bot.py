import os
import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
from keep_alive import keep_alive

# LIÊN KẾT VỚI CÁC MODULE (COGS ARCHITECTURE)
from masoi import phong_choi, GameMaSoi, LobbyMaSoi, tao_embed_lobby, dondep_game
import masoi_engine
import nhatu
import quanlybang
import ticket  
import pinggame # MODULE TÌM TRẬN GAME MỚI

intents = discord.Intents.default()
intents.message_content = True

# ==========================================
# KHỞI TẠO KIẾN TRÚC BOT CHUYÊN NGHIỆP (AUTOSHARDED)
# ==========================================
class AnhTaiBot(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # 1. Khởi chạy các Module con độc lập
        nhatu.setup_nhatu(self)
        quanlybang.setup_bang(self)
        ticket.setup_ticket(self) 
        pinggame.setup_pinggame(self) # Bật Module Ping Game
        
        # 2. Bắn toàn bộ Slash Commands lên máy chủ Discord
        await self.tree.sync()
        print("✅ Đã đồng bộ thành công hệ thống Slash Commands (/) lên Discord!", flush=True)

bot = AnhTaiBot()

phong_coquay = {}

# ==========================================
# CLASS CÒ QUAY NGA
# ==========================================
class LuotCoQuayNga(discord.ui.View):
    def __init__(self, danh_sach, vi_tri, so_lo, vien, channel_id):
        super().__init__(timeout=None)
        self.danh_sach = danh_sach
        self.so_lo = so_lo 
        self.vien = vien
        self.channel_id = channel_id

    @discord.ui.button(label="🔫 Bóp Cò", style=discord.ButtonStyle.danger)
    async def nut_bop_co(self, interaction: discord.Interaction, button: discord.ui.Button):
        nguoi_dang_cam = self.danh_sach[(self.vien - 1) % len(self.danh_sach)]
        if interaction.user != nguoi_dang_cam:
            try: await interaction.response.send_message("❌ Tránh ra! Chưa tới lượt của bạn cầm súng!", ephemeral=True, delete_after=3.0)
            except Exception: pass
        else:
            try: await interaction.response.defer()
            except Exception: pass
            
            for child in self.children: child.disabled = True
            embed = interaction.message.embeds[0]
            embed.color = discord.Color.dark_red()
            
            so_lo_con_lai = self.so_lo - self.vien + 1
            ty_le_chet_phan_tram = round((1 / so_lo_con_lai) * 100, 1)
            
            embed.description = f"🥶 {nguoi_dang_cam.mention} toát mồ hôi lạnh, từ từ kê nòng súng sát vào thái dương...\n*(Tỷ lệ đạn nổ ở lượt này là: **{ty_le_chet_phan_tram}%**)*"
            try: await interaction.edit_original_response(embed=embed, view=self)
            except Exception: pass
            await asyncio.sleep(1.5)
            
            embed.description = f"🤞 Khẽ nhắm chặt mắt... {nguoi_dang_cam.mention} siết cò...\n*(Tỷ lệ đạn nổ ở lượt này là: **{ty_le_chet_phan_tram}%**)*"
            try: await interaction.edit_original_response(embed=embed)
            except Exception: pass
            await asyncio.sleep(2.5)

            is_dead = (random.randint(1, so_lo_con_lai) == 1)

            if is_dead:
                ds_song = [p for p in self.danh_sach if p != nguoi_dang_cam]
                chuoi_song = ", ".join([p.mention for p in ds_song])
                embed.description = f"💥 **ĐÙNG!!!** 💥\n\n🩸 Máu văng tung tóe!\n💀 {nguoi_dang_cam.mention} gục xuống hoàn toàn...\n\n🏆 **NHỮNG NGƯỜI SỐNG SÓT:**\n{chuoi_song}"
                embed.color = discord.Color.from_rgb(139, 0, 0)
                try: await interaction.edit_original_response(embed=embed, view=None)
                except Exception: pass
                if self.channel_id in phong_coquay: del phong_coquay[self.channel_id]
                self.stop()
            else:
                self.vien += 1
                nguoi_tiep = self.danh_sach[(self.vien - 1) % len(self.danh_sach)]
                for child in self.children: child.disabled = False
                embed.color = discord.Color.gold()
                embed.description = f"💨 *Cạch...*\n😅 Đạn lép! {nguoi_dang_cam.mention} thở dốc, run rẩy truyền súng cho người tiếp theo.\n\n🎯 **LƯỢT {self.vien}/{self.so_lo}:**\nĐến lượt {nguoi_tiep.mention} đối mặt với tử thần!"
                try: await interaction.edit_original_response(embed=embed, view=self)
                except Exception: pass

    @discord.ui.button(label="🏳️ Bỏ Cuộc", style=discord.ButtonStyle.secondary)
    async def nut_bo_cuoc(self, interaction: discord.Interaction, button: discord.ui.Button):
        nguoi_dang_cam = self.danh_sach[(self.vien - 1) % len(self.danh_sach)]
        if interaction.user != nguoi_dang_cam:
            try: await interaction.response.send_message("❌ Bạn không cầm súng thì bỏ cuộc kiểu gì?", ephemeral=True, delete_after=3.0)
            except Exception: pass
        else:
            try: await interaction.response.defer()
            except Exception: pass
            for child in self.children: child.disabled = True
            
            self.danh_sach.remove(nguoi_dang_cam)
            embed = interaction.message.embeds[0]
            
            if len(self.danh_sach) == 1:
                embed.color = discord.Color.green()
                embed.description = f"🏳️ {nguoi_dang_cam.mention} đã sợ hãi vứt súng bỏ chạy!\n\n🏆 {self.danh_sach[0].mention} là người cuối cùng trụ lại và giành chiến thắng tuyệt đối!"
                try: await interaction.edit_original_response(embed=embed, view=None)
                except Exception: pass
                if self.channel_id in phong_coquay: del phong_coquay[self.channel_id]
                self.stop()
            else:
                nguoi_tiep = self.danh_sach[(self.vien - 1) % len(self.danh_sach)]
                for child in self.children: child.disabled = False
                embed.color = discord.Color.orange()
                
                so_lo_con_lai = self.so_lo - self.vien + 1
                ty_le_chet_phan_tram = round((1 / so_lo_con_lai) * 100, 1)
                
                embed.description = f"🏳️ {nguoi_dang_cam.mention} đã hèn nhát bỏ chạy rớt cả dép!\n\n🎯 **LƯỢT {self.vien}/{self.so_lo}:**\nSúng được truyền lại cho {nguoi_tiep.mention}!\n*(Tỷ lệ đạn nổ ở lượt này vẫn là: **{ty_le_chet_phan_tram}%**)*"
                try: await interaction.edit_original_response(embed=embed, view=self)
                except Exception: pass

class LobbyCoQuayNga(discord.ui.View):
    def __init__(self, host, channel_id):
        super().__init__(timeout=None)
        self.host = host
        self.nguoi_choi = [host]
        self.channel_id = channel_id

    @discord.ui.button(label="✋ Tham Gia", style=discord.ButtonStyle.primary)
    async def nut_tham_gia(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.nguoi_choi:
            try: await interaction.response.send_message("❌ Bạn đã ở trong sảnh rồi!", ephemeral=True, delete_after=3.0)
            except Exception: pass
        else:
            try: await interaction.response.defer()
            except Exception: pass
            self.nguoi_choi.append(interaction.user)
            embed = interaction.message.embeds[0]
            ds_chuoi = "\n".join([f"• {p.mention}" for p in self.nguoi_choi])
            embed.description = f"👑 **Chủ phòng:** {self.host.mention}\n\n👥 **Danh sách người chơi ({len(self.nguoi_choi)} người):**\n{ds_chuoi}\n\n*(Mỗi người tham gia sẽ tăng thêm 3 lỗ đạn trống)*"
            try: await interaction.edit_original_response(embed=embed, view=self)
            except Exception: pass

    @discord.ui.button(label="▶️ Bắt Đầu", style=discord.ButtonStyle.success)
    async def nut_bat_dau(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.host:
            try: await interaction.response.send_message("❌ Chỉ chủ phòng mới được quyền bắt đầu!", ephemeral=True, delete_after=3.0)
            except Exception: pass
        else:
            if len(self.nguoi_choi) < 2:
                try: await interaction.response.send_message("❌ Cần ít nhất 2 người để bắt đầu trò chơi!", ephemeral=True, delete_after=3.0)
                except Exception: pass
            else:
                try: await interaction.response.defer()
                except Exception: pass
                embed = interaction.message.embeds[0]
                embed.color = discord.Color.red()
                embed.description = "🔥 Trò chơi sinh tử chính thức bắt đầu!\n\n🔫 Đang mở ổ súng..."
                try: await interaction.edit_original_response(embed=embed, view=None)
                except Exception: pass
                random.shuffle(self.nguoi_choi)
                so_lo = len(self.nguoi_choi) * 3
                vi_tri_dan = random.randint(1, so_lo)
                await asyncio.sleep(2)
                embed.description = f"🌀 Đang nạp 1 viên đạn duy nhất vào ổ súng có **{so_lo} lỗ**...\n*Rẹt rẹt rẹt...* Khóa nòng! 🔒"
                try: await interaction.edit_original_response(embed=embed)
                except Exception: pass
                await asyncio.sleep(2.5)
                view_moi = LuotCoQuayNga(self.nguoi_choi, vi_tri_dan, so_lo, 1, self.channel_id)
                nguoi_dau = self.nguoi_choi[0]
                
                ty_le_chet_phan_tram = round((1 / so_lo) * 100, 1)
                
                embed.description = f"🎯 **LƯỢT 1/{so_lo}:**\nKhẩu súng lạnh ngắt đang được đặt vào tay {nguoi_dau.mention}!\nBóp cò hay hèn nhát bỏ cuộc?\n*(Tỷ lệ đạn nổ ở lượt này là: **{ty_le_chet_phan_tram}%**)*"
                try: await interaction.edit_original_response(embed=embed, view=view_moi)
                except Exception: pass
                self.stop()

    @discord.ui.button(label="❌ Hủy", style=discord.ButtonStyle.danger)
    async def nut_huy(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.host:
            try: await interaction.response.send_message("❌ Chỉ chủ phòng mới được quyền hủy!", ephemeral=True, delete_after=3.0)
            except Exception: pass
        else:
            try: await interaction.response.defer()
            except Exception: pass
            embed = interaction.message.embeds[0]
            embed.color = discord.Color.dark_grey()
            embed.description = "🛑 Trò chơi đã bị hủy bởi chủ phòng."
            try: await interaction.edit_original_response(embed=embed, view=None)
            except Exception: pass
            if self.channel_id in phong_coquay: del phong_coquay[self.channel_id]
            self.stop()

# ==========================================
# CÁC SỰ KIỆN QUAN TRỌNG CỦA BOT
# ==========================================
@bot.event
async def on_ready():
    print(f"✅ Bot {bot.user} đã trực tuyến!", flush=True)
    print(f"🌐 Hệ thống đang hoạt động với {bot.shard_count} Shard(s) phân luồng mạng.", flush=True)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound): return 
    print(f"[RADAR BẮT LỖI] User {ctx.author} gặp lỗi: {error}", flush=True)

# ==========================================
# HỆ THỐNG SLASH COMMANDS (/)
# ==========================================

@bot.tree.command(name="ver", description="Kiểm tra phiên bản hiện tại của hệ thống Bot")
async def slash_ver(interaction: discord.Interaction):
    await interaction.response.send_message("🤖 Phiên bản hiện tại: **1.0.5 (Tích hợp Ping Game Tự Động)**", ephemeral=True)

@bot.tree.command(name="help", description="Hiển thị bảng danh sách các lệnh của Bot")
async def slash_help(interaction: discord.Interaction):
    embed = discord.Embed(title="📚 BẢNG HƯỚNG DẪN SỬ DỤNG BOT", color=discord.Color.blue())
    embed.description = "Dưới đây là danh sách các lệnh Slash (/) hiện có của hệ thống. Bạn chỉ cần gõ ký tự `/` và chọn lệnh tương ứng để sử dụng."
    
    embed.add_field(name="🎮 Tìm Trận Cùng Anh Em", value="`/pingvalorant` : Đăng bài tìm đồng đội Valorant (Tự động bắt Voice)", inline=False)
    embed.add_field(name="🎲 Giải Trí & Tiện Ích", value="`/tungxu` : Tung đồng xu nhân phẩm (Sấp/Ngửa)\n`/chon` : Nhờ bot nhắm mắt chọn bừa 1 phương án\n`/chiabang` : Chia đội ngẫu nhiên (Ví dụ: 5v5, 2v2)", inline=False)
    embed.add_field(name="🎭 Trò Chơi (Boardgame)", value="`/taophongmasoi` : Khởi tạo sảnh chờ game Ma Sói\n`/taophongcoquay` : Khởi tạo sảnh chờ Cò Quay Nga", inline=False)
    embed.add_field(name="⚖️ Hệ Thống Nhà Tù (Admin)", value="`/jail` : Bắt giam thành viên phạm luật\n`/unjail` : Đặc xá, ân xá cho tù nhân\n`/kiemtratu` : Xem thông tin và thời gian án phạt", inline=False)
    embed.add_field(name="📊 Quản Lý Bảng (Admin)", value="`/taobang` : Tạo bảng duy trì điểm danh theo tháng\n`/copybang` : Chuyển dữ liệu điểm danh sang tháng mới", inline=False)
    embed.add_field(name="🎟️ Hệ Thống Ticket (Admin)", value="`/ticket_panel` : Gửi bảng điều khiển để member tạo Ticket", inline=False)
    embed.add_field(name="⚙️ Hệ Thống", value="`/ver` : Kiểm tra phiên bản Bot\n`/help` : Mở bảng hướng dẫn này", inline=False)
    
    embed.set_footer(text="Mọi ý tưởng, thắc mắc, lỗi của BOT vui lòng liên hệ ADMIN để báo cáo.")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="tungxu", description="Tung đồng xu nhân phẩm (Sấp/Ngửa)")
async def slash_tungxu(interaction: discord.Interaction):
    ket_qua = random.choice(["Mặt SẤP 🪙", "Mặt NGỬA 🪙"])
    await interaction.response.send_message(f"🎲 {interaction.user.mention} vừa tung đồng xu và nhận được: **{ket_qua}**")

@bot.tree.command(name="chon", description="Nhờ thần Khỉ nhắm mắt chọn bừa 1 người hoặc 1 phương án")
@app_commands.describe(danh_sach="Nhập các lựa chọn, cách nhau bằng dấu phẩy (Ví dụ: Tài, Sáng, Thế)")
async def slash_chon(interaction: discord.Interaction, danh_sach: str):
    cac_lua_chon = [nguoi.strip() for nguoi in danh_sach.split(',')] if ',' in danh_sach else [nguoi.strip() for nguoi in danh_sach.split()]
    cac_lua_chon = [nguoi for nguoi in cac_lua_chon if nguoi]
    
    if len(cac_lua_chon) < 2: 
        await interaction.response.send_message("🤔 Phải nhập ít nhất 2 lựa chọn thì mới gọi là chọn ngẫu nhiên chứ!", ephemeral=True)
        return
        
    ket_qua = random.choice(cac_lua_chon)
    await interaction.response.send_message(f"🎲 Khỉ thần nhắm mắt chọn bừa...\n🎯 Lựa chọn cuối cùng là: **{ket_qua}** 🎉")

@bot.tree.command(name="chiabang", description="Tự động xáo trộn và chia nhóm thành 2 đội")
@app_commands.describe(the_thuc="Ví dụ: 5v5, 2v2", danh_sach="Tag người chơi hoặc nhập tên, cách nhau bằng dấu phẩy")
async def slash_chiabang(interaction: discord.Interaction, the_thuc: str, danh_sach: str):
    nguoi_choi = [nguoi.strip() for nguoi in danh_sach.split(',')] if ',' in danh_sach else [nguoi.strip() for nguoi in danh_sach.split()]
    nguoi_choi = [nguoi for nguoi in nguoi_choi if nguoi]
    
    if len(nguoi_choi) < 2: 
        await interaction.response.send_message("🤔 Phải có ít nhất 2 người mới chia bảng được!", ephemeral=True)
        return
        
    nguoi_choi = random.sample(nguoi_choi, len(nguoi_choi))
    diem_giua = random.choice([len(nguoi_choi) // 2, (len(nguoi_choi) + 1) // 2]) if len(nguoi_choi) % 2 != 0 else len(nguoi_choi) // 2
    doi_1, doi_2 = nguoi_choi[:diem_giua], nguoi_choi[diem_giua:]
    
    chuoi_doi_1 = "\n".join([f"• {nguoi}" for nguoi in doi_1])
    chuoi_doi_2 = "\n".join([f"• {nguoi}" for nguoi in doi_2])
    
    embed = discord.Embed(title=f"⚔️ BẢNG ĐẤU: {the_thuc.upper()}", color=discord.Color.red())
    embed.add_field(name=f"🔴 ĐỘI ĐỎ ({len(doi_1)} người)", value=chuoi_doi_1, inline=True)
    embed.add_field(name=f"🔵 ĐỘI XANH ({len(doi_2)} người)", value=chuoi_doi_2, inline=True)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="taophongmasoi", description="Khởi tạo sảnh chờ Boardgame Ma Sói")
async def slash_taophongmasoi(interaction: discord.Interaction):
    if interaction.channel.id in phong_choi:
        await interaction.response.send_message("⚠️ Kênh này đang diễn ra một trận Ma Sói rồi! Hãy chờ kết thúc hoặc tạo ở kênh khác.", ephemeral=True)
    else:
        try:
            await interaction.response.defer()
            game = GameMaSoi(interaction.user, interaction.channel)
            game.nguoi_choi.append(interaction.user)
            phong_choi[interaction.channel.id] = game
            game.main_message = await interaction.followup.send(embed=tao_embed_lobby(game), view=LobbyMaSoi(game))
        except Exception as e:
            print(f"Lỗi khởi tạo phòng ma sói: {e}", flush=True)

@bot.tree.command(name="taophongcoquay", description="Khởi tạo sảnh chờ sinh tử Cò Quay Nga")
async def slash_taophongcoquay(interaction: discord.Interaction):
    if interaction.channel.id in phong_coquay:
        await interaction.response.send_message("⚠️ Kênh này đang diễn ra một trận Cò Quay Nga rồi! Hãy chờ kết thúc hoặc tạo ở kênh khác.", ephemeral=True)
    else:
        phong_coquay[interaction.channel.id] = True
        embed = discord.Embed(title="💥 PHÒNG CHỜ CÒ QUAY NGA 💥", color=discord.Color.dark_red())
        embed.description = f"👑 **Chủ phòng:** {interaction.user.mention}\n\n👥 **Danh sách người chơi (1 người):**\n• {interaction.user.mention}\n\n*(Mỗi người tham gia sẽ tăng thêm 3 lỗ đạn trống)*"
        view = LobbyCoQuayNga(interaction.user, interaction.channel.id)
        await interaction.response.send_message(content=interaction.user.mention, embed=embed, view=view)

if __name__ == "__main__":
    keep_alive()
    token = os.environ.get("DISCORD_TOKEN")
    if token is None: 
        print("LỖI: Chưa cài đặt DISCORD_TOKEN trong phần Settings -> Variables and secrets!", flush=True)
    else: 
        bot.run(token)