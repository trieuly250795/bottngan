from zlapi.models import Message, MultiMsgStyle, MessageStyle
from config import PREFIX
import requests
import urllib.parse
from youtube_search import YoutubeSearch
import json

des = {
    'tác giả': "Rosy",
    'mô tả': "Tìm kiếm video YouTube",
    'tính năng': [
        "📨 Tìm kiếm video trên YouTube dựa trên từ khóa do người dùng cung cấp.",
        "🔍 Trả về danh sách video liên quan từ YouTube.",
        "📄 Hiển thị các thông tin liên quan đến video như tiêu đề, kênh, lượt xem, thời gian đăng tải và thời lượng.",
        "🔗 Cung cấp liên kết đến video trên YouTube.",
        "🔔 Thông báo lỗi cụ thể nếu có vấn đề xảy ra khi xử lý yêu cầu."
    ],
    'hướng dẫn sử dụng': [
        "📩 Gửi lệnh ytbsearch <từ khóa> để tìm kiếm video trên YouTube.",
        "📌 Ví dụ: ytbsearch funny cats để tìm kiếm video về mèo vui nhộn trên YouTube.",
        "✅ Nhận thông báo trạng thái và kết quả ngay lập tức."
    ]
}


def translate_time(publish_time):
    translations = {
        'day': 'ngày', 'days': 'ngày',
        'hour': 'giờ', 'hours': 'giờ',
        'minute': 'phút', 'minutes': 'phút',
        'second': 'giây', 'seconds': 'giây',
        'week': 'tuần', 'weeks': 'tuần',
        'month': 'tháng', 'months': 'tháng',
        'year': 'năm', 'years': 'năm',
        'ago': 'trước'
    }
    for eng, viet in translations.items():
        publish_time = publish_time.replace(eng, viet)
    return publish_time

def translate_views(views):
    views = views.replace('views', 'lượt xem')
    return views

def handle_ytbsearch_command(message, message_object, thread_id, thread_type, author_id, client):
    # Gửi phản ứng ngay khi người dùng soạn đúng lệnh
    action = "✅"
    client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)
    text = message.split()

    if len(text) < 2:
        error_message = "Hãy nhập từ khóa để tìm kiếm video trên YouTube.\n Cú pháp: ytbsearch < từ khoá>"
        style_error = MultiMsgStyle(
            [
                MessageStyle(
                    offset=0,
                    length=len(error_message),
                    style="color",
                    color="#15a85f",
                    auto_format=False,
                ),
                MessageStyle(
                    offset=0,
                    length=len(error_message),
                    style="font",
                    size="16",
                    auto_format=False,
                ),
            ]
        )
        client.sendMessage(Message(text=error_message, style=style_error), thread_id, thread_type)
        return

    query = " ".join(text[1:])

    results = YoutubeSearch(query, max_results=5).to_json()
    data = json.loads(results)

    if not data['videos']:
        no_result_message = "Không tìm thấy kết quả cho từ khóa: {query}"
        style_no_result = MultiMsgStyle(
            [
                MessageStyle(
                    offset=0,
                    length=len(no_result_message),
                    style="color",
                    color="#15a85f",
                    auto_format=False,
                ),
                MessageStyle(
                    offset=0,
                    length=len(no_result_message),
                    style="font",
                    size="16",
                    auto_format=False,
                ),
            ]
        )
        client.sendMessage(Message(text=no_result_message, style=style_no_result), thread_id, thread_type)
        return

    message_to_send = ""
    for idx, video in enumerate(data['videos'], 1):
        translated_time = translate_time(video['publish_time'])
        translated_views = translate_views(video['views'])
        message_to_send += (
    f"🔸                 {idx}.\n"
    f"👤 𝗞𝗲̂𝗻𝗵: {video['channel']}\n"
    f"🎬 𝗧𝗶𝗲̂𝘂 đ𝗲̂̀:  {video['title']}\n"  # Tiêu đề nổi bật bằng biểu tượng
    f"👀 𝗟𝘂̛𝗼̛̣𝘁 𝘅𝗲𝗺: {translated_views}\n"
    f"⏳ 𝗧𝗵𝗼̛̀𝗶 𝗴𝗶𝗮𝗻 đ𝗮̃ 𝘂𝗽: {translated_time}\n"
    f"⏰ 𝗧𝗵𝗼̛̀𝗶 𝗹𝘂̛𝗼̛̣𝗻𝗴: {video['duration']}\n"
    f"🔗 𝗟𝗶𝗻𝗸 𝘃𝗶𝗱𝗲𝗼: [Xem tại đây](https://www.youtube.com{video['url_suffix']})\n"
    f"───────────────────\n\n"
)

    gui = f"{message_to_send}\nĐể xem video vui lòng ấn vào link"

    style_gui = MultiMsgStyle(
        [
            MessageStyle(
                offset=0,
                length=len(gui),
                style="color",
                color="#000000",
                auto_format=False,
            ),
            MessageStyle(
                offset=0,
                length=len(gui),
                style="font",
                size="16",
                auto_format=False,
            ),
        ]
    )

    client.replyMessage(
        Message(text=gui, style=style_gui),
        message_object,
        thread_id,
        thread_type
    )
    action = "✅"  # Phản ứng bạn muốn gửi
    client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)

def get_mitaizl():
    return {
        'yt': handle_ytbsearch_command
    }
