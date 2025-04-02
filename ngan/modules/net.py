from zlapi import ZaloAPI
from zlapi.models import Message
import speedtest

des = {
    'tác giả': "Rosy",
    'mô tả': "Bot hỗ trợ kiểm tra tốc độ mạng chi tiết và gửi kết quả cho người dùng.",
    'tính năng': [
        "⚡ Kiểm tra tốc độ tải xuống và tải lên của mạng.",
        "🔍 Lấy thông tin về ping và server tốt nhất.",
        "📨 Gửi tin nhắn với kết quả kiểm tra tốc độ mạng chi tiết.",
        "🔔 Thông báo kết quả kiểm tra tốc độ mạng với thời gian sống (TTL) khác nhau.",
        "🔒 Chỉ quản trị viên mới có quyền sử dụng lệnh này."
    ],
    'hướng dẫn sử dụng': [
        "📩 Gửi lệnh để bot kiểm tra tốc độ mạng và gửi kết quả chi tiết.",
        "📌 Bot sẽ gửi kết quả kiểm tra tốc độ mạng bao gồm tốc độ tải xuống, tải lên, ping và thông tin server.",
        "✅ Nhận thông báo trạng thái kiểm tra tốc độ mạng ngay lập tức."
    ]
}

def handle_speedtest_command(message, message_object, thread_id, thread_type, author_id, client):
    try:
        # Khởi tạo Speedtest
        st = speedtest.Speedtest()
        
        # Lấy server tốt nhất (nếu không xác định server cụ thể)
        best_server = st.get_best_server()

        # Tiến hành kiểm tra tốc độ download và upload
        download_speed = st.download() / 1_000_000  # Chuyển đổi từ bps sang Mbps
        upload_speed = st.upload() / 1_000_000    # Chuyển đổi từ bps sang Mbps
        ping = st.results.ping

        # Lấy các thông tin khác từ kết quả
        server_name = best_server['name']
        server_location = best_server['country']
        server_host = best_server['host']
        client_ip = st.results.client['ip']
        timestamp = st.results.timestamp

        # Format kết quả đầy đủ
        message_content = f"> Tốc độ mạng hiện tại:\n" \
                          f"⚡ Tốc độ tải xuống: {download_speed:.2f} Mbps\n" \
                          f"⚡ Tốc độ tải lên: {upload_speed:.2f} Mbps\n" \
                          f"⚡ Ping: {ping} ms\n\n" \
                          f"Thông tin server:\n" \
                          f"🌍 Server: {server_name} ({server_location})\n" \
                          f"📍 Địa chỉ IP của bạn: {client_ip}\n" \
                          f"🕒 Thời gian kiểm tra: {timestamp}\n" \
                          f"🔄 Server sử dụng: {server_host}"

        # Gửi tin nhắn với kết quả
        message_to_send = Message(text=message_content)
        client.replyMessage(
            message_to_send,
            message_object,
            thread_id,
            thread_type,
            ttl=120000
        )

    except Exception as e:
        error_message = Message(text=f"Đã xảy ra lỗi khi đo tốc độ mạng: {str(e)}")
        client.sendMessage(error_message, thread_id, thread_type)

def get_mitaizl():
    return {
        'net': handle_speedtest_command
    }
