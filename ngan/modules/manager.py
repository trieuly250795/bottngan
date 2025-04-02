import json
import os
import random

from zlapi.models import Message, MessageStyle, MultiMsgStyle
from config import ADMIN, PREFIX

# Đường dẫn file lưu trữ danh sách nhóm
GROUP_FILE = "danhsachnhom.json"

def load_groups():
    """
    Tải dữ liệu từ file JSON chứa danh sách nhóm.
    Nếu file không tồn tại hoặc lỗi định dạng, trả về danh sách rỗng.
    """
    if not os.path.exists(GROUP_FILE):
        return []
    try:
        with open(GROUP_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Lỗi tải danh sách nhóm: {str(e)}")
        return []

def save_groups(groups):
    """Lưu danh sách nhóm vào file JSON với định dạng UTF-8."""
    with open(GROUP_FILE, "w", encoding="utf-8") as f:
        json.dump(groups, f, ensure_ascii=False, indent=4)

def add_group(group_id, group_name):
    """
    Thêm nhóm vào danh sách với thông tin tên và id.
    Trả về True nếu thêm thành công, False nếu group id đã tồn tại.
    """
    groups = load_groups()
    for group in groups:
        if group.get("group_id") == group_id:
            return False
    groups.append({"group_id": group_id, "group_name": group_name})
    save_groups(groups)
    return True

def remove_group(group_id):
    """
    Xóa nhóm khỏi danh sách.
    Trả về True nếu xóa thành công, False nếu group id không tồn tại.
    """
    groups = load_groups()
    for group in groups:
        if group.get("group_id") == group_id:
            groups.remove(group)
            save_groups(groups)
            return True
    return False

def list_groups():
    """Trả về danh sách nhóm."""
    return load_groups()

def send_reply_with_style(client, text, message_object, thread_id, thread_type, ttl=None, color="#db342e"):
    """
    Gửi tin nhắn phản hồi với định dạng màu sắc và in đậm.
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
    msg = Message(text=text, style=style)
    if ttl is not None:
        client.replyMessage(msg, message_object, thread_id, thread_type, ttl=ttl)
    else:
        client.replyMessage(msg, message_object, thread_id, thread_type)

def handle_addgroup_command(message, message_object, thread_id, thread_type, author_id, client):
    """
    Xử lý lệnh thêm nhóm.
    Cú pháp: addgroup <group_id>
    """
    command_prefix = "addgroup"
    content = message[len(command_prefix):].strip()
    if not content:
        error_msg = Message(text="Cú pháp: addgroup <group_id>")
        client.sendMessage(error_msg, thread_id, thread_type)
        return

    group_id_input = content.strip()
    # Lấy thông tin nhóm dựa vào group_id_input
    try:
        group_info = client.fetchGroupInfo(group_id_input)
        group = group_info.gridInfoMap[group_id_input]
        group_name = group.name
    except Exception as e:
        error_msg = Message(text="Không thể lấy thông tin nhóm.")
        client.sendMessage(error_msg, thread_id, thread_type)
        return

    if add_group(group_id_input, group_name):
        reply_text = f"✅ Đã thêm nhóm:\n👥 {group_name}\n🆔 {group_id_input}\n vào danh sách không gửi link"
    else:
        reply_text = f"⚠️ Nhóm: {group_name} \n🆔 {group_id_input}) đã tồn tại."
    send_reply_with_style(client, reply_text, message_object, thread_id, thread_type, ttl=120000)

def handle_delgroup_command(message, message_object, thread_id, thread_type, author_id, client):
    """
    Xử lý lệnh xóa nhóm.
    Cú pháp: delgroup <group_id>
    """
    command_prefix = "delgroup"
    content = message[len(command_prefix):].strip()
    if not content:
        error_msg = Message(text="Cú pháp: delgroup <group_id>")
        client.sendMessage(error_msg, thread_id, thread_type)
        return

    group_id_input = content.strip()
    # Tìm tên nhóm từ danh sách đã lưu
    groups = list_groups()
    group_name = None
    for grp in groups:
        if grp.get("group_id") == group_id_input:
            group_name = grp.get("group_name")
            break

    if remove_group(group_id_input):
        if group_name is None:
            group_name = group_id_input
        reply_text = f"❌ Đã xóa nhóm\n👥 {group_name}\n🆔 {group_id_input}\n khỏi danh sách không gửi link "
    else:
        reply_text = f"⚠️ Nhóm với ID: {group_id_input} không tồn tại."
    send_reply_with_style(client, reply_text, message_object, thread_id, thread_type, ttl=120000)

def handle_listgroup_command(message, message_object, thread_id, thread_type, author_id, client):
    """
    Xử lý lệnh xem danh sách nhóm.
    Cú pháp: listgroup
    """
    groups = list_groups()
    if not groups:
        reply_text = "Danh sách không gửi link nhóm trống."
    else:
        reply_text = "Danh sách nhóm không gửi link vào:\n" + "\n".join(
            [f"{i+1}.   {grp['group_name']}\n🆔  {grp['group_id']}" for i, grp in enumerate(groups)])
    send_reply_with_style(client, reply_text, message_object, thread_id, thread_type, ttl=120000)

def get_mitaizl():
    """
    Trả về một dictionary ánh xạ lệnh tới các hàm xử lý tương ứng.
    """
    return {
        'addgroup': handle_addgroup_command,
        'delgroup': handle_delgroup_command,
        'listgroup': handle_listgroup_command
    }
