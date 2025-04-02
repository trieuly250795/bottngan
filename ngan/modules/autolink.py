import time
import json
import logging
from zlapi.models import Message, ThreadType, MultiMsgStyle, MessageStyle

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

des = {
    'tác giả': "Rosy",
    'mô tả': "Gửi tin nhắn ngay lập tức đến toàn bộ nhóm",
    'tính năng': [
        "📨 Gửi tin nhắn ngay lập tức đến toàn bộ nhóm.",
        "🔍 Lọc các nhóm không nằm trong danh sách loại trừ.",
        "📄 Sử dụng định dạng màu sắc và cỡ chữ cho tin nhắn.",
        "🔄 Khởi chạy tính năng tự động gửi tin nhắn trong một luồng riêng.",
        "🔔 Thông báo lỗi cụ thể nếu có vấn đề xảy ra khi xử lý yêu cầu."
    ],
    'hướng dẫn sử dụng': [
        "📩 Gửi lệnh autolink để gửi tin nhắn ngay lập tức đến toàn bộ nhóm.",
        "📌 Ví dụ: autolink để gửi tin nhắn ngay lập tức đến toàn bộ nhóm.",
        "✅ Nhận thông báo trạng thái và kết quả ngay lập tức."
    ]
}

# Nội dung tin nhắn chính (giữ nguyên nội dung)
MESSAGE_TEXT = """🌟 𝐑𝐎𝐒𝐘 𝐀𝐑𝐄𝐍𝐀 𝐒𝐇𝐎𝐏 🌟
🔥 𝐇𝐚𝐜𝐤 𝐦𝐚𝐩 𝐮𝐲 𝐭𝐢́𝐧 - 𝐂𝐚̣̂𝐩 𝐧𝐡𝐚̣̂𝐭 𝐥𝐢𝐞̂𝐧 𝐭𝐮̣𝐜 🔥

📢 THÔNG BÁO UPDATE ANDROID - IOS
🔗 https://zalo.me/g/ohcfct225
🔶LQ ACE 3 MIỀN
🔗 https://zalo.me/g/rrywmq953

🔴 LEO RANK VÀ ĐẤU TRƯỜNG LIÊN QUÂN
🔶 Box 1: Bá chủ Liên quân
🔗 https://zalo.me/g/pszswa548
🔶 Box 4: Kẻ thống trị Liên quân
🔗 https://zalo.me/g/ochyyh448
🔶 Box 6: Hội Kẻ Hủy Diệt Rank
🔗 https://zalo.me/g/qlhssk809
🔶 Box 7: 100 ⭐ K phải giấc mơ
🔗 https://zalo.me/g/xvtszw104
🔶 Box 13: Leo rank bằng 4 Chân
   https://zalo.me/g/spaqlb267
🔶 Box 19: Chinh phục rank đồng
🔗 https://zalo.me/g/lulmlw377
🔶 Box 21: Người gác cổng Bình Nguyên
🔗 https://zalo.me/g/lalvob031
🔶 Box 22: Bộ lạc Liên Quân
🔗 https://zalo.me/g/crgyqw748

🔴 HẠ RANK CẤP TỐC
🔶 Box 8: Sẵn sàng 1 VS 9
🔗 https://zalo.me/g/sjrbqa638
🔶 Box 10: Hạ rank không phanh
🔗 https://zalo.me/g/vtgpfr533
🔶 Box 11: Hạn rank Xuống Đáy Xã Hội
🔗 https://zalo.me/g/dmgtoc729
🔶 Box 12: Cuộc chiến Hạ Rank
🔗 https://zalo.me/g/tlxiin969
🔶 Box 14: Hạ Rank Cũng vui
🔗 https://zalo.me/g/byuqks230
🔶 Box 15: Hạ Rank Trải Nghiệm
🔗 https://zalo.me/g/khjrna643
🔶 Box 17: Hạ Rank Chờ Cơ hội
🔗 https://zalo.me/g/smibnr474
🔶 Box 20: Binh Đoàn Tụt Hạng
🔗 https://zalo.me/g/ysdgtu142
🔶 Box 23: Thắng làm vua - Thua làm lại
🔗 https://zalo.me/g/lnuarr372

🔴 ĐĂNG KÍ ĐI BOT VÀ HỖ TRỢ ĐẤU ĐỘI
⚡ Box 2: Đăng ký đi bot
🔗 https://zalo.me/g/bjnwqv874
⚡ Box 3: Đăng ký bot 5 game
🔗 https://zalo.me/g/jlgahh907
⚡ Box 5: TLT - Nor 5v5
🔗 https://zalo.me/g/lzygxi684
⚡ Box 18: TLT 3v3
🔗 https://zalo.me/g/zaiqug348

🔴 CỘNG ĐỒNG NGHIỆN GAME
🎮 Box 16: Hội những người mê LQ
🔗 https://zalo.me/g/zfziaz213
"""

