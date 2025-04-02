import json
import os
import random

from zlapi.models import Message, MessageStyle, MultiMsgStyle
from config import ADMIN, PREFIX

# Đường dẫn file lưu trữ danh sách người dùng bị cấm
BANNED_USERS_FILE = "banned_users.json"

def load_banned_users():
    """
    Tải dữ liệu từ file JSON chứa danh sách người dùng bị cấm.
    Nếu file không tồn tại hoặc lỗi định dạng, trả về danh sách rỗng.
    """
    if not os.path.exists(BANNED_USERS_FILE):
        return []
    try:
        with open(BANNED_USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Lỗi tải danh sách người dùng bị cấm: {str(e)}")
        return []

def save_banned_users(banned_users):
    """Lưu danh sách người dùng bị cấm vào file JSON với định dạng UTF-8."""
    with open(BANNED_USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(banned_users, f, ensure_ascii=False, indent=4)

def add_banned_user(user_id, user_name):
    """
    Thêm người dùng vào danh sách cấm dựa theo user_id và user_name.
    Trả về True nếu thêm thành công, False nếu user_id đã tồn tại.
    """
    banned_users = load_banned_users()
    for user in banned_users:
        if user.get("user_id") == user_id:
            return False
    banned_users.append({"user_id": user_id, "user_name": user_name})
    save_banned_users(banned_users)
    return True

def remove_banned_user(user_id):
    """
    Xóa người dùng khỏi danh sách cấm.
    Trả về True nếu xóa thành công, False nếu user_id không tồn tại.
    """
    banned_users = load_banned_users()
    for user in banned_users:
        if user.get("user_id") == user_id:
            banned_users.remove(user)
            save_banned_users(banned_users)
            return True
    return False

def list_banned_users():
    """Trả về danh sách người dùng bị cấm."""
    return load_banned_users()

def send_reply_with_style(client, text, message_object, thread_id, thread_type, ttl=30000, color="#000000"):
    """
    Gửi tin nhắn phản hồi với định dạng màu sắc và in đậm.
    TTL được đặt mặc định là 30000.
    """
    base_length = len(text)
    adjusted_length = base_length + 355  # Đảm bảo áp dụng style cho toàn bộ tin nhắn
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
    msg = Message(text=text, style=style)
    client.replyMessage(msg, message_object, thread_id, thread_type, ttl=ttl)

def fetch_target_info(target_input, message_object, client, command_prefix):
    """
    Xác định target_id từ tag hoặc tham số nhập và lấy thông tin người dùng.
    Trả về tuple (target_id, target_name) hoặc None nếu có lỗi.
    """
    # Ưu tiên sử dụng thông tin từ tag nếu có
    if message_object.mentions and len(message_object.mentions) > 0:
        target_id = message_object.mentions[0]['uid']
    else:
        target_id = target_input.strip()
    if not target_id:
        return None

    try:
        # Lấy thông tin người dùng từ API
        info_response = client.fetchUserInfo(target_id)
        profiles = info_response.unchanged_profiles or info_response.changed_profiles
        target_info = profiles[str(target_id)]
        
        # Nếu target_info là dictionary thì lấy theo key, nếu không thì dùng getattr
        if isinstance(target_info, dict):
            target_name = target_info.get("zaloName") or target_info.get("username") or target_info.get("name")
        else:
            target_name = getattr(target_info, 'zaloName', None) or getattr(target_info, 'username', None) or getattr(target_info, 'name', None)
        
        if not target_name:
            target_name = "Unknown"
        else:
            target_name = str(target_name)
        return target_id, target_name
    except Exception as e:
        print(f"Lỗi fetch thông tin cho target {target_id}: {e}")
        return None

def handle_addban_command(message, message_object, thread_id, thread_type, author_id, client):
    """
    Xử lý lệnh thêm người dùng vào danh sách cấm.
    
    Hỗ trợ:
      - addban <id người dùng>
      - addban (với tag người dùng)
      
    Cách sử dụng:
      - Ví dụ: `{PREFIX}addban 123456789` để thêm người dùng với ID 123456789.
      - Hoặc tag người dùng rồi gõ lệnh: `{PREFIX}addban` (bot sẽ lấy uid của người được tag).
    """
    # Kiểm tra quyền admin
    if author_id != ADMIN:
        error_msg = Message(text="❌ Chỉ admin mới có quyền sử dụng lệnh này.")
        client.sendMessage(error_msg, thread_id, thread_type)
        return

    command_prefix = "addban"
    param = message[len(command_prefix):].strip()

    target = fetch_target_info(param, message_object, client, command_prefix)
    if target is None:
        error_msg = Message(text=f"Cú pháp: {PREFIX}addban <id> hoặc tag người dùng.\nKhông thể lấy thông tin người dùng.")
        client.sendMessage(error_msg, thread_id, thread_type)
        return

    target_id, target_name = target

    if add_banned_user(target_id, target_name):
        reply_text = f"✅ Đã thêm người dùng:\n👤 {target_name}\n🆔 {target_id}\n vào danh sách cấm giao tiếp với bot."
    else:
        reply_text = f"⚠️ Người dùng: {target_name}\n🆔 {target_id}\n đã tồn tại trong danh sách cấm."
    send_reply_with_style(client, reply_text, message_object, thread_id, thread_type, ttl=30000)

def handle_delban_command(message, message_object, thread_id, thread_type, author_id, client):
    """
    Xử lý lệnh xóa người dùng khỏi danh sách cấm.
    
    Hỗ trợ:
      - delban <id người dùng>
      - delban (với tag người dùng)
      
    Cách sử dụng:
      - Ví dụ: `{PREFIX}delban 123456789` để xóa người dùng với ID 123456789.
      - Hoặc tag người dùng rồi gõ lệnh: `{PREFIX}delban` (bot sẽ lấy uid của người được tag).
    """
    # Kiểm tra quyền admin
    if author_id != ADMIN:
        error_msg = Message(text="❌ Chỉ admin mới có quyền sử dụng lệnh này.")
        client.sendMessage(error_msg, thread_id, thread_type)
        return

    command_prefix = "delban"
    param = message[len(command_prefix):].strip()

    target = fetch_target_info(param, message_object, client, command_prefix)
    if target is None:
        error_msg = Message(text=f"Cú pháp: {PREFIX}delban <id> hoặc tag người dùng.\nKhông thể lấy thông tin người dùng.")
        client.sendMessage(error_msg, thread_id, thread_type)
        return

    target_id, target_name = target

    if remove_banned_user(target_id):
        reply_text = f"❌ Đã xóa người dùng:\n👤 {target_name}\n🆔 {target_id}\n khỏi danh sách cấm giao tiếp với bot."
    else:
        reply_text = f"⚠️ Người dùng với ID: {target_id} không tồn tại trong danh sách cấm."
    send_reply_with_style(client, reply_text, message_object, thread_id, thread_type, ttl=30000)

def handle_listban_command(message, message_object, thread_id, thread_type, author_id, client):
    """
    Xử lý lệnh xem danh sách người dùng bị cấm.
    
    Cách sử dụng:
      - Ví dụ: `{PREFIX}listban` để hiển thị danh sách người dùng cấm giao tiếp với bot.
    """
    # Kiểm tra quyền admin
    if author_id != ADMIN:
        error_msg = Message(text="❌ Chỉ admin mới có quyền sử dụng lệnh này.")
        client.sendMessage(error_msg, thread_id, thread_type)
        return

    banned_users = list_banned_users()
    if not banned_users:
        reply_text = "Danh sách người dùng cấm giao tiếp với bot trống."
    else:
        reply_text = "Danh sách người dùng cấm giao tiếp với bot:\n" + "\n".join(
            [f"{i+1}.   {usr['user_name']}\n🆔 {usr['user_id']}" for i, usr in enumerate(banned_users)]
        )
    send_reply_with_style(client, reply_text, message_object, thread_id, thread_type, ttl=30000)

def get_mitaizl():
    """
    Trả về một dictionary ánh xạ lệnh tới các hàm xử lý tương ứng cho quản lý người dùng bị cấm.
    
    Các lệnh hỗ trợ:
      - addban: Thêm người dùng vào danh sách cấm (theo tag hoặc ID)
      - delban: Xóa người dùng khỏi danh sách cấm (theo tag hoặc ID)
      - listban: Hiển thị danh sách người dùng cấm giao tiếp với bot
    """
    return {
        'addban': handle_addban_command,
        'delban': handle_delban_command,
        'listban': handle_listban_command
    }
