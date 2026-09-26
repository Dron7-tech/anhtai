import discord
import random
import asyncio
import masoi  # Trích xuất module gốc để Monkey-Patching

# =========================================================================
# LỚP UI (USER INTERFACE) OVERRIDE: XỬ LÝ LỖI MENU VÀ RÀNG BUỘC ĐỒNG MINH
# =========================================================================

class SafeMenuGietPhuThuy(discord.ui.Select):
    def __init__(self, game, uid):
        self.game = game
        self.uid = uid
        options = [discord.SelectOption(label="Không Giết Ai", value="skip")]
        try:
            for pid in game.con_song:
                p = game.lay_nguoi_choi(pid)
                if pid != uid: # EDGE CASE: Phù Thủy không thể tự độc bản thân
                    options.append(discord.SelectOption(label=f"Giết: {p.display_name}", value=str(pid)))
        except Exception: pass
        super().__init__(placeholder="☠️ Chọn người để Giết (Bình Độc)...", options=options[:25])

    async def callback(self, interaction: discord.Interaction):
        try:
            val = self.values[0]
            if val != "skip":
                self.game.hanh_dong_dem[self.uid] = f"kill_{val}"
                self.game.da_hanh_dong.add(self.uid)
                try: await interaction.response.send_message(f"✅ Đã dùng Bình Độc lên mục tiêu!\n*(Tự biến mất sau 3s)*", ephemeral=True, delete_after=3.0)
                except Exception: pass
                await masoi.cap_nhat_embed_chinh(self.game)
                await masoi.kiem_tra_het_dem(self.game)
            else:
                try: await interaction.response.defer()
                except Exception: pass
        except Exception: pass

class SafeMenuChonDem(discord.ui.Select):
    def __init__(self, game, uid, role):
        self.game = game
        self.uid = uid
        self.role = role
        options = []
        max_v = 1
        ph = "Chọn mục tiêu..."
        
        try:
            if role in ["cupid", "thoitieu"]:
                max_v = min(2, len(game.con_song))
                ph = "Chọn 2 mục tiêu..."
                for pid in game.con_song: 
                    options.append(discord.SelectOption(label=game.lay_nguoi_choi(pid).display_name, value=str(pid)))
            elif role == "ketrom":
                for r in getattr(game, "ketrom_choices", []): 
                    options.append(discord.SelectOption(label=masoi.TUDIEN_VAI.get(r, str(r)), value=str(r)))
            elif role == "hoasoi":
                options.append(discord.SelectOption(label="Phe Dân Làng", value="danlang"))
                options.append(discord.SelectOption(label="Phe Sói", value="soi"))
            elif role == "cobe":
                options.append(discord.SelectOption(label="Nhìn trộm Sói", value="peek"))
                options.append(discord.SelectOption(label="Ngủ ngoan", value="skip"))
            else:
                options.append(discord.SelectOption(label="Bỏ qua (Không hành động)", value="skip"))
                for pid in game.con_song:
                    # EDGE CASE: Ràng buộc Bảo Vệ
                    if role == "baove" and pid == getattr(game, "last_protected_id", None):
                        continue
                    
                    # EDGE CASE: Sát thủ không tự sát
                    if role == "satthu" and pid == uid:
                        continue 

                    # EDGE CASE: Ràng buộc Bầy Sói (Friendly Fire Prevention)
                    if role in masoi.PHE_SOI_KILLERS:
                        if game.vai_tro.get(pid) in masoi.PHE_SOI_KILLERS:
                            # Ngoại lệ: Sói Trắng đêm chẵn được cắn đồng loại
                            if role == "soitrang" and getattr(game, "ngay", 1) % 2 == 0:
                                pass
                            else:
                                continue # Sói khác tuyệt đối không cắn nhau
                    
                    options.append(discord.SelectOption(label=game.lay_nguoi_choi(pid).display_name, value=str(pid)))
        except Exception as e: 
            print(f"Lỗi Render Menu Đêm: {e}")
            options.append(discord.SelectOption(label="Bỏ qua", value="skip"))

        super().__init__(placeholder=ph, min_values=1 if role not in ["cupid", "thoitieu"] else max_v, max_values=max_v, options=options[:25])

    async def callback(self, interaction: discord.Interaction):
        try:
            val = self.values[0]
            if self.role in ["cupid", "thoitieu"]:
                self.game.hanh_dong_dem[self.uid] = f"{self.values[0]}_{self.values[1]}"
                msg = "✅ Đã xác nhận 2 mục tiêu."
            else:
                if val == "skip":
                    self.game.hanh_dong_dem[self.uid] = "skip"
                    msg = "Bạn đã chọn bỏ qua."
                elif self.role in ["ketrom", "hoasoi", "cobe"]:
                    self.game.hanh_dong_dem[self.uid] = str(val)
                    msg = "✅ Đã xác nhận lựa chọn của bạn."
                    # Đệ quy Kẻ Trộm ngày 1
                    if self.role == "ketrom" and str(val) in ["cupid", "trehoang"] and getattr(self.game, "ngay", 1) == 1:
                        self.game.vai_tro[self.uid] = str(val) 
                        view_chon = discord.ui.View()
                        view_chon.add_item(SafeMenuChonDem(self.game, self.uid, str(val)))
                        try: await interaction.response.send_message("👇 Hãy sử dụng kỹ năng mới nhận:", view=view_chon, ephemeral=True, delete_after=10.0)
                        except Exception: pass
                        return
                else:
                    self.game.hanh_dong_dem[self.uid] = int(val)
                    msg = f"✅ Đã xác nhận mục tiêu."
            
            self.game.da_hanh_dong.add(self.uid)
            try: await interaction.response.send_message(f"{msg}\n*(Tự biến mất sau 3s)*", ephemeral=True, delete_after=3.0)
            except Exception: pass
            
            await masoi.cap_nhat_embed_chinh(self.game)
            await masoi.kiem_tra_het_dem(self.game)
        except Exception as e:
            print(f"Lỗi Callback Menu Đêm: {e}")

