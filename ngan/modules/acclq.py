import random
import time
import chardet
from zlapi.models import Message, MultiMsgStyle, MessageStyle  # đảm bảo đã import các lớp style

des = {
    'tác giả': "Rosy",
    'mô tả': "Gửi tài khoản Liên Quân miễn phí",
    'tính năng': [
        "📨 Gửi tài khoản Liên Quân miễn phí từ danh sách có sẵn.",
        "🔍 Kiểm tra quyền admin và thời gian cooldown trước khi gửi tài khoản.",
        "📝 Đọc và ghi danh sách tài khoản từ file.",
        "🔔 Thông báo lỗi cụ thể nếu có vấn đề xảy ra khi xử lý yêu cầu."
    ],
    'hướng dẫn sử dụng': [
        "📩 Gửi lệnh acclq để nhận tài khoản Liên Quân miễn phí.",
        "📌 Ví dụ: acclq để nhận tài khoản Liên Quân.",
        "✅ Nhận thông báo trạng thái và kết quả ngay lập tức."
    ]
}

# Danh sách ID admin
ADMIN_IDS = ['2670654904430771575']
# Cooldown giữa các lần lấy tài khoản (5 phút)
COOLDOWN_SECONDS = 10 * 60  
# Lưu thời gian sử dụng của từng người
user_cooldowns = {}

# Đường dẫn file chứa danh sách tài khoản
ACCOUNT_FILE_PATH = 'accounts.txt'

def detect_file_encoding(file_path):
    """Tự động phát hiện mã hóa file để đọc đúng dữ liệu."""
    try:
        with open(file_path, 'rb') as file:
            raw_data = file.read()
        result = chardet.detect(raw_data)
        return result["encoding"]
    except Exception as e:
        print(f"Lỗi khi phát hiện mã hóa file: {str(e)}")
        return 'utf-8'

def read_accounts_from_file(file_path):
    """Đọc danh sách tài khoản từ file."""
    try:
        encoding = detect_file_encoding(file_path)
        with open(file_path, 'r', encoding=encoding) as file:
            accounts = file.readlines()
        # Loại bỏ các dòng trống và khoảng trắng thừa
        return [account.strip() for account in accounts if account.strip()]
    except Exception as e:
        print(f"Lỗi khi đọc file: {str(e)}")
        return []

def write_accounts_to_file(file_path, accounts):
    """Ghi danh sách tài khoản còn lại vào file."""
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            for account in accounts:
                file.write(account + "\n")
    except Exception as e:
        print(f"Lỗi khi ghi file: {str(e)}")

def parse_account_info(account_str):
    """
    Chuyển đổi chuỗi tài khoản thành dictionary.
    
    Định dạng mong đợi (các trường cách nhau bởi ký tự '|' và các trường sau có định dạng 'LABEL : giá trị'):
      Tài khoản|Mật khẩu|NAME : ...|RANK : ...|LEVEL : ...|TƯỚNG : ...|SKIN : ...|...
    
    Nếu một số trường không có, thì sẽ được gán giá trị rỗng.
    """
    parts = [p.strip() for p in account_str.split('|') if p.strip()]
    
    keys = [
        "Tài khoản", "Mật khẩu", "Tên", "Rank", "Level", "Tướng", "Skin",
        "Quân Huy", "Lịch sử nạp", "Sò", "CMND", "Email", "Tình trạng Email",
        "Authen", "SĐT", "Facebook", "BAND", "Ngày đăng ký", "Region",
        "Đăng nhập lần cuối", "SS", "SSS", "Anime", "Hot", "Tình trạng"
    ]
    
    account_info = {}
    for i, key in enumerate(keys):
        if i < len(parts):
            part = parts[i]
            if ':' in part:
                # Tách phần label và value; chỉ tách phần đầu tiên gặp dấu ':'
                _, value = part.split(':', 1)
                account_info[key] = value.strip()
            else:
                account_info[key] = part.strip()
        else:
            # Nếu không có phần nào cho key này, gán chuỗi rỗng
            account_info[key] = ""
    
    return account_info

def send_message_with_style(client, text, thread_id, thread_type, color="#000000", font_size="6", ttl=60000):
    """
    Gửi tin nhắn với định dạng màu sắc và cỡ chữ.
    """
    if not text:
        return  # Tránh gửi tin nhắn rỗng

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
            style="font",
            size=font_size,
            auto_format=False
        )
    ])
    client.send(Message(text=text, style=style), thread_id=thread_id, thread_type=thread_type, ttl=ttl)

