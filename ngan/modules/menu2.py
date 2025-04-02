import os
import importlib
import time
from datetime import datetime
from zlapi.models import Message

# Thông tin mô tả lệnh, phiên bản và credits
des = {
    'tác giả': "Rosy",
    'mô tả': "Hiển thị danh sách các lệnh hiện có của bot một cách trực quan với ảnh nền và phản hồi emoji.",
    'tính năng': [
        "🔹 Hiển thị danh sách các lệnh cùng hướng dẫn sử dụng chi tiết.",
        "🔹 Gửi phản hồi bằng emoji (✅) để xác nhận lệnh đã được nhận.",
        "🔹 Gửi ảnh nền kèm theo tin nhắn, giúp hiển thị menu rõ ràng và trực quan.",
        "🔹 Hỗ trợ định dạng tin nhắn đẹp mắt, dễ đọc và dễ theo dõi."
    ],
    'hướng dẫn sử dụng': [
        "📩 Gửi lệnh menu (hoặc help) để hiển thị danh sách các lệnh hiện có.",
        "📸 Kiểm tra tin nhắn có kèm theo ảnh nền chứa menu các lệnh của bot.",
        "✅ Nhận phản hồi bằng emoji sau khi lệnh được xử lý thành công."
    ]
}


def handle_menu_command(message, message_object, thread_id, thread_type, author_id, client):
    """
    Xử lý lệnh hiển thị menu công cụ cho bot.

    Khi người dùng gửi lệnh menu, hàm này thực hiện các bước sau:
      - Xây dựng nội dung menu (danh sách các lệnh và mô tả).
      - Gửi phản hồi với emoji "✅" nhằm xác nhận đã nhận lệnh.
      - Gửi ảnh nền kèm theo thông điệp menu đến cuộc trò chuyện.

    Các tham số:
      - message: Tin nhắn gốc.
      - message_object: Đối tượng tin nhắn hiện có.
      - thread_id: ID của cuộc trò chuyện.
      - thread_type: Loại cuộc trò chuyện.
      - author_id: ID của người gửi.
      - client: Đối tượng client của bot dùng để gửi phản hồi và ảnh.
    """
    menu_message = (
        "📄 𝐌𝐞𝐧𝐮 𝐓𝐨𝐨𝐥\n"
        " Soạn help + tên lệnh để xem mô tả \n" 
         "---------------------------------\n"
        "   ┣━ 📟 𝗮𝗰𝗰𝗹𝗾 — Acc Liên Quân\n"
        "   ┣━ 🎫 𝗰𝗮𝗿𝗱 — Danh tính\n"
        "   ┣━ 🔍 𝘁𝘁 — Video TikTok\n"
        "   ┣━ 🔍 𝘆𝘁 — YouTube\n"
        "   ┣━ 🔍 𝘄𝗶𝗸𝗶 — Wikipedia\n"
        "   ┣━ 🔍 𝗳𝗯 — Info Facebook\n"
        "   ┣━ 🔍 𝗽𝗶𝗻 — Ảnh Printerest\n"
        "   ┣━ 🔗 𝗴𝗲𝘁𝗹𝗶𝗻𝗸 — Ảnh/video → link\n"
        "   ┣━ ℹ️ 𝗶𝟰 — Info Zalo\n"
        "   ┣━ 🆔 𝘂𝗶𝗱 — get UID\n"
        "   ┣━ 👥 𝗴𝗿𝗼𝘂𝗽 — Nhóm\n"
        "   ┣━ 🕒️ 𝘁𝗶𝗺𝗲 — Đồng hồ\n"
        "   ┣━ 🚗 𝗽𝗵𝗮𝘁𝗻𝗴𝘂𝗼𝗶 — Phạt nguội\n"
        "   ┣━ 🔢 𝗰𝗮𝗹𝗰 — Casio\n"
        "   ┣━ 🌤️ 𝘁𝗵𝗼𝗶𝗍𝗶𝗲𝘁 — Thời tiết\n"
        "   ┣━ 🅉 𝘇𝗹 — Time Zalo\n"
        "   ┣━ 📈 𝘁𝘆𝗴𝗶𝗮 — Tỷ giá\n"
        "   ┣━ 📅 𝗮𝗺𝗹𝗶𝗰𝗵 — Âm lịch\n"
        "   ┣━ 🈹 𝗱𝗶𝗰𝗵 — Dịch văn bản\n"
        "   ┣━ 🌐 𝗮𝗽𝗶 — Trạng thái API\n"
        "   ┣━ 🔊 𝗱𝗼𝗰 — Đọc tin (reply)\n"
        "   ┗━ 🔎 𝘀𝗰𝗮𝗻𝘁𝗲𝘅𝘁 — Quét ảnh → văn bản\n"
        "   ┗━ 🔎 𝗱𝗶𝗻𝗵𝗴𝗶𝗮𝘀𝗱𝘁\n"
        "---------------------------------\n"
        "   ┣━ 🙏 𝗯𝗮𝗻𝘁𝗵𝗼 — Ảnh bàn thờ troll\n"
        "   ┣━ 📸 𝗰𝗮𝗽 — Màn hình web\n"
        "   ┣━ 🎨 𝗰𝗮𝗻𝘃𝗮 — Ảnh từ văn bản\n"
        "   ┣━ ⏬ 𝗴𝗲𝘁𝗼𝗶𝗰𝗲 — Âm thanh từ link\n"
        "   ┣━ ⏬ 𝗺𝗲𝗱𝗶𝗮 — Tải media\n"
        "   ┣━ 📝 𝗻𝗼𝘁𝗲 — Ghi chú → link\n"
        "   ┣━ 🔳 𝗾𝗿 — Mã QR\n"
        "   ┣━ 🔍 𝘀𝗰𝗮𝗻𝗾𝗿 — Quét QR\n"
        "   ┣━ ✍️ 𝘁𝗲𝘅𝘁𝟮𝗾𝗿 — QR từ text\n"
        "   ┣━ 🏞️ 𝗰𝗼𝘃𝗲𝗿 — Ảnh bìa\n"
        "   ┣━ ⏫ 𝗶𝗺𝗴𝘂𝗿 — Ảnh lên imgur\n"
        "   ┗━ 🎭 𝘀𝘁𝗸𝘁𝗻 — Sticker từ ảnh\n"
        "---------------------------------\n"
        "   ┣━ 💬 𝗯𝗼𝘁 — Chat bot\n"
        "   ┣━ 🎓 𝘁𝗲𝗮𝗰𝗵 — Dạy bot\n"
        "   ┣━ 💕 𝗹𝗼𝘃𝗲 — Bói tình duyên\n"
        "   ┣━ 💪 𝗱𝗲𝗽𝘁𝗿𝗮𝗶 — Đẹp trai\n"
        "   ┣━ 🌈 𝗴𝗮𝘆 — Độ gay\n"
        "   ┣━ 💌 𝘁𝗵𝗶𝗻𝗵 — Thả thính\n"
        "   ┣━ 🃏 𝗯𝗼𝗶 — Bói bài\n"
        "   ┗━ 💬 𝗴𝗲𝗻 — Chat Gemini\n"
        "---------------------------------\n"
        "   ┣━ 🎧 𝘀𝗰𝗹 — Nhạc SoundCloud\n"
        "   ┣━ 📋 𝘀𝗰𝗹𝗹𝗶𝘀𝘁 — DS nhạc\n"
        "   ┣━ ⏬ 𝘀𝗰𝗹𝗼𝗮𝗱 — Download nhạc\n"
        "   ┣━ 🔊 𝘃𝗼𝗶𝗰𝗲 — Giọng đọc\n"
        "   ┗━ ▶️ play on/off — DS phát\n"
        "🔧 𝗗𝗶̣𝗰𝗵 𝘃𝘂̣ 𝗧𝗶𝗲̣̂𝗻 𝗜́𝗰𝗵\n"
        "   ┣━ ⏬ down — Tải media\n"
        "   ┗━ ❓ help — Danh sách lệnh\n"
    )
    
    # Gửi phản hồi với emoji "✅" để xác nhận đã nhận lệnh
    action = "✅ "
    client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)

    # Gửi ảnh nền (local image) kèm theo thông điệp menu
    client.sendLocalImage(
        "wcmenu2.jpg",
        thread_id=thread_id,
        thread_type=thread_type,
        message=Message(text=menu_message),
        ttl=30000,           # Thời gian tồn tại của tin nhắn (ví dụ: 120000 ms)
        width=1920,           # Chiều rộng ảnh (ví dụ: 1920 pixel)
        height=1080           # Chiều cao ảnh (ví dụ: 1080 pixel)
    )


def get_mitaizl():
    """
    Trả về dictionary chứa các lệnh của module.

    Trong đó:
      - 'menu2': Tham chiếu đến hàm handle_menu_command.
    """
    return {
        'menu2': handle_menu_command
    }
