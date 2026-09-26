import discord
import random
import asyncio

# ==========================================
# CÁC BIẾN CƠ BẢN VÀ TỪ ĐIỂN CỦA GAME
# ==========================================
phong_choi = {}

DS_DAN = ["tientri", "phuthuy", "baove", "thosan", "cupid", "cobe", "gialang", "kengoc", "detethan", "hiepsi", "quangau", "concao", "goihon", "phapsucam", "haichiem", "baanh_em", "trehoang"]
DS_SOI = ["soicon", "soitt", "soichua", "soi_hacam", "soi_laynhiem", "soi_acmong", "taysai", "hoasoi"]
DS_PHE3 = ["soitrang", "thoitieu", "chandoi", "thiensu", "ketrom", "giaochu", "satthu", "macayrong"]

TUDIEN_VAI = {
    "danlang": "Dân Làng 🧑‍🌾", "tientri": "Tiên Tri 👁️", "phuthuy": "Phù Thủy 🧪", "baove": "Bảo Vệ 🛡️",
    "thosan": "Thợ Săn 🏹", "cupid": "Thần Tình Yêu 💘", "cobe": "Cô Bé 👧", "gialang": "Già Làng 👴",
    "kengoc": "Kẻ Ngốc 🤡", "detethan": "Dê Tế Thần 🐐", "hiepsi": "Hiệp Sĩ Kiếm Rỉ 🗡️", "quangau": "Người Quản Gấu 🐻",
    "concao": "Con Cáo 🦊", "goihon": "Người Gọi Hồn 👻", "phapsucam": "Pháp Sư Câm 🤐", "haichiem": "Hai Chị Em 👯‍♀️",
    "baanh_em": "Ba Anh Em 👨‍👦‍👦", "trehoang": "Đứa Trẻ Hoang Dã 👶",
    "soi": "Sói Thường 🐺", "soicon": "Sói Con 🐾", "soitt": "Sói Tiên Tri 🐺👁️", "soichua": "Sói Đầu Đàn 👑🐺",
    "soi_hacam": "Sói Hắc Ám 🌑", "soi_laynhiem": "Sói Lây Nhiễm 🦠", "soi_acmong": "Sói Ác Mộng 💤",
    "taysai": "Tay Sai 🦇", "hoasoi": "Người Hóa Sói 🐺🧑",
    "soitrang": "Sói Trắng 🤍", "thoitieu": "Người Thổi Tiêu 🪈", "chandoi": "Chán Đời 🎭", "thiensu": "Thiên Sứ 👼",
    "ketrom": "Kẻ Trộm 🕵️", "giaochu": "Giáo Chủ 📿", "satthu": "Kẻ Sát Nhân 🔪", "macayrong": "Ma Cà Rồng 🦇"
}

TUDIEN_PHE = {
    "danlang": "Phe Dân Làng", "tientri": "Phe Dân Làng", "phuthuy": "Phe Dân Làng", "baove": "Phe Dân Làng",
    "thosan": "Phe Dân Làng", "cupid": "Phe Dân Làng", "cobe": "Phe Dân Làng", "gialang": "Phe Dân Làng",
    "kengoc": "Phe Dân Làng", "detethan": "Phe Dân Làng", "hiepsi": "Phe Dân Làng", "quangau": "Phe Dân Làng",
    "concao": "Phe Dân Làng", "goihon": "Phe Dân Làng", "phapsucam": "Phe Dân Làng", "haichiem": "Phe Dân Làng",
    "baanh_em": "Phe Dân Làng", "trehoang": "Phe Dân Làng",
    "soi": "Phe Sói", "soicon": "Phe Sói", "soitt": "Phe Sói", "soichua": "Phe Sói",
    "soi_hacam": "Phe Sói", "soi_laynhiem": "Phe Sói", "soi_acmong": "Phe Sói",
    "taysai": "Phe Sói", "hoasoi": "Phe Sói",
    "soitrang": "Phe Thứ 3", "thoitieu": "Phe Thứ 3", "chandoi": "Phe Thứ 3", "thiensu": "Phe Thứ 3",
    "ketrom": "Phe Thứ 3", "giaochu": "Phe Thứ 3", "satthu": "Phe Thứ 3", "macayrong": "Phe Thứ 3"
}

MOTA_VAI = {
    "danlang": "Không có kỹ năng đặc biệt. Hãy quan sát, biện luận để tìm ra Ma Sói và treo cổ chúng vào ban ngày.",
    "tientri": "Mỗi đêm, được chọn 1 người để soi xem có phải là Sói hay không.",
    "phuthuy": "Sở hữu 1 bình cứu và 1 bình độc (chỉ dùng 1 lần). Có thể chọn cứu người bị Sói cắn hoặc độc chết 1 người vào ban đêm.",
    "baove": "Mỗi đêm bảo vệ 1 người (không được bảo vệ 1 người 2 đêm liên tiếp). Người đó không thể bị Sói cắn chết đêm đó.",
    "thosan": "Nếu bị Sói cắn hoặc bị treo cổ, bạn được quyền kéo theo 1 người chết cùng trước khi nhắm mắt.",
    "cupid": "Đêm đầu tiên, chọn ghép đôi 2 người. Nếu 1 trong 2 chết, người kia cũng sẽ chết theo.",
    "cobe": "Ban đêm có quyền nhìn trộm hang Sói. Tuy nhiên có 20% xác suất bạn sẽ bị Sói phát hiện và giết chết.",
    "gialang": "Có 2 mạng khi bị Sói cắn. Nếu chết do bị Treo cổ, Phù Thủy độc hoặc Thợ Săn bắn, Dân Làng sẽ mất toàn bộ kỹ năng.",
    "kengoc": "Nếu bị làng treo cổ, bạn lật bài lên để thoát chết, nhưng sẽ vĩnh viễn bị tước quyền biểu quyết.",
    "detethan": "Nếu kết quả biểu quyết ban ngày có tỷ số hòa, bạn sẽ tự động là người chết thay.",
    "hiepsi": "Nếu bị Sói cắn chết, con Sói ngồi ngay bên trái bạn sẽ tự động chết vì nhiễm trùng vào đêm hôm sau.",
    "quangau": "Ban ngày, nếu có Sói ngồi cạnh bạn (trái hoặc phải), con gấu của bạn sẽ gầm lên để cảnh báo làng.",
    "concao": "Đêm đến soi 3 người liền kề. Nếu có ít nhất 1 Sói, giữ lại kỹ năng. Nếu không có Sói nào, mất kỹ năng vĩnh viễn.",
    "goihon": "Có khả năng giao tiếp, được phép truy cập và nói chuyện trong Kênh Địa Ngục với những người đã chết.",
    "phapsucam": "Mỗi đêm chọn 1 người. Sáng hôm sau, người đó sẽ bị câm (không được chat và bị tước quyền vote).",
    "haichiem": "Tỉnh dậy vào đêm đầu tiên để biết mặt nhau qua một kênh chat riêng biệt. Nhớ tin tưởng đồng đội.",
    "baanh_em": "Tỉnh dậy vào đêm đầu tiên để nhận diện 3 anh em qua kênh chat riêng biệt. Lực lượng vote cực mạnh.",
    "trehoang": "Đêm đầu chọn 1 người làm thần tượng. Nếu thần tượng chết, bạn sẽ hóa điên và biến thành phe Sói.",
    "soi": "Mỗi đêm, thức dậy cùng bầy Sói để chọn và cắn 1 nạn nhân.",
    "soicon": "Nếu bị dân làng treo cổ ban ngày, đêm tiếp theo bầy Sói phẫn nộ sẽ được quyền cắn 2 người thay vì 1.",
    "soitt": "Cùng bầy Sói cắn người. Sau đó được quyền soi thêm 1 người xem có phải Sói không (kết quả báo vào hang Sói).",
    "soichua": "Có quyền lực tối cao, phiếu cắn của bạn vào ban đêm được tính bằng 2 phiếu.",
    "soi_hacam": "Miễn là bầy Sói chưa có ai chết, bạn mang lại bùa chú cho bầy Sói cắn thêm 1 nạn nhân phụ mỗi đêm.",
    "soi_laynhiem": "Có quyền dùng chức năng lây nhiễm (1 lần duy nhất), biến nạn nhân bị Sói cắn thành Sói thay vì giết chết.",
    "soi_acmong": "Mỗi đêm chọn 1 người. Kỹ năng của người đó trong đêm nay sẽ bị phong ấn hoàn toàn.",
    "taysai": "Biết toàn bộ danh sách Sói từ đầu game nhưng Sói không biết bạn là ai. Bạn thắng khi Sói thắng.",
    "hoasoi": "Đêm đầu tiên, bạn có quyền lựa chọn theo phe Dân Làng hoặc biến thành phe Sói vĩnh viễn.",
    "soitrang": "Cắn người cùng bầy Sói. Vào các đêm chẵn, bạn được quyền giết thêm 1 con Sói. Thắng khi sống sót một mình.",
    "thoitieu": "Mỗi đêm thôi miên 2 người. Bạn chiến thắng ngay lập tức nếu tất cả người còn sống đều đang bị thôi miên.",
    "chandoi": "Thắng cuộc và kết thúc game ngay lập tức nếu bạn đánh lừa được Dân Làng treo cổ mình vào ban ngày.",
    "thiensu": "Thắng cuộc ngay lập tức nếu lừa được Dân Làng treo cổ mình vào Ngày 1. Nếu qua Ngày 1 sẽ hóa thành Dân thường.",
    "ketrom": "Đêm đầu tiên, được phép chọn 1 trong 2 vai trò bị bỏ ngoài rìa để biến hóa thân thành vai đó.",
    "giaochu": "Mỗi đêm kết nạp 1 người vào tà giáo. Bạn chiến thắng nếu tất cả những người còn sống đều là giáo đồ.",
    "satthu": "Mỗi đêm ám sát 1 người, miễn nhiễm hoàn toàn với việc bị Sói cắn. Thắng khi là người sống sót cuối cùng.",
    "macayrong": "Mỗi đêm cắn 1 người biến thành Ma Cà Rồng, tước đi kỹ năng của họ. Thắng khi bầy đàn chiếm một nửa số người sống."
}

PHE_SOI_KILLERS = ["soi", "soicon", "soitt", "soichua", "soi_hacam", "soi_laynhiem", "soi_acmong", "hoasoi"]
PHE_3_KILLERS = ["soitrang", "satthu", "macayrong"]
VAI_KHONG_DEM = ["danlang", "gialang", "kengoc", "detethan", "hiepsi", "quangau", "haichiem", "baanh_em", "trehoang", "chandoi", "thiensu", "taysai", "cobe", "goihon"]

# ==========================================
# CÁC HÀM XỬ LÝ HỆ THỐNG KÊNH & HIỂN THỊ
# ==========================================
async def dondep_game(game):
    if game.channel.guild.me.guild_permissions.mute_members:
        for p in game.nguoi_choi:
            member = game.channel.guild.get_member(p.id)
            if member and member.voice:
                try: await member.edit(mute=False)
                except Exception: pass
    try: 
        if game.gen_channel: await game.gen_channel.delete()
        if game.wolf_channel: await game.wolf_channel.delete()
        if game.hell_channel: await game.hell_channel.delete()
        if game.haichiem_channel: await game.haichiem_channel.delete()
        if game.baanh_channel: await game.baanh_channel.delete()
    except Exception: pass
    if game.channel.id in phong_choi: del phong_choi[game.channel.id]