# =========================================================================
# CORE ENGINE: MA TRẬN XỬ LÝ ĐÊM TỐI & XUNG ĐỘT (CROSS-ROLE ENGINE)
# =========================================================================
async def safe_kiem_tra_het_dem(game):
    if getattr(game, "trang_thai", "") != "night": return
    if len(getattr(game, "da_hanh_dong", [])) < len(getattr(game, "con_song", [])): return
    
    try:
        game.trang_thai = "processing_night"
        await masoi.hien_thi_loading(game, "Màn đêm đang khép lại. Tính toán sinh tử...")
        
        # SỬ DỤNG SET() CHỐNG CRASH CÁI CHẾT ĐA NGUỒN
        danh_sach_chet = set()
        hanh_dong_hop_le = {}
        
        # BƯỚC 1: KHÓA KỸ NĂNG (SILENCER)
        blocked_id = None
        try:
            for uid, hanh_dong in game.hanh_dong_dem.items():
                if game.vai_tro.get(uid) == "soi_acmong" and hanh_dong != "skip":
                    blocked_id = int(hanh_dong)
        except Exception: pass

        # Filter hành động hợp lệ
        for uid, hanh_dong in game.hanh_dong_dem.items():
            if uid == blocked_id or hanh_dong == "skip": continue
            hanh_dong_hop_le[uid] = hanh_dong

        # Rủi ro nhìn trộm của Cô Bé (Tính như sát thương Sói gốc)
        cobe_id = None
        cobe_chet = False
        try:
            for u, a in hanh_dong_hop_le.items():
                if game.vai_tro.get(u) == "cobe" and a == "peek":
                    cobe_id = u
                    if random.randint(1, 100) <= 20: cobe_chet = True
        except Exception: pass

        # BƯỚC 2: BẢO VỆ (SHIELDING)
        try:
            game.muc_tieu_baove = None
            for uid, hanh_dong in hanh_dong_hop_le.items():
                if game.vai_tro.get(uid) == "baove": 
                    if int(hanh_dong) != getattr(game, "last_protected_id", None):
                        game.muc_tieu_baove = int(hanh_dong)
                        game.last_protected_id = game.muc_tieu_baove
                    else:
                        game.muc_tieu_baove = None
        except Exception: pass

        # BƯỚC 3: SÁT THƯƠNG SÓI CHÍNH QUY & BUFF TỨC GIẬN
        phieu_soi = {}
        try:
            for uid, hanh_dong in hanh_dong_hop_le.items():
                vai = game.vai_tro.get(uid)
                if vai in masoi.PHE_SOI_KILLERS and vai != "soitrang":
                    mt = int(hanh_dong)
                    w = 2 if vai == "soichua" else 1 
                    phieu_soi[mt] = phieu_soi.get(mt, 0) + w
                elif vai == "soitrang" and getattr(game, "ngay", 1) % 2 == 1:
                    mt = int(hanh_dong)
                    phieu_soi[mt] = phieu_soi.get(mt, 0) + 1
        except Exception: pass

        wolf_victims = []
        if phieu_soi:
            try:
                max_p = max(phieu_soi.values())
                ung_cu_vien = [k for k, v in phieu_soi.items() if v == max_p]
                primary_target = random.choice(ung_cu_vien)
                wolf_victims.append(primary_target)
                
                # Check Buff Sói Con / Sói Hắc Ám
                soi_hacam_active = getattr(game, "soi_hacam_buff", False) and not any(game.vai_tro.get(x) in masoi.PHE_SOI_KILLERS for x in [p.id for p in getattr(game, "nguoi_choi", [])] if x not in game.con_song)
                if getattr(game, "soicon_buff", False) or soi_hacam_active:
                    other_votes = [k for k in phieu_soi.keys() if k != primary_target]
                    if other_votes: 
                        wolf_victims.append(random.choice(other_votes))
                    else:
                        other_alive = [p for p in game.con_song if p != primary_target and game.vai_tro.get(p) not in masoi.PHE_SOI_KILLERS]
                        if other_alive: wolf_victims.append(random.choice(other_alive))
            except Exception: pass
            
        if cobe_chet: wolf_victims.append(cobe_id)

        # BƯỚC 4: CỨU CHỮA (HEAL) & SÓI LÂY NHIỄM (INFECT)
        witch_healed_id = None
        witch_poison_id = None
        try:
            for uid, hanh_dong in hanh_dong_hop_le.items():
                if game.vai_tro.get(uid) == "phuthuy":
                    if str(hanh_dong).startswith("save_"):
                        witch_healed_id = int(str(hanh_dong).split("_")[1])
                        game.phuthuy_da_cuu = True
                    elif str(hanh_dong).startswith("kill_"):
                        witch_poison_id = int(str(hanh_dong).split("_")[1])
                        game.phuthuy_da_giet = True
        except Exception: pass

        lay_nhiem_id = next((int(a) for u, a in hanh_dong_hop_le.items() if game.vai_tro.get(u) == "soi_laynhiem"), None)
        
        final_wolf_kills = []
        try:
            for t in wolf_victims:
                if t == witch_healed_id:  # Phù thủy cứu -> Thanh tẩy lây nhiễm
                    if t == lay_nhiem_id and getattr(game, "soi_laynhiem_can_infect", False):
                        game.soi_laynhiem_can_infect = False 
                    continue
                if t == getattr(game, "muc_tieu_baove", None): continue 
                if game.vai_tro.get(t) == "satthu": continue  # Sát thủ miễn nhiễm
                
                # Bị lây nhiễm thành công
                if t == lay_nhiem_id and getattr(game, "soi_laynhiem_can_infect", False):
                    game.vai_tro[t] = "soi" 
                    game.soi_laynhiem_can_infect = False
                    continue
                    
                final_wolf_kills.append(t)
        except Exception: pass

        # Kiểm tra nội tại Già Làng với sát thương vật lý
        try:
            for t in list(final_wolf_kills):
                if game.vai_tro.get(t) == "gialang":
                    if getattr(game, "gialang_lives", 2) > 1:
                        game.gialang_lives -= 1
                        final_wolf_kills.remove(t)
                    else:
                        game.danlang_skills_active = False 
        except Exception: pass

        danh_sach_chet.update(final_wolf_kills)
        if final_wolf_kills: 
            game.news.append("🐺 Bầy Sói đã tấn công đẫm máu mục tiêu trong đêm!")

        # BƯỚC 5: SÁT THƯƠNG PHỤ XUYÊN KHIÊN & NỌC ĐỘC HIỆP SĨ
        secondary_kills = []
        if witch_poison_id: secondary_kills.append(witch_poison_id)
        
        try:
            for uid, hanh_dong in hanh_dong_hop_le.items():
                vai = game.vai_tro.get(uid)
                if vai == "satthu": secondary_kills.append(int(hanh_dong))
                elif vai == "soitrang" and getattr(game, "ngay", 1) % 2 == 0: secondary_kills.append(int(hanh_dong))
        except Exception: pass
                        
        if getattr(game, 'hiepsi_poisoned_id', None) and game.hiepsi_poisoned_id in game.con_song:
            secondary_kills.append(game.hiepsi_poisoned_id)
            game.news.append("🗡️ Lưỡi kiếm rỉ sét đã phát tác chất độc lên một con Sói!")
            game.hiepsi_poisoned_id = None

        try:
            for t in secondary_kills:
                if game.vai_tro.get(t) == "gialang":
                    game.danlang_skills_active = False # Chết xuyên khiên -> Mất luôn hiệu ứng
                    game.news.append("👴 Già Làng đã bị sát hại bất ngờ! Dân Làng bàng hoàng đánh mất sức mạnh.")
                danh_sach_chet.add(t)
        except Exception: pass

        # Truy vết độc Hiệp sĩ (nếu Hiệp sĩ vừa bị Sói cắn)
        try:
            for t in list(final_wolf_kills):
                if game.vai_tro.get(t) == "hiepsi":
                    search_idx = game.con_song.index(t)
                    for _ in range(len(game.con_song)):
                        search_idx = search_idx - 1 if search_idx > 0 else len(game.con_song) - 1
                        if game.vai_tro.get(game.con_song[search_idx]) in masoi.PHE_SOI_KILLERS:
                            game.hiepsi_poisoned_id = game.con_song[search_idx]
                            break
        except Exception: pass

        # BƯỚC 6: KỸ NĂNG THÔNG TIN VÀ CẤY TAG THEO THỨ TỰ
        try:
            for uid, hanh_dong in hanh_dong_hop_le.items():
                vai = game.vai_tro.get(uid)
                if vai == "phapsucam": game.nguoi_bi_cam = int(hanh_dong)
                elif vai == "giaochu": 
                    if int(hanh_dong) not in getattr(game, "giaochu_cult", []): game.giaochu_cult.append(int(hanh_dong))
                elif vai == "macayrong": 
                    target = int(hanh_dong)
                    # Ma cà rồng không cắn được Sói
                    if game.vai_tro.get(target) not in masoi.PHE_SOI_KILLERS:
                        if target not in getattr(game, "vampire_bitten", []):
                            game.vampire_bitten.append(target)
                            game.vai_tro[target] = "danlang" 
                elif vai == "cupid":
                    ids = str(hanh_dong).split("_")
                    game.cupid_linked = [int(ids[0]), int(ids[1])]
                elif vai == "thoitieu":
                    ids = str(hanh_dong).split("_")
                    game.thoitieu_hypnotized.extend([int(ids[0]), int(ids[1])])
                elif vai == "trehoang":
                    if not getattr(game, "trehoang_idol", {}).get(uid): game.trehoang_idol[uid] = int(hanh_dong)
        except Exception: pass

        # Lấy mục tiêu ghim của Thợ săn
        try:
            for uid, hanh_dong in game.hanh_dong_dem.items(): # Bỏ qua silence vì báo thù là bị động
                if game.vai_tro.get(uid) == "thosan" and hanh_dong != "skip":
                    game.muc_tieu_thosan = int(hanh_dong)
        except Exception: pass

        # BƯỚC 7: CÁI CHẾT ĐỆ QUY (CUPID CHAIN) VÀ BÁO THÙ (HUNTER)
        final_deaths = set(danh_sach_chet)
        try:
            # Tình yêu
            added_by_cupid = set()
            for c in list(final_deaths):
                if c in getattr(game, "cupid_linked", []):
                    other = game.cupid_linked[0] if game.cupid_linked[1] == c else game.cupid_linked[1]
                    if other in game.con_song:
                        added_by_cupid.add(other)
                        game.news.append("💘 Có người đã quyết định quyên sinh theo tình yêu của mình!")
                        if game.vai_tro.get(other) == "gialang": game.danlang_skills_active = False
            final_deaths.update(added_by_cupid)

            # Thợ săn báo thù
            thosan_id = next((u for u, v in game.vai_tro.items() if v == "thosan"), None)
            if thosan_id in final_deaths and getattr(game, "muc_tieu_thosan", None) and game.muc_tieu_thosan in game.con_song and game.muc_tieu_thosan not in final_deaths:
                final_deaths.add(game.muc_tieu_thosan)
                game.news.append("🏹 Thợ Săn đã dùng chút sức tàn bắn một phát đạn chí mạng trước khi ngã xuống!")
                if game.vai_tro.get(game.muc_tieu_thosan) == "gialang": game.danlang_skills_active = False
        except Exception: pass

        # THỰC THI XÓA SỔ VÀ THÔNG BÁO LÊN KÊNH
        game.soicon_buff = False
        try:
            for c in list(final_deaths):
                if c in getattr(game, "con_song", []): 
                    game.con_song.remove(c) 
                if getattr(game, "mayor_id", None) == c: game.mayor_id = None
                
            # Trẻ Hoang kiểm tra Idol chết sau khi clear danh sách (Idol chết, Trẻ hoang PHẢI CÒN SỐNG)
            for tr_id, idol in getattr(game, "trehoang_idol", {}).items():
                if idol in final_deaths and tr_id in game.con_song: 
                    game.vai_tro[tr_id] = "soi"
                    game.news.append("🐺 Có tiếng hú hoang dã vang dội từ rừng sâu báo hiệu một sinh vật vừa đánh mất nhân tính...")

            # Phân quyền vong hồn
            for c in list(final_deaths):
                nguoi_chet = game.lay_nguoi_choi(c)
                if nguoi_chet:
                    tin_chet = f"💀 Đêm qua, **{nguoi_chet.mention}** đã tử nạn!"
                    if game.cai_dat.get("hien_vai"): tin_chet += f" (Họ là **{masoi.TUDIEN_VAI.get(game.vai_tro.get(c), 'Không rõ')}**)"
                    game.news.append(tin_chet)
                    if getattr(game, "hell_channel", None):
                        try: await game.hell_channel.set_permissions(nguoi_chet, read_messages=True, send_messages=True)
                        except Exception: pass
                    if getattr(game, "wolf_channel", None) and game.vai_tro.get(c) in masoi.PHE_SOI_KILLERS:
                        try: await game.wolf_channel.set_permissions(nguoi_chet, read_messages=False)
                        except Exception: pass
        except Exception: pass

        if not final_deaths:
            game.news.append("🌅 Một đêm trôi qua bình yên, không có giọt máu nào đổ xuống!")
            
        thang, lido = game.kiem_tra_thang()
        if thang:
            phe = "MA SÓI 🐺" if thang == "soi" else "THẾ LỰC THỨ 3 🩸" if thang == "phe3" else "DÂN LÀNG 🧑‍🌾"
            if thang == "hoa": phe = "HÒA"
            await masoi.ket_thuc_game(game, lido, phe)
            return
            
        await masoi.bat_dau_sang(game)
    except Exception as e:
        print(f"Lỗi hệ thống cực kỳ nghiêm trọng trong safe_kiem_tra_het_dem: {e}")
        await masoi.bat_dau_sang(game)

