import requests
import urllib.parse
import tempfile
import os
from zlapi.models import Message, MultiMsgStyle, MessageStyle

des = {
    'tác giả': "Rosy",
    'mô tả': "Tìm kiếm thông tin tài khoản TikTok",
    'tính năng': [
        "🔍 Tìm kiếm thông tin tài khoản TikTok dựa trên username.",
        "📄 Hiển thị thông tin chi tiết về tài khoản (ID, tên hiển thị, tên người dùng, số người theo dõi, lượt thích, số video, trạng thái xác thực, bảo mật, cài đặt, liên kết mạng xã hội, ...).",
        "❗ Thông báo lỗi cụ thể nếu có vấn đề xảy ra khi gọi API."
    ],
    'hướng dẫn sử dụng': [
        "📩 Gửi lệnh: ttinfo <username> để tìm kiếm thông tin tài khoản TikTok.",
        "📌 Ví dụ: ttinfo dungkon2002",
        "✅ Nhận thông báo trạng thái và kết quả ngay lập tức."
    ]
}

def format_number(num):
    """
    Định dạng số theo kiểu có dấu chấm phân cách hàng nghìn, ví dụ: 1000 -> '1.000'
    Nếu giá trị không phải số, trả về nguyên giá trị đó.
    """
    try:
        return f"{int(num):,}".replace(",", ".")
    except (ValueError, TypeError):
        return num

def handle_tiktok_info_command(message, message_object, thread_id, thread_type, author_id, client):
    # Gửi phản ứng ngay khi nhận được lệnh
    action = "✅"
    client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)

    content = message.strip().split()
    if len(content) < 2:
        menu_message = "Hãy nhập username của tài khoản TikTok cần tìm kiếm\nCú pháp: ttinfo <username>"
        style = MultiMsgStyle([
            MessageStyle(offset=0, length=len(menu_message), style="color", color="#15a85f", auto_format=False),
            MessageStyle(offset=0, length=len(menu_message), style="font", size="16", auto_format=False)
        ])
        error_message = Message(text=menu_message, style=style)
        client.replyMessage(error_message, message_object, thread_id, thread_type, ttl=60000)
        return

    username = " ".join(content[1:]).strip()
    try:
        encoded_username = urllib.parse.quote(username)
        api_url = f"https://api.sumiproject.net/tiktok?info={encoded_username}"
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()

        # Kiểm tra kết quả trả về từ API
        if data.get("code") != 0 or "data" not in data or "user" not in data["data"]:
            error_message = Message(text="Không tìm thấy thông tin tài khoản TikTok cho username đã cung cấp.")
            client.replyMessage(error_message, message_object, thread_id, thread_type, ttl=60000)
            return

        user = data["data"]["user"]
        stats = data["data"].get("stats", {})

        # Xây dựng nội dung tin nhắn với thông tin tài khoản (đã dịch sang tiếng Việt)
        info_text = (
            f"🆔 Tên hiển thị      : {user.get('nickname', 'N/A')}\n"
            f"👤 Tên người dùng    : @{user.get('uniqueId', 'N/A')}\n"
            f"🔖 ID                : {user.get('id', 'N/A')}\n"
            f"✅ Đã xác thực       : {user.get('verified', 'N/A')}\n\n"
            
            f"👥 Người theo dõi    : {format_number(stats.get('followerCount', 'N/A'))}\n"
            f"🔄 Đang theo dõi     : {format_number(stats.get('followingCount', 'N/A'))}\n"
            f"❤️ Số lượt thích     : {format_number(stats.get('heartCount', 'N/A'))}\n"
            f"🎥 Số video          : {format_number(stats.get('videoCount', 'N/A'))}\n\n"
            
            f"🆔 SecUid            : {user.get('secUid', 'N/A')}\n"
            f"🔒 Bí mật           : {user.get('secret', 'N/A')}\n"
            f"🎤 Cài đặt Duet      : {user.get('duetSetting', 'N/A')}\n"
            f"✂️  Cài đặt Stitch    : {user.get('stitchSetting', 'N/A')}\n"
            f"💬 Cài đặt Bình luận : {user.get('commentSetting', 'N/A')}\n"
            f"💖 Cho phép Yêu thích: {user.get('openFavorite', 'N/A')}\n\n"
            
            f"🔒 Tài khoản riêng tư : {user.get('privateAccount', 'N/A')}\n"
            f"📢 Quảng cáo ảo      : {user.get('isADVirtual', 'N/A')}\n"
            f"🚸 Dưới 18 tuổi      : {user.get('isUnderAge18', 'N/A')}\n\n"
            
            f"▶️ Kênh YouTube      : {user.get('youtube_channel_title', 'N/A')}\n"
            f"🆔 YouTube ID       : {user.get('youtube_channel_id', 'N/A')}\n"
            f"🐦 Twitter ID       : {user.get('twitter_id', 'N/A')}\n"
            f"📸 INS ID           : {user.get('ins_id', 'N/A')}\n\n"
            
            f"💞 Quan hệ           : {user.get('relation', 'N/A')}\n"
            f"⚖️  FTC               : {user.get('ftc', 'N/A')}\n\n"
            
            f"📝 Chữ ký          : {user.get('signature', 'N/A')}"
        )


        # Lấy URL avatar kích thước lớn (avatarLarger) từ kết quả API
        avatar_url = user.get("avatarLarger")
        if avatar_url:
            try:
                # Tải ảnh avatar về và lưu vào file tạm thời
                avatar_response = requests.get(avatar_url)
                avatar_response.raise_for_status()
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                    tmp_file.write(avatar_response.content)
                    temp_image_path = tmp_file.name
            except Exception as e:
                # Nếu tải ảnh không thành công, sẽ gửi tin nhắn chỉ có info_text
                temp_image_path = None
        else:
            temp_image_path = None

        result_message = Message(text=info_text)

        # Nếu có file ảnh avatar tạm, sử dụng sendLocalImage để gửi kèm info_text
        if temp_image_path:
            client.sendLocalImage(
                imagePath=temp_image_path,
                thread_id=thread_id,
                thread_type=thread_type,
                message=result_message
            )
            # Xóa file tạm sau khi gửi
            os.remove(temp_image_path)
        else:
            # Nếu không có ảnh, gửi chỉ tin nhắn thông tin
            client.replyMessage(result_message, message_object, thread_id, thread_type, ttl=86400000)

    except requests.exceptions.RequestException as e:
        error_message = Message(text=f"Đã xảy ra lỗi khi gọi API: {str(e)}")
        client.replyMessage(error_message, message_object, thread_id, thread_type, ttl=60000)
    except Exception as e:
        error_message = Message(text=f"Đã xảy ra lỗi không xác định: {str(e)}")
        client.replyMessage(error_message, message_object, thread_id, thread_type, ttl=60000)

def get_mitaizl():
    return {
        'ttinfo': handle_tiktok_info_command
    }