async def thiet_lap_kenh(game, interaction):
    cat = interaction.channel.category
    ow_gen = {interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False), interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)}
    ow_wolf = {interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False), interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)}
    ow_hell = {interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False), interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)}
    ow_haichiem = {interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False), interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)}
    ow_baanh = {interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False), interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)}
    
    for p in game.nguoi_choi:
        ow_gen[p] = discord.PermissionOverwrite(read_messages=True, send_messages=False, connect=True, speak=False)
        v = game.vai_tro.get(p.id)
        if v in PHE_SOI_KILLERS or v == "taysai": ow_wolf[p] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        if v == "goihon": ow_hell[p] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        if v == "cobe": ow_wolf[p] = discord.PermissionOverwrite(read_messages=True, send_messages=False)
        if v == "haichiem": ow_haichiem[p] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        if v == "baanh_em": ow_baanh[p] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
            
    try:
        game.gen_channel = await interaction.guild.create_text_channel(f"ngoi-lang-{random.randint(100,999)}", overwrites=ow_gen, category=cat)
        game.wolf_channel = await interaction.guild.create_text_channel(f"hang-soi-{random.randint(100,999)}", overwrites=ow_wolf, category=cat)
        game.hell_channel = await interaction.guild.create_text_channel(f"dia-nguc-{random.randint(100,999)}", overwrites=ow_hell, category=cat)
        if any(v == "haichiem" for v in game.vai_tro.values()): game.haichiem_channel = await interaction.guild.create_text_channel(f"hai-chi-em-{random.randint(100,999)}", overwrites=ow_haichiem, category=cat)
        if any(v == "baanh_em" for v in game.vai_tro.values()): game.baanh_channel = await interaction.guild.create_text_channel(f"ba-anh-em-{random.randint(100,999)}", overwrites=ow_baanh, category=cat)
        
        await game.gen_channel.send("🏡 **NGÔI LÀNG ĐÃ ĐƯỢC THÀNH LẬP**\nĐây là khu vực dành riêng cho việc thảo luận và trao đổi của mọi người. Toàn bộ thông báo trò chơi, chọn chức năng và biểu quyết sẽ diễn ra ở kênh gốc tạo phòng.")
        await game.wolf_channel.send("🐺 **HANG SÓI ĐÃ ĐƯỢC MỞ**\nSói có thể thảo luận tự do tại đây xuyên suốt trò chơi.")
        await game.hell_channel.send("👻 **ĐỊA NGỤC MÔN ĐÃ MỞ**\nNgười Gọi Hồn và những linh hồn đã chết sẽ tụ tập tại đây.")
        if game.haichiem_channel: await game.haichiem_channel.send("👯‍♀️ **Kênh riêng của Hai Chị Em**.")
        if game.baanh_channel: await game.baanh_channel.send("👨‍👦‍👦 **Kênh riêng của Ba Anh Em**.")
    except Exception: pass

async def khoa_mo_kenh_chung(game, dong_cua):
    if not game.gen_channel: return
    for p in game.nguoi_choi:
        if p.id in game.con_song:
            if dong_cua:
                try: await game.gen_channel.set_permissions(p, read_messages=True, send_messages=False, connect=True, speak=False)
                except Exception: pass
            else:
                try: await game.gen_channel.set_permissions(p, read_messages=True, send_messages=True, connect=True, speak=True)
                except Exception: pass

async def cap_nhat_mic(game, la_ban_dem):
    if not game.channel.guild.me.guild_permissions.mute_members: return
    for p in game.nguoi_choi:
        member = game.channel.guild.get_member(p.id)
        if member and member.voice:
            try:
                if la_ban_dem: await member.edit(mute=True)
                else: await member.edit(mute=False) if (p.id in game.con_song and p.id != game.nguoi_bi_cam) else await member.edit(mute=True)
            except Exception: pass

def tao_tin_tuc(game):
    if not game.news: return "Chưa có sự kiện nào đáng chú ý."
    return "\n".join([f"• {n}" for n in game.news[-6:]])

def tao_embed_game(game, title, desc, color):
    embed = discord.Embed(title=title, description=desc, color=color)
    if game.trang_thai in ["voting", "mayor_election"]:
        if game.cai_dat["an_phieu"]:
            chi_tiet = f"🗳️ Đã có {len(game.phieu_ngay)} phiếu được bỏ kín."
        else:
            chi_tiet = ""
            for v_id, t_val in game.phieu_ngay.items():
                nguoi_bau = game.lay_nguoi_choi(v_id)
                if nguoi_bau:
                    if t_val == "skip": chi_tiet += f"• {nguoi_bau.mention} đã chọn **Bỏ qua**\n"
                    else: chi_tiet += f"• {nguoi_bau.mention} bỏ phiếu cho {game.lay_nguoi_choi(int(t_val)).mention}\n"
        embed.description += f"\n\n🗳️ **Tình trạng phiếu bầu trực tiếp:**\n{chi_tiet}"

    embed.add_field(name="📰 Bản Tin Trực Tiếp", value=tao_tin_tuc(game), inline=False)
    ds = "\n".join([f"• {game.lay_nguoi_choi(p).mention}" for p in game.con_song])
    embed.add_field(name=f"👥 Sống Sót ({len(game.con_song)})", value=ds if ds else "Không còn ai", inline=False)
    if game.mayor_id and game.mayor_id in game.con_song:
        embed.add_field(name="🎖️ Trưởng Làng", value=game.lay_nguoi_choi(game.mayor_id).mention, inline=False)
    return embed

async def cap_nhat_embed_chinh(game, view=None):
    if not game.main_message: return
    try:
        embed = tao_embed_game(game, game.embed_title, game.embed_desc, game.embed_color)
        
        pending_ids = []
        if game.trang_thai == "night":
            pending_ids = [p for p in game.con_song if p not in game.da_hanh_dong]
        elif game.trang_thai == "mayor_election":
            pending_ids = [p for p in game.con_song if p not in game.phieu_ngay]
        elif game.trang_thai == "voting":
            pending_ids = [p for p in game.con_song if p not in game.phieu_ngay and p != game.nguoi_bi_cam and not (game.vai_tro.get(p) == "kengoc" and game.kengoc_revealed)]
        elif game.trang_thai == "hunter_action":
            thosan_id = next((u for u, v in game.vai_tro.items() if v == "thosan" and u in game.con_song), None)
            if thosan_id: pending_ids = [thosan_id]

        content_ping = None
        if pending_ids:
            pending_mentions = [game.lay_nguoi_choi(uid).mention for uid in pending_ids if game.lay_nguoi_choi(uid)]
            embed.add_field(name="⏳ Chưa hành động / Bỏ phiếu", value=", ".join(pending_mentions), inline=False)
            content_ping = " ".join(pending_mentions) + " ⏳ Làng đang chờ bạn!"
        
        if game.trang_thai in ["voting", "mayor_election"]:
            so_nguoi = len(game.con_song) if game.trang_thai == "mayor_election" else (len(game.con_song) - (1 if game.nguoi_bi_cam in game.con_song else 0))
            embed.set_footer(text=f"Tiến độ bỏ phiếu: {len(game.phieu_ngay)}/{so_nguoi} người.")
            
        if view == "remove":
            await game.main_message.edit(content=content_ping, embed=embed, view=None)
        elif view is not None:
            await game.main_message.edit(content=content_ping, embed=embed, view=view)
        else:
            await game.main_message.edit(content=content_ping, embed=embed)
    except Exception as e:
        print("Lỗi update embed:", e)

async def hien_thi_loading(game, text):
    embed = discord.Embed(title="⏳ ĐANG XỬ LÝ QUÁ TRÌNH", description=text, color=discord.Color.blurple())
    try: await game.main_message.edit(content=None, embed=embed, view=None)
    except Exception: pass
    await asyncio.sleep(4)

def tao_embed_lobby(game):
    embed = discord.Embed(title="🐺 PHÒNG CHỜ MA SÓI 🐺", color=discord.Color.dark_red())
    embed.description = f"👑 **Chủ phòng:** {game.host.mention}\n*(Cần ít nhất 2 người)*"
    tg = "Vô Hạn" if game.cai_dat["thoi_gian_ngay"] == 0 else f"{game.cai_dat['thoi_gian_ngay']} giây"
    hv = "Bật" if game.cai_dat["hien_vai"] else "Tắt"
    ap = "Bật" if game.cai_dat["an_phieu"] else "Tắt"
    embed.add_field(name="⚙️ Cài Đặt Chung", value=f"- Sói Tối Thiểu: **{game.cai_dat['min_soi']}**\n- Dân Tối Thiểu: **{game.cai_dat['min_dan']}**\n- Thời gian ngày: **{tg}**\n- Lộ vai khi chết: **{hv}**\n- Bỏ phiếu ẩn: **{ap}**", inline=False)
    dan = [TUDIEN_VAI[v] for v in game.cai_dat["vai_cho_phep"] if v in DS_DAN]
    soi = [TUDIEN_VAI[v] for v in game.cai_dat["vai_cho_phep"] if v in DS_SOI]
    phe3 = [TUDIEN_VAI[v] for v in game.cai_dat["vai_cho_phep"] if v in DS_PHE3]
    if dan: embed.add_field(name="🧑‍🌾 Phe Dân Làng", value=", ".join(dan), inline=False)
    if soi: embed.add_field(name="🐺 Phe Sói Biến Thể", value=", ".join(soi), inline=False)
    if phe3: embed.add_field(name="🩸 Phe Thứ 3", value=", ".join(phe3), inline=False)
    ds = "\n".join([f"• {p.mention}" for p in game.nguoi_choi])
    embed.add_field(name=f"👥 Người Chơi ({len(game.nguoi_choi)})", value=ds if ds else "Chưa có ai", inline=False)
    return embed

