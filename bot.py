import os
import discord
from discord.ext import commands
import json
import random
import asyncio
from keep_alive import keep_alive

# LIÊN KẾT VỚI FILE masoi.py
from masoi import phong_choi, GameMaSoi, LobbyMaSoi, tao_embed_lobby, dondep_game
import masoi_engine

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

phong_coquay = {}

DANH_SACH_QUAN_LY = [
    1028173204029722696,  
    999988887777666655   
]

def co_quyen_quan_ly(user):
    if user.guild_permissions.administrator: return True
    if user.id in DANH_SACH_QUAN_LY: return True
    return False

def lay_ten_file(thang): return f"bang_thang_{thang}.json"

def doc_du_lieu(thang):
    if os.path.exists(lay_ten_file(thang)):
        try:
            with open(lay_ten_file(thang), "r", encoding="utf-8") as f: 
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception as e:
            print(f"Lỗi đọc file dữ liệu {thang}: {e}")
            return {}
    return {}

def luu_du_lieu(thang, data):
    try:
        with open(lay_ten_file(thang), "w", encoding="utf-8") as f: 
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Lỗi lưu file dữ liệu {thang}: {e}")

def tao_embed_bang(thang, data):
    embed = discord.Embed(title=f"📊 BẢNG DUY TRÌ SERVER - THÁNG {thang}", color=discord.Color.blue())
    chuoi_hien_thi = ""
    for id_hoac_ten, info in data.items():
        if isinstance(info, dict):
            trang_thai = "✅ Đã đóng" if info.get("status", False) else "❌ Chưa đóng"
            chuoi_hien_thi += f"• {id_hoac_ten}: {trang_thai}\n"
    embed.description = chuoi_hien_thi if chuoi_hien_thi else "Danh sách đang trống."
    return embed

