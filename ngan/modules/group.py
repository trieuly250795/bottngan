from datetime import datetime
from zlapi.models import *

def send_message_with_style(client, text, thread_id, thread_type, color="#db342e"):
    """
    Gửi tin nhắn với định dạng màu sắc.
    """
    base_length = len(text)
    adjusted_length = base_length + 355
    style = MultiMsgStyle([  # Applying both color and font size
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
                size="6",
                auto_format=False
        )
    ])
    client.send(Message(text=text, style=style), thread_id=thread_id, thread_type=thread_type, ttl=60000)

def handle_info(message, message_object, thread_id, thread_type, author_id, bot):
    # Gửi phản ứng ngay khi người dùng soạn đúng lệnh
    action = "✅"
    bot.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)

    def get_name(id):
        try:
            user_info = bot.fetchUserInfo(id)
            return user_info.changed_profiles[id].zaloName
        except KeyError:
            return "Không tìm thấy tên"

    msg_error = f"Đã xảy ra lỗi🤧"
    
    key_translation = {
        'blockName': '\n🚫 𝗖𝗵𝗮̣̆𝗻 𝘁𝗲̂𝗻 𝗻𝗵𝗼́𝗺 (Không cho phép user đổi tên & ảnh đại diện nhóm)',
        'signAdminMsg': '\n✍️ 𝗚𝗵𝗶𝗺 (Đánh dấu tin nhắn từ chủ/phó nhóm)',
        'addMemberOnly': '\n👤 𝗖𝗵𝗶̉ 𝘁𝗵𝗲̂𝗺 𝘁𝗵𝗮̀𝗻𝗵 𝘃𝗶𝗲̂𝗻 (Khi tắt link tham gia nhóm)',
        'setTopicOnly': '\n📝 𝗖𝗵𝗼 𝗽𝗵𝗲́𝗽 𝗺𝗲𝗺𝗯𝗲𝗿𝘀 𝗴𝗵𝗶𝗺 (tin nhắn, ghi chú, bình chọn)',
        'enableMsgHistory': '\n📜 𝗕𝗮̣̂𝘁 𝗹𝗶̣𝗰𝗵 𝘀𝘂̛ 𝘁𝗶𝗻 𝗻𝗵𝗮̆́𝗻 (Cho phép new members đọc tin nhắn gần nhất)',
        'lockCreatePost': '\n🔒 𝗞𝗵𝗼́𝗮 𝘁𝗮̣𝗼 𝗯𝗮̀𝗶 đ𝗮̆𝗻𝗴 (Không cho phép members tạo ghi chú, nhắc hẹn)',
        'lockCreatePoll': '\n🔒 𝗞𝗵𝗼́𝗮 𝘁𝗮̣𝗼 𝗰𝘂𝗼̣̂𝗰 𝘁𝗵𝗮̆𝗺 𝗱𝗼̀ (Không cho phép members tạo bình chọn)',
        'joinAppr': '\n✅ 𝗗𝘂𝘆𝗲̣̂𝘁 𝘃𝗮̀𝗼 𝗻𝗵𝗼́𝗺 (Chế độ phê duyệt thành viên)',
        'bannFeature': '\n🚫 𝗧𝗶́𝗻𝗵 𝗻𝗮̆𝗻𝗴 𝗰𝗮̂́𝗺',
        'dirtyMedia': '\n⚠️ 𝗡𝗼̣̂𝗶 𝗱𝗨𝗻𝗴 𝗻𝗵𝗮̣𝘆 𝗰𝗮̉𝗺',
        'banDuration': '\n⏳ 𝗧𝗵𝗼̛̀𝗶 𝗴𝗶𝗮𝗻 𝗰𝗮̂́𝗺',
        'lockSendMsg': '\n🔒 𝗞𝗵𝗼́𝗮 𝗴𝘂̛̉𝗶 𝘁𝗶𝗻 𝗻𝗵𝗮̆́𝗻',
        'lockViewMember': '\n🔒 𝗞𝗵𝗼́𝗮 𝘅𝗲𝗺 𝘁𝗵𝗮̀𝗻𝗵 𝘃𝗶𝗲̂𝗻'
    }
    
    try:
        # Lấy thông tin nhóm
        group = bot.fetchGroupInfo(thread_id).gridInfoMap[thread_id]
        
        # Tạo tin nhắn chứa thông tin nhóm
        msg = ""
        msg += f"   𝗧𝗵𝗼̂𝗻𝗴 𝘁𝗶𝗻 𝗰𝗵𝗶 𝘁𝗶𝗲̂́𝘁 𝗻𝗵𝗼́𝗺:\n------------------------------------------------------ \n{group.name}\n------------------------------------------------------\n"
        msg += f"𝗜𝗗: {group.groupId}\n"
        msg += f"📝 𝗠𝗶𝗲̂𝘂 𝘁𝗮̉: {'Mặc định' if group.desc == '' else group.desc}\n"
        msg += f"🔑 𝗧𝗿𝘂̛𝗼̛̉𝗻𝗴 𝗻𝗵𝗼́𝗺: {get_name(group.creatorId)}\n"
        msg += f"🗝️ 𝗣𝗵𝗼́ 𝗻𝗵𝗼́𝗺: {', '.join([get_name(member) for member in group.adminIds])}\n"

        # Thành viên đang chờ duyệt vào nhóm
        update_mems_info = ', '.join([get_name(member) for member in group.updateMems]) if group.updateMems else ""
        msg += f"⭕ 𝗧𝗵𝗮̀𝗻𝗵 𝘃𝗶𝗲̂𝗻 đ𝗮𝗻𝗴 𝗰𝗵𝗼̛̀ 𝗱𝘂𝘆𝗲̣̂𝘁 𝘃𝗮̀𝗼 𝗻𝗵𝗼́𝗺: {update_mems_info}\n"

        # Thông tin tổng số thành viên
        msg += f"⭕ Tổng {group.totalMember} thành viên\n"

        # Thời gian tạo nhóm
        createdTime = group.createdTime
        formatted_time = datetime.fromtimestamp(createdTime / 1000).strftime('%H:%M %d/%m/%Y')
        msg += f"📆 𝗧𝗵𝗼̛̀𝗶 𝗴𝗶𝗮𝗻 𝘁𝗮̣𝗼: {formatted_time}\n"
        
        # Lấy cấu hình nhóm và dịch sang tiếng Việt
        setting = group.setting
        config_string = ', '.join([f"{key_translation[key]}: {'Bật' if value == 1 else 'Tắt'}" for key, value in setting.items()])
        msg += f"⚙️ 𝗖𝗮̂́𝗨 𝗵𝗶̀𝗻𝗵: {config_string}\n"
        
        # Ảnh đại diện nhóm
        msg += f"⭕ Ảnh đại diện thu nhỏ: {'Mặc định' if group.avt == '' else group.avt}\n"
        msg += f"⭕ Ảnh đại diện đầy đủ: {'Mặc định' if group.fullAvt == '' else group.fullAvt}\n"
        
        # Gửi tin nhắn với thông tin nhóm với màu sắc và font size
        send_message_with_style(bot, msg, thread_id, thread_type, color="#db342e")

    except Exception as e:
        # Nếu xảy ra lỗi, gửi tin nhắn lỗi
        print(f"Error: {e}")
        send_message_with_style(bot, msg_error, thread_id, thread_type)

# Hàm trả về lệnh của bot
def get_mitaizl():
    return {
        'group': handle_info
    }