def handle_send_accounts_command(message, message_object, thread_id, thread_type, author_id, client):
    # Gửi phản ứng ngay khi người dùng soạn đúng lệnh
    action = "✅"
    client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)
    """Xử lý lệnh gửi tài khoản."""
    try:
        # Kiểm tra cooldown nếu người dùng không phải admin
        if author_id not in ADMIN_IDS:
            now = time.time()
            if author_id in user_cooldowns:
                elapsed = now - user_cooldowns[author_id]
                if elapsed < COOLDOWN_SECONDS:
                    remaining = int(COOLDOWN_SECONDS - elapsed)
                    minutes = remaining // 60
                    seconds = remaining % 60
                    send_message_with_style(
                        client,
                        f"Bạn phải đợi {minutes} phút {seconds} giây nữa mới có thể lấy acc tiếp",
                        thread_id,
                        thread_type,
                        ttl=10000
                    )
                    return
            user_cooldowns[author_id] = now

        # Đọc danh sách tài khoản từ file
        accounts = read_accounts_from_file(ACCOUNT_FILE_PATH)
        if not accounts:
            send_message_with_style(client, "Không thể đọc danh sách tài khoản hoặc danh sách đã hết.", thread_id, thread_type, ttl=30000)
            return

        # Chọn một tài khoản ngẫu nhiên và xoá khỏi danh sách
        selected_account = random.choice(accounts)
        accounts.remove(selected_account)
        write_accounts_to_file(ACCOUNT_FILE_PATH, accounts)

        # Phân tích thông tin tài khoản
        account_info = parse_account_info(selected_account)
        if not account_info:
            send_message_with_style(client, "Định dạng tài khoản không hợp lệ.", thread_id, thread_type)
            return

        # Tạo nội dung tin nhắn gửi tài khoản với đầy đủ các thông tin
        message_to_send = (
            "🎮 𝐀𝐂𝐂 𝐋𝐈𝐄̂𝐍 𝐐𝐔𝐀̂𝐍 𝐌𝐈𝐄̂̃𝐍 𝐏𝐇𝐈́ 🎮\n"
            "⚠️ ACC LQ SẼ BỊ XÓA SAU 3 PHÚT\n"
            "⚠️ VUI LÒNG LƯU LẠI\n"
            "⚠️ Hãy cảm ơn admin Quách Hoàng Hà đã tài trợ\n"
            "⚠️ Acc đã lấy sẽ tự xóa khỏi kho acc để tránh trùng nhau\n"
            "🔄 Acc random free tỉ lệ : Acc đen 95% / Acc trắng 3% / Acc Vip 2%\n"
            f"🔢 𝐒𝐨̂́ 𝐚𝐜𝐜 𝐜𝐨̀𝐧 𝐥𝐚̣𝐢 𝐜𝐮̉𝐚 𝐛𝐨𝐭: {len(accounts)}\n"
            "------------------------------------------------------\n"
            f"👤 Tài khoản: {account_info.get('Tài khoản', 'Không rõ')}\n"
            f"🔒 Mật khẩu: {account_info.get('Mật khẩu', 'Không rõ')}\n"
            f"📝 Tên nhân vật: {account_info.get('Tên', 'Không rõ')}\n"
            f"⭐ Rank: {account_info.get('Rank', 'Không rõ')}\n"
            f"📈 Cấp: {account_info.get('Level', 'Không rõ')}\n"
            f"🛡️ Tướng: {account_info.get('Tướng', 'Không rõ')}\n"
            f"🎨 Skin: {account_info.get('Skin', 'Không rõ')}\n"
            f"🆔 CMND: {account_info.get('CMND', 'Không rõ')}\n"
            f"🏅 Quân Huy: {account_info.get('Quân Huy', 'Không rõ')}\n"
            f"💰 Lịch sử nạp: {account_info.get('Lịch sử nạp', 'Không rõ')}\n"
            f"🐚 Sò: {account_info.get('Sò', 'Không rõ')}\n"
            f"📧 Email: {account_info.get('Email', 'Không rõ')}\n"
            f"📩 Tình trạng Email: {account_info.get('Tình trạng Email', 'Không rõ')}\n"
            f"🔐 Authen: {account_info.get('Authen', 'Không rõ')}\n"
            f"📞 SĐT: {account_info.get('SĐT', 'Không rõ')}\n"
            f"📘 Facebook: {account_info.get('Facebook', 'Không rõ')}\n"
            f"🚫 BAND: {account_info.get('BAND', 'Không rõ')}\n"
            f"📅 Ngày đăng ký: {account_info.get('Ngày đăng ký', 'Không rõ')}\n"
            f"🌍 Region: {account_info.get('Region', 'Không rõ')}\n"
            f"⏰ Đăng nhập lần cuối: {account_info.get('Đăng nhập lần cuối', 'Không rõ')}\n"
            f"🖥️ SS: {account_info.get('SS', 'Không rõ')}\n"
            f"🖥️ SSS: {account_info.get('SSS', 'Không rõ')}\n"
            f"🎥 Anime: {account_info.get('Anime', 'Không rõ')}\n"
            f"🔥 Hot: {account_info.get('Hot', 'Không rõ')}\n"
            f"⚙️ Tình trạng: {account_info.get('Tình trạng', 'Không rõ')}\n"
        )

        send_message_with_style(client, message_to_send, thread_id, thread_type, ttl=180000)
        print(f"Đã gửi 1 tài khoản cho người dùng {author_id}")

    except Exception as e:
        error_message = f"Lỗi khi gửi tài khoản: {str(e)}"
        send_message_with_style(client, error_message, thread_id, thread_type)

    # Gửi reaction xác nhận
    client.sendReaction(message_object, "✅", thread_id, thread_type, reactionType=75)

def get_mitaizl():
    """Trả về dictionary các lệnh."""
    return {
        'acclq': handle_send_accounts_command
    }
