import json
import random
import time
import os
from zlapi.models import *
from config import ADMIN, PREFIX

des = {
    'tác giả': "Rosy",
    'mô tả': "Quản lý tài chính trong game Tài Xỉu",
    'tính năng': [
        "💸 Chuyển tiền cho người khác.",
        "💰 Kiểm tra số dư của bạn hoặc người khác.",
        "🏆 Xem bảng xếp hạng người giàu nhất.",
        "🎁 Nhận tiền miễn phí mỗi ngày.",
        "➕ Thêm tiền cho bản thân (chỉ dành cho Admin).",
        "🔧 Cộng tiền cho người khác (chỉ dành cho Admin).",
        "❌ Trừ tiền của người khác (chỉ dành cho Admin).",
        "🔄 Reset số dư toàn hệ thống (chỉ dành cho Admin)."
    ],
    'hướng dẫn sử dụng': [
        "📩 Gửi lệnh tx <tùy chọn> để thực hiện các chức năng quản lý tài chính.",
        "📌 Ví dụ: tx pay @nguoitag 100 để chuyển 100 VNĐ cho người được tag.",
        "✅ Nhận thông báo trạng thái và kết quả thực hiện ngay lập tức."
    ]
}

user_cooldowns = {}
tromtien_cooldowns = {}
duel_requests = {}


def is_admin(author_id):
    return author_id == ADMIN

