from zlapi.models import Message
from config import ADMIN

des = {
    'version': "1.0.0",
    'credits': "TRBAYK (NGSON)",
    'description': "Thay đổi cài đặt nhóm."
}

def send_error_message(client, thread_id, thread_type, message):
    error_message = Message(text=message)
    client.sendMessage(error_message, thread_id, thread_type)

def check_admin_permissions(author_id, creator_id, admin_ids):
    all_admin_ids = set(admin_ids)
    all_admin_ids.add(creator_id)
    all_admin_ids.update(ADMIN)
    return author_id in all_admin_ids

def validate_setting(setting):
    valid_settings = {
        "blockname": "blockName",
        "signadminmsg": "signAdminMsg",
        "addmemberonly": "addMemberOnly",
        "settopiconly": "setTopicOnly",
        "enablemsghistory": "enableMsgHistory",
        "lockcreatepost": "lockCreatePost",
        "lockcreatepoll": "lockCreatePoll",
        "joinappr": "joinAppr",
        "locksendmsg": "lockSendMsg",
        "lockviewmember": "lockViewMember",
        "lockgroup": "lockGroup",          # Khóa nhóm
        "listmembers": "listMembers",      # Xem danh sách thành viên
        "groupinfo": "groupInfo"           # Xem thông tin nhóm
    }
    return valid_settings.get(setting.lower())

# Các hàm xử lý cài đặt nhóm
def handle_block_name(action, thread_id, client):
    new_value = 1 if action == "on" else 0 if action == "off" else None
    if new_value is not None:
        client.changeGroupSetting(groupId=thread_id, blockName=new_value)
        return f"Đã {'bật' if new_value == 1 else 'tắt'} tên nhóm thành công."
    return "Hành động không hợp lệ. Vui lòng sử dụng 'on' hoặc 'off'."

def handle_sign_admin_msg(action, thread_id, client):
    new_value = 1 if action == "on" else 0 if action == "off" else None
    if new_value is not None:
        client.changeGroupSetting(groupId=thread_id, signAdminMsg=new_value)
        return f"Đã {'bật' if new_value == 1 else 'tắt'} ghi chú admin thành công."
    return "Hành động không hợp lệ. Vui lòng sử dụng 'on' hoặc 'off'."

def handle_add_member_only(action, thread_id, client):
    new_value = 1 if action == "on" else 0 if action == "off" else None
    if new_value is not None:
        client.changeGroupSetting(groupId=thread_id, addMemberOnly=new_value)
        return f"Đã {'bật' if new_value == 1 else 'tắt'} chế độ chỉ cho phép thêm thành viên thành công."
    return "Hành động không hợp lệ. Vui lòng sử dụng 'on' hoặc 'off'."

def handle_set_topic_only(action, thread_id, client):
    new_value = 1 if action == "on" else 0 if action == "off" else None
    if new_value is not None:
        client.changeGroupSetting(groupId=thread_id, setTopicOnly=new_value)
        return f"Đã {'bật' if new_value == 1 else 'tắt'} chỉ cho phép thay đổi chủ đề thành công."
    return "Hành động không hợp lệ. Vui lòng sử dụng 'on' hoặc 'off'."

def handle_enable_msg_history(action, thread_id, client):
    new_value = 1 if action == "on" else 0 if action == "off" else None
    if new_value is not None:
        client.changeGroupSetting(groupId=thread_id, enableMsgHistory=new_value)
        return f"Đã {'bật' if new_value == 1 else 'tắt'} lịch sử tin nhắn thành công."
    return "Hành động không hợp lệ. Vui lòng sử dụng 'on' hoặc 'off'."

def handle_lock_create_post(action, thread_id, client):
    new_value = 1 if action == "on" else 0 if action == "off" else None
    if new_value is not None:
        client.changeGroupSetting(groupId=thread_id, lockCreatePost=new_value)
        return f"Đã {'bật' if new_value == 1 else 'tắt'} khóa tạo bài viết thành công."
    return "Hành động không hợp lệ. Vui lòng sử dụng 'on' hoặc 'off'."

