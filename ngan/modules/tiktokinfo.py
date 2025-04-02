from zlapi.models import Message
import requests
import os

des = {
    'version': "1.0.2",
    'credits': "Nguyễn Đức Tài",
    'description': "Lấy thông tin người dùng tiktok từ id"
}

def handle_tiktokinfo_command(message, message_object, thread_id, thread_type, author_id, client):
    # Gửi phản ứng ngay khi người dùng soạn đúng lệnh
    action = "✅"
    client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)
    content = message.strip().split()

    if len(content) < 2:
        error_message = Message(text="Vui lòng nhập một id tiktok cần lấy thông tin.")
        client.replyMessage(error_message, message_object, thread_id, thread_type)
        return

    iduser = content[1].strip()

    try:
        api_url = f'https://subhatde.id.vn/tiktok/infov2?username={iduser}'
        response = requests.get(api_url)
        response.raise_for_status()

        data = response.json()

        if 'id' not in data:
            raise KeyError("API trả về kết quả không thành công.")

        uid = data.get('id')
        username = data.get('username')
        name = data.get('nickname')
        tieusu = data.get('signature', 'Không có thông tin tiểu sử')
        avt = data.get('avatarLarger')
        
        # Thống kê
        tim = data.get('heartCount', 0)
        dangfl = data.get('followingCount', 0)
        sofl = data.get('followerCount', 0)
        tongvd = data.get('videoCount', 0)

        gui = (
            f"• Tên: {name}\n"
            f"• Id TikTok: {uid}\n"
            f"• Username TikTok: {username}\n"
            f"• Tiểu sử: {tieusu}\n"
            f"• Số follower: {sofl}\n"
            f"• Đang follower: {dangfl}\n"
            f"• Số video đã đăng: {tongvd}\n"
            f"• Tổng số tim TikTok: {tim}"
        )

        messagesend = Message(text=gui)

        if avt:
            image_response = requests.get(avt)
            image_response.raise_for_status()  # Kiểm tra lỗi khi lấy ảnh
            image_path = 'modules/cache/temp_tiktok.jpeg'

            with open(image_path, 'wb') as f:
                f.write(image_response.content)

            client.sendLocalImage(
                image_path, 
                message=messagesend,
                thread_id=thread_id,
                thread_type=thread_type,
                width=2500,
                height=2500
            )

            os.remove(image_path)
        else:
            raise Exception("Không thể gửi ảnh.")

    except requests.exceptions.RequestException as e:
        error_message = Message(text=f"Đã xảy ra lỗi khi gọi API: {str(e)}")
        client.sendMessage(error_message, thread_id, thread_type)
    except KeyError as e:
        error_message = Message(text=f"Dữ liệu từ API không đúng cấu trúc: {str(e)}")
        client.sendMessage(error_message, thread_id, thread_type)
    except Exception as e:
        error_message = Message(text=f"Đã xảy ra lỗi không xác định: {str(e)}")
        client.sendMessage(error_message, thread_id, thread_type)

def get_mitaizl():
    return {
        'tiktokinfo': handle_tiktokinfo_command
    }