from zlapi.models import *
import datetime
import os
import subprocess
import time  # Thêm import time để sử dụng delay

admin_ids = ['2670654904430771575']  # Thay thế bằng ID admin thực tế

des = {
    'tác giả': "Rosy",
    'mô tả': "Gửi SMS và gọi điện một cách an toàn",
    'tính năng': [
        "📨 Gửi SMS và thực hiện cuộc gọi điện thoại.",
        "🔒 Kiểm tra quyền admin trước khi thực hiện lệnh.",
        "🔍 Kiểm tra định dạng số điện thoại và xử lý các lỗi liên quan.",
        "🔔 Thông báo lỗi cụ thể nếu cú pháp lệnh không chính xác hoặc giá trị không hợp lệ."
    ],
    'hướng dẫn sử dụng': [
        "📩 Gửi lệnh spamsms <số điện thoại> <số lần gửi> để gửi SMS và thực hiện cuộc gọi.",
        "📌 Ví dụ: spamsms 0123456789 5 để gửi SMS và thực hiện cuộc gọi đến số 0123456789 5 lần.",
        "✅ Nhận thông báo trạng thái và kết quả gửi SMS ngay lập tức."
    ]
}

def handle_sms_command(message, message_object, thread_id, thread_type, author_id, client):
    parts = message.split()
    if len(parts) < 3:
        client.replyMessage(
            Message(text='🚫 **Nhập số đt con chó cần spam và số lần gửi**'),
            message_object, thread_id=thread_id, thread_type=thread_type, ttl=60000
        )
        return

    attack_phone_number, number_of_times = parts[1], int(parts[2])

    if not (attack_phone_number.isnumeric() and len(attack_phone_number) == 10 and attack_phone_number not in ['113', '911', '114', '115', '0347460743']):
        client.replyMessage(
            Message(text='❌ **𝐒𝐨̂́ đ𝐢𝐞̣̂𝐧 𝐭𝐡𝐨𝐚̣𝐢 𝐤𝐡𝐨̂𝐧𝐠 𝐡𝐨̛̣𝐩 𝐥𝐞̣̂🤬!**'),
            message_object, thread_id=thread_id, thread_type=thread_type, ttl=60000
        )
        return

    current_time = datetime.datetime.now()
    is_admin = author_id in admin_ids  # Hạn chế key FREE: Người dùng không phải admin chỉ được spam với số lần gửi từ 5 đến 10

    if not is_admin and (number_of_times < 5 or number_of_times > 10):
        client.replyMessage(
            Message(text='🚫 **Sdt đã được thêm vào danh sách spam**'),
            message_object, thread_id=thread_id, thread_type=thread_type, ttl=60000
        )
        return
        
    # Thông báo bắt đầu
    client.replyMessage(
        Message(text="⏳ Bắt đầu gửi SMS và thực hiện cuộc gọi..."),
        message_object, thread_id=thread_id, thread_type=thread_type, ttl=60000
    )    

    # Bỏ chức năng cooldown: Không kiểm tra thời gian giữa các lệnh gửi liên tiếp
    process = subprocess.Popen([
        "python", os.path.join(os.getcwd(), "smsv2.py"), attack_phone_number, str(number_of_times)
    ])
    
    for i in range(1, number_of_times + 1):
        time_str = current_time.strftime("%d/%m/%Y %H:%M:%S")
        masked_number = f"{attack_phone_number[:3]}***{attack_phone_number[-3:]}"
        msg_content = (
            f"🚀 Báo cáo spam SMS từ Bot\n"
            f"📞 Số điện thoại: {masked_number}\n"
            f"⏰ Thời gian: {time_str}\n"
            f"🔁 Đã hoàn thành: {i}/{number_of_times}\n"
            f"⏳ Thời gian chờ : 120 seconds\n"
            f"👤 Admin: Rosy"
        )
        
        mention = Mention(author_id, length=len("Người quản lý"), offset=0)
        style = MultiMsgStyle([MessageStyle(style="color", color="#4caf50", length=len(msg_content), offset=0)])
        
        client.replyMessage(
            Message(text=msg_content.strip(), style=style, mention=mention),
            message_object, thread_id=thread_id, thread_type=thread_type, ttl=60000
        )
        time.sleep(1)  # Thêm delay 1 giây giữa các lần gửi báo cáo
    
    process.wait()
    
    # Thông báo hoàn thành
    client.replyMessage(
        Message(text= f"✅ Đã hoàn thành {number_of_times} lần gửi SMS và thực hiện cuộc gọi tới {masked_number} "),
        message_object, thread_id=thread_id, thread_type=thread_type, ttl=60000
    )

def get_mitaizl():
    return {'spamsms': handle_sms_command}