def handle_lock_create_poll(action, thread_id, client):
    new_value = 1 if action == "on" else 0 if action == "off" else None
    if new_value is not None:
        client.changeGroupSetting(groupId=thread_id, lockCreatePoll=new_value)
        return f"Đã {'bật' if new_value == 1 else 'tắt'} khóa tạo khảo sát thành công."
    return "Hành động không hợp lệ. Vui lòng sử dụng 'on' hoặc 'off'."

def handle_join_appr(action, thread_id, client):
    new_value = 1 if action == "on" else 0 if action == "off" else None
    if new_value is not None:
        client.changeGroupSetting(groupId=thread_id, joinAppr=new_value)
        return f"Đã {'bật' if new_value == 1 else 'tắt'} yêu cầu gia nhập thành công."
    return "Hành động không hợp lệ. Vui lòng sử dụng 'on' hoặc 'off'."

def handle_lock_send_msg(action, thread_id, client):
    new_value = 1 if action == "on" else 0 if action == "off" else None
    if new_value is not None:
        client.changeGroupSetting(groupId=thread_id, lockSendMsg=new_value)
        return f"Đã {'bật' if new_value == 1 else 'tắt'} khóa gửi tin nhắn thành công."
    return "Hành động không hợp lệ. Vui lòng sử dụng 'on' hoặc 'off'."

def handle_lock_view_member(action, thread_id, client):
    new_value = 1 if action == "on" else 0 if action == "off" else None
    if new_value is not None:
        client.changeGroupSetting(groupId=thread_id, lockViewMember=new_value)
        return f"Đã {'bật' if new_value == 1 else 'tắt'} khóa xem thành viên thành công."
    return "Hành động không hợp lệ. Vui lòng sử dụng 'on' hoặc 'off'."

# Các hàm xử lý mới
def handle_lock_group(action, thread_id, client):
    """Khóa hoặc mở khóa nhóm."""
    new_value = 1 if action == "on" else 0 if action == "off" else None
    if new_value is not None:
        client.changeGroupSetting(groupId=thread_id, lockGroup=new_value)
        return f"Nhóm đã {'được khóa' if new_value == 1 else 'mở khóa'} thành công."
    return "Hành động không hợp lệ. Vui lòng sử dụng 'on' hoặc 'off'."

def handle_list_members(thread_id, client):
    """Hiển thị danh sách thành viên trong nhóm."""
    group_info = client.fetchGroupInfo(thread_id)
    if group_info and thread_id in group_info.gridInfoMap:
        group_data = group_info.gridInfoMap[thread_id]
        members = group_data.get('members', [])
        member_list = "\n".join([f"{index}. {member}" for index, member in enumerate(members, start=1)])
        return f"Danh sách thành viên:\n{member_list}"
    return "Không thể lấy danh sách thành viên."

def handle_group_info(thread_id, client):
    """Hiển thị thông tin nhóm."""
    group_info = client.fetchGroupInfo(thread_id)
    if group_info and thread_id in group_info.gridInfoMap:
        group_data = group_info.gridInfoMap[thread_id]
        members_count = group_data.get('totalMember')
        last_message = group_data.get('lastMessage', 'Không có tin nhắn gần đây.')
        
        msg = f"Thông tin nhóm:\n"
        msg += f"- Số lượng thành viên: {members_count}\n"
        msg += f"- Tin nhắn gần đây: {last_message}"
        return msg
    return "Không thể lấy thông tin nhóm."

