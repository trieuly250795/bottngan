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
def handle_menu_command(message, message_object, thread_id, thread_type, author_id, client):
    menu_message = (
    "📄 🌸 𝐌𝐞𝐧𝐮 𝐀𝐝𝐦𝐢𝐧 🌸\n"
    "---------------------------------\n"
    "☀ 𝐓𝐀̂́𝐍 𝐂𝐎̂𝐍𝐆\n"
    "---------------------------------\n"    
    "   ┣━ 🚀 𝗮𝘁𝘁𝗮𝗰𝗸 - Tấn công Zalo\n"
    "   ┣━ 🚀 𝗮𝘁𝗸 - Tấn công tag\n"
    "   ┣━ 🚀 𝗮𝘁𝗸𝗻𝗮𝗺𝗲𝗴𝗿 - Tấn công tên nhóm\n"
    "   ┣━ 🚀 𝗽𝗼𝗹𝗹𝘄𝗮𝗿 - Sập box\n"
    "   ┣━ 📨 𝘀𝗽𝗮𝗺𝘀𝗺𝘀 - Tấn công SMS\n"
    "   ┣━ 💥 𝗮𝘁𝗸𝘀𝘁𝗸 - Spam sticker\n"
    "   ┗━ 💥 𝗮𝘁𝗸𝗯𝘂𝗴 - Gửi stk lag\n"
    "---------------------------------\n"    
    "☀ 𝐐𝐔𝐀̉𝐍 𝐋𝐈́ 𝐁𝐎𝐓\n"
    "---------------------------------\n"    
    "   ┣━ 🔄 𝗿𝗺 - Đổi tên bot\n"
    "   ┣━ ⚙️ 𝗰𝗺𝗱 - Load/unload lệnh\n"
    "   ┣━ ⚙️ 𝗽𝗿𝗲𝗳𝗶𝘅 - Xem tiền tố\n"
    "   ┣━ ⚙️ 𝘀𝗲𝘁𝗽𝗿𝗲𝗳𝗶𝘅 - Đổi tiền tố\n"
    "   ┣━ 📜 𝘀𝗵𝗮𝗿𝗲𝗰𝗼𝗱𝗲 - Chia sẻ code\n"
    "   ┣━ 📶 𝗻𝗲𝘁 — Kiểm tra mạng\n"
    "   ┣━ ⚙️ 𝘀𝘆𝘀 — Xem hệ thống\n"
    "   ┗━ 🔍 𝗮𝗽𝗶 — Kiểm tra API\n"
    "---------------------------------\n"    
    "☀ 𝐐𝐔𝐀̉𝐍 𝐋𝐈́ 𝐓𝐈𝐍 𝐍𝐇𝐀̆́𝐍\n"
    "---------------------------------\n"    
    "   ┣━ 📤 𝘀𝗲𝗻𝗱𝘂𝘀𝗲𝗿 - Gửi tin spam\n"
    "   ┣━ 📢 𝘁𝗮𝗴𝗮𝗹𝗹 - Tag tất cả\n"
    "   ┣━ 📢 𝘁𝗮𝗴𝗮𝗹𝗹𝗺𝗲𝗺 - Tag tất cả\n"
    "   ┣━ ✏️ 𝗿𝗲𝗻𝗮𝗺𝗲𝗰𝗺𝗱 - Đổi tên lệnh\n"
    "   ┣━ 🖼️ 𝘀𝗲𝗻𝗱𝗽𝗶𝗰 - Gửi ảnh nhóm\n"
    "   ┣━ 🔗 𝘀𝗲𝗻𝗱𝗹𝗶𝗻𝗸 - Gửi link\n"
    "   ┣━ 💬 𝘀𝗲𝗻𝗱𝗺𝘀𝗴 - Gửi tin nhóm\n"
    "   ┣━ 🔗 𝘀𝗲𝗻𝗱𝗹 - Gửi link tag\n"
    "   ┣━ 🔗 𝘀𝗲𝗻𝗱𝗹𝟮 - Gửi link toàn nhóm\n"
    "   ┣━ 🆔 𝗴𝗲𝘁𝗶𝗱𝗯𝘆𝗹𝗶𝗻𝗸 - Lấy ID nhóm\n"
    "   ┣━ 📨 𝘀𝗲𝗻𝗱𝗶𝗱𝘀 - Gửi tin theo ID\n"
    "   ┗━ 📨 𝘀𝗲𝗻𝗱𝗻𝗵𝗼𝗺 - Gửi tin theo link\n"
    "---------------------------------\n"    
    "☀ 𝐓𝐔̛𝐎̛𝐍𝐆 𝐓𝐀́𝐂 𝐍𝐇𝐎́𝐌\n"
    "---------------------------------\n"    
    "   ┣━ 📝 𝗹𝗶𝘀𝘁𝗳𝗿𝗶𝗲𝗻𝗱𝘀 - DS bạn bè\n"
    "   ┣━ 📝 𝗹𝗶𝘀𝘁𝗴𝗿𝗼𝘂𝗽𝘀 - DS nhóm\n"
    "   ┣━ 📝 𝗹𝗶𝘀𝘁𝗺𝗲𝗺𝗯𝗲𝗿𝘀 - DS thành viên\n"
    "   ┣━ 🆔 𝗴𝗿𝗶𝗱 - Lấy ID nhóm\n"
    "   ┣━ 🔍 𝗳𝗶𝗻𝗱𝗴𝗿𝗯𝘆𝗶𝗱 - Tìm nhóm theo ID\n"
    "   ┣━ 🤝 𝗸𝗯 - Kết bạn tất cả\n"
    "   ┣━ 🔀 𝗷𝗼𝗶𝗻 - Tham gia nhóm\n"
    "   ┣━ ↩️ 𝗹𝗲𝗮𝘃𝗲 - Rời nhóm\n"
    "   ┗━ ↩️ 𝗹𝗲𝗮 - Rời nhóm (ID)\n"
    "---------------------------------\n"    
    "☀ 𝐓𝐀́𝐂 𝐕𝐔̣ 𝐊𝐇𝐀́𝐂\n"
    "---------------------------------\n"    
    "   ┣━ 📨 𝘀𝗲𝗻𝗱𝘀𝘁𝗸 - Gửi stk\n"
    "   ┣━ 📌 𝘁𝗼𝗱𝗼𝗴𝗿 - Gửi todo\n"
    "   ┗━ 📌 𝘀𝗽𝗮𝗺𝘁𝗼𝗱𝗼 - Spam todo\n"
    "\n"
)

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
        'menu4': handle_menu_command
    }
