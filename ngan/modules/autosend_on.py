import time
import random
import requests
import json
from zlapi.models import Message, ThreadType
from datetime import datetime, timedelta
import pytz
import threading

des = {
    'tác giả': "Rosy",
    'mô tả': "Tự động gửi tin nhắn vào các khung giờ cố định",
    'tính năng': [
        "🕒 Gửi tin nhắn vào các khung giờ cố định hàng ngày.",
        "🎬 Gửi video ngẫu nhiên từ danh sách cố định.",
        "🔍 Lọc và gửi tin nhắn đến các nhóm không nằm trong danh sách loại trừ.",
        "🔄 Khởi chạy tính năng tự động trong một luồng riêng.",
        "🔔 Thông báo lỗi cụ thể nếu có vấn đề xảy ra khi xử lý yêu cầu."
    ],
    'hướng dẫn sử dụng': [
        "📩 Gửi lệnh tudonggui để bật tính năng tự động gửi tin nhắn theo các khung giờ cố định.",
        "📌 Ví dụ: tudonggui để bật tính năng tự động gửi tin nhắn.",
        "✅ Nhận thông báo trạng thái và kết quả ngay lập tức."
    ]
}

# Các khung giờ gửi tin nhắn cố định
TIME_SLOTS = {"07:00", "10:18", "11:00", "12:46", "13:40", "15:00", "17:00", "19:10", "21:00", "23:00"}

# Nội dung tin nhắn cố định
FIXED_MESSAGE = """🌟 𝐑𝐎𝐒𝐘 𝐀𝐑𝐄𝐍𝐀 𝐒𝐇𝐎𝐏 🌟
🔥 𝐇𝐚𝐜𝐤 𝐦𝐚𝐩 𝐮𝐲 𝐭𝐢́𝐧 - 𝐂𝐚̣̂𝐩 𝐧𝐡𝐚̣̂𝐭 𝐥𝐢𝐞̂𝐧 𝐭𝐮̣𝐜 🔥

📢 THÔNG BÁO UPDATE ANDROID - IOS
🔗 https://zalo.me/g/ohcfct225
🔶LQ ACE 3 MIỀN
🔗 https://zalo.me/g/rrywmq953

🔴 LEO RANK VÀ ĐẤU TRƯỜNG LIÊN QUÂN
🔶 Box 1: Bá chủ Liên quân
🔗 https://zalo.me/g/cayqae880
🔶 Box 4: Kẻ thống trị Liên quân
🔗 https://zalo.me/g/ochyyh448
🔶 Box 6: Hội Kẻ Hủy Diệt Rank
🔗 https://zalo.me/g/qlhssk809
🔶 Box 7: 100 ⭐ K phải giấc mơ
🔗 https://zalo.me/g/xvtszw104
🔶 Box 13: Leo rank bằng 4 Chân
   https://zalo.me/g/spaqlb267
🔶 Box 19: Chinh phục rank đồng
🔗 https://zalo.me/g/lulmlw377
🔶 Box 21: Người gác cổng Bình Nguyên
🔗 https://zalo.me/g/lalvob031
🔶 Box 22: Bộ lạc Liên Quân
🔗 https://zalo.me/g/crgyqw748

🔴 HẠ RANK CẤP TỐC
🔶 Box 8: Sẵn sàng 1 VS 9
🔗 https://zalo.me/g/sjrbqa638
🔶 Box 10: Hạ rank không phanh
🔗 https://zalo.me/g/vtgpfr533
🔶 Box 11: Hạn rank Xuống Đáy Xã Hội
🔗 https://zalo.me/g/dmgtoc729
🔶 Box 12: Cuộc chiến Hạ Rank
🔗 https://zalo.me/g/tlxiin969
🔶 Box 14: Hạ Rank Cũng vui
🔗 https://zalo.me/g/byuqks230
🔶 Box 15: Hạ Rank Trải Nghiệm
🔗 https://zalo.me/g/khjrna643
🔶 Box 17: Hạ Rank Chờ Cơ hội
🔗 https://zalo.me/g/smibnr474
🔶 Box 20: Binh Đoàn Tụt Hạng
🔗 https://zalo.me/g/ysdgtu142
🔶 Box 23: Thắng làm vua - Thua làm lại
🔗 https://zalo.me/g/lnuarr372

🔴 ĐĂNG KÍ ĐI BOT VÀ HỖ TRỢ ĐẤU ĐỘI
⚡ Box 2: Đăng ký đi bot
🔗 https://zalo.me/g/bjnwqv874
⚡ Box 3: Đăng ký bot 5 game
🔗 https://zalo.me/g/jlgahh907
⚡ Box 5: TLT - Nor 5v5
🔗 https://zalo.me/g/lzygxi684
⚡ Box 18: TLT 3v3
🔗 https://zalo.me/g/zaiqug348

🔴 CỘNG ĐỒNG NGHIỆN GAME
🎮 Box 16: Hội những người mê LQ
🔗 https://zalo.me/g/phgqga791"""