# ==========================================
# CÁC CLASS LƯU TRỮ VÀ XỬ LÝ LÔ GIC GAME
# ==========================================
class GameMaSoi:
    def __init__(self, host, channel):
        self.host = host
        self.channel = channel
        self.nguoi_choi = []
        self.vai_tro = {}
        self.con_song = []
        self.trang_thai = "lobby"
        self.hanh_dong_dem = {}
        self.da_hanh_dong = set()
        self.phieu_ngay = {}
        self.ngay = 1
        self.main_message = None
        self.gen_channel = None
        self.wolf_channel = None
        self.hell_channel = None
        self.haichiem_channel = None
        self.baanh_channel = None
        self.phuthuy_da_giet = False
        self.phuthuy_da_cuu = False
        self.gialang_lives = 2
        self.danlang_skills_active = True
        self.kengoc_revealed = False
        self.muc_tieu_thosan = None
        self.muc_tieu_baove = None
        self.last_protected_id = None
        self.muc_tieu_cuu = None
        self.nguoi_bi_cam = None
        self.mayor_id = None
        self.cupid_linked = []
        self.hiepsi_poisoned_id = None
        self.concao_active = True
        self.trehoang_idol = {}
        self.soicon_buff = False
        self.soi_hacam_buff = True
        self.soi_laynhiem_can_infect = True
        self.thoitieu_hypnotized = []
        self.giaochu_cult = []
        self.vampire_bitten = []
        self.ketrom_choices = []
        self.news = []
        self.embed_title = ""
        self.embed_desc = ""
        self.embed_color = discord.Color.default()
        self.cai_dat = {"min_soi": 1, "min_dan": 1, "vai_cho_phep": ["tientri", "baove", "phuthuy"], "thoi_gian_ngay": 0, "hien_vai": True, "an_phieu": False}

    def chia_vai(self):
        sl = len(self.nguoi_choi)
        pool = ["soi"] * self.cai_dat["min_soi"] + ["danlang"] * self.cai_dat["min_dan"]
        vai_chon = list(self.cai_dat["vai_cho_phep"])
        random.shuffle(vai_chon)
        tong_sl = sl + 2 if "ketrom" in vai_chon else sl
        while len(pool) < tong_sl:
            if len(vai_chon) > 0: pool.append(vai_chon.pop(0))
            else: pool.append("danlang")
        if len(pool) > tong_sl: pool = pool[:tong_sl]
        if not any(v in PHE_SOI_KILLERS for v in pool) and sl > 1: pool[0] = "soi"
        random.shuffle(pool)
        for i, p in enumerate(self.nguoi_choi):
            self.vai_tro[p.id] = pool[i]
            self.con_song.append(p.id)
        if "ketrom" in self.cai_dat["vai_cho_phep"]:
            self.ketrom_choices = pool[sl:sl+2]

    def kiem_tra_thang(self):
        try:
            so_soi = sum(1 for u in self.con_song if self.vai_tro.get(u) in PHE_SOI_KILLERS)
            so_sk = sum(1 for u in self.con_song if self.vai_tro.get(u) in PHE_3_KILLERS)
            so_tot = len(self.con_song) - so_soi - so_sk
            
            thoitieu_id = next((u for u, v in self.vai_tro.items() if v == "thoitieu" and u in self.con_song), None)
            if thoitieu_id:
                alive_no_tt = [u for u in self.con_song if u != thoitieu_id]
                if alive_no_tt and all(u in self.thoitieu_hypnotized for u in alive_no_tt): return "phe3", "Người Thổi Tiêu đã thôi miên tất cả!"
                
            giaochu_id = next((u for u, v in self.vai_tro.items() if v == "giaochu" and u in self.con_song), None)
            if giaochu_id:
                if all(u in self.giaochu_cult or u == giaochu_id for u in self.con_song): return "phe3", "Giáo Chủ đã thu nạp tất cả!"
                
            macayrong_id = next((u for u, v in self.vai_tro.items() if v == "macayrong" and u in self.con_song), None)
            if macayrong_id:
                vamp_alive = [u for u in self.con_song if u in self.vampire_bitten or u == macayrong_id]
                if len(vamp_alive) >= len(self.con_song) / 2: return "phe3", "Ma Cà Rồng đã áp đảo!"
                
            if len(self.con_song) == 1:
                u = self.con_song[0]
                if self.vai_tro.get(u) == "soitrang": return "phe3", "Sói Trắng là kẻ sống sót cuối cùng!"
                if self.vai_tro.get(u) == "satthu": return "phe3", "Sát Thủ là kẻ sống sót cuối cùng!"

            if len(self.con_song) == 0: return "hoa", "Tất cả mọi người đều đã bỏ mạng!"
            if so_sk > 0:
                if so_soi == 0 and so_tot <= 1: return "phe3", "Thế lực thứ 3 đã thảm sát toàn bộ bản làng!"
                if so_sk == len(self.con_song): return "phe3", "Thế lực thứ 3 là những kẻ sống sót cuối cùng!"
            else:
                if so_soi == 0: return "danlang", "Tất cả Ma Sói đã bị thanh trừng sạch sẽ!"
                if so_soi >= so_tot: return "soi", "Ma Sói đã chiếm thế thượng phong hoàn toàn!"
            return None, None
        except Exception:
            return None, None

    def lay_nguoi_choi(self, uid):
        for p in self.nguoi_choi:
            if p.id == uid: return p
        return None

# ==========================================
# CÁC CLASS UI (NÚT BẤM, LỰA CHỌN)
# ==========================================
class CaiDatMaSoi(discord.ui.View):
    def __init__(self, game):
        super().__init__(timeout=None)
        self.game = game
        
        op_dan = [discord.SelectOption(label="✅ CHỌN TẤT CẢ PHE DÂN", value="all_dan"), discord.SelectOption(label="❌ BỎ CHỌN TẤT CẢ PHE DÂN", value="none_dan")] + [discord.SelectOption(label=TUDIEN_VAI[v], value=v, default=(v in game.cai_dat["vai_cho_phep"])) for v in DS_DAN]
        self.sel_dan = discord.ui.Select(placeholder="Cài đặt nhóm Phe Dân Làng...", min_values=1, max_values=19, options=op_dan[:25], row=0)
        self.sel_dan.callback = self.cb_dan
        self.add_item(self.sel_dan)
        
        op_soi = [discord.SelectOption(label="✅ CHỌN TẤT CẢ SÓI", value="all_soi"), discord.SelectOption(label="❌ BỎ CHỌN TẤT CẢ SÓI", value="none_soi")] + [discord.SelectOption(label=TUDIEN_VAI[v], value=v, default=(v in game.cai_dat["vai_cho_phep"])) for v in DS_SOI]
        self.sel_soi = discord.ui.Select(placeholder="Cài đặt nhóm Sói Biến Thể...", min_values=1, max_values=10, options=op_soi, row=1)
        self.sel_soi.callback = self.cb_soi
        self.add_item(self.sel_soi)
        
        op_phe3 = [discord.SelectOption(label="✅ CHỌN TẤT CẢ PHE 3", value="all_phe3"), discord.SelectOption(label="❌ BỎ CHỌN TẤT CẢ PHE 3", value="none_phe3")] + [discord.SelectOption(label=TUDIEN_VAI[v], value=v, default=(v in game.cai_dat["vai_cho_phep"])) for v in DS_PHE3]
        self.sel_phe3 = discord.ui.Select(placeholder="Cài đặt nhóm Phe Thứ 3...", min_values=1, max_values=10, options=op_phe3, row=2)
        self.sel_phe3.callback = self.cb_phe3
        self.add_item(self.sel_phe3)

        self.btn_soithuong = discord.ui.Button(label=f"🐺 Sói Tối Thiểu: {game.cai_dat['min_soi']}", style=discord.ButtonStyle.primary, row=3)
        self.btn_soithuong.callback = self.cb_btn_soi
        self.add_item(self.btn_soithuong)

        self.btn_danthuong = discord.ui.Button(label=f"🧑‍🌾 Dân Tối Thiểu: {game.cai_dat['min_dan']}", style=discord.ButtonStyle.primary, row=3)
        self.btn_danthuong.callback = self.cb_btn_dan
        self.add_item(self.btn_danthuong)

        self.btn_tg = discord.ui.Button(label=f"⏱️ Ngày: {'Vô hạn' if game.cai_dat['thoi_gian_ngay']==0 else str(game.cai_dat['thoi_gian_ngay'])+'s'}", style=discord.ButtonStyle.primary, row=3)
        self.btn_tg.callback = self.cb_btn_tg
        self.add_item(self.btn_tg)

        self.btn_hv = discord.ui.Button(label=f"👁️ Lộ vai: {'Bật' if game.cai_dat['hien_vai'] else 'Tắt'}", style=discord.ButtonStyle.secondary, row=4)
        self.btn_hv.callback = self.cb_btn_hv
        self.add_item(self.btn_hv)

        self.btn_ap = discord.ui.Button(label=f"🗳️ Bỏ phiếu ẩn: {'Bật' if game.cai_dat['an_phieu'] else 'Tắt'}", style=discord.ButtonStyle.secondary, row=4)
        self.btn_ap.callback = self.cb_btn_ap
        self.add_item(self.btn_ap)

        self.btn_xong = discord.ui.Button(label="✅ XONG & LƯU BẢNG", style=discord.ButtonStyle.success, row=4)
        self.btn_xong.callback = self.cb_btn_xong
        self.add_item(self.btn_xong)
        
    async def cb_dan(self, interaction):
        if interaction.user.id != self.game.host.id: 
            try: await interaction.response.send_message("❌ Bạn không phải là chủ phòng!\n*(Tin nhắn này sẽ tự biến mất sau 3s)*", ephemeral=True, delete_after=3.0)
            except Exception: pass
        else:
            try: await interaction.response.defer()
            except Exception: pass
            if self.game.trang_thai == "lobby":
                vals = self.sel_dan.values
                if "none_dan" in vals: self.game.cai_dat["vai_cho_phep"] = [v for v in self.game.cai_dat["vai_cho_phep"] if v not in DS_DAN]
                elif "all_dan" in vals: self.game.cai_dat["vai_cho_phep"] = [v for v in self.game.cai_dat["vai_cho_phep"] if v not in DS_DAN] + DS_DAN
                else: self.game.cai_dat["vai_cho_phep"] = [v for v in self.game.cai_dat["vai_cho_phep"] if v not in DS_DAN] + vals
                try: await interaction.edit_original_response(view=CaiDatMaSoi(self.game))
                except Exception: pass

    async def cb_soi(self, interaction):
        if interaction.user.id != self.game.host.id: 
            try: await interaction.response.send_message("❌ Bạn không phải là chủ phòng!\n*(Tin nhắn này sẽ tự biến mất sau 3s)*", ephemeral=True, delete_after=3.0)
            except Exception: pass
        else:
            try: await interaction.response.defer()
            except Exception: pass
            if self.game.trang_thai == "lobby":
                vals = self.sel_soi.values
                if "none_soi" in vals: self.game.cai_dat["vai_cho_phep"] = [v for v in self.game.cai_dat["vai_cho_phep"] if v not in DS_SOI]
                elif "all_soi" in vals: self.game.cai_dat["vai_cho_phep"] = [v for v in self.game.cai_dat["vai_cho_phep"] if v not in DS_SOI] + DS_SOI
                else: self.game.cai_dat["vai_cho_phep"] = [v for v in self.game.cai_dat["vai_cho_phep"] if v not in DS_SOI] + vals
                try: await interaction.edit_original_response(view=CaiDatMaSoi(self.game))
                except Exception: pass

    async def cb_phe3(self, interaction):
        if interaction.user.id != self.game.host.id: 
            try: await interaction.response.send_message("❌ Bạn không phải là chủ phòng!\n*(Tin nhắn này sẽ tự biến mất sau 3s)*", ephemeral=True, delete_after=3.0)
            except Exception: pass
        else:
            try: await interaction.response.defer()
            except Exception: pass
            if self.game.trang_thai == "lobby":
                vals = self.sel_phe3.values
                if "none_phe3" in vals: self.game.cai_dat["vai_cho_phep"] = [v for v in self.game.cai_dat["vai_cho_phep"] if v not in DS_PHE3]
                elif "all_phe3" in vals: self.game.cai_dat["vai_cho_phep"] = [v for v in self.game.cai_dat["vai_cho_phep"] if v not in DS_PHE3] + DS_PHE3
                else: self.game.cai_dat["vai_cho_phep"] = [v for v in self.game.cai_dat["vai_cho_phep"] if v not in DS_PHE3] + vals
                try: await interaction.edit_original_response(view=CaiDatMaSoi(self.game))
                except Exception: pass

    async def cb_btn_soi(self, interaction):
        if interaction.user.id != self.game.host.id: 
            try: await interaction.response.send_message("❌ Bạn không phải là chủ phòng!\n*(Tin nhắn này sẽ tự biến mất sau 3s)*", ephemeral=True, delete_after=3.0)
            except Exception: pass
        else:
            try: await interaction.response.defer()
            except Exception: pass
            if self.game.trang_thai == "lobby":
                self.game.cai_dat["min_soi"] = (self.game.cai_dat["min_soi"] + 1) % 6
                try: await interaction.edit_original_response(view=CaiDatMaSoi(self.game))
                except Exception: pass

    async def cb_btn_dan(self, interaction):
        if interaction.user.id != self.game.host.id: 
            try: await interaction.response.send_message("❌ Bạn không phải là chủ phòng!\n*(Tin nhắn này sẽ tự biến mất sau 3s)*", ephemeral=True, delete_after=3.0)
            except Exception: pass
        else:
            try: await interaction.response.defer()
            except Exception: pass
            if self.game.trang_thai == "lobby":
                self.game.cai_dat["min_dan"] = (self.game.cai_dat["min_dan"] + 1) % 11
                try: await interaction.edit_original_response(view=CaiDatMaSoi(self.game))
                except Exception: pass

    async def cb_btn_tg(self, interaction):
        if interaction.user.id != self.game.host.id: 
            try: await interaction.response.send_message("❌ Bạn không phải là chủ phòng!\n*(Tin nhắn này sẽ tự biến mất sau 3s)*", ephemeral=True, delete_after=3.0)
            except Exception: pass
        else:
            try: await interaction.response.defer()
            except Exception: pass
            if self.game.trang_thai == "lobby":
                tgs = [0, 60, 120, 300, 800]
                self.game.cai_dat["thoi_gian_ngay"] = tgs[(tgs.index(self.game.cai_dat["thoi_gian_ngay"]) + 1) % len(tgs)]
                try: await interaction.edit_original_response(view=CaiDatMaSoi(self.game))
                except Exception: pass

    async def cb_btn_hv(self, interaction):
        if interaction.user.id != self.game.host.id: 
            try: await interaction.response.send_message("❌ Bạn không phải là chủ phòng!\n*(Tin nhắn này sẽ tự biến mất sau 3s)*", ephemeral=True, delete_after=3.0)
            except Exception: pass
        else:
            try: await interaction.response.defer()
            except Exception: pass
            if self.game.trang_thai == "lobby":
                self.game.cai_dat["hien_vai"] = not self.game.cai_dat["hien_vai"]
                try: await interaction.edit_original_response(view=CaiDatMaSoi(self.game))
                except Exception: pass

    async def cb_btn_ap(self, interaction):
        if interaction.user.id != self.game.host.id: 
            try: await interaction.response.send_message("❌ Bạn không phải là chủ phòng!\n*(Tin nhắn này sẽ tự biến mất sau 3s)*", ephemeral=True, delete_after=3.0)
            except Exception: pass
        else:
            try: await interaction.response.defer()
            except Exception: pass
            if self.game.trang_thai == "lobby":
                self.game.cai_dat["an_phieu"] = not self.game.cai_dat["an_phieu"]
                try: await interaction.edit_original_response(view=CaiDatMaSoi(self.game))
                except Exception: pass

    async def cb_btn_xong(self, interaction):
        if interaction.user.id != self.game.host.id: 
            try: await interaction.response.send_message("❌ Bạn không phải là chủ phòng!\n*(Tin nhắn này sẽ tự biến mất sau 3s)*", ephemeral=True, delete_after=3.0)
            except Exception: pass
        else:
            try: await interaction.response.defer()
            except Exception: pass
            if self.game.trang_thai == "lobby":
                try: await self.game.main_message.edit(content=None, embed=tao_embed_lobby(self.game))
                except Exception: pass
                try: await interaction.followup.send("✅ Đã lưu cấu hình lên sảnh chính!\n*(Tin nhắn này sẽ tự biến mất sau 3s)*", ephemeral=True, delete_after=3.0)
                except Exception: pass

