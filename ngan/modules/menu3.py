import os
import importlib
import time
from zlapi.models import Message
from datetime import datetime

des = {
    'tác giả': "Rosy",
    'mô tả': "Hiển thị menu trò chơi và gửi hình ảnh đính kèm.",
    'tính năng': [
        "📜 Hiển thị menu trò chơi",
        "🎲 Liệt kê các trò chơi như Bầu Cua, Tài Xỉu, Đuổi hình bắt chữ",
        "🖼️ Gửi kèm hình ảnh minh họa menu trò chơi",
        "⚡ Phản hồi ngay khi người dùng nhập lệnh",
        "✅ Tích hợp phản ứng khi sử dụng lệnh"
    ],
    'hướng dẫn sử dụng': [
        "📩 Dùng lệnh 'menu3' để hiển thị menu trò chơi và gửi hình ảnh đính kèm.",
        "📌 Ví dụ: nhập menu3 để hiển thị danh sách trò chơi.",
        "✅ Nhận thông báo trạng thái và kết quả ngay lập tức."
    ]
}

# Hàm xử lý lệnh menu
def handle_menu_command(message, message_object, thread_id, thread_type, author_id, client):
    menu_message = f"""
    🌸 𝐓𝐫𝐨̛̣ 𝐋𝐲́ 𝐌𝐲𝐚 🌸
    ---------------------------------
    📄 𝐌𝐞𝐧𝐮 𝐆𝐚𝐦𝐞
    ---------------------------------
    ☀ 𝐓𝐑𝐎̀ 𝐂𝐇𝐎̛𝐈
       ┣━ 🎲 𝗯𝗰𝘂𝗮 — Chơi Bầu Cua
       ┣━ 🎲 𝘁𝘅𝗶𝘂 — Chơi Tài Xỉu
       ┣━ 🖼️ 𝗱𝗵𝗯𝗰 — Đuổi hình bắt chữ 1 (1 ảnh)
       ┣━ 🖼️ 𝗱𝗵𝗯𝗰𝟮 — Đuổi hình bắt chữ 2 (2 ảnh)
       ┣━ 🎯 𝗿𝗮𝗻𝗱𝗼𝗺 — Trò chơi random
       ┗━ 🔢 𝗱𝗼𝗮𝗻𝘀𝗼𝗻𝗴𝗮𝘂𝗻𝗵𝗶𝗲𝗻 — Trò chơi đoán số
    ☀ 𝐌𝐄𝐍𝐔 𝐆𝐀𝐌𝐄
       ┣━ 📜 𝗯𝗰 — Menu Bầu Cua
       ┗━ 📜 𝘁𝘅 — Menu Tài Xỉu
    \n
"""
    # Thêm hành động phản hồi
    action = "✅ "
    client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)
    client.sendLocalImage(
        "wcmenu3.jpg", 
        thread_id=thread_id, 
        thread_type=thread_type, 
        message=Message(text=menu_message), 
        ttl=120000, 
        width=1920,  # ví dụ: chiều rộng 1920 pixel
        height=1080  # ví dụ: chiều cao 1080 pixel
    )

# Hàm trả về danh sách lệnh và hàm xử lý tương ứng
def get_mitaizl():
    return {
        'menu3': handle_menu_command
    }
