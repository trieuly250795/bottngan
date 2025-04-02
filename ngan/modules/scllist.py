import os
import re
import requests
import yt_dlp
from zlapi import *
from zlapi.models import *
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

des = {
    'tác giả': "Rosy",
    'mô tả': "Tìm kiếm và tải nhạc từ SoundCloud",
    'tính năng': [
        "🔍 Tìm kiếm bài hát trên SoundCloud dựa trên từ khóa người dùng nhập.",
        "🎵 Hiển thị danh sách bài hát tìm được và thông tin chi tiết.",
        "⬇️ Tải nhạc từ SoundCloud.",
        "📨 Gửi phản hồi với kết quả tìm kiếm và thông tin chi tiết về bài hát.",
        "🗂️ Tải nhạc lên Uguu.se để dễ dàng chia sẻ.",
        "🗑️ Tự động xóa file sau khi tải lên."
    ],
    'hướng dẫn sử dụng': [
        "📩 Gửi lệnh scllist <từ khóa> để tìm kiếm bài hát trên SoundCloud.",
        "📌 Ví dụ: scllist Imagine Dragons để tìm kiếm bài hát của Imagine Dragons.",
        "✅ Nhận thông báo trạng thái và kết quả tìm kiếm ngay lập tức."
    ]
}

def get_headers():
    user_agent = UserAgent()
    return {
        "User-Agent": user_agent.random,
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": 'https://soundcloud.com/',
        "Upgrade-Insecure-Requests": "1"
    }

def search_song(query):
    try:
        search_url = f'https://m.soundcloud.com/search?q={requests.utils.quote(query)}'
        response = requests.get(search_url, headers=get_headers())
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        url_pattern = re.compile(r'^/[^/]+/[^/]+$')
        results = []
        for element in soup.select('div > ul > li > div'):
            a_tag = element.select_one('a')
            if a_tag and a_tag.has_attr('href'):
                relative_url = a_tag['href']
                if url_pattern.match(relative_url):
                    title = a_tag.get('aria-label', 'Không rõ')
                    url = 'https://soundcloud.com' + relative_url
                    img_tag = element.select_one('img')
                    cover_url = img_tag['src'] if img_tag and img_tag.has_attr('src') else None
                    artist = element.select_one('span').text if element.select_one('span') else "Không rõ"
                    duration = element.select_one('.sc-ministats-duration').text if element.select_one('.sc-ministats-duration') else "Không rõ"
                    results.append((url, title, cover_url, artist, duration))
                if len(results) == 10:
                    break
        return results
    except Exception as e:
        print(f"Lỗi khi tìm kiếm bài hát: {e}")
        return []

def download(link):
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'cache/downloaded_file.%(ext)s',
            'noplaylist': True,
            'quiet': True
        }
        os.makedirs('cache', exist_ok=True)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=True)
        return ydl.prepare_filename(info_dict)
    except Exception as e:
        print(f"Lỗi khi tải âm thanh: {e}")
        return None

def upload_to_uguu(file_path):
    url = "https://uguu.se/upload"
    try:
        with open(file_path, 'rb') as file:
            files = {'files[]': (os.path.basename(file_path), file)}
            response = requests.post(url, files=files, headers=get_headers())
            response.raise_for_status()
            return response.json().get('files', [{}])[0].get('url')
    except Exception as e:
        print(f"Lỗi khi tải lên: {e}")
        return None

def delete_file(file_path):
    try:
        os.remove(file_path)
        print(f"Đã xóa tệp: {file_path}")
    except Exception as e:
        print(f"Lỗi khi xóa tệp: {e}")

def handle_nhac_command(message, message_object, thread_id, thread_type, author_id, client):
    content = message.strip().split()
    client.sendReaction(message_object, "✅", thread_id, thread_type, reactionType=75)
    if len(content) < 2:
        error_message = Message(text="Đéo nhập tên bài hát sao tìm ???\nCú pháp: scl <từ khóa>")
        client.replyMessage(error_message, message_object, thread_id, thread_type, ttl=600000)
        return
    tenbaihat = ' '.join(content[1:])
    search_message = Message(text=f"🔎 Đang tìm kiếm bài hát: {tenbaihat} từ SoundCloud...")
    client.replyMessage(search_message, message_object, thread_id, thread_type, ttl=20000)
    song_list = search_song(tenbaihat)
    if not song_list:
        error_message = Message(text="Không tìm thấy bài hát nào phù hợp.")
        client.replyMessage(error_message, message_object, thread_id, thread_type)
        return
    song_message = "🎶 𝐃𝐚𝐧𝐡 𝐬𝐚́𝐜𝐡 𝐛𝐚̀𝐢 𝐡𝐚́𝐭:\nChọn bài bằng cách:\n 𝘀𝗰𝗹 [tiêu đề]\n─────────────────────\n"
    for idx, (url, title, cover, artist, duration) in enumerate(song_list):
        song_message += f"🔹 {idx+1}. {title}\n"
        song_message += f" 🎤 Nghệ sĩ: {artist}\n"
        song_message += f" ⏰ Thời gian: {duration}\n"
        song_message += "─────────────────────\n"
    client.replyMessage(Message(text=song_message), message_object, thread_id, thread_type, ttl=60000)

def handle_song_selection(message, message_object, thread_id, thread_type, author_id, client):
    try:
        choice = int(message.strip())
        if 1 <= choice <= len(song_list):
            link, title, cover, artist, duration = song_list[choice - 1]
            mp3_file = download(link)
            if not mp3_file:
                client.replyMessage(Message(text="Không thể tải file âm thanh."), message_object, thread_id, thread_type)
                return
            upload_response = upload_to_uguu(mp3_file)
            if not upload_response:
                client.replyMessage(Message(text="Không thể tải lên Uguu.se."), message_object, thread_id, thread_type)
                return
            messagesend = Message(text=f"🎵 Bài Hát: {title}\n🎤 Nghệ sĩ: {artist}\n⏳ Độ dài : {duration}")
            client.replyMessage(messagesend, message_object, thread_id, thread_type)
            client.sendRemoteVoice(voiceUrl=upload_response, thread_id=thread_id, thread_type=thread_type, ttl=120000000)
            delete_file(mp3_file)
        else:
            client.replyMessage(Message(text="⚠️ Lựa chọn không hợp lệ!"), message_object, thread_id, thread_type)
    except ValueError:
        client.replyMessage(Message(text="⚠️ Vui lòng nhập số để chọn bài hát!"), message_object, thread_id, thread_type)
    client.waitForMessage(handle_song_selection, thread_id, thread_type, timeout=30)

def get_mitaizl():
    return {
        'scllist': handle_nhac_command
    }
