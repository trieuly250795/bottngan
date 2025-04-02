from zlapi.models import *
from config import IMEI  # Nhập IMEI từ file cấu hình
import time

des = {
    'tác giả': "Rosy",
    'mô tả': "Bot hỗ trợ rời khỏi nhóm Zalo dựa trên danh sách ID nhóm do người dùng cung cấp.",
    'tính năng': [
        "🚪 Rời khỏi các nhóm Zalo theo danh sách ID nhóm do người dùng cung cấp.",
        "🔍 Lấy thông tin chi tiết nhóm trước khi rời bao gồm tên trưởng nhóm, phó nhóm và số thành viên.",
        "🔔 Thông báo kết quả rời khỏi nhóm với thời gian sống (TTL) khác nhau.",
        "🔒 Chỉ quản trị viên mới có quyền sử dụng lệnh này."
    ],
    'hướng dẫn sử dụng': [
        "📩 Gửi lệnh để bot rời khỏi nhóm Zalo kèm theo danh sách ID nhóm.",
        "📌 Hỗ trợ nhập nhiều ID nhóm cùng lúc, cách nhau bằng dấu cách.",
        "✅ Nhận thông báo trạng thái rời khỏi nhóm ngay lập tức."
    ]
}

# Danh sách ADMIN ID được phép sử dụng lệnh
ADMIN_IDS = ["2670654904430771575"]  # Thay bằng ID thực tế của Admin

def send_message_with_style(client, text, thread_id, thread_type, color="#000000", max_length=1500, delay=3):
    """
    Gửi tin nhắn với định dạng màu sắc và font chữ, chia nhỏ tin nhắn nếu quá dài.
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
            style="font",
            size="1",
            auto_format=False
        )
    ])
    
    chunks = [text[i:i+max_length] for i in range(0, len(text), max_length)]
    for chunk in chunks:
        client.send(Message(text=chunk, style=style), thread_id=thread_id, thread_type=thread_type, ttl=60000)
        time.sleep(delay)

def handle_leave_group_by_id(message, message_object, thread_id, thread_type, author_id, bot):
    """
    Rời nhóm dựa trên danh sách ID nhóm do người dùng cung cấp, đồng thời lấy thông tin chi tiết nhóm.
    """
    if author_id not in ADMIN_IDS:
        error_msg = "Bạn không có quyền sử dụng lệnh này."
        send_message_with_style(bot, error_msg, thread_id, thread_type)
        return
    
    bot.sendReaction(message_object, "✅", thread_id, thread_type, reactionType=75)
    
    args = message.split()
    if len(args) < 2:
        send_message_with_style(bot, "Vui lòng nhập ít nhất một ID nhóm để rời.", thread_id, thread_type)
        return
    
    group_ids = args[1:]
    msg = "🚪 Đang rời khỏi các nhóm:\n"
    
    for group_id in group_ids:
        try:
            # Lấy thông tin nhóm trước khi rời
            group_info = bot.fetchGroupInfo(group_id).gridInfoMap[group_id]
            
            # Lấy tên trưởng nhóm và phó nhóm
            def get_name(user_id):
                try:
                    user_info = bot.fetchUserInfo(user_id)
                    return user_info.changed_profiles[user_id].zaloName
                except KeyError:
                    return "Không tìm thấy tên"
            
            group_name = group_info.name
            leader_name = get_name(group_info.creatorId)
            admin_names = ", ".join([get_name(admin_id) for admin_id in group_info.adminIds])
            total_members = group_info.totalMember
            
            # Rời nhóm
            bot.leaveGroup(group_id, imei=IMEI)
            
            msg += (
                f"✅ Đã rời khỏi nhóm: {group_name}\n"
                f"👤 Trưởng nhóm: {leader_name}\n"
                f"👥 Phó nhóm: {admin_names}\n"
                f"👤 Số thành viên: {total_members}\n"
                f"-----------------------------------\n"
            )
        except Exception as e:
            msg += f"⚠️ Lỗi khi rời nhóm {group_id}: {e}\n"
    
    send_message_with_style(bot, msg, thread_id, thread_type, color="#db342e", max_length=1500, delay=3)

def get_mitaizl():
    return {
        'lea': handle_leave_group_by_id
    }
