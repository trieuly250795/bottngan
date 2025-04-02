import random
from zlapi.models import Message

des = {
    'tác giả': "Rosy",
    'mô tả': "Bot hỗ trợ gửi menu các lệnh và một video ngẫu nhiên cho người dùng.",
    'tính năng': [
        "📋 Gửi menu các lệnh có thể sử dụng cho người dùng.",
        "🎥 Gửi video ngẫu nhiên từ danh sách video đã thiết lập.",
        "🔔 Thông báo kết quả gửi video với thời gian sống (TTL) khác nhau.",
        "📦 Gửi tin nhắn kèm định dạng màu sắc và font chữ đặc biệt.",
        "🔒 Chỉ quản trị viên mới có quyền sử dụng lệnh này."
    ],
    'hướng dẫn sử dụng': [
        "📩 Gửi lệnh để bot gửi menu các lệnh và một video ngẫu nhiên cho người dùng.",
        "📌 Bot sẽ gửi video và menu các lệnh có thể sử dụng.",
        "✅ Nhận thông báo trạng thái gửi video và menu ngay lập tức."
    ]
}

# Danh sách các link video
VIDEO_LIST = [
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
    "https://i.imgur.com/dw3lqxi.mp4"  # Thêm các link khác nếu cần
]

def handle_menu_command(message, message_object, thread_id, thread_type, author_id, client):
    # Chọn ngẫu nhiên một video từ danh sách
    video_url = random.choice(VIDEO_LIST)

    # Nội dung menu
    menu_message = """
══════════════════════
            🌸 MENU ADMIN 🌸
══════════════════════
➤ 📷 𝗺𝗲𝗻𝘂𝟭 : Xem ảnh/video
➤ 🔧 𝗺𝗲𝗻𝘂𝟮 : Công cụ hỗ trợ
➤ 🧩 𝗺𝗲𝗻𝘂𝟯 : Chơi game
➤ ⚙️ 𝗺𝗲𝗻𝘂𝟰 : Lệnh Admin
➤ ⚙️ 𝗺𝗲𝗻𝘂𝟓 : Lệnh Admin
➤ ⚙️ 𝗺𝗲𝗻𝘂𝗴𝗿: Cài đặt nhóm
➤ 🔒 𝗺𝗲𝗻𝘂𝗮𝗱: Quản trị nhóm
➤ 🛰️ 𝗯𝗼𝘁𝘁 : Điều khiển Bot
══════════════════════
          ✨ Gõ lệnh để bắt đầu!
══════════════════════
"""

    # Gửi video từ URL đã chọn
    client.sendRemoteVideo(
        video_url,
        None,  # Không có thumbnail
        duration=10,  # Đặt thời lượng video (có thể tự động lấy nếu API hỗ trợ)
        message=Message(text=menu_message),
        thread_id=thread_id,
        thread_type=thread_type,
        width=1920,
        height=1080,
        ttl=60000,
    )

    # Thêm hành động phản hồi (nếu cần)
    action = "✅"
    client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)

def get_mitaizl():
    return {
        'menu': handle_menu_command
    }
