import random
import json
import os
from datetime import datetime, timedelta
from zlapi import Message, ThreadType, MultiMsgStyle, MessageStyle

des = {
    'tác giả': "Rosy",
    'mô tả': "Đo độ gay của người dùng được tag và phân loại dựa trên phần trăm đo được.",
    'tính năng': [
        "📊 Đo độ gay của người dùng được tag",
        "⏳ Hạn chế số lần sử dụng trong 24 giờ",
        "🔄 Lưu trữ và cập nhật thông tin sử dụng",
        "📈 Tạo ngẫu nhiên phần trăm độ gay cho lần đầu sử dụng",
        "🔍 Phân loại kết quả theo phần trăm: 1-20% trai thẳng, 21-40% bóng, 41-60% thích mặc váy, 61-80% bê đê chúa, 81-100% chuẩn bị đi Thái",
        "⚡ Gửi phản hồi nhanh chóng với kết quả đo và phân loại",
        "🛠️ Tích hợp phản ứng khi sử dụng lệnh"
    ],
    'hướng dẫn sử dụng': [
        "📩 Dùng lệnh 'gay @name' để đo độ gay của người dùng được tag.",
        "📌 Ví dụ: gay @username để đo độ gay của người dùng có tên 'username'.",
        "✅ Nhận thông báo trạng thái và kết quả ngay lập tức."
    ]
}

# Đường dẫn tới tệp lưu trữ thông tin sử dụng
GAY_TEST_FILE = 'gay_test_usage.json'

def load_usage_data():
    if os.path.exists(GAY_TEST_FILE):
        with open(GAY_TEST_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_usage_data(data):
    with open(GAY_TEST_FILE, 'w') as f:
        json.dump(data, f)

def classify_gay_percentage(percentage):
    if 1 <= percentage <= 20:
        return "trai thẳng"
    elif 21 <= percentage <= 40:
        return "bóng"
    elif 41 <= percentage <= 60:
        return "thích mặc váy"
    elif 61 <= percentage <= 80:
        return "bê đê chúa"
    elif 81 <= percentage <= 100:
        return "chuẩn bị đi Thái"
    else:
        return "không xác định"

def handle_gay_test(message, message_object, thread_id, thread_type, author_id, client):
    # Gửi phản ứng ngay khi người dùng soạn lệnh "gay"
    action = "✅"
    client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)

    mentions = message_object.mentions  # Lấy danh sách người dùng được tag
    usage_data = load_usage_data()  # Tải thông tin sử dụng

    # Nếu không có người nào được tag, thông báo lỗi
    if not mentions or len(mentions) < 1:
        menu_message = "Vui lòng nhập cú pháp: 'gay @name'"
        style = MultiMsgStyle([
            MessageStyle(offset=0, length=len(menu_message), style="color", color="#15a85f", auto_format=False),
            MessageStyle(offset=0, length=len(menu_message), style="font", size="16", auto_format=False),
        ])
        client.replyMessage(
            Message(text=menu_message, style=style),
            message_object, thread_id, thread_type, ttl=10000
        )
        return

    now = datetime.now()
    results = []  # Danh sách chứa kết quả cho từng người được tag

    # Duyệt qua từng người dùng được tag
    for mention in mentions:
        person_id = mention.id
        person_name = mention.name

        # Nếu đã từng được đo, lấy lại thông tin và kiểm tra hạn mức sử dụng
        if person_id in usage_data:
            gay_percentage = usage_data[person_id]['gay_percentage']
            last_used = datetime.fromisoformat(usage_data[person_id]['last_used'])
            count = usage_data[person_id]['count']

            # Nếu đã sử dụng quá số lần cho phép trong 24 giờ, thông báo cho người dùng
            if count >= 2 and now < last_used + timedelta(days=1):
                time_remaining = (last_used + timedelta(days=1) - now).total_seconds()
                hours_remaining = int(time_remaining // 3600)
                minutes_remaining = int((time_remaining % 3600) // 60)
                results.append(f"{person_name} đã sử dụng quá số lần cho phép. Vui lòng thử lại sau {hours_remaining} giờ {minutes_remaining} phút.")
                continue  # Bỏ qua người dùng này và không tính lại phần trăm
            else:
                usage_data[person_id]['count'] += 1
                usage_data[person_id]['last_used'] = str(now)
        else:
            # Nếu lần đầu sử dụng, tạo ngẫu nhiên phần trăm độ gay và lưu lại
            gay_percentage = random.randint(1, 100)
            usage_data[person_id] = {
                'gay_percentage': gay_percentage,
                'count': 1,
                'last_used': str(now)
            }

        # Phân loại kết quả dựa trên phần trăm đo được
        classification = classify_gay_percentage(usage_data[person_id]['gay_percentage'])
        results.append(f"{person_name} có độ gay là {usage_data[person_id]['gay_percentage']}% ({classification}).")
    
    # Lưu lại thông tin sử dụng đã cập nhật
    save_usage_data(usage_data)

    # Kết hợp tất cả kết quả thành một thông điệp tổng hợp
    final_message = "\n".join(results)
    style = MultiMsgStyle([
        MessageStyle(offset=0, length=len(final_message), style="color", color="#15a85f", auto_format=False),
        MessageStyle(offset=0, length=len(final_message), style="font", size="16", auto_format=False),
    ])
    client.replyMessage(
        Message(text=final_message, style=style),
        message_object, thread_id, thread_type, ttl=120000
    )

def get_mitaizl():
    return {
        'gay': handle_gay_test
    }
