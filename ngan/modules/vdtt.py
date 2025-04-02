import random
import requests
import urllib.parse
from zlapi.models import Message, MultiMsgStyle, MessageStyle

des = {
    'version': '1.0.5',
    'credits': 'Trung Trí',
    'description': 'Search TikTok videos'
}

def handle_tiktok_command(message, message_object, thread_id, thread_type, author_id, client):
    # Gửi phản ứng ngay khi người dùng soạn đúng lệnh
    action = "✅"
    client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)
    content = message.strip().split()

    if len(content) < 2:
        menu_message = "Hãy nhập 1 từ khoá để tìm kiếm video từ tiktok\n Cú pháp: vdtt <từ khoá>"
        
        style = MultiMsgStyle(
            [
                MessageStyle(
                    offset=0,
                    length=len(menu_message),
                    style="color",
                    color="#15a85f",  # Màu xanh lục cho toàn bộ text
                    auto_format=False,
                ),
                MessageStyle(
                    offset=0,
                    length=len(menu_message),
                    style="font",
                    size="16",  # Kích thước font chữ là 16
                    auto_format=False,
                ),
            ]
        )
        
        error_message = Message(text=menu_message, style=style)
        client.replyMessage(error_message, message_object, thread_id, thread_type, ttl=60000)
        return

    keyword = " ".join(content[1:]).strip()

    try:
        encoded_keyword = urllib.parse.quote(keyword)
        search_url = f'https://subhatde.id.vn/tiktok/searchvideo?keywords={encoded_keyword}'
        search_response = requests.get(search_url)
        search_response.raise_for_status()

        search_data = search_response.json()

        if 'data' not in search_data or 'videos' not in search_data['data']:
            error_message = Message(text="No TikTok videos found for the requested keyword.")
            client.replyMessage(error_message, message_object, thread_id, thread_type, ttl=60000)
            return

        videos = search_data['data']['videos']
        if len(videos) == 0:
            error_message = Message(text="No TikTok videos found for the requested keyword.")
            client.replyMessage(error_message, message_object, thread_id, thread_type, ttl=60000)
            return

        selected_video = random.choice(videos)
        video_url = f"https://www.tiktok.com/@{selected_video['author']['unique_id']}/video/{selected_video['video_id']}"

        download_url = f'https://subhatde.id.vn/tiktok/downloadvideo?url={video_url}'
        download_response = requests.get(download_url)
        download_response.raise_for_status()

        download_data = download_response.json()

        if 'data' not in download_data or 'play' not in download_data['data']:
            error_message = Message(text="Unable to retrieve video download link from TikTok.")
            client.replyMessage(error_message, message_object, thread_id, thread_type, ttl=60000)
            return

        video_url = download_data['data']['play']
        title = download_data['data']['title']
        region = download_data['data']['region']
        size_kb = download_data['data']['size']
        size_mb = size_kb / 1024
        processed_time = download_data['processed_time']
        thumbnail_url = 'https://i.imgur.com/W2YfEPm.jpeg'
        duration = '36000'
        user_info = client.fetchUserInfo(author_id)
        user_name = user_info.changed_profiles[author_id].zaloName
        
        video_info = (
            f"[ {user_name} ]\n\n"
            f"⭕Tiêu đề: {title}\n"
            f"⭕Tác giả: @{selected_video['author']['unique_id']}\n"
            f"⭕Khu vực: {region}\n"
            f"⭕Kích cỡ: {size_mb:.2f} KB\n"
            f"⭕Thời lượng: {processed_time}"
        )
        
        messagesend = Message(text=video_info)
        client.sendRemoteVideo(
            video_url, 
            thumbnail_url,
            duration=duration,
            message=messagesend,
            thread_id=thread_id,
            thread_type=thread_type,
            ttl=86400000,
            width=1200,
            height=1600
        )

    except requests.exceptions.RequestException as e:
        error_message = Message(text=f"An error occurred when calling the API: {str(e)}")
        client.replyMessage(error_message, message_object, thread_id, thread_type, ttl=60000)
    except Exception as e:
        error_message = Message(text=f"An unknown error occurred: {str(e)}")
        client.replyMessage(error_message, message_object, thread_id, thread_type, ttl=60000)

def get_mitaizl():
    return {
        'vdtt': handle_tiktok_command
    }