# Hàm chính để xử lý lệnh
def handle_group_setting_command(message, message_object, thread_id, thread_type, author_id, client):
    text = message.split()
    # Gửi phản ứng ngay khi người dùng soạn đúng lệnh
    action = "✅"
    client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)

    if len(text) < 3:
        error_message = Message(text="Vui lòng sử dụng cú pháp: grsetting <setting> <on/off>.\n\n"
                                      "Các cài đặt hợp lệ bao gồm:\n\n"
                                      "⭕ blockname: Bật/tắt việc thay đổi tên nhóm.\n\n"
                                      "⭕ signadminmsg: Bật/tắt ghi chú admin trong tin nhắn.\n\n"
                                      "⭕ addmemberonly: Bật/tắt chế độ chỉ cho phép thêm thành viên.\n\n"
                                      "⭕ settopiconly: Bật/tắt việc chỉ cho phép thay đổi chủ đề.\n\n"
                                      "⭕ enablemsghistory: Bật/tắt lịch sử tin nhắn trong nhóm.\n\n"
                                      "⭕ lockcreatepost: Bật/tắt việc khóa tạo bài viết.\n\n"
                                      "⭕ lockcreatepoll: Bật/tắt việc khóa tạo khảo sát.\n\n"
                                      "⭕ joinappr: Bật/tắt yêu cầu phê duyệt khi gia nhập nhóm.\n\n"
                                      "⭕ locksendmsg: Bật/tắt việc khóa gửi tin nhắn.\n\n"
                                      "⭕ lockviewmember: Bật/tắt việc khóa xem danh sách thành viên.\n\n"
                                      "⭕ lockgroup: Bật/tắt khóa nhóm.\n\n"
                                      "⭕ listmembers: Xem danh sách thành viên.\n\n"
                                      "⭕ groupinfo: Xem thông tin nhóm.\n\n"
                                      "⭕ active: Kiểm tra các tính năng hiện tại.\n\n"
                                      "⭕ promote:Nâng cấp thành viên lên admin nhóm " )
        client.replyMessage(error_message, message_object, thread_id, thread_type)
        return

    setting = text[1].lower()
    action = text[2].lower() if len(text) > 2 else None
    #Nâng cấp thành viên lên admin nhóm 
    if setting == "promote" and action:
        member_id = action
        result_message = handle_promote_to_admin(member_id, thread_id, client)
        client.replyMessage(Message(text=result_message), message_object, thread_id, thread_type)
    
    # Kiểm tra nếu lệnh yêu cầu liệt kê các tính năng hiện tại
    if setting == "active":
        result_message = handle_list_active_settings(thread_id, client)
        client.replyMessage(Message(text=result_message), message_object, thread_id, thread_type)
        return

    group_info = client.fetchGroupInfo(thread_id)
    if not group_info or thread_id not in group_info.gridInfoMap:
        send_error_message(client, thread_id, thread_type, "Không thể lấy thông tin nhóm.")
        return

    group_data = group_info.gridInfoMap[thread_id]
    creator_id = group_data.get('creatorId')
    admin_ids = group_data.get('adminIds', [])

    if not check_admin_permissions(author_id, creator_id, admin_ids):
        send_error_message(client, thread_id, thread_type, "Chỉ admin mới có thể sử dụng.")
        return

    setting_action_map = {
        "blockname": handle_block_name,
        "signadminmsg": handle_sign_admin_msg,
        "addmemberonly": handle_add_member_only,
        "settopiconly": handle_set_topic_only,
        "enablemsghistory": handle_enable_msg_history,
        "lockcreatepost": handle_lock_create_post,
        "lockcreatepoll": handle_lock_create_poll,
        "joinappr": handle_join_appr,
        "locksendmsg": handle_lock_send_msg,
        "lockviewmember": handle_lock_view_member,
        "lockgroup": handle_lock_group,           # Khóa nhóm
        "listmembers": handle_list_members,       # Xem danh sách thành viên
        "groupinfo": handle_group_info            # Xem thông tin nhóm
    }

    setting_func = validate_setting(setting)
    if not setting_func:
        send_error_message(client, thread_id, thread_type, "Cài đặt không hợp lệ. Vui lòng sử dụng một trong các cài đặt hợp lệ.")
        return

    # Nếu là các cài đặt yêu cầu 'on/off', thực hiện thao tác
    if action:
        result_message = setting_action_map[setting](action, thread_id, client)
    else:
        result_message = setting_action_map[setting](thread_id, client)
    
    send_error_message(client, thread_id, thread_type, result_message)

def get_mitaizl():
    return {
        'gr': handle_group_setting_command
    }