# =========================================================================
# CORE ENGINE: XỬ LÝ BIỂU QUYẾT VÀ TỬ HÌNH NGÀY
# =========================================================================
async def safe_kiem_tra_het_treo_co(game):
    if getattr(game, "trang_thai", "") != "voting": return
    so_nguoi_duoc_vote = len(game.con_song) - (1 if getattr(game, "nguoi_bi_cam", None) in game.con_song else 0)
    if len(game.phieu_ngay) < so_nguoi_duoc_vote: return
    
    try:
        game.trang_thai = "processing_voting"
        await masoi.hien_thi_loading(game, "Đang kiểm tra kết quả hành hình...")
        
        dem_phieu = {}
        for p, v in game.phieu_ngay.items():
            # Trưởng làng mất quyền nhân đôi nếu là Kẻ Ngốc đã lật bài
            weight = 1
            if p == getattr(game, "mayor_id", None):
                if not (game.vai_tro.get(p) == "kengoc" and getattr(game, "kengoc_revealed", False)):
                    weight = 2
            dem_phieu[v] = dem_phieu.get(v, 0) + weight
            
        max_phieu = max(dem_phieu.values()) if dem_phieu else 0
        nhung_nguoi_max = [k for k, v in dem_phieu.items() if v == max_phieu]
        
        hanged_id = None
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
                game.news.append(f"🪢 Làng đã treo cổ **{nguoi_chet.mention}** và mắc mưu hắn vĩnh viễn!")
                await masoi.ket_thuc_game(game, "Kẻ chán đời đã đạt được mục đích bị treo cổ!", "CHÁN ĐỜI 🎭")
                return
            elif vai_chet == "thiensu" and getattr(game, "ngay", 2) == 1:
                game.news.append(f"🪢 Làng đã bị thao túng và treo cổ **{nguoi_chet.mention}** ngay Ngày 1!")
                await masoi.ket_thuc_game(game, "Thiên sứ đã được giải thoát ngay ngày đầu!", "THIÊN SỨ 👼")
                return
            elif vai_chet == "kengoc" and not getattr(game, "kengoc_revealed", False):
                game.kengoc_revealed = True
                game.news.append(f"🪢 Đám đông định treo cổ **{nguoi_chet.mention}**, nhưng họ lật bài là **Kẻ Ngốc 🤡**! Thoát chết nhưng bị tước quyền biểu quyết vĩnh viễn.")
                hanged_id = None 
            elif vai_chet == "thosan":
                game.news.append(f"🪢 Làng quyết định treo cổ **{nguoi_chet.mention}**!")
                await masoi.hien_thi_loading(game, "Thợ Săn đang vùng vẫy trước giá treo cổ và rút súng ra...")
                await masoi.bat_dau_thosan_ban(game, hanged_id)
                return
            else:
                final_lynch_deaths = set()
                if hanged_id is not None: final_lynch_deaths.add(hanged_id)
                
                # Check lụy tình (Chết do lụy tình không lật bài Kẻ Ngốc/Thiên sứ)
                if hanged_id in getattr(game, "cupid_linked", []):
                    other = game.cupid_linked[0] if game.cupid_linked[1] == hanged_id else game.cupid_linked[1]
                    if other in game.con_song:
                        final_lynch_deaths.add(other)
                        game.news.append(f"💘 Chứng kiến cái chết, {game.lay_nguoi_choi(other).mention} đã tự vẫn theo tình yêu!")
                
                try:
                    for c in list(final_lynch_deaths):
                        v_c = game.vai_tro.get(c)
                        if v_c == "soicon": game.soicon_buff = True
                        if v_c == "gialang":
                            game.danlang_skills_active = False
                            game.news.append("👴 Già Làng đã chết thảm! Kỹ năng Dân Làng bị phong ấn toàn bộ.")
                        if v_c == "thosan" and c != hanged_id:
                            await masoi.bat_dau_thosan_ban(game, c)
                            return
                        
                        if c in game.con_song: game.con_song.remove(c)
                        if getattr(game, "mayor_id", None) == c: game.mayor_id = None
                        
                        for tr_id, idol in getattr(game, "trehoang_idol", {}).items():
                            if idol == c and tr_id in game.con_song: 
                                game.vai_tro[tr_id] = "soi"
                                game.news.append("🐺 Có tiếng hú hoang dã vang dội từ rừng sâu báo hiệu một sinh vật vừa biến đổi...")
                        
                        p_obj = game.lay_nguoi_choi(c)
                        if p_obj:
                            if c == hanged_id: tin = f"🪢 Làng đã thống nhất treo cổ **{p_obj.mention}**!"
                            else: tin = f"💀 **{p_obj.mention}** đã nhắm mắt xuôi tay vì đau buồn!"
                                
                            if game.cai_dat.get("hien_vai"): tin += f" (Họ là **{masoi.TUDIEN_VAI.get(v_c, 'Không rõ')}**)"
                            game.news.append(tin)
                            if getattr(game, "hell_channel", None):
                                try: await game.hell_channel.set_permissions(p_obj, read_messages=True, send_messages=True)
                                except Exception: pass
                except Exception: pass
            
        thang, lido = game.kiem_tra_thang()
        if thang:
            phe = "MA SÓI 🐺" if thang == "soi" else "THẾ LỰC THỨ 3 🩸" if thang == "phe3" else "DÂN LÀNG 🧑‍🌾"
            if thang == "hoa": phe = "HÒA"
            await masoi.ket_thuc_game(game, lido, phe)
            return
            
        game.ngay += 1
        game.nguoi_bi_cam = None
        # Xóa tư cách Thiên sứ nếu qua Ngày 1
        if "thiensu" in game.vai_tro.values() and game.ngay > 1:
            for uid, vai in game.vai_tro.items():
                if vai == "thiensu": game.vai_tro[uid] = "danlang"
        await masoi.bat_dau_dem(game)
    except Exception as e:
        print(f"Lỗi hệ thống nghiêm trọng trong safe_kiem_tra_het_treo_co: {e}")
        game.ngay += 1
        await masoi.bat_dau_dem(game)


# =========================================================================
# THỰC THI MONKEY-PATCHING LÊN MODULE GỐC MA SÓI
# =========================================================================
masoi.MenuChonDem = SafeMenuChonDem
masoi.MenuGietPhuThuy = SafeMenuGietPhuThuy
masoi.kiem_tra_het_dem = safe_kiem_tra_het_dem
masoi.kiem_tra_het_treo_co = safe_kiem_tra_het_treo_co
print("🚀 Đã tải thành công Ma Sói Core Engine (Anti-Crash & Edge Cases Resolved)!")