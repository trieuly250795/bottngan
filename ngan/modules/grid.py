from zlapi.models import *

def send_simple_message(client, text, thread_id, thread_type):
    """
    Gửi tin nhắn đơn giản.
    """
    client.send(Message(text=text), thread_id=thread_id, thread_type=thread_type, ttl=60000)

def get_group_id(message, message_object, thread_id, thread_type, author_id, bot):
    try:
        # Lấy thông tin nhóm
        group = bot.fetchGroupInfo(thread_id).gridInfoMap[thread_id]
        
        # Tạo tin nhắn chỉ chứa ID nhóm
        msg = f"📌 𝗜𝗗 𝗡𝗵𝗼́𝗺: {group.groupId}"
        
        # Gửi tin nhắn
        send_simple_message(bot, msg, thread_id, thread_type)
    except Exception as e:
        print(f"Error: {e}")
        send_simple_message(bot, "Đã xảy ra lỗi khi lấy ID nhóm 🤧", thread_id, thread_type)

def get_mitaizl():
    return {
        'grid': get_group_id
    }
