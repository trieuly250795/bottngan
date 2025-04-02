import time
from zlapi.models import Message, Mention, ZaloAPIException, ThreadType
from config import ADMIN

des = {
    'tác giả': "Rosy",
    'mô tả': "Gửi tin nhắn đến danh sách nhóm",
    'tính năng': [
        "📨 Gửi tin nhắn đến các nhóm bằng link nhóm Zalo.",
        "🔍 Kiểm tra định dạng link nhóm và xử lý lỗi liên quan.",
        "🔗 Gửi tin nhắn với nội dung chỉ định đến các nhóm đã nhập.",
        "🔒 Kiểm tra quyền admin trước khi thực hiện lệnh.",
        "📝 Hiển thị kết quả tổng hợp của việc gửi tin nhắn."
    ],
    'hướng dẫn sử dụng': [
        "📩 Gửi lệnh sendnhom <link1> <link2> ... | <nội dung> để gửi tin nhắn đến danh sách nhóm.",
        "📌 Ví dụ: sendnhom https://zalo.me/group1 https://zalo.me/group2 | Chào các bạn! để gửi tin nhắn 'Chào các bạn!' đến các nhóm được liệt kê.",
        "✅ Nhận thông báo trạng thái và kết quả gửi tin nhắn ngay lập tức."
    ]
}

def handle_sendnhom_command(message, message_object, thread_id, thread_type, author_id, client):
    # Kiểm tra quyền admin
    if author_id not in ADMIN:
        client.replyMessage(
            Message(text="🚫 Bạn không có quyền sử dụng lệnh này!"),
            message_object, thread_id, thread_type
        )
        print("🚫 Người dùng không có quyền sử dụng lệnh này!")
        return
    
    try:
        # Loại bỏ tiền tố lệnh "sendnhom" và tách chuỗi theo ký tự "|" để lấy danh sách link nhóm và nội dung tin nhắn
        command_body = message[len("sendnhom"):].strip()
        parts = command_body.split("|")

        # Kiểm tra số lượng phần tử trong lệnh
        if len(parts) < 2:
            client.replyMessage(
                Message(text="⚠️ Vui lòng cung cấp đầy đủ thông tin theo định dạng:\nsendnhom link1 link2 ... | nội dung tin nhắn"),
                message_object, thread_id, thread_type, ttl=10000
            )
            print("⚠️ Thiếu thông tin: yêu cầu định dạng: sendnhom link1 link2 ... | nội dung tin nhắn")
            return
        
        # Phần đầu: danh sách các link nhóm (cách nhau bởi khoảng trắng)
        group_links_str = parts[0].strip()
        if not group_links_str:
            client.replyMessage(
                Message(text="⚠️ Vui lòng cung cấp ít nhất 1 link nhóm!"),
                message_object, thread_id, thread_type, ttl=10000
            )
            print("⚠️ Không có link nhóm được cung cấp!")
            return
        
        group_links = group_links_str.split()
        
        # Kiểm tra tính hợp lệ của từng link nhóm
        for url in group_links:
            if not url.startswith("https://zalo.me/"):
                client.replyMessage(
                    Message(text=f"⛔ Link không hợp lệ: {url}. Link phải bắt đầu bằng https://zalo.me/"),
                    message_object, thread_id, thread_type
                )
                print(f"⛔ Link không hợp lệ: {url}. Link phải bắt đầu bằng https://zalo.me/")
                return
        
        # Phần thứ hai: nội dung tin nhắn cần gửi (không để trống)
        message_content = parts[1].strip()
        if not message_content:
            client.replyMessage(
                Message(text="⚠️ Nội dung tin nhắn không được để trống!"),
                message_object, thread_id, thread_type, ttl=10000
            )
            print("⚠️ Nội dung tin nhắn không được để trống!")
            return
        
        # Thông báo đã nhận lệnh và in ra terminal
        client.replyMessage(
            Message(text="🔄 Đã nhận lệnh gửi tin nhắn đến các nhóm..."),
            message_object, thread_id, thread_type, ttl=5000
        )
        print("🔄 Đã nhận lệnh gửi tin nhắn đến các nhóm...")
        time.sleep(2)

        results = []
        for url in group_links:
            print(f"⏳ Đang xử lý nhóm: {url}")
            
            # Tham gia nhóm
            join_result = client.joinGroup(url)
            if not join_result:
                msg = f"❌ Không thể tham gia nhóm: {url}"
                results.append(msg)
                print(msg)
                continue
            time.sleep(2)

            # Lấy thông tin nhóm
            group_info = client.getiGroup(url)
            if not isinstance(group_info, dict) or 'groupId' not in group_info:
                msg = f"❌ Không lấy được thông tin nhóm: {url}"
                results.append(msg)
                print(msg)
                continue

            group_id = group_info['groupId']
            time.sleep(2)

            # Gửi tin nhắn cho nhóm
            mention = Mention("-1", length=len(message_content), offset=0)
            client.send(
                Message(text=message_content, mention=mention),
                group_id, ThreadType.GROUP, ttl=100000
            )
            time.sleep(1.5)
            msg = f"✅ Đã gửi tin nhắn đến nhóm {group_id}"
            results.append(msg)
            print(msg)

        # Gửi kết quả tổng hợp về cho người dùng và in kết quả ra terminal
        result_text = "\n".join(results)
        client.replyMessage(
            Message(text=result_text),
            message_object, thread_id, thread_type, ttl=180000
        )
        print("Kết quả tổng hợp:")
        print(result_text)

    except ZaloAPIException as e:
        error_msg = f"❌ Lỗi API: {str(e)}"
        client.replyMessage(
            Message(text=error_msg),
            message_object, thread_id, thread_type
        )
        print(error_msg)
    except Exception as e:
        error_msg = f"❌ Lỗi: {str(e)}"
        client.replyMessage(
            Message(text=error_msg),
            message_object, thread_id, thread_type
        )
        print(error_msg)

def get_mitaizl():
    return {
        'sendnhom': handle_sendnhom_command
    }
