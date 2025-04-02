from zlapi.models import Message, MultiMsgStyle, MessageStyle

des = {
    'tác giả': "Rosy",
    'mô tả': "Trợ lý chatbot quản lý nhóm với nhiều tính năng tiện ích.",
    'tính năng': [
        "📋 Gửi menu các lệnh quản lý nhóm cho người dùng.",
        "🔍 Kiểm tra cú pháp lệnh và phản hồi bằng menu hướng dẫn.",
        "📨 Gửi tin nhắn với định dạng màu sắc và font chữ đặc biệt.",
        "📊 Cung cấp các lệnh chống spam, quản lý thành viên, quản lý nội dung và tùy chỉnh nhóm.",
        "🔔 Thông báo kết quả kiểm tra lệnh với thời gian sống (TTL) khác nhau.",
        "🔒 Chỉ quản trị viên mới có quyền sử dụng lệnh này."
    ],
    'hướng dẫn sử dụng': [
        "📩 Gửi lệnh để bot kiểm tra cú pháp và phản hồi bằng menu hướng dẫn.",
        "📌 Bot sẽ gửi menu các lệnh quản lý nhóm với định dạng màu sắc và font chữ đặc biệt.",
        "✅ Nhận thông báo trạng thái kiểm tra lệnh và menu hướng dẫn ngay lập tức."
    ]
}


def send_message_with_style(client, text, thread_id, thread_type, color="#db342e"):
    """
    Gửi tin nhắn với định dạng màu sắc.
    """
    base_length = len(text)
    adjusted_length = base_length + 355
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
                style="bold",
                size="8",
                auto_format=False
        )
    ])
    client.send(Message(text=text, style=style), thread_id=thread_id, thread_type=thread_type, ttl=60000)