# Danh sách URL video cố định
FIXED_VIDEO_URLS = [
    "https://i.imgur.com/O7XR8Rz.mp4",  
    "https://i.imgur.com/eE6rtGX.mp4",  
    "https://i.imgur.com/EeVB353.mp4",  
    "https://i.imgur.com/Cs92gTl.mp4",  
    "https://i.imgur.com/vxkRRBo.mp4",  
    "https://i.imgur.com/kXJL9z1.mp4",  
    "https://i.imgur.com/0LCJ39R.mp4",  
    "https://i.imgur.com/6cwiZBh.mp4",  
    "https://i.imgur.com/3w5tn0a.mp4",  
    "https://i.imgur.com/Hxu8kbV.mp4",  
    "https://i.imgur.com/pUUnb6O.mp4",  
    "https://i.imgur.com/nATPd6k.mp4",  
    "https://i.imgur.com/dw3lqxi.mp4"
]

# Múi giờ Việt Nam
VN_TZ = pytz.timezone('Asia/Ho_Chi_Minh')

def get_excluded_group_ids():
    """
    Đọc tệp danhsachnhom.json và trả về tập hợp các group_id.
    Giả sử tệp chứa danh sách các đối tượng với các khóa "group_id" và "group_name".
    """
    try:
        with open("danhsachnhom.json", "r", encoding="utf-8") as f:
            groups = json.load(f)
            return {grp.get("group_id") for grp in groups}
    except Exception as e:
        print(f"Lỗi khi đọc file danhsachnhom.json: {e}")
        return set()

def get_allowed_groups(client, excluded_group_ids):
    """Lọc danh sách nhóm không nằm trong danh sách loại trừ."""
    all_groups = client.fetchAllGroups()
    return {gid for gid in all_groups.gridVerMap.keys() if gid not in excluded_group_ids}

def send_message_to_group(client, thread_id, current_time_str):
    """Gửi video ngẫu nhiên và tin nhắn cố định đến một nhóm."""
    video_url = random.choice(FIXED_VIDEO_URLS)
    message_text = f"🕒 BÂY GIỜ LÀ {current_time_str} \n{FIXED_MESSAGE}"
    message = Message(text=message_text)
    try:
        client.sendRemoteVideo(
            video_url,
            None,
            duration=10,
            message=message,
            thread_id=thread_id,
            thread_type=ThreadType.GROUP,
            width=1920,
            height=1080,
            ttl=600000
        )
    except Exception as e:
        print(f"Error sending message to {thread_id}: {e}")

def auto_send(client, allowed_thread_ids):
    """Chạy vòng lặp tự động gửi tin nhắn theo khung giờ định sẵn."""
    last_sent_time = None
    while True:
        now = datetime.now(VN_TZ)
        current_time_str = now.strftime("%H:%M")
        if current_time_str in TIME_SLOTS and (last_sent_time is None or now - last_sent_time >= timedelta(minutes=1)):
            try:
                for thread_id in allowed_thread_ids:
                    send_message_to_group(client, thread_id, current_time_str)
                    time.sleep(2)  # Delay giữa các nhóm
                last_sent_time = now
            except Exception as e:
                print(f"Error during auto send: {e}")
        time.sleep(30)

def start_auto(client):
    """Khởi chạy chức năng tự động gửi tin nhắn."""
    try:
        # Lấy danh sách group id từ file để loại trừ
        excluded_group_ids = get_excluded_group_ids()
        allowed_thread_ids = get_allowed_groups(client, excluded_group_ids)
        auto_send(client, allowed_thread_ids)
    except Exception as e:
        print(f"Error initializing auto-send: {e}")

def handle_autosend_start(message, message_object, thread_id, thread_type, author_id, client):
    """Xử lý lệnh bật tính năng tự động gửi tin nhắn."""
    threading.Thread(target=start_auto, args=(client,), daemon=True).start()
    response_message = Message(text="Đã bật tính năng tự động rải link theo thời gian đã định ✅🚀")
    client.replyMessage(response_message, message_object, thread_id, thread_type)

def get_mitaizl():
    return {
        'autosend_on': handle_autosend_start
    }
