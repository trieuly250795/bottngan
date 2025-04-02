from zlapi.models import *

# Danh sách ADMIN ID được phép sử dụng lệnh
ADMIN_IDS = ["2670654904430771575"]  # Thay bằng ID thực tế của Admin

def send_message_with_style(client, text, thread_id, thread_type, color="#000000"):
    """
    Gửi tin nhắn với định dạng màu sắc và font chữ.
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
    client.send(Message(text=text, style=style), thread_id=thread_id, thread_type=thread_type, ttl=60000)

def handle_find_group_name(message, message_object, thread_id, thread_type, author_id, bot):
    """
    Tìm tên nhóm dựa trên danh sách ID nhóm do người dùng cung cấp.
    """
    if author_id not in ADMIN_IDS:
        error_msg = "Bạn không có quyền sử dụng lệnh này."
        send_message_with_style(bot, error_msg, thread_id, thread_type)
        return
    
    bot.sendReaction(message_object, "✅", thread_id, thread_type, reactionType=75)
    
    # Định nghĩa hàm get_name để lấy tên người dùng (dựa vào creatorId)
    def get_name(user_id):
        if not user_id:
            return "Không tìm thấy tên"
        try:
            user_info = bot.fetchUserInfo(user_id)
            return user_info.changed_profiles.get(user_id, {}).get('zaloName', "Không tìm thấy tên")
        except Exception:
            return "Không tìm thấy tên"
    
    args = message.split()
    if len(args) < 2:
        send_message_with_style(bot, "Vui lòng nhập ít nhất một ID nhóm cần tìm.", thread_id, thread_type)
        return
    
    group_ids = args[1:]
    msg = "🔍 Kết quả tìm kiếm nhóm:\n"
    
    for group_id in group_ids:
        try:
            group_info = bot.fetchGroupInfo(group_id).gridInfoMap.get(group_id, None)
            if not group_info:
                msg += f"❌ Không tìm thấy nhóm với ID: {group_id}\n"
                continue
            
            msg += (
                f"✅ 𝗡𝗵𝗼́𝗺: {group_info.name}\n"
                f"👤 𝗧𝗿𝘂̛𝗼̛̉𝗻𝗴 𝗻𝗵𝗼́𝗺: {group_info.creatorId}\n"
                f"🔑 𝗧𝗿𝘂̛𝗼̛̉𝗻𝗴 𝗻𝗵𝗼́𝗺: {get_name(group_info.creatorId)}\n"
                f"👥 𝗦𝗼̂́ 𝗧𝗵𝗮̀𝗻𝗵 𝗩𝗶𝗲̂𝗻: {group_info.totalMember}\n"
                f"🆔 𝗜𝗗 𝗡𝗵𝗼́𝗺: {group_id}\n"
                f"---------------------------------\n"
            )
        except Exception as e:
            msg += f"⚠️ Lỗi khi lấy thông tin nhóm {group_id}: {e}\n"
    
    send_message_with_style(bot, msg, thread_id, thread_type, color="#000000")

def get_mitaizl():
    return {
        '`': handle_find_group_name
    }
