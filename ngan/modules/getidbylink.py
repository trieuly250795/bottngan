import re
from zlapi.models import Message, ZaloAPIException, ThreadType
from config import ADMIN
import time

des = {
    'tác giả': "Rosy",
    'mô tả': "Lấy ID nhóm thông qua phương thức geti mà không cần tham gia nhóm. Hỗ trợ xử lý nhiều liên kết cùng lúc, kể cả khi lệnh chứa thêm văn bản mô tả.",
    'tính năng': [
        "🔍 Kiểm tra quyền hạn của người dùng trước khi thực hiện lệnh",
        "🔗 Xác minh và kiểm tra tính hợp lệ của liên kết nhóm Zalo",
        "📡 Lấy thông tin nhóm qua phương thức geti mà không cần tham gia nhóm",
        "📝 Hỗ trợ xử lý nhiều liên kết nhóm cùng lúc (trích xuất từ văn bản có chứa mô tả)",
        "📩 Trả về tin nhắn chứa danh sách Group ID tương ứng với từng link (mỗi ID ở 1 dòng)",
        "⏱ Thêm thời gian trễ 1 giây giữa các yêu cầu và trước khi gửi kết quả",
        "🎉 Phản ứng khi nhận lệnh, in tiến trình ra terminal và gửi tin nhắn bắt đầu & hoàn thành"
    ],
    'hướng dẫn sử dụng': [
        "📩 Gửi lệnh: getidbylink <nội dung chứa các liên kết nhóm>",
        "✅ Bot sẽ phản ứng khi nhận lệnh, gửi tin nhắn bắt đầu, in tiến trình ra terminal, và cuối cùng gửi 1 tin nhắn chứa danh sách Group ID (mỗi ID ở 1 dòng) sau khi hoàn thành"
    ]
}

def handle_getidbylink_command(message, message_object, thread_id, thread_type, author_id, client):
    # Kiểm tra quyền sử dụng lệnh
    if author_id not in ADMIN:
        client.replyMessage(
            Message(text="🚫 Bạn không có quyền sử dụng lệnh này!"),
            message_object, thread_id, thread_type
        )
        print("[WARNING] Người dùng không có quyền sử dụng lệnh.")
        return

    # Gửi tin nhắn bắt đầu
    client.replyMessage(
        Message(text="🚀 Bắt đầu lấy thông tin nhóm..."),
        message_object, thread_id, thread_type
    )
    print("[START] Đang bắt đầu lấy thông tin nhóm...")

    try:
        # Trích xuất tất cả các liên kết hợp lệ từ nội dung tin nhắn
        links = re.findall(r"https://zalo\.me/g/\S+", message)
        if not links:
            client.replyMessage(
                Message(text="⚠️ Không tìm thấy liên kết hợp lệ nào trong lệnh!"),
                message_object, thread_id, thread_type, ttl=10000
            )
            print("[ERROR] Không tìm thấy liên kết hợp lệ nào.")
            return

        result_lines = []

        for url in links:
            url = url.strip()
            print(f"[INFO] Đang lấy thông tin nhóm từ: {url}")
            time.sleep(1)  # Thời gian trễ trước khi gửi yêu cầu
            group_info = client.getiGroup(url)
            if not isinstance(group_info, dict) or 'groupId' not in group_info:
                result_lines.append(f"❌ {url}: Không lấy được thông tin nhóm!")
                print(f"[ERROR] Không lấy được thông tin nhóm từ: {url}")
            else:
                group_id = group_info['groupId']
                result_lines.append(f"{group_id}")
                print(f"[SUCCESS] Lấy được Group ID {group_id} từ: {url}")
            time.sleep(1)  # Thời gian trễ giữa các yêu cầu

        time.sleep(1)  # Thời gian trễ trước khi gửi kết quả tổng hợp
        final_message = "✅ Hoàn thành lấy thông tin nhóm. Kết quả:\n" + "\n".join(result_lines)
        client.replyMessage(
            Message(text=final_message),
            message_object, thread_id, thread_type, ttl=180000
        )
        print("[COMPLETE] Đã gửi kết quả về cho người dùng.")

    except ZaloAPIException as e:
        client.replyMessage(
            Message(text=f"❌ Lỗi API: {str(e)}"),
            message_object, thread_id, thread_type
        )
        print(f"[EXCEPTION] Lỗi API: {str(e)}")
    except Exception as e:
        client.replyMessage(
            Message(text=f"❌ Lỗi: {str(e)}"),
            message_object, thread_id, thread_type
        )
        print(f"[EXCEPTION] Lỗi: {str(e)}")

def get_mitaizl():
    return {
        'getidbylink': handle_getidbylink_command
    }
