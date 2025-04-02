import json
import os
import random

from zlapi.models import Message, MessageStyle, MultiMsgStyle
from config import ADMIN, PREFIX

# Đường dẫn file lưu trữ danh sách nhóm bị cấm giao tiếp với bot
BANNED_GROUPS_FILE = "banned_groups.json"

def load_banned_groups():
    """
    Tải dữ liệu từ file JSON chứa danh sách nhóm bị cấm giao tiếp với bot.
    Nếu file không tồn tại hoặc lỗi định dạng, trả về danh sách rỗng.
    """
    if not os.path.exists(BANNED_GROUPS_FILE):
        return []
    try:
        with open(BANNED_GROUPS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Lỗi tải danh sách nhóm bị cấm: {str(e)}")
        return []

def save_banned_groups(banned_groups):
    """Lưu danh sách nhóm bị cấm vào file JSON với định dạng UTF-8."""
    with open(BANNED_GROUPS_FILE, "w", encoding="utf-8") as f:
        json.dump(banned_groups, f, ensure_ascii=False, indent=4)

def add_banned_group(group_id, group_name):
    """
    Thêm nhóm vào danh sách cấm dựa theo group_id và group_name.
    Trả về True nếu thêm thành công, False nếu group_id đã tồn tại.
    """
    banned_groups = load_banned_groups()
    for group in banned_groups:
        if group.get("group_id") == group_id:
            return False
    banned_groups.append({"group_id": group_id, "group_name": group_name})
    save_banned_groups(banned_groups)
    return True

def remove_banned_group(group_id):
    """
    Xóa nhóm khỏi danh sách cấm.
    Trả về True nếu xóa thành công, False nếu group_id không tồn tại.
    """
    banned_groups = load_banned_groups()
    for group in banned_groups:
        if group.get("group_id") == group_id:
            banned_groups.remove(group)
            save_banned_groups(banned_groups)
            return True
    return False

def list_banned_groups():
    """Trả về danh sách nhóm bị cấm giao tiếp với bot."""
    return load_banned_groups()

def send_reply_with_style(client, text, message_object, thread_id, thread_type, ttl=30000, color="#000000"):
    """
    Gửi tin nhắn phản hồi với định dạng màu sắc và in đậm.
    TTL được đặt mặc định là 30000.
    """
    base_length = len(text)
    adjusted_length = base_length + 355
    style = MultiMsgStyle([
        MessageStyle(
            offset=0,
            length=adjusted_length,
            style="color",
            color=color,
            auto_format=False
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

def fetch_group_info(target_input, message_object, client, command_prefix):
    """
    Xác định group_id từ tag hoặc tham số nhập và lấy thông tin nhóm từ API.
    Trả về tuple (group_id, group_name) hoặc None nếu có lỗi.
    """
    # Nếu có tag nhóm (nếu API hỗ trợ), ưu tiên sử dụng thông tin từ message_object.mentions
    if message_object.mentions and len(message_object.mentions) > 0:
        group_id = message_object.mentions[0]['uid']
    else:
        group_id = target_input.strip()
    if not group_id:
        return None
    try:
        group_info = client.fetchGroupInfo(group_id)
        group = group_info.gridInfoMap[group_id]
        group_name = group.name
        return group_id, group_name
    except Exception as e:
        print(f"Lỗi fetch thông tin cho group {group_id}: {e}")
        return None

def handle_addbgroup_command(message, message_object, thread_id, thread_type, author_id, client):
    """
    Xử lý lệnh thêm nhóm vào danh sách nhóm bị cấm giao tiếp với bot.
    
    Hỗ trợ:
      - addbgroup <group_id>
      - addbgroup (với tag nhóm, nếu được hỗ trợ)
    
    Cách sử dụng:
      - Ví dụ: `{PREFIX}addbgroup 123456789` để thêm nhóm với ID là 123456789.
      - Hoặc tag nhóm và gõ lệnh: `{PREFIX}addbgroup` (bot sẽ lấy group id từ tag).
    """
    # Kiểm tra quyền admin
    if author_id != ADMIN:
        error_msg = Message(text="❌ Chỉ admin mới có quyền sử dụng lệnh này.")
        client.sendMessage(error_msg, thread_id, thread_type)
        return

    command_prefix = "addbgroup"
    param = message[len(command_prefix):].strip()
    group = fetch_group_info(param, message_object, client, command_prefix)
    if group is None:
        error_msg = Message(text=f"Cú pháp: {PREFIX}addbgroup <group_id> hoặc tag nhóm.\nKhông thể lấy thông tin nhóm.")
        client.sendMessage(error_msg, thread_id, thread_type)
        return

    group_id, group_name = group

    if add_banned_group(group_id, group_name):
        reply_text = f"✅ Đã thêm nhóm:\n👥 {group_name}\n🆔 {group_id}\n vào danh sách nhóm bị cấm giao tiếp với bot."
    else:
        reply_text = f"⚠️ Nhóm: {group_name}\n🆔 {group_id}\n đã tồn tại trong danh sách nhóm bị cấm."
    send_reply_with_style(client, reply_text, message_object, thread_id, thread_type, ttl=30000)

def handle_delbgroup_command(message, message_object, thread_id, thread_type, author_id, client):
    """
    Xử lý lệnh xóa nhóm khỏi danh sách nhóm bị cấm giao tiếp với bot.
    
    Hỗ trợ:
      - delbgroup <group_id>
      - delbgroup (với tag nhóm, nếu được hỗ trợ)
    
    Cách sử dụng:
      - Ví dụ: `{PREFIX}delbgroup 123456789` để xóa nhóm với ID là 123456789.
      - Hoặc tag nhóm và gõ lệnh: `{PREFIX}delbgroup` (bot sẽ lấy group id từ tag).
    """
    # Kiểm tra quyền admin
    if author_id != ADMIN:
        error_msg = Message(text="❌ Chỉ admin mới có quyền sử dụng lệnh này.")
        client.sendMessage(error_msg, thread_id, thread_type)
        return

    command_prefix = "delbgroup"
    param = message[len(command_prefix):].strip()
    group = fetch_group_info(param, message_object, client, command_prefix)
    if group is None:
        error_msg = Message(text=f"Cú pháp: {PREFIX}delbgroup <group_id> hoặc tag nhóm.\nKhông thể lấy thông tin nhóm.")
        client.sendMessage(error_msg, thread_id, thread_type)
        return

    group_id, group_name = group

    if remove_banned_group(group_id):
        reply_text = f"❌ Đã xóa nhóm:\n👥 {group_name}\n🆔 {group_id}\n khỏi danh sách nhóm bị cấm giao tiếp với bot."
    else:
        reply_text = f"⚠️ Nhóm với ID: {group_id} không tồn tại trong danh sách nhóm bị cấm."
    send_reply_with_style(client, reply_text, message_object, thread_id, thread_type, ttl=30000)

def handle_listbgroup_command(message, message_object, thread_id, thread_type, author_id, client):
    """
    Xử lý lệnh xem danh sách nhóm bị cấm giao tiếp với bot.
    
    Cú pháp: listbgroup
    """
    # Kiểm tra quyền admin
    if author_id != ADMIN:
        error_msg = Message(text="❌ Chỉ admin mới có quyền sử dụng lệnh này.")
        client.sendMessage(error_msg, thread_id, thread_type)
        return

    banned_groups = list_banned_groups()
    if not banned_groups:
        reply_text = "Danh sách nhóm bị cấm giao tiếp với bot trống."
    else:
        reply_text = "Danh sách nhóm bị cấm giao tiếp với bot:\n" + "\n".join(
            [f"{i+1}.   {grp['group_name']}\n🆔 {grp['group_id']}" for i, grp in enumerate(banned_groups)]
        )
    send_reply_with_style(client, reply_text, message_object, thread_id, thread_type, ttl=30000)

def get_mitaizl():
    """
    Trả về một dictionary ánh xạ lệnh tới các hàm xử lý tương ứng cho quản lý nhóm bị cấm giao tiếp với bot.
    
    Các lệnh hỗ trợ:
      - addbgroup: Thêm nhóm vào danh sách bị cấm (theo tag hoặc ID)
      - delbgroup: Xóa nhóm khỏi danh sách bị cấm (theo tag hoặc ID)
      - listbgroup: Hiển thị danh sách nhóm bị cấm giao tiếp với bot.
    """
    return {
        'addbgroup': handle_addbgroup_command,
        'delbgroup': handle_delbgroup_command,
        'listbgroup': handle_listbgroup_command
    }
