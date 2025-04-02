import os
import requests
from zlapi.models import Message

# Thư mục cache
CACHE_DIR = 'modules/cache'
os.makedirs(CACHE_DIR, exist_ok=True)

def lam_net_anh(image_url):
    """Gửi yêu cầu làm nét ảnh và lưu vào cache."""
    print(f"[INFO] Nhận yêu cầu làm nét ảnh từ link: {image_url}")
    
    api_url = f"https://api.sumiproject.net/lamnet?link={image_url}"
    print(f"[INFO] Đang gửi yêu cầu làm nét ảnh: {image_url}")

    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            image_path = os.path.join(CACHE_DIR, "anh_lam_net.png")
            with open(image_path, 'wb') as file:
                file.write(response.content)
            print(f"[INFO] Ảnh đã được làm nét thành công và lưu vào cache: {image_path}")
            return image_path
        else:
            print(f"[ERROR] API trả về mã lỗi: {response.status_code}")
            return None
    except Exception as e:
        print(f"[ERROR] Lỗi khi gọi API làm nét ảnh: {e}")
        return None

def handle_lam_net_command(message, message_object, thread_id, thread_type, author_id, client):
    """Xử lý lệnh làm nét ảnh."""
    content = message.strip().split()
    
    if len(content) < 2:
        error_msg = Message(text="❌ Vui lòng nhập link ảnh cần làm nét.")
        client.replyMessage(error_msg, message_object, thread_id, thread_type, ttl=60000)
        return

    image_url = content[1]
    loading_msg = Message(text="✨ Đang làm nét ảnh... Vui lòng đợi một chút.")
    client.replyMessage(loading_msg, message_object, thread_id, thread_type, ttl=60000)

    # Gọi API làm nét ảnh
    image_path = lam_net_anh(image_url)

    if image_path:
        # Kiểm tra file có tồn tại không trước khi gửi
        if os.path.exists(image_path):
            try:
                print(f"[INFO] Đang gửi ảnh đã làm nét: {image_path}")
                success_msg = Message(text="✨ Ảnh đã làm nét xong! Hãy lưu ảnh để xem full kích thước:")
                client.sendLocalImage(
                    imagePath=image_path,
                    message=success_msg,
                    thread_id=thread_id,
                    thread_type=thread_type,
                    ttl=60000
                )
                print(f"[INFO] Ảnh đã được gửi thành công.")
                
                # Xóa ảnh sau khi gửi
                os.remove(image_path)
                print(f"[INFO] Đã xóa ảnh tạm trong cache: {image_path}")
            except Exception as e:
                print(f"[ERROR] Lỗi khi gửi ảnh: {e}")
        else:
            print(f"[ERROR] File ảnh không tồn tại: {image_path}")
            error_msg = Message(text="❌ Lỗi: File ảnh không tồn tại. Vui lòng thử lại.")
            client.replyMessage(error_msg, message_object, thread_id, thread_type)
    else:
        error_msg = Message(text="❌ Đã xảy ra lỗi khi làm nét ảnh. Vui lòng thử lại.")
        client.replyMessage(error_msg, message_object, thread_id, thread_type)

# Đăng ký lệnh
def get_mitaizl():
    return {
        'up': handle_lam_net_command,
    }
