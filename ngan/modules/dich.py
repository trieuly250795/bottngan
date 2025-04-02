from zlapi import ZaloAPI
from zlapi.models import *
import time
from concurrent.futures import ThreadPoolExecutor
import threading
from deep_translator import GoogleTranslator
from googletrans import Translator  # Sử dụng googletrans để phát hiện ngôn ngữ
import asyncio

des = {
    'version': "1.0.0",
    'credits': "ROSY FIX",
    'description': "Dịch ngôn ngữ"
}

# Danh sách các ngôn ngữ được hỗ trợ (mã: tên tiếng Việt)
SUPPORTED_LANGUAGES = {
    "af": "Tiếng Afrikaans",
    "ar": "Tiếng Ả Rập",
    "az": "Tiếng Azerbaijan",
    "be": "Tiếng Belarus",
    "bg": "Tiếng Bulgaria",
    "bn": "Tiếng Bengali",
    "bs": "Tiếng Bosnia",
    "ca": "Tiếng Catalan",
    "cs": "Tiếng Séc",
    "cy": "Tiếng Xứ Wales",
    "da": "Tiếng Đan Mạch",
    "de": "Tiếng Đức",
    "el": "Tiếng Hy Lạp",
    "en": "Tiếng Anh",
    "eo": "Tiếng Esperanto",
    "es": "Tiếng Tây Ban Nha",
    "et": "Tiếng Estonia",
    "fa": "Tiếng Ba Tư",
    "fi": "Tiếng Phần Lan",
    "fr": "Tiếng Pháp",
    "ga": "Tiếng Ireland",
    "gl": "Tiếng Galicia",
    "gu": "Tiếng Gujarati",
    "hi": "Tiếng Hindi",
    "hr": "Tiếng Croatia",
    "ht": "Tiếng Haiti Creole",
    "hu": "Tiếng Hungary",
    "hy": "Tiếng Armenia",
    "id": "Tiếng Indonesia",
    "is": "Tiếng Iceland",
    "it": "Tiếng Ý",
    "ja": "Tiếng Nhật",
    "ka": "Tiếng Georgia",
    "kk": "Tiếng Kazakh",
    "km": "Tiếng Khmer",
    "kn": "Tiếng Kannada",
    "ko": "Tiếng Hàn",
    "ky": "Tiếng Kyrgyz",
    "lb": "Tiếng Luxembourg",
    "lo": "Tiếng Lào",
    "lt": "Tiếng Lithuania",
    "lv": "Tiếng Latvia",
    "mg": "Tiếng Malagasy",
    "mk": "Tiếng Macedonia",
    "ml": "Tiếng Malayalam",
    "mn": "Tiếng Mông Cổ",
    "mr": "Tiếng Marathi",
    "ms": "Tiếng Mã Lai",
    "mt": "Tiếng Malta",
    "ne": "Tiếng Nepali",
    "nl": "Tiếng Hà Lan",
    "no": "Tiếng Na Uy",
    "pa": "Tiếng Punjabi",
    "pl": "Tiếng Ba Lan",
    "pt": "Tiếng Bồ Đào Nha",
    "ro": "Tiếng Romania",
    "ru": "Tiếng Nga",
    "sk": "Tiếng Slovak",
    "sl": "Tiếng Slovenia",
    "sq": "Tiếng Albania",
    "sr": "Tiếng Serbia",
    "sv": "Tiếng Thụy Điển",
    "sw": "Tiếng Swahili",
    "ta": "Tiếng Tamil",
    "te": "Tiếng Telugu",
    "th": "Tiếng Thái",
    "tl": "Tiếng Tagalog",
    "tr": "Tiếng Thổ Nhĩ Kỳ",
    "uk": "Tiếng Ukraina",
    "ur": "Tiếng Urdu",
    "uz": "Tiếng Uzbekistan",
    "vi": "Tiếng Việt",
    "zh-cn": "Tiếng Trung (Giản thể)",
    "zh-tw": "Tiếng Trung (Phồn thể)"
}

# Alias mapping: cho phép dùng "tw" thay cho "zh-cn" (tiếng Trung Giản thể)
ALIAS_LANGUAGES = {
    "tw": "zh-cn",  # khi người dùng nhập "tw", ta hiểu là "zh-cn"
    # Nếu cần, bạn có thể thêm alias khác, ví dụ: "tc": "zh-tw"
}

def get_supported_languages_message():
    # Tạo thông điệp hiển thị hướng dẫn và danh sách ngôn ngữ hỗ trợ
    languages_list = [f"{code}: {name}" for code, name in SUPPORTED_LANGUAGES.items()]
    # Thêm alias vào danh sách hiển thị (nếu cần)
    for alias, real in ALIAS_LANGUAGES.items():
        if real in SUPPORTED_LANGUAGES:
            languages_list.append(f"{alias}: {SUPPORTED_LANGUAGES[real]}")
    languages_str = "\n".join(languages_list)
    message = (
        "Cú pháp sử dụng:\n"
        "  dich <ngôn ngữ cuối> <văn bản>\n"
        "Hoặc khi reply vào tin nhắn của người khác:\n"
        "  dich <ngôn ngữ cuối>\n\n"
        "Ví dụ:\n"
        "  dich en Xin chào, bạn khỏe không?\n"
        "  (hoặc reply tin nhắn của người khác và soạn: dich en)\n\n"
        "Danh sách ngôn ngữ được hỗ trợ:\n"
        f"{languages_str}"
    )
    return message

