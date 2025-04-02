import os
import importlib
import time
from zlapi.models import Message
from datetime import datetime

# Thông tin mô tả module
des = {
    'tác giả': "Rosy",
    'mô tả': "Hiển thị menu admin và gửi hình ảnh đính kèm.",
    'tính năng': [
        "📜 Hiển thị menu admin",
        "🚀 Liệt kê các lệnh tấn công, quản lý bot, quản lý tin nhắn và tương tác nhóm",
        "🖼️ Gửi kèm hình ảnh minh họa menu admin",
        "⚡ Phản hồi ngay khi người dùng nhập lệnh",
        "✅ Tích hợp phản ứng khi sử dụng lệnh"
    ],
    'hướng dẫn sử dụng': [
        "📩 Dùng lệnh 'menu4' để hiển thị menu admin và gửi hình ảnh đính kèm.",
        "📌 Ví dụ: nhập menu4 để hiển thị danh sách lệnh admin.",
        "✅ Nhận thông báo trạng thái và kết quả ngay lập tức."
    ]
}

# Hàm xử lý lệnh menu
def handle_menu5_command(message, message_object, thread_id, thread_type, author_id, client):
    menu_message = f"""
--------------------------------
🌟 𝐌𝐞𝐧𝐮 𝟓 🌟
--------------------------------
👥 𝗮𝗱𝗱𝗴𝗿𝗼𝘂𝗽: Thêm nhóm (ko gửi link)  
❌ 𝗱𝗲𝗹𝗴𝗿𝗼𝘂𝗽: Xóa nhóm (ko gửi link)  
📋 𝗹𝗶𝘀𝘁𝗴𝗿𝗼𝘂𝗽: DS nhóm (ko gửi link)
--------------------------------
🙅‍♂️ 𝗮𝗱𝗱𝗯𝗮𝗻: Cấm người dùng  
🔓 𝗱𝗲𝗹𝗯𝗮𝗻: Gỡ cấm người dùng  
📜 𝗹𝗶𝘀𝘁𝗯𝗮𝗻: DS người dùng cấm
--------------------------------
🚫 𝗮𝗱𝗱𝗯𝗴𝗿𝗼𝘂𝗽: Thêm nhóm cấm  
✔️ 𝗱𝗲𝗹𝗯𝗴𝗿𝗼𝘂𝗽: Xóa nhóm cấm  
📑 𝗹𝗶𝘀𝘁𝗯𝗴𝗿𝗼𝘂𝗽: DS nhóm cấm
--------------------------------
"""

    # Thêm hành động phản hồi
    action = "✅ "
    client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)
    client.sendLocalImage(
        "wcmenu4.jpg", 
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
        'menu5': handle_menu5_command
    }