class LobbyMaSoi(discord.ui.View):
    def __init__(self, game):
        super().__init__(timeout=None)
        self.game = game

    @discord.ui.button(label="✋ Tham Gia", style=discord.ButtonStyle.primary)
    async def nut_tham_gia(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.game.nguoi_choi:
            try: await interaction.response.send_message("❌ Bạn đã ở trong phòng rồi!\n*(Tin nhắn này sẽ tự biến mất sau 3s)*", ephemeral=True, delete_after=3.0)
            except Exception: pass
        else:
            try: await interaction.response.defer()
            except Exception: pass
            self.game.nguoi_choi.append(interaction.user)
            try: await interaction.edit_original_response(embed=tao_embed_lobby(self.game), view=self)
            except Exception: pass

    @discord.ui.button(label="⚙️ Cài Đặt (Chủ Phòng)", style=discord.ButtonStyle.secondary)
    async def nut_cai_dat(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.game.host.id:
            try: await interaction.response.send_message("❌ Chỉ chủ phòng mới được thay đổi cài đặt!\n*(Tin nhắn này sẽ tự biến mất sau 3s)*", ephemeral=True, delete_after=3.0)
            except Exception: pass
        else:
            try: await interaction.response.send_message("⚙️ BẢNG CÀI ĐẶT TRÒ CHƠI\n*(Bảng này sẽ tự hủy sau 30s)*", view=CaiDatMaSoi(self.game), ephemeral=True, delete_after=30.0)
            except Exception: pass

    @discord.ui.button(label="▶️ Bắt Đầu", style=discord.ButtonStyle.success)
    async def nut_bat_dau(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.game.host.id:
            try: await interaction.response.send_message("❌ Chỉ chủ phòng mới được quyền bắt đầu!\n*(Tin nhắn này sẽ tự biến mất sau 3s)*", ephemeral=True, delete_after=3.0)
            except Exception: pass
        else:
            if len(self.game.nguoi_choi) < 2:
                try: await interaction.response.send_message("❌ Trò chơi yêu cầu tối thiểu 2 người!\n*(Tin nhắn này sẽ tự biến mất sau 3s)*", ephemeral=True, delete_after=3.0)
                except Exception: pass
            else:
                try: await interaction.response.defer()
                except Exception: pass
                self.game.chia_vai()
                await hien_thi_loading(self.game, "Đang thiết lập Không gian trò chơi (Tạo Kênh và Phân Quyền)...")
                await thiet_lap_kenh(self.game, interaction)
                await bat_dau_dem(self.game)

    @discord.ui.button(label="❌ Xóa Phòng", style=discord.ButtonStyle.danger)
    async def nut_xoa(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.game.host.id:
            try: await interaction.response.send_message("❌ Chỉ chủ phòng mới được xóa phòng!\n*(Tin nhắn này sẽ tự biến mất sau 3s)*", ephemeral=True, delete_after=3.0)
            except Exception: pass
        else:
            try: await interaction.response.defer()
            except Exception: pass
            await dondep_game(self.game)
            embed = interaction.message.embeds[0]
            embed.color = discord.Color.dark_grey()
            embed.description = "🛑 Phòng đã bị hủy bởi chủ phòng."
            try: await interaction.edit_original_response(embed=embed, view=None)
            except Exception: pass

class MenuBieuQuyet(discord.ui.Select):
    def __init__(self, game, uid, is_mayor):
        self.game = game
        self.uid = uid
        self.is_mayor = is_mayor
        options = [discord.SelectOption(label="Bỏ qua (Phiếu trắng)", value="skip")]
        for pid in game.con_song:
            p = game.lay_nguoi_choi(pid)
            options.append(discord.SelectOption(label=p.display_name, value=str(pid)))
        super().__init__(placeholder="Chọn người...", options=options[:25])

    async def callback(self, interaction: discord.Interaction):
        val = self.values[0]
        self.game.phieu_ngay[self.uid] = val
        msg = "Bạn đã chọn Bỏ qua." if val == "skip" else f"Bạn đã bỏ phiếu cho **{self.game.lay_nguoi_choi(int(val)).display_name}**."
        
        try: await interaction.response.send_message(f"✅ {msg}\n*(Tin nhắn này sẽ tự biến mất sau 3s)*", ephemeral=True, delete_after=3.0)
        except Exception: pass
        await cap_nhat_embed_chinh(self.game)
        
        if self.is_mayor: await kiem_tra_het_bau_truong_lang(self.game)
        else: await kiem_tra_het_treo_co(self.game)

class ViewBieuQuyetNgay(discord.ui.View):
    def __init__(self, game, is_mayor):
        super().__init__(timeout=None)
        self.game = game
        self.is_mayor = is_mayor

    @discord.ui.button(label="Bỏ Phiếu", style=discord.ButtonStyle.danger)
    async def nut_bo_phieu(self, interaction: discord.Interaction, button: discord.ui.Button):
        uid = interaction.user.id
        if uid not in self.game.con_song:
            try: await interaction.response.send_message("👻 Bạn đã chết, không thể bỏ phiếu!\n*(Tin nhắn này sẽ tự biến mất sau 3s)*", ephemeral=True, delete_after=3.0)
            except Exception: pass
        else:
            if not self.is_mayor and (uid == self.game.nguoi_bi_cam or (self.game.vai_tro.get(uid) == "kengoc" and self.game.kengoc_revealed)):
                try: await interaction.response.send_message("🤐 Bạn đã bị tước quyền biểu quyết!\n*(Tin nhắn này sẽ tự biến mất sau 3s)*", ephemeral=True, delete_after=3.0)
                except Exception: pass
            else:
                view_chon = discord.ui.View()
                view_chon.add_item(MenuBieuQuyet(self.game, uid, self.is_mayor))
                try: await interaction.response.send_message("👇 Hãy đưa ra quyết định (Phiếu mới sẽ đè lên phiếu cũ):\n*(Bảng lựa chọn này sẽ tự biến mất sau 10s)*", view=view_chon, ephemeral=True, delete_after=10.0)
                except Exception: pass

    @discord.ui.button(label="🎭 Xem Vai Trò & Cách Chơi", style=discord.ButtonStyle.secondary)
    async def nut_xem_vai(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            uid = interaction.user.id
            if uid not in self.game.vai_tro:
                await interaction.response.send_message("❌ Bạn không tham gia trận này!\n*(Tin nhắn này sẽ tự biến mất sau 3s)*", ephemeral=True, delete_after=3.0)
                return
                
            vai = self.game.vai_tro.get(uid)
            trang_thai = "💀 Đã chết" if uid not in self.game.con_song else "❤️ Còn sống"
            mota = MOTA_VAI.get(vai, "Không có dữ liệu kỹ năng.")
            ten_vai = TUDIEN_VAI.get(vai, "Chưa rõ")
            phe_vai = TUDIEN_PHE.get(vai, "Chưa rõ")
            
            msg = f"🎭 **Vai trò của bạn:** {ten_vai} ({phe_vai})\n❤️ **Trạng thái:** {trang_thai}\n\n📖 **Kỹ năng & Cách chơi:**\n{mota}\n\n*(Bảng hướng dẫn này sẽ tự biến mất sau 10s)*"
            await interaction.response.send_message(msg, ephemeral=True, delete_after=10.0)
        except Exception as e:
            try: await interaction.response.send_message(f"⚠️ Lỗi hiển thị vai trò: {str(e)}\n*(Hệ thống tự báo cáo để tránh sập)*", ephemeral=True, delete_after=5.0)
            except Exception: pass

    @discord.ui.button(label="🛑 Reset Game (Lỗi)", style=discord.ButtonStyle.danger, row=1)
    async def nut_reset_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.game.host.id:
            try: await interaction.response.send_message("❌ Chỉ chủ phòng mới được dùng nút này!\n*(Tin nhắn này sẽ tự biến mất sau 3s)*", ephemeral=True, delete_after=3.0)
            except Exception: pass
        else:
            try: await interaction.response.defer()
            except Exception: pass
            embed = discord.Embed(title="🛑 TRẬN ĐẤU BỊ RESET", description="Chủ phòng đã đóng phòng khẩn cấp.", color=discord.Color.dark_grey())
            try: await self.game.main_message.edit(content=None, embed=embed, view=None)
            except Exception: pass
            await dondep_game(self.game)
            self.stop()

class MenuCuuPhuThuy(discord.ui.Select):
    def __init__(self, game, uid):
        self.game = game
        self.uid = uid
        options = [discord.SelectOption(label="Không Cứu Ai", value="skip")]
        for pid in game.con_song:
            p = game.lay_nguoi_choi(pid)
            options.append(discord.SelectOption(label=f"Cứu: {p.display_name}", value=str(pid)))
        super().__init__(placeholder="🧪 Chọn người để Cứu (Bình Thần)...", options=options[:25])

    async def callback(self, interaction: discord.Interaction):
        val = self.values[0]
        if val != "skip":
            self.game.hanh_dong_dem[self.uid] = f"save_{val}"
            self.game.da_hanh_dong.add(self.uid)
            try: await interaction.response.send_message(f"✅ Đã dùng Bình Cứu lên {self.game.lay_nguoi_choi(int(val)).display_name}!\n*(Tự biến mất sau 3s)*", ephemeral=True, delete_after=3.0)
            except Exception: pass
            await cap_nhat_embed_chinh(self.game)
            await kiem_tra_het_dem(self.game)
        else:
            try: await interaction.response.defer()
            except Exception: pass

class MenuGietPhuThuy(discord.ui.Select):
    def __init__(self, game, uid):
        self.game = game
        self.uid = uid
        options = [discord.SelectOption(label="Không Giết Ai", value="skip")]
        for pid in game.con_song:
            p = game.lay_nguoi_choi(pid)
            if pid != uid: options.append(discord.SelectOption(label=f"Giết: {p.display_name}", value=str(pid)))
        super().__init__(placeholder="☠️ Chọn người để Giết (Bình Độc)...", options=options[:25])

    async def callback(self, interaction: discord.Interaction):
        val = self.values[0]
        if val != "skip":
            self.game.hanh_dong_dem[self.uid] = f"kill_{val}"
            self.game.da_hanh_dong.add(self.uid)
            try: await interaction.response.send_message(f"✅ Đã dùng Bình Độc lên {self.game.lay_nguoi_choi(int(val)).display_name}!\n*(Tự biến mất sau 3s)*", ephemeral=True, delete_after=3.0)
            except Exception: pass
            await cap_nhat_embed_chinh(self.game)
            await kiem_tra_het_dem(self.game)
        else:
            try: await interaction.response.defer()
            except Exception: pass

class ViewChonDemPhuThuy(discord.ui.View):
    def __init__(self, game, uid):
        super().__init__(timeout=None)
        self.game = game
        self.uid = uid
        if not game.phuthuy_da_cuu:
            self.add_item(MenuCuuPhuThuy(game, uid))
        if not game.phuthuy_da_giet:
            self.add_item(MenuGietPhuThuy(game, uid))

    @discord.ui.button(label="Bỏ Qua Đêm Nay (Giữ Bình)", style=discord.ButtonStyle.secondary)
    async def nut_bo_qua(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.game.hanh_dong_dem[self.uid] = "skip"
        self.game.da_hanh_dong.add(self.uid)
        try: await interaction.response.send_message("✅ Bạn đã chọn cất giữ bình cho đêm sau.\n*(Tự biến mất sau 3s)*", ephemeral=True, delete_after=3.0)
        except Exception: pass
        await cap_nhat_embed_chinh(self.game)
        await kiem_tra_het_dem(self.game)

class MenuChonDem(discord.ui.Select):
    def __init__(self, game, uid, role):
        self.game = game
        self.uid = uid
        self.role = role
        options = []
        max_v = 1
        ph = "Chọn mục tiêu..."
        if role in ["cupid", "thoitieu"]:
            max_v = min(2, len(game.con_song))
            ph = "Chọn 2 mục tiêu..."
            for pid in game.con_song: options.append(discord.SelectOption(label=game.lay_nguoi_choi(pid).display_name, value=str(pid)))
        elif role == "ketrom":
            for r in game.ketrom_choices: options.append(discord.SelectOption(label=TUDIEN_VAI[r], value=str(r)))
        elif role == "hoasoi":
            options.append(discord.SelectOption(label="Phe Dân Làng", value="danlang"))
            options.append(discord.SelectOption(label="Phe Sói", value="soi"))
        elif role == "cobe":
            options.append(discord.SelectOption(label="Nhìn trộm Sói", value="peek"))
            options.append(discord.SelectOption(label="Ngủ ngoan", value="skip"))
        else:
            options.append(discord.SelectOption(label="Bỏ qua (Không hành động)", value="skip"))
            for pid in game.con_song:
                if role == "baove" and pid == game.last_protected_id: pass
                elif pid != uid or role == "baove" or role == "satthu":
                    options.append(discord.SelectOption(label=game.lay_nguoi_choi(pid).display_name, value=str(pid)))
        
        super().__init__(placeholder=ph, min_values=1 if role not in ["cupid", "thoitieu"] else max_v, max_values=max_v, options=options[:25])

    async def callback(self, interaction: discord.Interaction):
        if self.role in ["cupid", "thoitieu"]:
            self.game.hanh_dong_dem[self.uid] = f"{self.values[0]}_{self.values[1]}"
            msg = "✅ Đã xác nhận 2 mục tiêu."
            if self.role == "cupid":
                self.game.news.append("💘 Một mũi tên tình yêu vô hình vừa được bắn ra trong màn đêm...")
            else:
                self.game.news.append("🪈 Văng vẳng trong gió có tiếng tiêu thôi miên ai oán khiến người ta mộng mị...")
        else:
            val = self.values[0]
            if val == "skip":
                self.game.hanh_dong_dem[self.uid] = "skip"
                msg = "Bạn đã chọn bỏ qua hành động đêm nay."
                if self.role == "cobe":
                    self.game.news.append("👧 Cô bé trùm chăn quyết định ngủ ngoan đêm nay.")
            elif self.role == "ketrom":
                self.game.hanh_dong_dem[self.uid] = str(val)
                msg = f"🕵️ Bạn đã đổi thành: **{TUDIEN_VAI[val]}**. Hệ thống đang tải kỹ năng mới..."
                self.game.news.append("🕵️ Có tiếng lục lọi đồ đạc, một kẻ nào đó vừa tráo đổi nhân dạng...")
                
                if str(val) in ["cupid", "trehoang"] and self.game.ngay == 1:
                    self.game.vai_tro[self.uid] = str(val) 
                    view_chon = discord.ui.View()
                    view_chon.add_item(MenuChonDem(self.game, self.uid, str(val)))
                    try: await interaction.response.send_message("👇 Hãy sử dụng ngay kỹ năng của vai trò mới nhận:\n*(Bảng lựa chọn này tự biến mất sau 10s)*", view=view_chon, ephemeral=True, delete_after=10.0)
                    except Exception: pass
                    return 
            elif self.role == "hoasoi":
                self.game.hanh_dong_dem[self.uid] = str(val)
                msg = f"🐺 Bạn đã chọn theo: **{'Phe Sói' if val == 'soi' else 'Phe Dân Làng'}**."
                self.game.news.append("🐺 Dưới ánh trăng, một cái bóng đang đứng giữa ranh giới của sự biến đổi...")
            elif self.role == "cobe":
                self.game.hanh_dong_dem[self.uid] = str(val)
                msg = "👧 Bạn đang lén nhìn trộm hang Sói..." if val == "peek" else "👧 Bạn đã trùm chăn ngủ ngoan."
                if val == "peek": self.game.news.append("👧 Cánh cửa khẽ cọt kẹt, có đôi mắt đang lén lút dòm ngó ra bên ngoài...")
            else:
                muc_tieu_id = int(val)
                muc_tieu_ten = self.game.lay_nguoi_choi(muc_tieu_id).display_name
                if self.role in PHE_SOI_KILLERS:
                    self.game.hanh_dong_dem[self.uid] = muc_tieu_id
                    msg = f"🐺 Bạn đã chọn cắn: **{muc_tieu_ten}**."
                    if not any("Một tiếng róc rách" in n for n in self.game.news[-3:]):
                        self.game.news.append("🐺 Có tiếng chân đạp lên cành cây khô, bầy Sói đang tụ tập săn mồi...")
                elif self.role in ["tientri", "soitt"]:
                    self.game.hanh_dong_dem[self.uid] = "skip"
                    phe = "Ma Sói 🐺" if self.game.vai_tro.get(muc_tieu_id) in PHE_SOI_KILLERS else "Người tốt / Trung lập 🧑‍🌾"
                    msg = f"👁️ {muc_tieu_ten} thuộc: **{phe}**"
                    self.game.news.append("👁️ Quả cầu pha lê lóe sáng, một nhà tiên tri vừa nhòm ngó danh tính ai đó.")
                elif self.role == "concao":
                    self.game.hanh_dong_dem[self.uid] = "skip"
                    idx = self.game.con_song.index(muc_tieu_id)
                    l_idx = idx - 1 if idx > 0 else len(self.game.con_song) - 1
                    r_idx = idx + 1 if idx < len(self.game.con_song) - 1 else 0
                    if any(self.game.vai_tro.get(self.game.con_song[i]) in PHE_SOI_KILLERS for i in [l_idx, idx, r_idx]):
                        msg = f"🦊 Cáo ngửi thấy mùi Sói quanh **{muc_tieu_ten}**!"
                        self.game.news.append("🦊 Con Cáo vừa đánh hơi thấy mùi hôi thối nguy hiểm gần đây.")
                    else:
                        msg = f"🦊 Không có Sói quanh **{muc_tieu_ten}**. Cáo đã mất kỹ năng vĩnh viễn!"
                        self.game.concao_active = False
                        self.game.news.append("🦊 Con Cáo đi tuần tra nhưng không phát hiện gì lạ, nó quay về ngủ yên vĩnh viễn.")
                elif self.role in PHE_3_KILLERS:
                    self.game.hanh_dong_dem[self.uid] = muc_tieu_id
                    msg = f"🔪 Bạn đã chọn tiêu diệt: **{muc_tieu_ten}**."
                    if self.role == "macayrong":
                        self.game.news.append("🧛 Một bóng đen khát máu vừa lướt qua màn đêm, để lại dấu răng găm chặt...")
                    elif self.role == "soitrang":
                        self.game.news.append("🐺 Sói Trắng nhếch mép, âm thầm chuẩn bị phản bội lại chính đồng loại của mình...")
                    else:
                        self.game.news.append("🔪 Có tiếng mài dao sắc lạnh, một kẻ sát nhân ẩn danh đang hành động.")
                elif self.role == "baove":
                    self.game.hanh_dong_dem[self.uid] = muc_tieu_id
                    msg = f"🛡️ Bạn đang bảo vệ: **{muc_tieu_ten}**."
                    self.game.news.append("🛡️ Bảo vệ đã quyết định xong mục tiêu canh gác đêm nay.")
                elif self.role == "phapsucam":
                    self.game.hanh_dong_dem[self.uid] = muc_tieu_id
                    msg = f"🤐 Bạn đã yểm bùa câm lên: **{muc_tieu_ten}**."
                    self.game.news.append("🤐 Một luồng ma thuật đen kịt vừa được phóng ra để phong ấn miệng lưỡi ai đó.")
                elif self.role == "thosan":
                    self.game.hanh_dong_dem[self.uid] = muc_tieu_id
                    msg = f"🏹 Bạn đã ghim tiêu điểm vào: **{muc_tieu_ten}**."
                    self.game.news.append("🏹 Có tiếng nạp đạn lách cách, Thợ săn đã chọn xong con mồi báo thù.")
                elif self.role == "giaochu":
                    self.game.hanh_dong_dem[self.uid] = muc_tieu_id
                    msg = f"📿 Bạn đã kết nạp: **{muc_tieu_ten}**."
                    self.game.news.append("📿 Lời rầm rì đọc chú vang lên, tà giáo lại vừa âm thầm nạp thêm tín đồ...")
                elif self.role == "trehoang":
                    self.game.hanh_dong_dem[self.uid] = muc_tieu_id
                    msg = f"👶 Bạn đã chọn thần tượng: **{muc_tieu_ten}**."
                    self.game.news.append("👶 Một đứa trẻ đang lén lút chọn cho mình một người bảo hộ trong màn đêm...")
                else:
                    self.game.hanh_dong_dem[self.uid] = muc_tieu_id
                    msg = f"✅ Đã xác nhận mục tiêu: **{muc_tieu_ten}**."
                
        self.game.da_hanh_dong.add(self.uid)
        try: await interaction.response.send_message(f"{msg}\n*(Tin nhắn này sẽ tự biến mất sau 3s)*", ephemeral=True, delete_after=3.0)
        except Exception: pass
        await cap_nhat_embed_chinh(self.game)
        await kiem_tra_het_dem(self.game)

class ViewHanhDongDem(discord.ui.View):
    def __init__(self, game):
        super().__init__(timeout=None)
        self.game = game

    @discord.ui.button(label="Hành Động Ban Đêm", style=discord.ButtonStyle.primary)
    async def nut_hanh_dong(self, interaction: discord.Interaction, button: discord.ui.Button):
        uid = interaction.user.id
        if uid not in self.game.con_song:
            try: await interaction.response.send_message("👻 Bạn đã chết!\n*(Tin nhắn này sẽ tự biến mất sau 3s)*", ephemeral=True, delete_after=3.0)
            except Exception: pass
        else:
            vai = self.game.vai_tro.get(uid)
            if uid in self.game.da_hanh_dong:
                try: await interaction.response.send_message("✅ Bạn đã hoàn thành hành động đêm nay!\n*(Tin nhắn này sẽ tự biến mất sau 3s)*", ephemeral=True, delete_after=3.0)
                except Exception: pass
            else:
                if vai == "phuthuy":
                    view_chon = ViewChonDemPhuThuy(self.game, uid)
                else:
                    view_chon = discord.ui.View()
                    view_chon.add_item(MenuChonDem(self.game, uid, vai))
                try: await interaction.response.send_message(f"Vai trò của bạn là **{TUDIEN_VAI[vai]}**.\n👇 Hãy chọn hành động đêm nay:\n*(Bảng lựa chọn này sẽ tự biến mất sau 10s)*", view=view_chon, ephemeral=True, delete_after=10.0)
                except Exception: pass

    @discord.ui.button(label="🎭 Xem Vai Trò & Cách Chơi", style=discord.ButtonStyle.secondary)
    async def nut_xem_vai(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            uid = interaction.user.id
            if uid not in self.game.vai_tro:
                await interaction.response.send_message("❌ Bạn không tham gia trận này!\n*(Tin nhắn này sẽ tự biến mất sau 3s)*", ephemeral=True, delete_after=3.0)
                return
                
            vai = self.game.vai_tro.get(uid)
            trang_thai = "💀 Đã chết" if uid not in self.game.con_song else "❤️ Còn sống"
            mota = MOTA_VAI.get(vai, "Không có dữ liệu kỹ năng.")
            ten_vai = TUDIEN_VAI.get(vai, "Chưa rõ")
            phe_vai = TUDIEN_PHE.get(vai, "Chưa rõ")
            
            msg = f"🎭 **Vai trò của bạn:** {ten_vai} ({phe_vai})\n❤️ **Trạng thái:** {trang_thai}\n\n📖 **Kỹ năng & Cách chơi:**\n{mota}\n\n*(Bảng hướng dẫn này sẽ tự biến mất sau 10s)*"
            await interaction.response.send_message(msg, ephemeral=True, delete_after=10.0)
        except Exception as e:
            try: await interaction.response.send_message(f"⚠️ Lỗi hiển thị vai trò: {str(e)}\n*(Hệ thống tự báo cáo để tránh sập)*", ephemeral=True, delete_after=5.0)
            except Exception: pass

    @discord.ui.button(label="🛑 Reset Game (Lỗi)", style=discord.ButtonStyle.danger, row=1)
    async def nut_reset_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.game.host.id:
            try: await interaction.response.send_message("❌ Chỉ chủ phòng mới được dùng nút này!\n*(Tin nhắn này sẽ tự biến mất sau 3s)*", ephemeral=True, delete_after=3.0)
            except Exception: pass
        else:
            try: await interaction.response.defer()
            except Exception: pass
            embed = discord.Embed(title="🛑 TRẬN ĐẤU BỊ RESET", description="Chủ phòng đã đóng phòng khẩn cấp.", color=discord.Color.dark_grey())
            try: await self.game.main_message.edit(content=None, embed=embed, view=None)
            except Exception: pass
            await dondep_game(self.game)
            self.stop()

# ==========================================
# CÁC HÀM XỬ LÝ LÔ GIC GAME THEO TRÌNH TỰ
# ==========================================
async def ket_thuc_game(game, lido, phe):
    game.trang_thai = "ended"
    game.embed_title = "🏆 KẾT THÚC TRÒ CHƠI"
    desc = f"**Lý do:** {lido}\n🎉 Phe **{phe}** đã giành chiến thắng!\n\n**🎭 DANH SÁCH VAI TRÒ CHUNG CUỘC:**\n"
    for p in game.nguoi_choi:
        vai = game.vai_tro.get(p.id)
        ten_vai = TUDIEN_VAI.get(vai, "Không rõ")
        desc += f"• {p.mention}: **{ten_vai}**\n"
        
    game.embed_desc = desc
    game.embed_color = discord.Color.gold()
    await cap_nhat_embed_chinh(game, view="remove")
    await dondep_game(game)

async def bat_dau_dem(game):
    game.trang_thai = "night"
    game.hanh_dong_dem = {}
    game.da_hanh_dong.clear()
    game.muc_tieu_baove = None
    game.muc_tieu_cuu = None
    
    for uid in game.con_song:
        vai = game.vai_tro.get(uid)
        can_skip = False
        if vai in VAI_KHONG_DEM: can_skip = True
        elif vai == "phuthuy" and game.phuthuy_da_giet and game.phuthuy_da_cuu: can_skip = True
        elif vai == "cupid" and game.ngay > 1: can_skip = True
        elif vai == "ketrom" and game.ngay > 1: can_skip = True
        elif vai == "hoasoi" and game.ngay > 1: can_skip = True
        elif vai == "haichiem" or vai == "baanh_em": can_skip = True
        elif vai == "trehoang" and game.ngay > 1: can_skip = True
        elif vai == "concao" and not game.concao_active: can_skip = True
        elif not game.danlang_skills_active and vai in DS_DAN: can_skip = True
        
        if can_skip:
            game.da_hanh_dong.add(uid)
            game.hanh_dong_dem[uid] = "skip"
            
    await hien_thi_loading(game, "Đang thiết lập bóng tối... Mọi người hãy nhắm mắt lại.")
    await khoa_mo_kenh_chung(game, dong_cua=True)
    await cap_nhat_mic(game, True)
    
    if "taysai" in game.vai_tro.values() and not hasattr(game, "taysai_notified"):
        game.taysai_notified = True
        wolves = [game.lay_nguoi_choi(u).display_name for u in game.con_song if game.vai_tro.get(u) in PHE_SOI_KILLERS]
        taysai_id = next((u for u, v in game.vai_tro.items() if v == "taysai"), None)
        if taysai_id:
            try:
                mem = game.lay_nguoi_choi(taysai_id)
                if mem: await mem.send(f"🦇 Bạn là Tay Sai! Danh sách Sói: {', '.join(wolves)}")
            except Exception: pass

    game.embed_title = f"🌙 ĐÊM {game.ngay}"
    game.embed_desc = "Màn đêm buông xuống... Kênh chat chung đã bị khóa.\nNhững ai có chức năng hãy nhấn nút bên dưới để hành động."
    game.embed_color = discord.Color.dark_theme()
    await cap_nhat_embed_chinh(game, view=ViewHanhDongDem(game))
    await kiem_tra_het_dem(game)

async def kiem_tra_het_dem(game):
    if game.trang_thai != "night": return
    if len(game.da_hanh_dong) < len(game.con_song): return
    
    try:
        game.trang_thai = "processing_night"
        await hien_thi_loading(game, "Đang tính toán kết quả của đêm qua...")
        danh_sach_chet = set()
        phieu_soi_chung = {}
        
        blocked_id = None
        for uid, hanh_dong in game.hanh_dong_dem.items():
            if game.vai_tro.get(uid) == "soi_acmong" and hanh_dong != "skip":
                try: blocked_id = int(hanh_dong)
                except Exception: pass

        for uid, hanh_dong in game.hanh_dong_dem.items():
            if uid == blocked_id or hanh_dong == "skip": continue
            if game.vai_tro.get(uid) == "baove": 
                try:
                    game.muc_tieu_baove = int(hanh_dong)
                    game.last_protected_id = game.muc_tieu_baove
                except Exception: pass

        hanh_dong_hop_le = {u: a for u, a in game.hanh_dong_dem.items() if u != blocked_id and a != "skip"}

        for uid, hanh_dong in hanh_dong_hop_le.items():
            vai = game.vai_tro.get(uid)
            if vai in PHE_SOI_KILLERS:
                try:
                    mt = int(hanh_dong)
                    w = 2 if vai == "soichua" else 1
                    phieu_soi_chung[mt] = phieu_soi_chung.get(mt, 0) + w
                except Exception: pass

        wolf_victims = []
        if phieu_soi_chung:
            max_p = max(phieu_soi_chung.values())
            ung_cu_vien = [k for k, v in phieu_soi_chung.items() if v == max_p]
            chet_soi_1 = random.choice(ung_cu_vien)
            wolf_victims.append(chet_soi_1)
            
            if game.soicon_buff or (game.soi_hacam_buff and not any(game.vai_tro.get(x) in PHE_SOI_KILLERS for x in game.nguoi_choi if x.id not in game.con_song)):
                other_votes = [k for k in phieu_soi_chung.keys() if k != chet_soi_1]
                if other_votes:
                    wolf_victims.append(random.choice(other_votes))
                else:
                    other_alive = [p for p in game.con_song if p != chet_soi_1]
                    if other_alive: wolf_victims.append(random.choice(other_alive))

        witch_healed_id = None
        witch_poison_id = None
        for uid, hanh_dong in hanh_dong_hop_le.items():
            if game.vai_tro.get(uid) == "phuthuy":
                if str(hanh_dong).startswith("save_"):
                    try:
                        witch_healed_id = int(str(hanh_dong).split("_")[1])
                        game.phuthuy_da_cuu = True
                    except Exception: pass
                elif str(hanh_dong).startswith("kill_"):
                    try:
                        witch_poison_id = int(str(hanh_dong).split("_")[1])
                        game.phuthuy_da_giet = True
                    except Exception: pass

        lay_nhiem_id = next((int(a) for u, a in hanh_dong_hop_le.items() if game.vai_tro.get(u) == "soi_laynhiem"), None)
        
        final_wolf_kills = []
        for t in wolf_victims:
            if t == witch_healed_id:
                if t == lay_nhiem_id and game.soi_laynhiem_can_infect:
                    game.soi_laynhiem_can_infect = False 
                continue
                
            if t == game.muc_tieu_baove:
                continue 
                
            if game.vai_tro.get(t) == "satthu":
                continue 
                
            if t == lay_nhiem_id and game.soi_laynhiem_can_infect:
                game.vai_tro[t] = "soi" 
                game.soi_laynhiem_can_infect = False
                continue
                
            final_wolf_kills.append(t)

        for t in list(final_wolf_kills):
            if game.vai_tro.get(t) == "gialang":
                if game.gialang_lives > 1:
                    game.gialang_lives -= 1
                    final_wolf_kills.remove(t)
                else:
                    game.danlang_skills_active = False 
            elif game.vai_tro.get(t) == "hiepsi":
                try:
                    search_idx = game.con_song.index(t)
                    for _ in range(len(game.con_song)):
                        search_idx = search_idx - 1 if search_idx > 0 else len(game.con_song) - 1
                        if game.vai_tro.get(game.con_song[search_idx]) in PHE_SOI_KILLERS:
                            game.hiepsi_poisoned_id = game.con_song[search_idx]
                            break
                except Exception: pass

        danh_sach_chet.update(final_wolf_kills)
        if final_wolf_kills:
            game.news.append("🐺 Bầy Sói đã tấn công đẫm máu một mục tiêu trong đêm!")

        secondary_kills = []
        if witch_poison_id: secondary_kills.append(witch_poison_id)
        
        for uid, hanh_dong in hanh_dong_hop_le.items():
            vai = game.vai_tro.get(uid)
            if vai == "satthu": 
                try: secondary_kills.append(int(hanh_dong))
                except Exception: pass
            elif vai == "soitrang" and game.ngay % 2 == 0: 
                try: secondary_kills.append(int(hanh_dong))
                except Exception: pass
            elif vai == "cobe" and hanh_dong == "peek":
                if random.randint(1, 100) <= 20:
                    if uid != game.muc_tieu_baove and uid != witch_healed_id:
                        secondary_kills.append(uid)
                        game.news.append("👧 Một tiếng hét thất thanh vang lên từ phía hang Sói...")
                        
        if hasattr(game, 'hiepsi_poisoned_id') and game.hiepsi_poisoned_id and game.hiepsi_poisoned_id in game.con_song:
            secondary_kills.append(game.hiepsi_poisoned_id)
            game.news.append("🗡️ Lưỡi kiếm rỉ sét đã phát tác chất độc lên một kẻ khát máu!")
            game.hiepsi_poisoned_id = None

        for t in secondary_kills:
            if game.vai_tro.get(t) == "gialang":
                game.danlang_skills_active = False
                game.news.append("👴 Già Làng đã bị sát hại bất ngờ! Dân Làng bàng hoàng đánh mất sức mạnh.")
            danh_sach_chet.add(t)

        for uid, hanh_dong in hanh_dong_hop_le.items():
            vai = game.vai_tro.get(uid)
            try:
                if vai == "thosan": game.muc_tieu_thosan = int(hanh_dong)
                elif vai == "phapsucam": game.nguoi_bi_cam = int(hanh_dong)
                elif vai == "giaochu": game.giaochu_cult.append(int(hanh_dong))
                elif vai == "macayrong": 
                    target = int(hanh_dong)
                    if game.vai_tro.get(target) not in PHE_SOI_KILLERS:
                        game.vampire_bitten.append(target)
                        game.vai_tro[target] = "danlang"
                elif vai == "cupid":
                    ids = str(hanh_dong).split("_")
                    game.cupid_linked = [int(ids[0]), int(ids[1])]
                elif vai == "thoitieu":
                    ids = str(hanh_dong).split("_")
                    game.thoitieu_hypnotized.extend([int(ids[0]), int(ids[1])])
                elif vai == "trehoang": game.trehoang_idol[uid] = int(hanh_dong)
            except Exception: pass

        final_deaths = set(danh_sach_chet)
        for c in list(final_deaths):
            if c in game.cupid_linked:
                other = game.cupid_linked[0] if game.cupid_linked[1] == c else game.cupid_linked[1]
                if other in game.con_song:
                    final_deaths.add(other)
                    game.news.append("💘 Có người đã quyết định quyên sinh theo tình yêu của mình!")
                    if game.vai_tro.get(other) == "gialang":
                        game.danlang_skills_active = False

        thosan_id = next((u for u, v in game.vai_tro.items() if v == "thosan"), None)
        if thosan_id in final_deaths and game.muc_tieu_thosan and game.muc_tieu_thosan in game.con_song and game.muc_tieu_thosan not in final_deaths:
            final_deaths.add(game.muc_tieu_thosan)
            game.news.append("🏹 Thợ Săn đã dùng chút sức tàn bắn một phát đạn chí mạng trước khi nhắm mắt!")
            if game.vai_tro.get(game.muc_tieu_thosan) == "gialang":
                game.danlang_skills_active = False

        game.soicon_buff = False
        for c in list(final_deaths):
            if c in game.con_song: game.con_song.remove(c)
            if c == game.mayor_id: game.mayor_id = None
            
            for tr_id, idol in game.trehoang_idol.items():
                if idol == c and tr_id in game.con_song: 
                    game.vai_tro[tr_id] = "soi"
                    game.news.append("🐺 Có tiếng hú hoang dã vang dội từ rừng sâu báo hiệu một sinh vật vừa biến đổi...")

            nguoi_chet = game.lay_nguoi_choi(c)
            if nguoi_chet:
                tin_chet = f"💀 Đêm qua, **{nguoi_chet.mention}** đã tử nạn!"
                if game.cai_dat["hien_vai"]: tin_chet += f" (Họ là **{TUDIEN_VAI[game.vai_tro.get(c)]}**)"
                game.news.append(tin_chet)
                if game.hell_channel:
                    try: await game.hell_channel.set_permissions(nguoi_chet, read_messages=True, send_messages=True)
                    except Exception: pass
                if game.wolf_channel and game.vai_tro.get(c) in PHE_SOI_KILLERS:
                    try: await game.wolf_channel.set_permissions(nguoi_chet, read_messages=False)
                    except Exception: pass

        if not final_deaths:
            game.news.append("🌅 Đêm qua trôi qua bình yên, không có ai chết!")
            
        thang, lido = game.kiem_tra_thang()
        if thang:
            phe = "MA SÓI 🐺" if thang == "soi" else "THẾ LỰC THỨ 3 🩸" if thang == "phe3" else "DÂN LÀNG 🧑‍🌾"
            if thang == "hoa": phe = "HÒA"
            await ket_thuc_game(game, lido, phe)
            return
            
        await bat_dau_sang(game)
    except Exception as e:
        print(f"Lỗi hệ thống trong kiem_tra_het_dem: {e}")
        await bat_dau_sang(game)

async def bat_dau_sang(game):
    await khoa_mo_kenh_chung(game, dong_cua=False)
    await cap_nhat_mic(game, False)
    
    quangau_id = next((u for u, v in game.vai_tro.items() if v == "quangau" and u in game.con_song), None)
    if quangau_id and game.danlang_skills_active:
        idx = game.con_song.index(quangau_id)
        l_idx = idx - 1 if idx > 0 else len(game.con_song) - 1
        r_idx = idx + 1 if idx < len(game.con_song) - 1 else 0
        if game.vai_tro.get(game.con_song[l_idx]) in PHE_SOI_KILLERS or game.vai_tro.get(game.con_song[r_idx]) in PHE_SOI_KILLERS:
            game.news.append("🐻 Quản Gấu đang giật mình vì con Gấu của họ gầm gừ dữ dội!")
            
    if game.mayor_id is None:
        game.trang_thai = "mayor_election"
        game.phieu_ngay = {}
        game.embed_title = f"☀️ SÁNG NGÀY {game.ngay} - BẦU TRƯỞNG LÀNG"
        game.embed_desc = "Mọi người hãy bỏ phiếu để chọn ra người lãnh đạo."
        game.embed_color = discord.Color.gold()
        await cap_nhat_embed_chinh(game, view=ViewBieuQuyetNgay(game, is_mayor=True))
    else:
        await bat_dau_thao_luan(game)

async def kiem_tra_het_bau_truong_lang(game):
    if game.trang_thai != "mayor_election": return
    if len(game.phieu_ngay) < len(game.con_song): return
    
    game.trang_thai = "processing_election"
    await hien_thi_loading(game, "Đang kiểm phiếu Bầu Trưởng Làng...")
    dem_phieu = {}
    for p in game.phieu_ngay.values():
        if p != "skip": dem_phieu[p] = dem_phieu.get(p, 0) + 1
    
    if dem_phieu:
        max_phieu = max(dem_phieu.values())
        ung_cu_vien = [k for k, v in dem_phieu.items() if v == max_phieu]
        game.mayor_id = int(random.choice(ung_cu_vien))
        game.news.append(f"🎖️ {game.lay_nguoi_choi(game.mayor_id).mention} đã đắc cử vị trí Trưởng Làng!")
    else:
        game.news.append("🎖️ Không ai muốn làm Trưởng Làng, vị trí này bị bỏ trống.")
    
    await bat_dau_thao_luan(game)

async def bat_dau_thao_luan(game):
    game.trang_thai = "discussion"
    cam_tb = f"\n🤐 Hôm nay **{game.lay_nguoi_choi(game.nguoi_bi_cam).mention}** đã bị câm!" if game.nguoi_bi_cam and game.nguoi_bi_cam in game.con_song else ""
    game.embed_title = f"🗣️ THẢO LUẬN NGÀY {game.ngay}"
    game.embed_desc = f"Mọi người hãy trao đổi thông tin ở Kênh Làng.{cam_tb}"
    game.embed_color = discord.Color.blue()
    
    class SkipThaoLuan(discord.ui.View):
        def __init__(self, g):
            super().__init__(timeout=None)
            self.g = g
            
        @discord.ui.button(label="⏩ Chuyển Sang Biểu Quyết (Chủ Phòng)", style=discord.ButtonStyle.danger)
        async def btn_skip(self, interaction, button):
            if interaction.user.id != self.g.host.id:
                try: await interaction.response.send_message("❌ Chức năng chỉ dành cho chủ phòng!\n*(Tin nhắn này sẽ tự biến mất sau 3s)*", ephemeral=True, delete_after=3.0)
                except Exception: pass
            else:
                try: await interaction.response.defer()
                except Exception: pass
                self.stop()
                await bat_dau_treo_co(self.g)
            
        @discord.ui.button(label="🛑 Reset Game (Lỗi)", style=discord.ButtonStyle.danger, row=1)
        async def btn_reset(self, interaction, button):
            if interaction.user.id != self.g.host.id:
                try: await interaction.response.send_message("❌ Chỉ chủ phòng mới được dùng nút này!\n*(Tin nhắn này sẽ tự biến mất sau 3s)*", ephemeral=True, delete_after=3.0)
                except Exception: pass
            else:
                try: await interaction.response.defer()
                except Exception: pass
                embed = discord.Embed(title="🛑 TRẬN ĐẤU BỊ RESET", description="Chủ phòng đã đóng phòng khẩn cấp.", color=discord.Color.dark_grey())
                try: await self.g.main_message.edit(content=None, embed=embed, view=None)
                except Exception: pass
                await dondep_game(self.g)
                self.stop()
            
    await cap_nhat_embed_chinh(game, view=SkipThaoLuan(game))
    
    if game.cai_dat["thoi_gian_ngay"] > 0:
        asyncio.create_task(dem_thoi_gian_thao_luan(game, game.ngay))

async def dem_thoi_gian_thao_luan(game, ngay_hien_tai):
    await asyncio.sleep(game.cai_dat["thoi_gian_ngay"])
    if game.channel.id in phong_choi and game.trang_thai == "discussion" and game.ngay == ngay_hien_tai:
        await bat_dau_treo_co(game)

async def bat_dau_treo_co(game):
    await hien_thi_loading(game, "Đã hết thời gian thảo luận. Chuẩn bị biểu quyết Treo Cổ...")
    game.trang_thai = "voting"
    game.phieu_ngay = {}
    game.embed_title = f"⚖️ BIỂU QUYẾT TREO CỔ NGÀY {game.ngay}"
    game.embed_desc = "Đã đến lúc phán xét. Quyết định ai sẽ lên máy chém hôm nay."
    game.embed_color = discord.Color.red()
    await cap_nhat_embed_chinh(game, view=ViewBieuQuyetNgay(game, is_mayor=False))

async def kiem_tra_het_treo_co(game):
    if game.trang_thai != "voting": return
    so_nguoi_duoc_vote = len(game.con_song) - (1 if game.nguoi_bi_cam in game.con_song else 0)
    if len(game.phieu_ngay) < so_nguoi_duoc_vote: return
    
    try:
        game.trang_thai = "processing_voting"
        await hien_thi_loading(game, "Đang đếm số phiếu hành hình...")
        
        dem_phieu = {}
        for p, v in game.phieu_ngay.items():
            weight = 2 if p == game.mayor_id else 1
            dem_phieu[v] = dem_phieu.get(v, 0) + weight
            
        max_phieu = max(dem_phieu.values())
        nhung_nguoi_max = [k for k, v in dem_phieu.items() if v == max_phieu]
        
        hanged_id = None
        thang, lido, phe = None, None, None

        if len(nhung_nguoi_max) == 1 and nhung_nguoi_max[0] != "skip":
            hanged_id = int(nhung_nguoi_max[0])
        else:
            detethan_id = next((u for u, v in game.vai_tro.items() if v == "detethan" and u in game.con_song), None)
            if detethan_id:
                hanged_id = detethan_id
                game.news.append("⚖️ Làng biểu quyết hòa! Dê Tế Thần sẽ bị mang ra làm vật hiến tế thay thế!")
            else:
                game.news.append("⚖️ Lượng phiếu ngang bằng hoặc đa số chọn Bỏ qua. Không ai bị treo cổ hôm nay.")
                
        if hanged_id:
            nguoi_chet = game.lay_nguoi_choi(hanged_id)
            vai_chet = game.vai_tro.get(hanged_id)
            
            if vai_chet == "chandoi":
                thang, lido, phe = "phe3", "Kẻ chán đời đã đạt được mục đích bị treo cổ!", "CHÁN ĐỜI 🎭"
                game.news.append(f"🪢 Làng đã treo cổ **{nguoi_chet.mention}** và mắc mưu hắn vĩnh viễn!")
                await ket_thuc_game(game, lido, phe)
                return
            elif vai_chet == "thiensu" and game.ngay == 1:
                thang, lido, phe = "phe3", "Thiên sứ đã được giải thoát ngay ngày đầu!", "THIÊN SỨ 👼"
                game.news.append(f"🪢 Làng đã bị thao túng và treo cổ **{nguoi_chet.mention}** ngay Ngày 1!")
                await ket_thuc_game(game, lido, phe)
                return
            elif vai_chet == "kengoc" and not game.kengoc_revealed:
                game.kengoc_revealed = True
                game.news.append(f"🪢 Đám đông định treo cổ **{nguoi_chet.mention}**, nhưng họ lật bài là **Kẻ Ngốc 🤡**! Thoát chết nhưng bị tước quyền biểu quyết vĩnh viễn.")
                hanged_id = None 
            elif vai_chet == "thosan":
                game.news.append(f"🪢 Làng quyết định treo cổ **{nguoi_chet.mention}**!")
                await hien_thi_loading(game, "Thợ Săn đang vùng vẫy trước giá treo cổ và rút súng ra...")
                await bat_dau_thosan_ban(game, hanged_id)
                return
            else:
                final_lynch_deaths = {hanged_id}
                
                if hanged_id in game.cupid_linked:
                    other = game.cupid_linked[0] if game.cupid_linked[1] == hanged_id else game.cupid_linked[1]
                    if other in game.con_song:
                        final_lynch_deaths.add(other)
                        game.news.append(f"💘 Chứng kiến cái chết, {game.lay_nguoi_choi(other).mention} đã tự vẫn theo tình yêu!")
                
                for c in list(final_lynch_deaths):
                    v_c = game.vai_tro.get(c)
                    if v_c == "soicon": game.soicon_buff = True
                    if v_c == "gialang":
                        game.danlang_skills_active = False
                        game.news.append("👴 Già Làng đã chết thảm! Kỹ năng Dân Làng bị phong ấn toàn bộ.")
                    if v_c == "thosan" and c != hanged_id:
                        await bat_dau_thosan_ban(game, c)
                        return
                    
                    if c in game.con_song: game.con_song.remove(c)
                    if c == game.mayor_id: game.mayor_id = None
                    
                    for tr_id, idol in game.trehoang_idol.items():
                        if idol == c and tr_id in game.con_song: 
                            game.vai_tro[tr_id] = "soi"
                            game.news.append("🐺 Có tiếng hú hoang dã vang dội từ rừng sâu báo hiệu một sinh vật vừa biến đổi...")
                    
                    p_obj = game.lay_nguoi_choi(c)
                    if c == hanged_id: tin = f"🪢 Làng đã thống nhất treo cổ **{p_obj.mention}**!"
                    else: tin = f"💀 **{p_obj.mention}** đã nhắm mắt xuôi tay!"
                        
                    if game.cai_dat["hien_vai"]: tin += f" (Họ là **{TUDIEN_VAI[v_c]}**)"
                    game.news.append(tin)
                    if p_obj and game.hell_channel:
                        try: await game.hell_channel.set_permissions(p_obj, read_messages=True, send_messages=True)
                        except Exception: pass
            
        if not thang:
            thang, lido = game.kiem_tra_thang()
            if thang:
                phe = "MA SÓI 🐺" if thang == "soi" else "THẾ LỰC THỨ 3 🩸" if thang == "phe3" else "DÂN LÀNG 🧑‍🌾"
                if thang == "hoa": phe = "HÒA"
                await ket_thuc_game(game, lido, phe)
                return
                
        game.ngay += 1
        game.nguoi_bi_cam = None
        if "thiensu" in game.vai_tro.values() and game.ngay > 1:
            for uid, vai in game.vai_tro.items():
                if vai == "thiensu": game.vai_tro[uid] = "danlang"
        await bat_dau_dem(game)
    except Exception as e:
        print(f"Lỗi hệ thống trong kiem_tra_het_treo_co: {e}")
        game.ngay += 1
        await bat_dau_dem(game)

async def bat_dau_thosan_ban(game, thosan_id):
    game.trang_thai = "hunter_action"
    game.embed_title = "🏹 CƠ HỘI CUỐI CÙNG CỦA THỢ SĂN"
    game.embed_desc = f"{game.lay_nguoi_choi(thosan_id).mention}, bạn sắp bị treo cổ! Hãy chọn một người để kéo theo xuống mồ."
    game.embed_color = discord.Color.dark_red()
    await cap_nhat_embed_chinh(game, view=HunterShootView(game, thosan_id))

    class HunterShootMenu(discord.ui.Select):
        def __init__(self, g, uid):
            self.g = g
            self.uid = uid
            options = [discord.SelectOption(label="Bỏ qua (Chết một mình)", value="skip")]
            for pid in g.con_song:
                p = g.lay_nguoi_choi(pid)
                if pid != uid: options.append(discord.SelectOption(label=p.display_name, value=str(pid)))
            super().__init__(placeholder="Chọn nạn nhân...", options=options[:25])
            
        async def callback(self, inter):
            if inter.user.id != self.uid:
                try: await inter.response.send_message("❌ Bạn không phải là Thợ Săn!\n*(Tin nhắn này sẽ tự biến mất sau 3s)*", ephemeral=True, delete_after=3.0)
                except Exception: pass
            else:
                try: await inter.response.defer()
                except Exception: pass
                
                val = self.values[0]
                if self.uid in self.g.con_song: self.g.con_song.remove(self.uid)
                if self.uid == self.g.mayor_id: self.g.mayor_id = None
                
                if val != "skip":
                    mt = int(val)
                    if mt in self.g.con_song: self.g.con_song.remove(mt)
                    if mt == self.g.mayor_id: self.g.mayor_id = None
                    self.g.news.append(f"💥 ĐÙNG! Trước khi tắt thở, Thợ Săn đã bắn nát đầu **{self.g.lay_nguoi_choi(mt).mention}**!")
                else:
                    self.g.news.append("💥 Thợ Săn đã chọn cái chết thanh thản một mình.")
                self.view.stop()
                
                thang, lido = self.g.kiem_tra_thang()
                if thang:
                    phe = "MA SÓI 🐺" if thang == "soi" else "THẾ LỰC THỨ 3 🩸" if thang == "phe3" else "DÂN LÀNG 🧑‍🌾"
                    if thang == "hoa": phe = "HÒA"
                    await ket_thuc_game(self.g, lido, phe)
                else:
                    self.g.ngay += 1
                    self.g.nguoi_bi_cam = None
                    await bat_dau_dem(self.g)
                
    class HunterShootView(discord.ui.View):
        def __init__(self, g, uid):
            super().__init__(timeout=None)
            self.add_item(HunterShootMenu(g, uid))
            
        @discord.ui.button(label="🛑 Reset Game (Lỗi)", style=discord.ButtonStyle.danger, row=1)
        async def btn_reset(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != self.g.host.id:
                try: await interaction.response.send_message("❌ Chỉ chủ phòng mới được dùng nút này!\n*(Tin nhắn này sẽ tự biến mất sau 3s)*", ephemeral=True, delete_after=3.0)
                except Exception: pass
            else:
                try: await interaction.response.defer()
                except Exception: pass
                embed = discord.Embed(title="🛑 TRẬN ĐẤU BỊ RESET", description="Chủ phòng đã đóng phòng khẩn cấp.", color=discord.Color.dark_grey())
                try: await self.g.main_message.edit(content=None, embed=embed, view=None)
                except Exception: pass
                await dondep_game(self.g)
                self.stop()