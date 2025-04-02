import re
import os
import requests
from zlapi.models import Message
from bs4 import BeautifulSoup

des = {
    'version': "1.0.8",
    'credits': "Nguyễn Đức Tài",
    'description': "Tải video hoặc ảnh từ link (capcut, tiktok, youtube, facebook, douyin)"
}

def handle_down_command(message, message_object, thread_id, thread_type, author_id, client):
    # Gửi phản ứng ngay khi người dùng soạn đúng lệnh
    action = "✅"
    client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)
    content = message.strip()

    def extract_links(content):
        urls = re.findall(r'(https?://[^\s]+)', content)
        
        soup = BeautifulSoup(content, "html.parser")
        href_links = [a['href'] for a in soup.find_all('a', href=True)]
        
        return urls + href_links

    links = extract_links(content)
    
    if not links:
        error_message = Message(text="Vui lòng nhập một đường link cần down hợp lệ.")
        client.replyMessage(error_message, message_object, thread_id, thread_type)
        return

    video_link = links[0].strip()

    def downall(api_url):
        try:
            response = requests.get(api_url)
            response.raise_for_status()
            data = response.json()
            
            if data.get('success') and data.get('data'):
                medias = data['data'].get('medias', [])
                tit = data['data'].get('title', 'Không có tiêu đề')
                dang = data['data'].get('source', 'Không có nguồn')

                image_links = []
                video_link = None

                for media in medias:
                    media_type = media.get('type')
                    loai = media.get('type')

                    if media_type == 'image':
                        image_links.append(media.get('url'))
                    elif media_type == 'video':
                        quality = media.get('quality')
                        desired_qualities = ['360p', 'no_watermark', 'SD', 'No Watermark', '']
                        if quality in desired_qualities:
                            video_link = media.get('url')

                return image_links, video_link, tit, dang, loai
        
        except requests.exceptions.RequestException as e:
            raise Exception(f"Đã xảy ra lỗi khi gọi API: {str(e)}")
        except KeyError as e:
            raise Exception(f"Dữ liệu từ API không đúng cấu trúc: {str(e)}")
        except Exception as e:
            raise Exception(f"Đã xảy ra lỗi không xác định: {str(e)}")

    api_url = f'https://subhatde.id.vn/youtube/download?url=https://youtu.be/lB3SRFPYf98?si=0ctivMXHz3ObQ-ge={video_link}'
    try:
        image_urls, video_url, tit, dang, loai = downall(api_url)

        sendtitle = f"Thể loại: {dang}\nTiêu đề: {tit}\nLoại: {loai}"
        headers = {'User-Agent': 'Mozilla/5.0'}

        if image_urls:
            for image_url in image_urls:
                image_response = requests.get(image_url, headers=headers)
                image_path = 'modules/cache/temp_image2r.jpeg'
                
                with open(image_path, 'wb') as f:
                    f.write(image_response.content)
                
                if os.path.exists(image_path):
                    message_to_send = Message(text=sendtitle)
                    client.sendLocalImage(
                        image_path, 
                        message=message_to_send,
                        thread_id=thread_id,
                        thread_type=thread_type,
                        width=1200,
                        height=1600
                    )
                    os.remove(image_path)
                else:
                    raise Exception("Không thể lưu ảnh")

        elif video_url and not image_urls:
            messagesend = Message(text=sendtitle)
            thumbnailUrl = 'https://files.catbox.moe/xjq5tm.jpeg'
            duration = '1000'

            client.sendRemoteVideo(
                video_url, 
                thumbnailUrl,
                duration=duration,
                message=messagesend,
                thread_id=thread_id,
                thread_type=thread_type,
                width=1200,
                height=1600
            )

        else:
            error_message = Message(text="Không tìm thấy video hoặc ảnh với yêu cầu.")
            client.sendMessage(error_message, thread_id, thread_type)
    
    except Exception as e:
        error_message = Message(text=str(e))
        client.sendMessage(error_message, thread_id, thread_type)

def get_mitaizl():
    return {
        'down': handle_down_command
    }