def load_money_data():
    try:
        with open('modules/cache/money.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_money_data(data):
    with open('modules/cache/money.json', 'w') as f:
        json.dump(data, f, indent=4)

def load_user_assets():
    try:
        with open('modules/cache/user_assets.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_user_assets(data):
    with open('modules/cache/user_assets.json', 'w') as f:
        json.dump(data, f, indent=4)
        
def load_vouchers():
    try:
        with open('modules/cache/vouchers.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_vouchers(data):
    with open('modules/cache/vouchers.json', 'w') as f:
        json.dump(data, f, indent=4)        

def format_money(amount):
    return f"{amount:,} VNĐ"

def get_user_name(client, user_id):
    try:
        user_info = client.fetchUserInfo(user_id)
        profile = user_info.changed_profiles.get(user_id, {})
        return profile.get('zaloName', 'Không xác định')
    except AttributeError:
        return 'Không xác định'

def send_message_with_style(client, text, thread_id, thread_type, color="#000000", font_size="6"):
    """
    Gửi tin nhắn với định dạng màu sắc và cỡ chữ.
    """
    if not text:
        return  # Tránh gửi tin nhắn rỗng

    base_length = len(text)
    adjusted_length = base_length + 400 # Đảm bảo áp dụng style cho toàn bộ tin nhắn
    style = MultiMsgStyle([
        MessageStyle(
            offset=0,
            length=adjusted_length,
            style="color",
            color=color,
            auto_format=False,
        ),
        MessageStyle(
            offset=0,
            length=adjusted_length,
            style="font",
            size=font_size,
            auto_format=False
        )
    ])
    client.send(Message(text=text, style=style), thread_id=thread_id, thread_type=thread_type, ttl=60000)
    
def show_money_menu(message, message_object, thread_id, thread_type, author_id, client):
    # Phản hồi ngay khi nhận được lệnh đúng định dạng
    client.sendReaction(message_object, "✅", thread_id, thread_type, reactionType=75)
    response_message = (
        "🎰 QUẢN LÍ TÀI CHÍNH 🎰\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💸 𝘁𝘅 𝗽𝗮𝘆 → Chuyển tiền cho người khác\n"
        "-  tx pay {số tiền} @username\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔍 𝘁𝘅 𝗰𝗵𝗲𝗰𝗸 → Kiểm tra số dư của bạn hoặc người khác\n"
        "-  tx check (hoặc) tx check @username\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🏆 𝘁𝘅 𝘁𝗼𝗽 → Xem bảng xếp hạng người giàu nhất\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🎁 𝘁𝘅 𝗱𝗮𝗶𝗹𝘆 → Nhận tiền miễn phí mỗi ngày\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🛒 𝘁𝘅 𝘀𝗵𝗼𝗽 → Mua sắm tài sản\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💳️ 𝘁𝘅 𝗯𝘂𝘆 → Mua tài sản\n"
        "-  tx buy {mã vật phẩm} [số lượng]\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💲️ 𝘁𝘅 𝘀𝗲𝗹𝗹 → Bán tài sản\n"
        "-  tx sell {mã vật phẩm} [số lượng]\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🗃️ 𝘁𝘅 𝘁𝗮𝗶𝘀𝗮𝗻 → Kiểm tra tài sản chi tiết\n"
        "- tx taisan"
        "- tx taisan @username\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🏷️ 𝘁𝘅 𝗰𝗼𝗱𝗲 → Nhập code để nhận tiền\n"
        "-  tx code {mã code}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🏷️ 𝘁𝘅 𝘁𝗿𝗼𝗺𝘁𝗶𝗲𝗻 → Trộm tiền từ người khác\n"
        "-  tx tromtien @username\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🏷️ 𝘁𝘅 𝘀𝗼𝗹𝗼 → Thách đấu solo đặt cược\n"
        "-  tx solo {số tiền cược} @username\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🏷️ 𝘁𝘅 𝘀𝗼𝗹𝗼 𝗰𝗵𝗮𝗽𝗻𝗵𝗮𝗻 → Chấp nhận thách đấu solo\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🛠️ 𝘁𝘅 𝘀𝗲𝘁𝗰𝗼𝗱𝗲 → Tạo code (Admin)\n"
        "-  tx setcode {số tiền} {mã code}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "➕ 𝘁𝘅 𝗮𝗱𝗱 → Thêm tiền cho bản thân (Admin)\n"
        "-  tx add {số tiền}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔧 𝘁𝘅 𝘀𝗲𝘁 → Cộng tiền cho người khác (Admin)\n"
        "-  tx set {số tiền} @username\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "❌ 𝘁𝘅 𝗱𝗲𝗹 → Trừ tiền của người khác (Admin)\n"
        "-  tx del {số tiền} @username\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔄 𝘁𝘅 𝗿𝘀 → Reset số dư toàn hệ thống (Admin)\n"
        "-  tx rs\n"
        "━━━━━━━━━━━━━━━━━━━━━━"
    )
    client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type, ttl=20000)

def get_rank_title(balance):
    if balance < 100_000:
        return "🌱 Tay trắng"
    elif balance < 1_000_000:
        return "🆕 Người mới vào nghề"
    elif balance < 10_000_000:
        return "🔰 Tập sự Tài Xỉu"
    elif balance < 50_000_000:
        return "📈 Con bạc tiềm năng"
    elif balance < 100_000_000:
        return "💼 Dân chơi có số má"
    elif balance < 500_000_000:
        return "💰 Cao thủ Tài Xỉu"
    elif balance < 1_000_000_000:
        return "🏆 Đại gia khu vực"
    elif balance < 10_000_000_000:
        return "💎 Triệu phú Tài Xỉu"
    elif balance < 50_000_000_000:
        return "🔥 Huyền thoại đỏ đen"
    elif balance < 100_000_000_000:
        return "👑 Thánh nhân cờ bạc"
    else:
        return "👑 Vua Tài Xỉu"

# Khởi tạo danh sách sản phẩm
shop_items = {
    "1": {"name": "¹🚀 - Tàu con thoi", "price": 1000000000000, "description": "Tàu con thoi – Phương tiện khám phá không gian, biểu tượng của công nghệ vũ trụ."},
    "2": {"name": "²⚔️ - Thanh Gươm Vua Arthur", "price": 150000000000000, "description": "Thanh Gươm Vua Arthur – Thanh kiếm huyền thoại, biểu tượng của công lý và quyền lực."},
    "3": {"name": "³🥚 - Trứng Rồng", "price": 125000000000000, "description": "Trứng Rồng – Trứng của loài rồng huyền thoại, chứa đựng sức mạnh vô biên."},
    "4": {"name": "⁴🦄 - Ngựa 1 Sừng", "price": 220000000000000, "description": "Ngựa 1 Sừng (Kỳ Lân) – Sinh vật huyền thoại, biểu tượng của sự thuần khiết và phép màu."},
    "5": {"name": "⁵👰 - Ngọc Trinh", "price": 50000000000, "description": "Ngọc Trinh – Người nổi tiếng, biểu tượng của vẻ đẹp và sự nổi tiếng."},
    "6": {"name": "⁶🐉 - Rồng Fafnir", "price": 230000000000000, "description": "Rồng Fafnir – Rồng huyền thoại trong thần thoại Bắc Âu, biểu tượng của sức mạnh và sự bảo vệ."},
    "7": {"name": "⁷💍 - Nhẫn kim cương vô giá", "price": 100000000000, "description": "Nhẫn kim cương vô giá – Biểu tượng của sự giàu có và quyền lực."},
    "8": {"name": "⁸🦅 - Thần Điêu", "price": 200000000000000, "description": "Thần Điêu – Loài chim huyền thoại trong văn hóa Trung Quốc, biểu tượng của sức mạnh và tự do."},
    "9": {"name": "⁹🌉 - Cầu Ô Thước", "price": 2000000000000, "description": "Cầu Ô Thước – Cây cầu huyền thoại trong truyền thuyết Ngưu Lang Chức Nữ, biểu tượng của tình yêu."},
    "10": {"name": "¹⁰🔱 - Đinh ba của Poseidon", "price": 180000000000000, "description": "Đinh ba của Poseidon – Vũ khí của thần biển Poseidon, biểu tượng của sức mạnh đại dương."},
    "11": {"name": "¹¹🧤 - Găng Tay Thanos", "price": 170000000000000, "description": "Găng Tay Thanos – Vũ khí vô song của Thanos, biểu tượng của quyền lực tuyệt đối."},
    "12": {"name": "¹²🔮 - Quả cầu tiên tri", "price": 180000000000000, "description": "Quả cầu tiên tri – Vật phẩm huyền bí giúp nhìn thấy tương lai, biểu tượng của trí tuệ thần thoại."},
    "13": {"name": "¹³🗡️ - Kiếm Muramasa", "price": 245000000000000, "description": "Kiếm Muramasa – Thanh kiếm huyền thoại của Nhật Bản, nổi tiếng với sức mạnh và sự sắc bén."},
    "14": {"name": "¹⁴🏎️ - Siêu xe Lamborghini Aventador", "price": 25000000000, "description": "Siêu xe Lamborghini Aventador – Thiết kế độc đáo, hiệu suất mạnh mẽ và ấn tượng."},
    "15": {"name": "¹⁵🛩️ - Máy bay tư nhân G650", "price": 1800000000000, "description": "Máy bay tư nhân Gulfstream G650 – Không gian bay sang trọng, tiện nghi cao cấp."},
    "16": {"name": "¹⁶🚀 - Tàu vũ trụ Space X Falcon 9", "price": 1400000000000, "description": "Tàu vũ trụ SpaceX Falcon 9 – Tiên phong trong khám phá không gian."},
    "17": {"name": "¹⁷✈️ - Máy bay Boeing 747", "price": 8000000000000, "description": "Máy bay Boeing 747 – Biểu tượng hàng không với cánh kép truyền thống."},
    "18": {"name": "¹⁸🏯 - Tử Cấm Thành", "price": 6000000000000, "description": "Tử Cấm Thành – Cung điện hoàng gia cổ ở Bắc Kinh, Trung Quốc, biểu tượng của triều đại Minh và Thanh."},
    "19": {"name": "¹⁹🏤 - Tháp Burj Khalifa", "price": 34500000000000, "description": "Tháp Burj Khalifa – Tòa nhà cao nhất thế giới, biểu tượng của Dubai."},
    "20": {"name": "²⁰🚂 - Tàu cao tốc Thượng Hải - Bắc Kinh", "price": 10000000000, "description": "Tàu cao tốc Thượng Hải - Bắc Kinh – Phương tiện di chuyển nhanh và hiệu quả."},
    "21": {"name": "²¹🏨 - Khách sạn Palace", "price": 10000000000000, "description": "Khách sạn Palace – Khách sạn sang trọng với kiến trúc cổ điển."},
    "22": {"name": "²²🚁 - Máy bay trực thăng Apache", "price": 1500000000, "description": "Máy bay trực thăng Apache – Máy bay chiến đấu mạnh mẽ, biểu tượng của sức mạnh quân sự."},
    "23": {"name": "²³🗽 - Tượng Nữ Thần Tự Do", "price": 1000000000000, "description": "Tượng Nữ Thần Tự Do – Biểu tượng của tự do, dân chủ và hòa bình."},
    "24": {"name": "²⁴📿 - Tràng hạt của Đức Phật", "price": 300000000000000, "description": "Tràng hạt của Đức Phật – Vật phẩm linh thiêng, biểu tượng của sự giác ngộ và bình an."},
    "25": {"name": "²⁵🛩️ - Máy bay chiến đấu F-16 Fighting Falcon", "price": 900000000000, "description": "Máy bay chiến đấu F-16 Fighting Falcon – Chiến đấu cơ hiện đại với hiệu suất ấn tượng."},
    "26": {"name": "²⁶👁️ - Mắt của Horus", "price": 130000000000000, "description": "Mắt của Horus – Biểu tượng bảo vệ và sức khỏe trong thần thoại Ai Cập cổ đại."},
    "27": {"name": "²⁷🏰 - Lâu đài ma ám", "price": 300000000000, "description": "Lâu đài ma ám – Địa điểm huyền bí và hấp dẫn."},
    "28": {"name": "²⁸🪔 - Đèn Diya", "price": 125000000000000, "description": "Đèn Diya – Chiếc đèn dầu, biểu tượng của ánh sáng và sự thịnh vượng trong thần thoại Hindu."},
    "29": {"name": "²⁹🏙️ - Thành phố tương lai", "price": 34500000000000, "description": "Thành phố tương lai – Đô thị với công nghệ tiên tiến."},
    "30": {"name": "³⁰🏟 - Sân vận động Mỹ Đình", "price": 1000000000000, "description": "Sân vận động Mỹ Đình – Hiện đại và biểu tượng thể thao của Việt Nam."},
    "31": {"name": "³¹🏖️ - Bãi biển An Bang", "price": 1500000000000, "description": "Bãi biển An Bang – Bãi biển yên bình ở Hội An, Việt Nam, với cát trắng và nước biển trong."},
    "32": {"name": "³²🛬 - Airbus A380", "price": 10000000000000, "description": "Airbus A380 – Máy bay thương mại khổng lồ, tiêu chuẩn toàn cầu."},
    "33": {"name": "³³🏛️ - Đền Parthenon", "price": 3500000000000, "description": "Đền Parthenon – Ngôi đền cổ kính trên Acropolis, Athens, Hy Lạp."},
    "34": {"name": "³⁴🏢 - Landmark 81", "price": 34500000000000, "description": "Landmark 81 – Biểu tượng phát triển đô thị đẳng cấp của Việt Nam."},
    "35": {"name": "³⁵🛳️ - Du thuyền Symphony of the Seas", "price": 28000000000000, "description": "Du thuyền Symphony of the Seas – Trải nghiệm xa hoa trên biển."},
    "36": {"name": "³⁶🚢 - Tàu sân bay USS Nimitz", "price": 103500000000000, "description": "Tàu sân bay USS Nimitz – Biểu tượng của sức mạnh quân sự."},
    "37": {"name": "³⁷🏛️ - Cung Điện Buckingham", "price": 50000000000000, "description": "Cung Điện Buckingham – Nơi ở của hoàng gia Anh, sang trọng và lịch sử."},
    "38": {"name": "³⁸🏝️ - Đảo thiên đường", "price": 100000000000000, "description": "Đảo thiên đường – Sở hữu một hòn đảo riêng."},
    "39": {"name": "³⁹🗼 - Tháp Eiffel", "price": 5000000000000, "description": "Tháp Eiffel – Biểu tượng của Paris, Pháp, một trong những công trình nổi tiếng nhất thế giới."},
    "40": {"name": "⁴⁰🏜️ - Sa mạc Sahara", "price": 2000000000000, "description": "Sa mạc Sahara – Sa mạc lớn nhất thế giới, trải dài qua nhiều quốc gia ở Châu Phi."},
    "41": {"name": "⁴¹🛰️ - Vệ tinh liên lạc", "price": 1400000000000, "description": "Vệ tinh liên lạc – Công nghệ truyền thông tiên tiến."},
    "42": {"name": "⁴²🚀 - Tàu Vũ Trụ Starship", "price": 115000000000000, "description": "Tàu Vũ Trụ Starship – Phương tiện khám phá không gian thế hệ mới."},
    "43": {"name": "⁴³🔭 - Trạm Vũ Trụ Quốc tế (ISS)", "price": 3450000000000000, "description": "Trạm Vũ Trụ Quốc tế (ISS) – Điểm hội tụ của công nghệ không gian quốc tế."},
    "44": {"name": "⁴⁴👑 - Vương miện hoàng gia", "price": 100000000000000000, "description": "Vương miện hoàng gia – Biểu tượng của quyền lực và sự giàu có."},
    "45": {"name": "⁴⁵🏯 - Vạn Lý Trường Thành", "price": 8000000000000, "description": "Vạn Lý Trường Thành – Công trình kiến trúc lịch sử vĩ đại của Trung Quốc, kéo dài hàng nghìn km."},
    "46": {"name": "⁴⁶💎 - Viên Ngọc Pandora", "price": 10000000000, "description": "Viên Ngọc Pandora – Viên ngọc quý, biểu tượng của vẻ đẹp và giá trị vũ trụ."},
    "47": {"name": "⁴⁷🌋 - Núi Lửa Etna", "price": 50000000000000, "description": "Núi Lửa Etna – Sức mạnh tự nhiên của ngọn núi lửa nổi tiếng ở Ý."},
    "48": {"name": "⁴⁸🔴 - Hành tinh Sao Hỏa", "price": 1000000000000000, "description": "Hành tinh Sao Hỏa – Hành tinh đỏ, mục tiêu chinh phục của nhân loại."},
    "49": {"name": "⁴⁹🪐 - Hành tinh Jupiter", "price": 10000000000000000, "description": "Hành tinh Jupiter – Vị vua của các hành tinh, biểu tượng của quyền lực thiên văn."},
    "50": {"name": "⁵⁰🔥 - Ngọn lửa vĩnh cửu", "price": 100000000000000, "description": "Ngọn lửa vĩnh cửu – Biểu tượng của sự bất diệt."},
    "51": {"name": "⁵¹⚡ - Sấm Sét Thần Zeus", "price": 200000000000000, "description": "Sấm Sét Thần Zeus – Biểu hiện quyền lực thiên nhiên trong thần thoại Hy Lạp."},
    "52": {"name": "⁵²🌠 - Sao băng Hyakutake", "price": 50000000000000, "description": "Sao băng Hyakutake – Cơn mưa sao băng huyền thoại, lung linh trên bầu trời."},
    "53": {"name": "⁵³☀️ - Hệ Mặt Trời Kepler-90", "price": 500000000000000, "description": "Hệ Mặt Trời Kepler-90 – Hệ sao với nhiều hành tinh, biểu tượng của sự đa dạng vũ trụ."},
    "54": {"name": "⁵⁴⭐ - Ngôi sao Sirius", "price": 100000000000000, "description": "Ngôi sao Sirius – Ngôi sao sáng nhất, điểm sáng trên bầu trời đêm."},
    "55": {"name": "⁵⁵🌀 - Hố đen vũ trụ", "price": 1000000000000000, "description": "Hố đen vũ trụ – Vùng không gian với lực hấp dẫn cực mạnh."},
    "56": {"name": "⁵⁶🌌 - Dải Ngân Hà Milky Way", "price": 10000000000000000000, "description": "Dải Ngân Hà Milky Way – Quang cảnh thiên văn bao la, chứa đựng vạn dặm sao."},
    "57": {"name": "⁵⁷🌟 - Thiên Hà Andromeda", "price": 20000000000000000000, "description": "Thiên Hà Andromeda – Hệ thiên hà xa xôi, huyền bí và đẹp mắt."},
    "58": {"name": "⁵⁸💥 - Siêu Nova SN 2014J", "price": 500000000000000, "description": "Siêu Nova SN 2014J – Vụ nổ sao khổng lồ, tái tạo năng lượng vũ trụ."},
    "59": {"name": "⁵⁹💫 - Vũ Trụ Vô Tận", "price": 100000000000000000000000, "description": "Vũ Trụ Vô Tận – Biểu tượng tối thượng của sự bao la và vô hạn trong vũ trụ."}
}
def show_assets(message, message_object, thread_id, thread_type, author_id, client):
    client.sendReaction(message_object, "✅", thread_id, thread_type, reactionType=75)
    money_data = load_money_data()
    user_assets = load_user_assets()
    assets = user_assets.get(str(author_id), [])
    balance = money_data.get(str(author_id), 0)
    if not assets:
        response_message = "❌ Bạn chưa sở hữu tài sản nào."
    else:
        response_message = "📜 DANH MỤC TÀI SẢN\n"
        response_message += "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        response_message += f"💰 Tiền mặt: {format_money(balance)}\n"
        response_message += "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        response_message += "🎁 Tài sản của bạn:\n"
        for asset in assets:
            item = shop_items.get(asset, {})
            if item:
                response_message += f"   • {item['name']} - {item['description']}\n"
            else:
                response_message += "   • ❌ Không tìm thấy tài sản này.\n"
        response_message += "━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Nếu tin nhắn quá dài, tự động chia thành nhiều tin
    max_length = 2000  # Ví dụ giới hạn 2000 ký tự
    while len(response_message) > max_length:
        part = response_message[:max_length]
        send_message_with_style(client, part, thread_id, thread_type)
        response_message = response_message[max_length:]
        time.sleep(1)  # Chờ 1 giây giữa các tin nhắn để tránh spam
    if response_message:
        send_message_with_style(client, response_message, thread_id, thread_type)

def handle_money_command(message, message_object, thread_id, thread_type, author_id, client):
    # Phản hồi ngay khi nhận lệnh
    client.sendReaction(message_object, "✅", thread_id, thread_type, reactionType=75)
    
    text = message.split()
    money_data = load_money_data()
    user_assets = load_user_assets()
    response_message = ""
    # Chuyển đổi author_id sang string để nhất quán với key trong file
    author_key = str(author_id)
    vouchers = load_vouchers()

    if len(text) < 2:
        show_money_menu(message, message_object, thread_id, thread_type, author_id, client)
        return
        
    if text[1] in ["set", "add", "rs", "del", "setcode"] and not is_admin(author_id):
        response_message = "❌ Lệnh này chỉ dành cho Admin."
        client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type, ttl=20000)
        return
    

    if text[1] == "set" and is_admin(author_id):
        if len(text) < 3 or not text[2].isdigit() or len(message_object.mentions) < 1:
            response_message = "❌ Vui lòng nhập số hợp lệ và tag người nhận\n✔ tx set {số tiền} @username"
        else:
            amount = int(text[2])
            target_id = str(message_object.mentions[0]['uid'])
            target_name = get_user_name(client, target_id)
            money_data[target_id] = money_data.get(target_id, 0) + amount
            save_money_data(money_data)
            response_message = f"✅ Đã cộng 💵 {format_money(amount)} cho 👨‍💼 {target_name}."
        client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type, ttl=20000) 
        return        

    elif text[1] == "add" and is_admin(author_id):
        if len(text) < 3 or not text[2].isdigit():
            response_message = "❌ Vui lòng nhập số hợp lệ."
        else:
            amount = int(text[2])
            money_data[author_key] = money_data.get(author_key, 0) + amount
            save_money_data(money_data)
            response_message = f"✅ Đã tự cộng thêm 💵 {format_money(amount)} cho bản thân."
        client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type, ttl=20000)        
        return
        
    elif text[1] == "rs" and is_admin(author_id):
        if os.path.exists('modules/cache/money.json'):
            os.remove('modules/cache/money.json')
        # Reset dữ liệu cũng nên reset file user_assets nếu cần
        response_message = "✅ Reset lại thành công toàn bộ số dư hệ thống."
        client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type, ttl=20000)    
        return
        
    elif text[1] == "del" and is_admin(author_id):
        if len(text) < 3:
            response_message = "❌ Vui lòng chỉ định số tiền hoặc 'all'."
        else:
            target_id = str(message_object.mentions[0]['uid']) if message_object.mentions else author_key
            target_name = get_user_name(client, target_id)
            if text[2] == "all":
                money_data[target_id] = 0
                response_message = f"✅ Đã trừ thành công toàn bộ tiền của {target_name}."
            elif text[2].isdigit():
                amount = int(text[2])
                money_data[target_id] = max(0, money_data.get(target_id, 0) - amount)
                response_message = f"✅ Đã trừ 💵 {format_money(amount)} của {target_name}."
            else:
                response_message = "❌ Vui lòng nhập số hợp lệ."
            save_money_data(money_data)
        client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type, ttl=20000)
        return
        
    elif text[1] == "daily":
        current_time = time.time()
        cooldown_time = 180  # thời gian chờ (giây)
        if author_key in user_cooldowns:
            time_since_last_use = current_time - user_cooldowns[author_key]
            if time_since_last_use < cooldown_time:
                remaining_time = cooldown_time - time_since_last_use
                client.replyMessage(
                    Message(text=f"Bạn phải đợi {int(remaining_time // 60)} phút {int(remaining_time % 60)} giây nữa mới có thể nhận tiền free."),
                    message_object, thread_id, thread_type, ttl=10000
                )
                return
        amount = random.randint(500000000, 1000000000)
        money_data[author_key] = money_data.get(author_key, 0) + amount
        user_cooldowns[author_key] = current_time
        save_money_data(money_data)
        response_message = f"✅ Rosy đã tặng bạn vốn khởi nghiệp 💵 {format_money(amount)} "
        client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type, ttl=20000)    
        return
        
    elif text[1] == "pay":
        if len(text) < 3 or not text[2].isdigit() or len(message_object.mentions) < 1:
            response_message = "❌ Vui lòng nhập số hợp lệ và tag người nhận\n✔ tx pay {số tiền} @username"
        else:
            amount = int(text[2])
            target_id = str(message_object.mentions[0]['uid'])
            target_name = get_user_name(client, target_id)
            if money_data.get(author_key, 0) >= amount:
                money_data[author_key] = money_data.get(author_key, 0) - amount
                money_data[target_id] = money_data.get(target_id, 0) + amount
                save_money_data(money_data)
                response_message = f"✅ Chuyển thành công 💵 {format_money(amount)} đến 👨‍💼 {target_name}."
            else:
                response_message = "❌ Số dư không đủ để thực hiện giao dịch."
            client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type, ttl=20000)        
            return
            
    elif text[1] == "top":
        top_users = sorted(money_data.items(), key=lambda x: x[1], reverse=True)[:10]
        response_message = "🌟 𝐁𝐀̉𝐍𝐆 𝐗𝐄̂́𝐏 𝐇𝐀̣𝐍𝐆 𝐓𝐀̀𝐈 𝐗𝐈̉𝐔\n"
        for idx, (uid, amount) in enumerate(top_users, 1):
            name = get_user_name(client, uid)
            rank_title = get_rank_title(amount)
            assets = user_assets.get(uid, [])
            assets_list = ", ".join([shop_items[item]["name"] for item in assets]) if assets else "Không có tài sản"
            response_message += (
                f"━━━━━━━━━━━━━\n"
                f"🏆  𝗧𝗼𝗽 {idx}: {name}\n"
                f"👨‍💼  𝐃𝐚𝐧𝐡 𝐡𝐢𝐞̣̂𝐮 : {rank_title}\n"
                f"💵  𝐓𝐢𝐞̂̀𝐧: {format_money(amount)}\n"
                f"🎁  𝐓𝐚̀𝐢 𝐬𝐚̉𝐧: {assets_list}\n"
                f"━━━━━━━━━━━━━\n"
            )

        # Nếu tin nhắn quá dài thì chia thành các tin nhắn nhỏ
        while len(response_message) > 1500:
            part = response_message[:1500]
            send_message_with_style(client, part, thread_id, thread_type)
            response_message = response_message[1500:]
            time.sleep(1) 
        if response_message:
            send_message_with_style(client, response_message, thread_id, thread_type)
        return    

    elif text[1] == "check":
        if message_object.mentions:
            target_id = str(message_object.mentions[0]['uid'])
            target_name = get_user_name(client, target_id)
            balance = money_data.get(target_id, 0)
            assets = user_assets.get(target_id, [])
            assets_list = ", ".join([shop_items[item]["name"] for item in assets]) if assets else "Không có tài sản"
            assets_count = len(assets)
            response_message = (
                f"✅ {target_name} hiện có:\n"
                f"💵 {format_money(balance)}\n"
                f"🎁 Tài sản: ({assets_count}/20)\n"
                f"{assets_list}."
            )
        else:
            balance = money_data.get(author_key, 0)
            assets = user_assets.get(author_key, [])
            assets_list = ", ".join([shop_items[item]["name"] for item in assets]) if assets else "Không có tài sản"
            assets_count = len(assets)
            author_name = get_user_name(client, author_id)
            response_message = (
                f"✅ {author_name}\n"
                f"✅ Số tiền của bạn hiện có:\n"
                f"💵 {format_money(balance)}\n"
                f"🎁 Tài sản: ({assets_count}/20)\n"
                f"{assets_list}"
            )
        send_message_with_style(client, response_message, thread_id, thread_type)
        return

    elif text[1] == "shop":
        response_message = "🛒 CỬA HÀNG TÀI XỈU 🛒\n💳 Sử dụng lệnh tx buy <mã số> để mua sản phẩm\n💳 Sử dụng lệnh tx sell <mã số> để bán sản phẩm\n💳 Sử dụng lệnh tx taisan để xem danh sách tài sản\n"
        response_message += "━━━━━━━━━━━━━━━━━━━━━━\n"
        for key, item in shop_items.items():
            response_message += f" {item['name']}\n 💲 {format_money(item['price'])}\n"
            response_message += f" 💡 {item['description']}\n"
            response_message += "━━━━━━━━━━━━━━━━━━━━━━\n"
        # Nếu tin nhắn quá dài thì chia thành các tin nhắn nhỏ
        while len(response_message) > 2000:
            part = response_message[:2000]
            send_message_with_style(client, part, thread_id, thread_type, font_size="4")
            response_message = response_message[2000:]
            time.sleep(1) 
        # Gửi phần còn lại (nếu có) với style
        if response_message:
            send_message_with_style(client, response_message, thread_id, thread_type, font_size="4")    
        return    

    elif text[1] == "buy":
        if len(text) < 3 or text[2] not in shop_items:
            response_message = "❌ Sản phẩm không hợp lệ hoặc không có trong cửa hàng."
        else:
            item_key = text[2]
            try:
                quantity = int(text[3]) if len(text) >= 4 else 1
                if quantity < 1:
                    raise ValueError
            except ValueError:
                response_message = "❌ Số lượng mua không hợp lệ."
                client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type, ttl=20000)
                return
            
            item = shop_items[item_key]
            total_price = item['price'] * quantity

            # Kiểm tra số lượng vật phẩm hiện có của người dùng
            assets = user_assets.get(author_key, [])
            current_quantity = len(assets)
            if current_quantity + quantity > 20:
                max_can_buy = 20 - current_quantity
                response_message = f"❌ Túi đồ của bạn đã đầy. Bạn chỉ có thể mua thêm tối đa {max_can_buy} sản phẩm nữa (giới hạn 20 vật phẩm)."
                client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type, ttl=20000)
                return

            if money_data.get(author_key, 0) >= total_price:
                money_data[author_key] -= total_price
                save_money_data(money_data)
                # Cập nhật tài sản: thêm item_key vào danh sách theo số lượng
                for _ in range(quantity):
                    assets.append(item_key)
                user_assets[author_key] = assets
                save_user_assets(user_assets)
                response_message = f"✅ Bạn đã mua thành công {item['name']} x {quantity} với tổng giá {format_money(total_price)}."
            else:
                response_message = "❌ Số dư không đủ để mua sản phẩm này."
            client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type, ttl=20000)
        return

    elif text[1] == "sell":
        if len(text) < 3 or text[2] not in user_assets.get(author_key, []):
            response_message = "❌ Bạn không sở hữu tài sản này."
        else:
            item_key = text[2]
            try:
                quantity = int(text[3]) if len(text) >= 4 else 1
                if quantity < 1:
                    raise ValueError
            except ValueError:
                response_message = "❌ Số lượng bán không hợp lệ."
                client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type, ttl=20000)
                return
            
            user_inventory = user_assets.get(author_key, [])
            if user_inventory.count(item_key) < quantity:
                response_message = "❌ Số lượng bán vượt quá số tài sản bạn đang sở hữu."
            else:
                item = shop_items[item_key]
                total_sale_price = 0
                # Tính tổng số tiền bán được cho số lượng sản phẩm
                for i in range(quantity):
                    sale_price = item['price'] * random.uniform(0.5, 3.0)
                    sale_price = round(sale_price)
                    total_sale_price += sale_price

                money_data[author_key] = money_data.get(author_key, 0) + total_sale_price
                save_money_data(money_data)
                # Loại bỏ sản phẩm đã bán ra khỏi danh sách tài sản
                for i in range(quantity):
                    user_inventory.remove(item_key)
                user_assets[author_key] = user_inventory
                save_user_assets(user_assets)

                # Tính lãi hoặc lỗ tổng cộng
                profit_loss_total = total_sale_price - (item['price'] * quantity)
                if profit_loss_total > 0:
                    profit_loss_message = f"🎉 Bạn đã có lãi 💸 {format_money(profit_loss_total)}."
                elif profit_loss_total < 0:
                    profit_loss_message = f"😞 Bạn đã bị lỗ 💸 {format_money(abs(profit_loss_total))}."
                else:
                    profit_loss_message = "🟢 Bạn đã bán đúng giá gốc."

                response_message = f"✅ Bạn đã bán {item['name']} x {quantity} và nhận được {format_money(total_sale_price)}.\n{profit_loss_message}"
            client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type, ttl=20000)
        return

    # Không cần `else` cuối cùng ở đây, vì bạn đã xử lý lỗi trước đó
    elif text[1] == "tang":
        # Kiểm tra xem đã cung cấp mã tài sản chưa
        if len(text) < 3:
            response_message = "❌ Vui lòng cung cấp mã số tài sản cần tặng.\n✔ Ví dụ: tx tang <mã số> @nguoiNhan"
        # Kiểm tra xem người gửi có sở hữu tài sản đó không
        elif text[2] not in user_assets.get(author_key, []):
            response_message = "❌ Bạn không sở hữu tài sản có mã số này."
        # Kiểm tra xem đã tag người nhận chưa
        elif not message_object.mentions:
            response_message = "❌ Vui lòng tag người nhận tài sản."
        else:
            target_id = str(message_object.mentions[0]['uid'])
            target_name = get_user_name(client, target_id)
            # Chuyển tài sản từ người gửi sang người nhận
            user_assets[author_key].remove(text[2])
            target_assets = user_assets.get(target_id, [])
            target_assets.append(text[2])
            user_assets[target_id] = target_assets
            save_user_assets(user_assets)
            asset_name = shop_items[text[2]]["name"]
            response_message = f"✅ Bạn đã tặng {asset_name} cho {target_name}."
        client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type, ttl=20000)
        return
       
    # Kiểm tra nếu lệnh là "taisan"
    elif  text[1] == "taisan":
        # Kiểm tra xem có tag người khác không
        if message_object.mentions:
            target_id = str(message_object.mentions[0]['uid'])  # Lấy ID của người được tag
            show_assets(message, message_object, thread_id, thread_type, target_id, client)  # Hiển thị tài sản của người đó
        else:
            show_assets(message, message_object, thread_id, thread_type, author_id, client)  # Hiển thị tài sản của chính người chơi
        return

    elif text[1] == "tromtien":
        # Kiểm tra cooldown cho lệnh trộm tiền
        current_time = time.time()
        cooldown_time = 60  # 60 giây cooldown
        if author_key in tromtien_cooldowns:
            time_since_last_use = current_time - tromtien_cooldowns[author_key]
            if time_since_last_use < cooldown_time:
                remaining_time = cooldown_time - time_since_last_use
                response_message = f"❌ Bạn hãy đợi {int(remaining_time // 60)} phút {int(remaining_time % 60)} giây nữa để trộm tiền tiếp."
                client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type, ttl=60000)
                return
        # Cập nhật thời gian sử dụng lệnh tromtien
        tromtien_cooldowns[author_key] = current_time

        # Xử lý logic trộm tiền
        if not message_object.mentions:
            response_message = "❌ Vui lòng tag người bạn muốn trộm tiền."
        else:
            target_id = str(message_object.mentions[0]['uid'])
            target_name = get_user_name(client, target_id)
            thief_balance = money_data.get(author_key, 0)
            target_balance = money_data.get(target_id, 0)
            if target_balance < 1000000:
                response_message = f"❌ {target_name} không có đủ tiền để trộm, tha nó đi"
            else:
                # Tính tỉ lệ giữa số dư của người trộm và nạn nhân
                balance_ratio = thief_balance / target_balance if target_balance > 0 else 1
                if balance_ratio < 0.5:
                    success_chance = 0.5
                elif balance_ratio <= 1:
                    success_chance = 0.3
                else:
                    success_chance = 0.2

                if random.random() < success_chance:
                    # Trộm thành công: trộm khoảng 20% số dư của nạn nhân ±5%
                    percent = 0.20 + random.uniform(-0.05, 0.05)
                    stolen_amount = round(target_balance * percent)
                    money_data[target_id] = max(0, target_balance - stolen_amount)
                    money_data[author_key] += stolen_amount
                    save_money_data(money_data)
                    response_message = f"🤣 Bạn đã trộm thành công {format_money(stolen_amount)} (khoảng {percent*100:.0f}%) từ {target_name}."
                else:
                    # Trộm thất bại: mất từ 20% đến 50% số dư của người trộm
                    penalty_percent = random.uniform(0.20, 0.50)
                    penalty = round(thief_balance * penalty_percent)
                    money_data[author_key] = max(0, thief_balance - penalty)
                    money_data[target_id] = target_balance + penalty
                    save_money_data(money_data)
                    response_message = f"😞 Bạn đã bị 👮 Police tóm khi ăn trộm tiền của {target_name} và bị phạt {format_money(penalty)} ( {penalty_percent*100:.0f}%)\nSố tiền này đã được đền bù cho bị hại"
        client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type, ttl=60000)
        return

    # -----------------------------
    # LỆNH ADMIN: Tạo code
    # -----------------------------
    elif  text[1] == "setcode" and is_admin(author_id):
        if len(text) < 4:
            response_message = "❌ Cú pháp: tx setcode <amount> <code>"
        else:
            try:
                amount = int(text[2])
                code = text[3].lower()
                vouchers = load_vouchers()
                if code in vouchers:
                    response_message = f"❌ code '{code}' đã tồn tại!"
                else:
                    vouchers[code] = {
                        "amount": amount,
                        "used_by": []   # Lưu danh sách người dùng đã sử dụng code
                    }
                    save_vouchers(vouchers)
                    response_message = f"✅ Đã tạo code '{code}' với số tiền {format_money(amount)}\nNgười chơi hãy nhập tx code <mã code> để nhận tiền"
            except ValueError:
                response_message = "❌ Số tiền không hợp lệ."
        client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type, ttl=600000)
        return

    # -----------------------------
    # LỆNH NGƯỜI CHƠI: Dùng code
    # tx code <code>
    # -----------------------------
    elif text[1] == "code":
        if len(text) < 3:
            response_message = "❌ Cú pháp: tx code <code>"
        else:
            code = text[2].lower()
            vouchers = load_vouchers()
            if code not in vouchers:
                response_message = "❌ Mã code không tồn tại."
            else:
                vdata = vouchers[code]
                used_by_list = vdata.get("used_by", [])
                if str(author_id) in used_by_list:
                    response_message = "❌ Bạn đã dùng code này rồi!"
                else:
                    amount = vdata["amount"]
                    money_data[str(author_id)] = money_data.get(str(author_id), 0) + amount
                    save_money_data(money_data)
                    used_by_list.append(str(author_id))
                    vouchers[code]["used_by"] = used_by_list
                    save_vouchers(vouchers)
                    response_message = f"✅ Bạn đã dùng code '{code}' và nhận {format_money(amount)}"
        client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type, ttl=20000)
        return
    
    elif text[1] == "solo":
        # Lệnh chấp nhận thách đấu: "tx solo chapnhan"
        if len(text) > 2 and text[2] == "chapnhan":
            if str(author_id) not in duel_requests:
                response_message = "❌ Không có lời thách đấu nào dành cho bạn."
            else:
                challenge = duel_requests.pop(str(author_id))
                # Kiểm tra thời gian hết hạn (ví dụ: 120 giây)
                current_time = time.time()
                if current_time - challenge["timestamp"] > 120:
                    response_message = "❌ Lời thách đấu đã hết hạn."
                else:
                    challenger_id = challenge["challenger"]
                    stake = challenge["stake"]
                    challenger_balance = money_data.get(challenger_id, 0)
                    opponent_balance = money_data.get(str(author_id), 0)
                    # Kiểm tra số dư của cả 2 bên
                    if challenger_balance < stake:
                        response_message = f"❌ {get_user_name(client, challenger_id)} không đủ tiền để đặt cược."
                    elif opponent_balance < stake:
                        response_message = "❌ Số dư của bạn không đủ để đặt cược."
                    else:
                        # Gửi GIF trước khi công bố kết quả (giữ nguyên phần này)
                        gif_path = "modules/cache/gif/gifrandom.gif"
                        client.sendLocalGif(
                            gifPath=gif_path,
                            thumbnailUrl=None,
                            thread_id=thread_id,
                            thread_type=thread_type,
                            width=1000,
                            height=600,
                            ttl=5000
                        )
                        time.sleep(5)

                        # Chọn ngẫu nhiên vật phẩm cho người thách đấu (challenger)
                        challenger_item_key = random.choice(list(shop_items.keys()))
                        challenger_item = shop_items[challenger_item_key]
                        # Chọn ngẫu nhiên vật phẩm cho người chấp nhận (opponent)
                        opponent_item_key = random.choice(list(shop_items.keys()))
                        opponent_item = shop_items[opponent_item_key]
                        
                        # So sánh giá trị vật phẩm để xác định người thắng
                        if challenger_item['price'] > opponent_item['price']:
                            winner_id = challenger_id
                            loser_id = str(author_id)
                        elif challenger_item['price'] < opponent_item['price']:
                            winner_id = str(author_id)
                            loser_id = challenger_id
                        else:
                            # Trường hợp giá trị bằng nhau: chọn ngẫu nhiên người thắng
                            if random.random() < 0.5:
                                winner_id = challenger_id
                                loser_id = str(author_id)
                            else:
                                winner_id = str(author_id)
                                loser_id = challenger_id
                        
                        # Cập nhật số dư
                        money_data[winner_id] = money_data.get(winner_id, 0) + stake
                        money_data[loser_id] = money_data.get(loser_id, 0) - stake
                        save_money_data(money_data)
                        
                        # Tạo thông báo kết quả
                        response_message = (
                            f"🏆 Kết quả thách đấu:\n"
                            f"{get_user_name(client, challenger_id)} bốc được {challenger_item['name']} (giá {format_money(challenger_item['price'])})\n"
                            f"{get_user_name(client, author_id)} bốc được {opponent_item['name']} (giá {format_money(opponent_item['price'])})\n"
                            f"🏅 Người chiến thắng là {get_user_name(client, winner_id)} và nhận được {format_money(stake)} từ {get_user_name(client, loser_id)}."
                        )
            client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type, ttl=60000)
            return

        # Trường hợp gửi lời thách đấu: "tx solo <số tiền cược> @đối_thủ" (giữ nguyên)
        else:
            if len(text) < 3 or not text[2].isdigit() or len(message_object.mentions) < 1:
                response_message = "❌ Vui lòng nhập số tiền cược hợp lệ và tag đối thủ. Ví dụ: tx solo 1000000 @username"
            else:
                stake = int(text[2])
                opponent_id = str(message_object.mentions[0]['uid'])
                # Kiểm tra nếu đối thủ đã có lời thách đấu chưa được xử lý
                if opponent_id in duel_requests:
                    response_message = f"❌ {get_user_name(client, opponent_id)} đã có một lời thách đấu chưa được trả lời."
                else:
                    duel_requests[opponent_id] = {
                        "challenger": author_key,
                        "stake": stake,
                        "timestamp": time.time()  # Lưu thời gian tạo lời thách đấu
                    }
                    response_message = (
                        f"⏳ Lời thách đấu đã gửi tới {get_user_name(client, opponent_id)}. "
                        f"Đối thủ hãy chấp nhận bằng lệnh 'tx solo chapnhan' trong vòng 2 phút."
                    )
            client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type, ttl=120000)
            return

def get_mitaizl():
    return {
        'tx': handle_money_command
    }