def handle_translate_command(message, message_object, thread_id, thread_type, author_id, client):
    # Phản ứng khi người dùng soạn đúng lệnh
    action = "✅"  # Phản ứng dấu kiểm
    client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)
    
    message_text = message_object.get('content', '').strip()
    parts = message_text.split(maxsplit=2)
    
    # Xử lý trường hợp reply: kiểm tra thuộc tính 'quote' dưới dạng object hoặc dict
    reply_message = None
    if hasattr(message_object, 'quote'):
        reply_message = message_object.quote
    elif 'quote' in message_object:
        reply_message = message_object.get('quote')
    
    # Nếu không có reply và cú pháp không đủ, gửi hướng dẫn
    if not reply_message and len(parts) < 3:
        help_message = get_supported_languages_message()
        client.replyMessage(Message(text=help_message), message_object, thread_id, thread_type, ttl=20000)
        return
    if len(parts) < 2:
        help_message = get_supported_languages_message()
        client.replyMessage(Message(text=help_message), message_object, thread_id, thread_type, ttl=20000)
        return

    # Lấy mã ngôn ngữ từ tham số ban đầu (không ép toàn bộ về chữ thường)
    raw_target = parts[1].strip()
    # Nếu có alias, chuyển đổi
    target_code = ALIAS_LANGUAGES.get(raw_target.lower(), raw_target)
    # Dùng chữ thường cho việc kiểm tra trong SUPPORTED_LANGUAGES
    target_lower = target_code.lower()
    
    # Kiểm tra xem ngôn ngữ đích có được hỗ trợ không
    if target_lower not in SUPPORTED_LANGUAGES:
        client.replyMessage(
            Message(text=f"Ngôn ngữ '{raw_target}' không được hỗ trợ.\n" + get_supported_languages_message()),
            message_object, thread_id, thread_type
        )
        return

    # Xác định văn bản cần dịch
    text_to_translate = ""
    if reply_message:
        # Cố gắng lấy trường 'msg' trước, nếu không có thì lấy 'content'
        try:
            text_to_translate = reply_message.get('msg', '').strip()
        except AttributeError:
            text_to_translate = getattr(reply_message, 'msg', '').strip()
        if not text_to_translate:
            try:
                text_to_translate = reply_message.get('content', '').strip()
            except AttributeError:
                text_to_translate = getattr(reply_message, 'content', '').strip()
        print(f"[DEBUG] Nội dung tin nhắn reply: '{text_to_translate}'")
        # Nếu tin reply không có nội dung, kiểm tra phần lệnh sau target language
        if not text_to_translate:
            if len(parts) < 3:
                help_message = get_supported_languages_message()
                client.replyMessage(Message(text=help_message), message_object, thread_id, thread_type)
                return
            else:
                text_to_translate = parts[2]
    else:
        text_to_translate = parts[2]

    if not text_to_translate:
        client.replyMessage(Message(text="Không tìm thấy nội dung để dịch."), message_object, thread_id, thread_type)
        return

    try:
        # Sử dụng googletrans để phát hiện ngôn ngữ nguồn (chạy coroutine với asyncio.run)
        translator_detect = Translator()
        detected = asyncio.run(translator_detect.detect(text_to_translate))
        source_lang = detected.lang

        # Lấy tên ngôn ngữ nguồn đầy đủ từ SUPPORTED_LANGUAGES (nếu có)
        source_lang_name = SUPPORTED_LANGUAGES.get(source_lang, source_lang)
        
        # Điều chỉnh mã ngôn ngữ cho deep_translator nếu cần
        if target_lower == "zh-cn":
            translator_target = "zh-CN"
        elif target_lower == "zh-tw":
            translator_target = "zh-TW"
        else:
            translator_target = target_lower

        translated = GoogleTranslator(source='auto', target=translator_target).translate(text_to_translate)
        
        # Lấy tên đầy đủ của ngôn ngữ đích từ SUPPORTED_LANGUAGES
        target_lang_name = SUPPORTED_LANGUAGES.get(target_lower, raw_target)
        
        # Tin nhắn 1: thông báo đã dịch
        message1 = f"Đã dịch từ {source_lang_name} sang {target_lang_name}"
        # Tin nhắn 2: nội dung đã dịch
        message2 = translated

        client.replyMessage(Message(text=message1), message_object, thread_id, thread_type, ttl=10000)
        client.replyMessage(Message(text=message2), message_object, thread_id, thread_type)
    except Exception as e:
        client.replyMessage(Message(text=f"Lỗi khi dịch: {str(e)}"), message_object, thread_id, thread_type, ttl=180000)

def get_mitaizl():
    return {
        'dich': handle_translate_command
    }