class BangDieuKhienBiMat(discord.ui.View):
    def __init__(self, thang, data, tin_nhan_public):
        super().__init__(timeout=None)
        self.thang = str(thang)
        self.tin_nhan_public = tin_nhan_public
        self.nguoi_chon = None
        
        options = []
        for id_hoac_ten, info in data.items():
            if isinstance(info, dict):
                ten = str(info.get("name", id_hoac_ten))[:95]
                val = str(id_hoac_ten)[:95]
                if not ten.strip(): ten = "Unknown"
                if not val.strip(): val = "Unknown_Val"
                options.append(discord.SelectOption(label=ten, value=val))
                
        if not options: 
            options.append(discord.SelectOption(label="Trống", value="none"))
            
        self.menu = discord.ui.Select(placeholder="1. Chọn người chơi ở đây...", options=options[:25])
        self.menu.callback = self.khi_chon_menu
        self.add_item(self.menu)

    async def khi_chon_menu(self, interaction: discord.Interaction):
        self.nguoi_chon = self.menu.values[0]
        try: await interaction.response.defer()
        except Exception: pass

    async def cap_nhat_giao_dien(self, interaction, data, thong_bao):
        luu_du_lieu(self.thang, data)
        try: await self.tin_nhan_public.edit(embed=tao_embed_bang(self.thang, data))
        except Exception: pass
        try: 
            await interaction.edit_original_response(content=thong_bao, view=BangDieuKhienBiMat(self.thang, data, self.tin_nhan_public))
        except Exception as e:
            print(f"Lỗi update UI nội bộ: {e}")

    @discord.ui.button(label="2. ✅ Tick", style=discord.ButtonStyle.success)
    async def nut_da_dong(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.nguoi_chon or self.nguoi_chon == "none":
            try: await interaction.response.send_message("⚠️ Vui lòng chọn 1 người từ Menu!\n*(Tin nhắn này sẽ tự biến mất sau 3s)*", ephemeral=True, delete_after=3.0)
            except Exception: pass
            return
            
        try: await interaction.response.defer()
        except Exception: pass
        data = doc_du_lieu(self.thang)
        key_goc = next((k for k in data if k.startswith(self.nguoi_chon)), None)
        if key_goc: data[key_goc]["status"] = True
        await self.cap_nhat_giao_dien(interaction, data, "✅ Đã đánh dấu Đã Đóng!")

    @discord.ui.button(label="2. ❌ Bỏ Tick", style=discord.ButtonStyle.danger)
    async def nut_chua_dong(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.nguoi_chon or self.nguoi_chon == "none":
            try: await interaction.response.send_message("⚠️ Vui lòng chọn 1 người từ Menu!\n*(Tin nhắn này sẽ tự biến mất sau 3s)*", ephemeral=True, delete_after=3.0)
            except Exception: pass
            return
            
        try: await interaction.response.defer()
        except Exception: pass
        data = doc_du_lieu(self.thang)
        key_goc = next((k for k in data if k.startswith(self.nguoi_chon)), None)
        if key_goc: data[key_goc]["status"] = False
        await self.cap_nhat_giao_dien(interaction, data, "❌ Đã Reset về Chưa Đóng!")

    @discord.ui.button(label="3. 🗑️ Xóa", style=discord.ButtonStyle.secondary)
    async def nut_xoa(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.nguoi_chon or self.nguoi_chon == "none":
            try: await interaction.response.send_message("⚠️ Vui lòng chọn 1 người từ Menu!\n*(Tin nhắn này sẽ tự biến mất sau 3s)*", ephemeral=True, delete_after=3.0)
            except Exception: pass
            return
            
        try: await interaction.response.defer()
        except Exception: pass
        data = doc_du_lieu(self.thang)
        key_goc = next((k for k in data if k.startswith(self.nguoi_chon)), None)
        if key_goc: del data[key_goc]
        await self.cap_nhat_giao_dien(interaction, data, "🗑️ Đã xóa người này khỏi danh sách!")

class NutGoiDieuKhien(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="⚙️ Mở Bảng Điều Khiển", style=discord.ButtonStyle.primary, custom_id="nut_quan_ly_vinh_vien")
    async def mo_bang_dieu_khien(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not co_quyen_quan_ly(interaction.user):
            try: await interaction.response.send_message("❌ Bạn không có quyền truy cập!\n*(Tin nhắn này sẽ tự biến mất sau 3s)*", ephemeral=True, delete_after=3.0)
            except Exception: pass
            return
            
        try: 
            if not interaction.message.embeds or not interaction.message.embeds[0].title:
                await interaction.response.send_message("❌ Bảng điều khiển cũ đã hỏng hoặc không có dữ liệu!", ephemeral=True)
                return
                
            thang = interaction.message.embeds[0].title.split("THÁNG ")[-1].strip()
            data = doc_du_lieu(thang)
            
            await interaction.response.send_message(
                content=f"🛠️ **Khu vực quản lý (Chỉ bạn nhìn thấy) - Tháng {thang}**\nHãy chọn người cần cập nhật:", 
                view=BangDieuKhienBiMat(thang, data, interaction.message), 
                ephemeral=True
            )
        except Exception as e: 
            print(f"Lỗi mở bảng điều khiển: {e}")
            try: await interaction.response.send_message("❌ Có lỗi xảy ra khi load dữ liệu của bảng.", ephemeral=True)
            except Exception: pass

class LuotCoQuayNga(discord.ui.View):
    def __init__(self, danh_sach, vi_tri, so_lo, vien, channel_id):
        super().__init__(timeout=None)
        self.danh_sach = danh_sach
        # Không dùng vi_tri nữa, thay vào đó dùng so_lo và vien để tính % nổ
        self.so_lo = so_lo 
        self.vien = vien
        self.channel_id = channel_id

    @discord.ui.button(label="🔫 Bóp Cò", style=discord.ButtonStyle.danger)
    async def nut_bop_co(self, interaction: discord.Interaction, button: discord.ui.Button):
        nguoi_dang_cam = self.danh_sach[(self.vien - 1) % len(self.danh_sach)]
        if interaction.user != nguoi_dang_cam:
            try: await interaction.response.send_message("❌ Tránh ra! Chưa tới lượt của bạn cầm súng!\n*(Tin nhắn này sẽ tự biến mất sau 3s)*", ephemeral=True, delete_after=3.0)
            except Exception: pass
        else:
            try: await interaction.response.defer()
            except Exception: pass
            
            for child in self.children: child.disabled = True
            embed = interaction.message.embeds[0]
            embed.color = discord.Color.dark_red()
            
            # Tính toán xác suất nổ dựa trên viên đạn hiện tại
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

            # Thuật toán quay Random theo tỷ lệ
            # random.randint(1, so_lo_con_lai) == 1 mô phỏng chính xác việc 1 viên đạn trong số các lỗ còn lại
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
                embed.description = f"💨 *Cạch...*\n😅 Đạn lép! {nguoi_dang_cam.mention} thở dốc, run rẩy đưa súng cho người tiếp theo.\n\n🎯 **LƯỢT {self.vien}/{self.so_lo}:**\nĐến lượt {nguoi_tiep.mention} đối mặt với tử thần!"
                try: await interaction.edit_original_response(embed=embed, view=self)
                except Exception: pass

    @discord.ui.button(label="🏳️ Bỏ Cuộc", style=discord.ButtonStyle.secondary)
    async def nut_bo_cuoc(self, interaction: discord.Interaction, button: discord.ui.Button):
        nguoi_dang_cam = self.danh_sach[(self.vien - 1) % len(self.danh_sach)]
        if interaction.user != nguoi_dang_cam:
            try: await interaction.response.send_message("❌ Bạn không cầm súng thì bỏ cuộc kiểu gì?\n*(Tin nhắn này sẽ tự biến mất sau 3s)*", ephemeral=True, delete_after=3.0)
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
                self.vien += 1
                nguoi_tiep = self.danh_sach[(self.vien - 1) % len(self.danh_sach)]
                for child in self.children: child.disabled = False
                embed.color = discord.Color.orange()
                embed.description = f"🏳️ {nguoi_dang_cam.mention} đã hèn nhát bỏ chạy rớt cả dép!\n\n🎯 **LƯỢT {self.vien}/{self.so_lo}:**\nSúng được nhặt lên bởi {nguoi_tiep.mention}!"
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
            try: await interaction.response.send_message("❌ Bạn đã ở trong sảnh rồi!\n*(Tin nhắn này sẽ tự biến mất sau 3s)*", ephemeral=True, delete_after=3.0)
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
            try: await interaction.response.send_message("❌ Chỉ chủ phòng mới được quyền bắt đầu!\n*(Tin nhắn này sẽ tự biến mất sau 3s)*", ephemeral=True, delete_after=3.0)
            except Exception: pass
        else:
            if len(self.nguoi_choi) < 2:
                try: await interaction.response.send_message("❌ Cần ít nhất 2 người để bắt đầu trò chơi!\n*(Tin nhắn này sẽ tự biến mất sau 3s)*", ephemeral=True, delete_after=3.0)
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
                embed.description = f"🎯 **LƯỢT 1/{so_lo}:**\nKhẩu súng lạnh ngắt đang được đặt vào tay {nguoi_dau.mention}!\nBóp cò hay hèn nhát bỏ cuộc?"
                try: await interaction.edit_original_response(embed=embed, view=view_moi)
                except Exception: pass
                self.stop()

    @discord.ui.button(label="❌ Hủy", style=discord.ButtonStyle.danger)
    async def nut_huy(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.host:
            try: await interaction.response.send_message("❌ Chỉ chủ phòng mới được quyền hủy!\n*(Tin nhắn này sẽ tự biến mất sau 3s)*", ephemeral=True, delete_after=3.0)
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

@bot.event
async def on_ready():
    bot.add_view(NutGoiDieuKhien())
    print(f"✅ Bot {bot.user} đã sẵn sàng toàn bộ (Đồng bộ bảng và Cò quay)!")

@bot.command()
async def ver(ctx):
    try: await ctx.send("🤖 Phiên bản hiện tại của bot: **0.71**")
    except Exception: pass

# ==========================================
# LỆNH GỌI TRÒ CHƠI MA SÓI TỪ FILE masoi.py
# ==========================================
@bot.command()
async def taophongmasoi(ctx):
    if ctx.channel.id in phong_choi:
        try: await ctx.send("⚠️ Kênh này đang diễn ra một trận Ma Sói rồi! Hãy chờ kết thúc hoặc tạo ở kênh khác.")
        except Exception: pass
    else:
        try:
            game = GameMaSoi(ctx.author, ctx.channel)
            game.nguoi_choi.append(ctx.author)
            phong_choi[ctx.channel.id] = game
            game.main_message = await ctx.send(embed=tao_embed_lobby(game), view=LobbyMaSoi(game))
        except Exception as e:
            print(f"Lỗi khởi tạo phòng ma sói: {e}")
            try: await ctx.send(f"❌ Có lỗi nội bộ khi liên kết mô-đun Ma Sói: `{e}`")
            except Exception: pass

@bot.command()
async def taophongcoquay(ctx):
    if ctx.channel.id in phong_coquay:
        try: await ctx.send("⚠️ Kênh này đang diễn ra một trận Cò Quay Nga rồi! Hãy chờ kết thúc hoặc tạo ở kênh khác.")
        except Exception: pass
    else:
        phong_coquay[ctx.channel.id] = True
        chuoi_tag = " ".join([m.mention for m in ctx.message.mentions]) if ctx.message.mentions else ""
        embed = discord.Embed(title="💥 PHÒNG CHỜ CÒ QUAY NGA 💥", color=discord.Color.dark_red())
        embed.description = f"👑 **Chủ phòng:** {ctx.author.mention}\n\n👥 **Danh sách người chơi (1 người):**\n• {ctx.author.mention}\n\n*(Mỗi người tham gia sẽ tăng thêm 3 lỗ đạn trống)*"
        view = LobbyCoQuayNga(ctx.author, ctx.channel.id)
        try: await ctx.send(content=chuoi_tag, embed=embed, view=view)
        except Exception: pass

@bot.command()
async def taobang(ctx, thang: str, *, danh_sach: str = ""):
    if not co_quyen_quan_ly(ctx.author): return 
    data = doc_du_lieu(thang)
    if danh_sach:
        cac_thanh_vien = [ten.strip() for ten in danh_sach.split(',')] if ',' in danh_sach else [ten.strip() for ten in danh_sach.split()]
        for chuoi_nhap in cac_thanh_vien:
            if chuoi_nhap:
                ten_hien_thi = chuoi_nhap
                for mem in ctx.message.mentions:
                    if str(mem.id) in chuoi_nhap:
                        ten_hien_thi = mem.display_name
                        break
                if chuoi_nhap not in data: data[chuoi_nhap] = {"name": ten_hien_thi, "status": False}
    luu_du_lieu(thang, data)
    embed_moi = tao_embed_bang(thang, data)
    da_xu_ly = False
    
    try:
        async for msg in ctx.channel.history(limit=100):
            if msg.author == bot.user and msg.embeds:
                if msg.embeds[0].title == f"📊 BẢNG DUY TRÌ SERVER - THÁNG {thang}":
                    try: await msg.edit(embed=embed_moi, view=NutGoiDieuKhien())
                    except Exception: pass
                    try: await ctx.message.delete()
                    except Exception: pass
                    da_xu_ly = True
                    break 
    except Exception:
        pass
        
    if not da_xu_ly:
        try: await ctx.send(embed=embed_moi, view=NutGoiDieuKhien())
        except Exception: pass
        try: await ctx.message.delete()
        except Exception: pass

@bot.command()
async def copybang(ctx, thang_cu: str, thang_moi: str):
    if not co_quyen_quan_ly(ctx.author): return
    data_cu = doc_du_lieu(thang_cu)
    if not data_cu: 
        try: await ctx.send(f"⚠️ Không tìm thấy file dữ liệu của tháng {thang_cu}!")
        except Exception: pass
        return
        
    data_moi = doc_du_lieu(thang_moi)
    for id_hoac_ten, info in data_cu.items():
        if isinstance(info, dict):
            if id_hoac_ten not in data_moi: 
                data_moi[id_hoac_ten] = {"name": info.get("name", id_hoac_ten), "status": False}
    luu_du_lieu(thang_moi, data_moi)
    try: await ctx.send(f"✅ Đã sao chép danh sách sang **tháng {thang_moi}**!")
    except Exception: pass
    try: await ctx.send(embed=tao_embed_bang(thang_moi, data_moi), view=NutGoiDieuKhien())
    except Exception: pass

@bot.command()
async def chiabang(ctx, the_thuc: str, *, danh_sach: str = ""):
    if not danh_sach: 
        try: await ctx.send("⚠️ Bạn chưa nhập danh sách! Cú pháp: `!chiabang 5v5 @nguoi1, @nguoi2, tên1, tên2`")
        except Exception: pass
    else:
        nguoi_choi = [nguoi.strip() for nguoi in danh_sach.split(',')] if ',' in danh_sach else [nguoi.strip() for nguoi in danh_sach.split()]
        nguoi_choi = [nguoi for nguoi in nguoi_choi if nguoi]
        if len(nguoi_choi) < 2: 
            try: await ctx.send("🤔 Phải có ít nhất 2 người mới chia bảng được!")
            except Exception: pass
        else:
            nguoi_choi = random.sample(nguoi_choi, len(nguoi_choi))
            diem_giua = random.choice([len(nguoi_choi) // 2, (len(nguoi_choi) + 1) // 2]) if len(nguoi_choi) % 2 != 0 else len(nguoi_choi) // 2
            doi_1, doi_2 = nguoi_choi[:diem_giua], nguoi_choi[diem_giua:]
            chuoi_doi_1 = "\n".join([f"• {nguoi}" for nguoi in doi_1])
            chuoi_doi_2 = "\n".join([f"• {nguoi}" for nguoi in doi_2])
            embed = discord.Embed(title=f"⚔️ BẢNG ĐẤU: {the_thuc.upper()}", color=discord.Color.red())
            embed.add_field(name=f"🔴 ĐỘI ĐỎ ({len(doi_1)} người)", value=chuoi_doi_1, inline=True)
            embed.add_field(name=f"🔵 ĐỘI XANH ({len(doi_2)} người)", value=chuoi_doi_2, inline=True)
            try: await ctx.send(embed=embed)
            except Exception: pass

@bot.command()
async def tungxu(ctx):
    ket_qua = random.choice(["Mặt SẤP 🪙", "Mặt NGỬA 🪙"])
    try: await ctx.send(f"🎲 {ctx.author.mention} vừa tung đồng xu và nhận được: **{ket_qua}**")
    except Exception: pass

@bot.command()
async def chon(ctx, *, danh_sach: str = ""):
    if not danh_sach: 
        try: await ctx.send("⚠️ Bạn chưa nhập gì cả! Cú pháp đúng: `!chon người A, người B, người C`")
        except Exception: pass
    else:
        cac_lua_chon = [nguoi.strip() for nguoi in danh_sach.split(',')] if ',' in danh_sach else [nguoi.strip() for nguoi in danh_sach.split()]
        cac_lua_chon = [nguoi for nguoi in cac_lua_chon if nguoi]
        if len(cac_lua_chon) < 2: 
            try: await ctx.send("🤔 Phải nhập ít nhất 2 người thì mới gọi là chọn ngẫu nhiên chứ!")
            except Exception: pass
        else:
            ket_qua = random.choice(cac_lua_chon)
            try: await ctx.send(f"🎲 Khỉ thần nhắm mắt chọn bừa...\n🎯 Người được chọn mặt gửi vàng chính là: **{ket_qua}** 🎉")
            except Exception: pass

if __name__ == "__main__":
    keep_alive()
    token = os.environ.get("DISCORD_TOKEN")
    if token is None: print("LỖI: Chưa cài đặt DISCORD_TOKEN trong phần Settings -> Variables and secrets!")
    else: bot.run(token)