def get_excluded_group_ids(filename="danhsachnhom.json"):
    """
    Đọc tệp JSON và trả về tập hợp các group_id cần loại trừ.
    Nếu file không tồn tại hoặc định dạng sai, trả về tập rỗng.
    """
    try:
        with open(filename, "r", encoding="utf-8") as f:
            groups = json.load(f)
            return {grp.get("group_id") for grp in groups if "group_id" in grp}
    except Exception as e:
        logging.error("Lỗi khi đọc file %s: %s", filename, e)
        return set()

def create_styled_msg(text, color="#db342e", bold_size="16"):
    """
    Tạo Message với định dạng màu và kiểu chữ in đậm.
    """
    style = MultiMsgStyle([
        MessageStyle(
            offset=0,
            length=len(text),
            style="color",
            color=color,
            auto_format=False,
        ),
        MessageStyle(
            offset=0,
            length=len(text),
            style="bold",
            size=bold_size,
            auto_format=False,
        ),
    ])
    return Message(text=text, style=style)

def send_message_now(client):
    """
    Gửi tin nhắn đã định dạng đến toàn bộ nhóm không nằm trong danh sách loại trừ.
    """
    # Tính toán vị trí highlight trong tin nhắn
    highlight_text = "🌟 𝐑𝐎𝐒𝐘 𝐀𝐑𝐄𝐍𝐀 𝐒𝐇𝐎𝐏 🌟 🔥 𝐇𝐚𝐜𝐤 𝐦𝐚𝐩 𝐮𝐲 𝐭𝐢́𝐧 - 𝐂𝐚̣̂𝐩 𝐧𝐡𝐚̣̂𝐭 𝐥𝐢𝐞̂𝐧 𝐭𝐮̣𝐜 🔥"
    highlight_offset = MESSAGE_TEXT.find(highlight_text)
    highlight_length = len(highlight_text)
    full_message_length = len(MESSAGE_TEXT)
    padding_length = 100  # Bù thêm cho toàn bộ văn bản

    style_message = MultiMsgStyle([
        MessageStyle(
            offset=highlight_offset,
            length=highlight_length,
            style="color",
            color="#db342e",
            auto_format=False,
        ),
        MessageStyle(
            offset=0,
            length=full_message_length + padding_length,
            style="bold",
            size="8",
            auto_format=False,
        ),
    ])

    # Lấy danh sách nhóm được phép gửi (loại trừ danh sách từ file)
    all_groups = client.fetchAllGroups()
    excluded_ids = get_excluded_group_ids()
    allowed_thread_ids = [
        gid for gid in all_groups.gridVerMap.keys() if gid not in excluded_ids
    ]

    for thread_id in allowed_thread_ids:
        logging.info("Đang gửi tin nhắn đến nhóm %s...", thread_id)
        msg = Message(text=MESSAGE_TEXT, style=style_message)
        try:
            client.sendMessage(msg, thread_id, thread_type=ThreadType.GROUP, ttl=600000)
            logging.info("Đã gửi tin nhắn đến nhóm %s", thread_id)
            time.sleep(2)
        except Exception as e:
            logging.error("Error sending message to %s: %s", thread_id, e)

def handle_autosend_start(message, message_object, thread_id, thread_type, author_id, client):
    """
    Xử lý khi lệnh 'autolink' được kích hoạt:
      - Gửi phản hồi ban đầu với style.
      - Gửi tin nhắn đến toàn bộ nhóm.
      - Sau đó trả lời lại người dùng với kết quả.
    """
    # Thêm reaction vào tin nhắn lệnh
    client.sendReaction(message_object, "✅", thread_id, thread_type, reactionType=75)
    
    # Gửi thông báo ban đầu
    initial_msg = create_styled_msg("Đang gửi tin nhắn đến toàn bộ nhóm...", bold_size="16")
    client.sendMessage(initial_msg, thread_id, thread_type, ttl=30000)
    
    # Gửi tin nhắn chính đến toàn bộ nhóm
    send_message_now(client)
    
    # Phản hồi kết quả cho người dùng
    response_msg = create_styled_msg("Đã gửi tin nhắn ngay lập tức đến toàn bộ nhóm ✅", bold_size="10")
    client.replyMessage(response_msg, message_object, thread_id, thread_type, ttl=30000)
    
    # Gửi lại reaction vào tin nhắn lệnh
    client.sendReaction(message_object, "✅", thread_id, thread_type, reactionType=75)

def get_mitaizl():
    return {
        'autolink': handle_autosend_start
    }