def handle_sim_command(message, message_object, thread_id, thread_type, author_id, client):
    """
    Xử lý lệnh 'sim' và phản hồi bằng menu hướng dẫn.
    """
    # Gửi phản ứng xác nhận với tin nhắn người dùng
    client.sendReaction(message_object, "✅", thread_id, thread_type, reactionType=99)

    # Kiểm tra cú pháp lệnh
    text_parts = message.split()
    if len(text_parts) < 2:
        # Nội dung hướng dẫn
        menu_texts = [
            """🌸 𝐓𝐫𝐨̛̣ 𝐋𝐲́ 𝐌𝐲𝐚 🌸  
━━━━━━━━━━━━━━━━━━━  
📑 𝐌𝐄𝐍𝐔 𝐐𝐔𝐀̉𝐍 𝐋𝐘́ 𝐍𝐇𝐎́𝐌  
━━━━━━━━━━━━━━━━━━━  
🛡 𝐂𝐇𝐎̂́𝐍𝐆 𝐒𝐏𝐀𝐌 & 𝐐𝐔𝐀̉𝐍 𝐋𝐘́:  
✔️ 𝗮𝗻𝘁𝗶𝘀𝗽𝗮𝗺 𝗼𝗻/𝗼𝗳𝗳 – Bật/tắt chống spam  
✔️ 𝗯𝗼𝘁𝘁 𝗼𝗻/𝗼𝗳𝗳 – Bật/tắt bot  
✔️ 𝘀𝗼𝘀 – Khóa nhóm ngay  

👥 𝐐𝐔𝐀̉𝐍 𝐋𝐘́ 𝐓𝐇𝐀̀𝐍𝐇 𝐕𝐈𝐄̂𝐍:  
✔️ 𝗯𝗼𝘁𝘁 𝗯𝗮𝗻/𝘂𝗻𝗯𝗮𝗻 – Khóa/mở mõm thành viên  
✔️ 𝗯𝗼𝘁𝘁 𝗸𝗶𝗰𝗸 – Xóa thành viên  
✔️ 𝗱𝘂𝘆𝗲𝘁𝗺𝗲𝗺 𝗹𝗶𝘀𝘁/𝗮𝗹𝗹 – Xem/duyệt danh sách chờ  

📜 𝐐𝐔𝐀̉𝐍 𝐋𝐘́ 𝐍𝐎̣̂𝐈 𝐃𝐔𝐍𝐆:  
✔️ 𝗯𝗼𝘁𝘁 𝗹𝗶𝗻𝗸 𝗼𝗻/𝗼𝗳𝗳 – Bật/tắt cấm link  
✔️ 𝗯𝗼𝘁𝘁 𝘄𝗼𝗿𝗱 𝗮𝗱𝗱/𝗿𝗲𝗺𝗼𝘃𝗲 – Thêm/xóa từ cấm  
✔️ 𝗯𝗼𝘁𝘁 𝗿𝘂𝗹𝗲 𝘄𝗼𝗿𝗱 𝗺 𝗻 – Cài đặt khóa mõm theo từ  
✔️ 𝗯𝗮𝗻/𝘂𝗻𝗯𝗮𝗻 – Xóa & chặn/mở chặn thành viên  
✔️ 𝗯𝗹𝗼𝗰𝗸/𝘂𝗻𝗯𝗹𝗼𝗰𝗸 – Chặn/mở chặn bằng UID  
✔️ 𝘅𝗼𝗮 – Xóa tin nhắn  

⚙️ 𝐓𝐈𝐄̣̂𝐍 𝐈́𝐂𝐇 𝐐𝐔𝐀̉𝐍 𝐋𝐘́:  
✔️ 𝗯𝗼𝘁𝘁 𝗶𝗻𝗳𝗼 – Thông tin bot  
✔️ 𝗯𝗼𝘁𝘁 𝗻𝗼𝗶𝗾𝘂𝘆 – Áp dụng nội quy nhóm  
✔️ 𝗯𝗼𝘁𝘁 𝘀𝗲𝘁𝘂𝗽 𝗼𝗻/𝗼𝗳𝗳 – Bật/tắt cài đặt nhóm  
✔️ 𝗯𝗼𝘁𝘁 𝗯𝗮𝗻 𝗹𝗶𝘀𝘁 – Danh sách khóa mõm  
✔️ 𝘀𝗲𝗻𝗱𝗮𝗹𝗹 – Gửi tin nhắn toàn nhóm  
✔️ 𝘀𝗲𝗻𝗱𝗽𝗶𝗰 – Gửi ảnh toàn nhóm  
""",
            """🔧 𝐓𝐔̀𝐘 𝐂𝐇𝐈̉𝐍𝐇 𝐍𝐇𝐎́𝐌:  
✔️ 𝗴𝗿 𝗯𝗹𝗼𝗰𝗸𝗻𝗮𝗺𝗲 𝗼𝗻/𝗼𝗳𝗳 – Khóa đổi tên nhóm  
✔️ 𝗴𝗿 𝘀𝗶𝗴𝗻𝗮𝗱𝗺𝗶𝗻𝗺𝘀𝗴 𝗼𝗻/𝗼𝗳𝗳 – Ghi chú admin trong tin nhắn  
✔️ 𝗴𝗿 𝗮𝗱𝗱𝗺𝗲𝗺𝗯𝗲𝗿𝗼𝗻𝗹𝘆 𝗼𝗻/𝗼𝗳𝗳 – Chỉ admin thêm thành viên  
✔️ 𝗴𝗿 𝘀𝗲𝘁𝘁𝗼𝗽𝗶𝗰𝗼𝗻𝗹𝘆 𝗼𝗻/𝗼𝗳𝗳 – Chỉ admin đổi chủ đề  
✔️ 𝗴𝗿 𝗲𝗻𝗮𝗯𝗹𝗲𝗺𝘀𝗴𝗵𝗶𝘀𝘁𝗼𝗿𝘆 𝗼𝗻/𝗼𝗳𝗳 – Bật/tắt lịch sử tin nhắn  
✔️ 𝗴𝗿 𝗹𝗼𝗰𝗸𝗰𝗿𝗲𝗮𝘁𝗲𝗽𝗼𝘀𝘁 𝗼𝗻/𝗼𝗳𝗳 – Khóa tạo bài viết  
✔️ 𝗴𝗿 𝗹𝗼𝗰𝗸𝗰𝗿𝗲𝗮𝘁𝗲𝗽𝗼𝗹𝗹 𝗼𝗻/𝗼𝗳𝗳 – Khóa tạo khảo sát  
✔️ 𝗴𝗿 𝗷𝗼𝗶𝗻𝗮𝗽𝗽𝗿 𝗼𝗻/𝗼𝗳𝗳 – Duyệt thành viên khi tham gia  
✔️ 𝗴𝗿 𝗹𝗼𝗰𝗸𝘀𝗲𝗻𝗱𝗺𝘀𝗴 𝗼𝗻/𝗼𝗳𝗳 – Khóa gửi tin nhắn  
✔️ 𝗴𝗿 𝗹𝗼𝗰𝗸𝘃𝗶𝗲𝘄𝗺𝗲𝗺𝗯𝗲𝗿 𝗼𝗻/𝗼𝗳𝗳 – Khóa xem danh sách thành viên  

📊 𝐓𝐇𝐎̂𝐍𝐆 𝐓𝐈𝐍 & 𝐐𝐔𝐀̉𝐍 𝐋𝐘́ 𝐍𝐀̂𝐍𝐆 𝐂𝐀𝐎:  
✔️ 𝗴𝗿 𝗹𝗶𝘀𝘁𝗺𝗲𝗺𝗯𝗲𝗿𝘀 – Danh sách thành viên  
✔️ 𝗴𝗿 𝗴𝗿𝗼𝘂𝗽𝗶𝗻𝗳𝗼 – Thông tin nhóm  
✔️ 𝗴𝗿 𝗯𝗮𝗻𝗻𝗳𝗲𝗮𝘁𝘂𝗿𝗲 𝗼𝗻/𝗼𝗳𝗳 – Bật/tắt cấm thành viên  
✔️ 𝗴𝗿 𝗱𝗶𝗿𝘁𝘆𝗺𝗲𝗱𝗶𝗮 𝗼𝗻/𝗼𝗳𝗳 – Kiểm soát nội dung  
✔️ 𝗴𝗿 𝗯𝗮𝗻𝗱𝘂𝗿𝗮𝘁𝗶𝗼𝗻 <𝘀𝗼̂́ 𝗽𝗵𝘂́𝘁> – Thời gian cấm thành viên  
✔️ 𝗴𝗿 𝗯𝗹𝗼𝗰𝗸𝗲𝗱𝗺𝗲𝗺𝗯𝗲𝗿𝘀 – Danh sách thành viên bị cấm  
✔️ 𝗴𝗿 𝗮𝗰𝘁𝗶𝘃𝗲 – Kiểm tra tính năng đang bật  
✔️ 𝗴𝗿 𝗽𝗿𝗼𝗺𝗼𝘁𝗲 – Thăng cấp admin  
"""
        ]

        # Gửi từng phần của menu với màu đỏ
        for part in menu_texts:
            send_message_with_style(client, part, thread_id, thread_type)
    else:
        # Thông báo lỗi khi cú pháp sai
        error_message_text = "🚫 Vui lòng nhập đúng cú pháp lệnh. Ví dụ: sim adgr"
        send_message_with_style(client, error_message_text, thread_id, thread_type, color="#ff0000")


def get_mitaizl():
    """
    Trả về cấu hình lệnh và handler tương ứng.
    """
    return {
        'menuad': handle_sim_command
    }
