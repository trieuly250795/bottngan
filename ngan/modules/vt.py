import time
import requests
import threading
import tempfile
from zlapi.models import Message

# Mô tả trò chơi (các thông tin hiển thị trên bot)
des = {
    'tác giả': "DũngKon-SUMIPROJECT",
    'mô tả': "Trò chơi Vua Tiếng Việt. Thách thức nhập chính xác từ khoá (bao gồm dấu tiếng Việt).",
    'tính năng': [
        "🎮 Nhận từ khoá từ API",
        "⌨️ Thử thách nhập chính xác chữ có dấu",
        "🚀 Kiểm tra và xử lý câu trả lời của người chơi",
        "📂 Lưu trữ phiên chơi theo từng nhóm/chat",
        "🔄 Tự động gửi câu hỏi mới khi trả lời đúng hoặc hết thời gian",
        "🛑 Lệnh vtstop để dừng chế độ tự động gửi câu hỏi"
    ],
    'hướng dẫn sử dụng': [
        "▶️ Dùng lệnh 'vt' để nhận từ khoá và bật chế độ tự động.",
        "✍️ Trả lời bằng cách nhập: tlvt <đáp án>",
        "⏳ Mỗi câu hỏi có thời gian hiệu lực là 3 phút.",
        "🎉 Trả lời đúng sẽ tự động gửi câu hỏi mới.",
        "⌛ Nếu hết thời gian, câu hỏi cũ sẽ bị bỏ và câu hỏi mới được gửi.",
        "🛑 Dùng lệnh 'vtstop' để dừng chế độ tự động gửi."
    ]
}

# Dictionary lưu trữ phiên chơi cho mỗi thread.
active_games = {}
# Biến lưu trạng thái tự động gửi (True: bật, False: tắt)
auto_mode = {}
# Lưu trữ đối tượng timer cho mỗi thread
auto_timers = {}

GAME_VALID_SECONDS = 180   # 3 phút
DEFAULT_REPLY_TTL = 60000  # 60 giây

def schedule_timer(thread_id, thread_type, client):
    print(f"DEBUG: schedule_timer() gọi cho thread {thread_id}")
    if thread_id in auto_timers:
        timer = auto_timers[thread_id]
        timer.cancel()
        print(f"DEBUG: Huỷ timer cũ cho thread {thread_id}")
    timer = threading.Timer(GAME_VALID_SECONDS, lambda: auto_timer_callback(thread_id, thread_type, client))
    auto_timers[thread_id] = timer
    timer.start()
    print(f"DEBUG: Đã đặt timer cho thread {thread_id}")

def auto_timer_callback(thread_id, thread_type, client):
    now = time.time()
    print(f"DEBUG: auto_timer_callback() gọi cho thread {thread_id} tại thời gian {now}")
    if thread_id in active_games:
        game_info = active_games[thread_id]
        elapsed = now - game_info["timestamp"]
        print(f"DEBUG: Thời gian đã trôi qua cho thread {thread_id}: {elapsed} giây")
        if elapsed >= GAME_VALID_SECONDS:
            active_games.pop(thread_id, None)
            print(f"DEBUG: Phiên chơi cho thread {thread_id} đã hết hạn và bị xoá.")
            if auto_mode.get(thread_id, False):
                client.sendMessage(thread_id, thread_type, text="⌛ Hết thời gian, câu hỏi mới đang được gửi tự động...")
                send_question_auto(thread_id, thread_type, client)

def send_question_auto(thread_id, thread_type, client):
    now = time.time()
    print(f"DEBUG: send_question_auto() gọi cho thread {thread_id} tại thời gian {now}")
    try:
        response = requests.get("https://api.sumiproject.net/game/vuatiengviet")
        print(f"DEBUG: Gọi API trả về mã trạng thái {response.status_code}")
        if response.status_code != 200:
            client.sendMessage(thread_id, thread_type, text="⚠️ Không thể truy cập API trò chơi. Vui lòng thử lại sau.")
            return
        data = response.json()
        print(f"DEBUG: Dữ liệu API nhận được: {data}")
        keyword = data.get("keyword")
        if not keyword:
            client.sendMessage(thread_id, thread_type, text="⚠️ Dữ liệu trò chơi không hợp lệ từ API.")
            return
        active_games[thread_id] = {
            "answer": keyword.lower().strip(),
            "timestamp": now
        }
        print(f"DEBUG: Lưu phiên chơi cho thread {thread_id} với đáp án: {keyword.lower().strip()}")
        response_text = (
            "👑 Trò chơi Vua Tiếng Việt\n"
            "👉 Hãy nhập đáp án bằng lệnh: tlvt <đáp án>\n"
            "⏳ Câu hỏi có hiệu lực trong 3 phút.\n"
            "🛑 Soạn vtstop để dừng chế độ tự động gửi câu hỏi."
        )
        client.sendMessage(thread_id, thread_type, Message(text=response_text))
        schedule_timer(thread_id, thread_type, client)
    except Exception as e:
        active_games.pop(thread_id, None)
        error_str = "🚨 Đã xảy ra lỗi: " + str(e)
        print(f"DEBUG: Exception trong send_question_auto() cho thread {thread_id}: {error_str}")
        client.sendMessage(thread_id, thread_type, text=error_str)

def handle_vt_command(message, message_object, thread_id, thread_type, author_id, client):
    print(f"DEBUG: handle_vt_command() được gọi cho thread {thread_id} với message: {message}")
    client.sendReaction(message_object, "✅", thread_id, thread_type, reactionType=75)
    parts = message.split()
    if len(parts) != 1:
        error_message = Message(text="❌ Cú pháp không hợp lệ.\n👉 Vui lòng nhập: vt")
        client.replyMessage(error_message, message_object, thread_id, thread_type, ttl=DEFAULT_REPLY_TTL)
        print("DEBUG: Cú pháp sai trong handle_vt_command()")
        return
    auto_mode[thread_id] = True
    now = time.time()
    if thread_id in active_games:
        game_info = active_games[thread_id]
        elapsed = now - game_info["timestamp"]
        if elapsed < GAME_VALID_SECONDS:
            remaining = int(GAME_VALID_SECONDS - elapsed)
            error_message = Message(text=f"⌛ Bạn đang có câu hỏi chưa kết thúc.\n💡 Hãy trả lời hoặc chờ {remaining} giây để nhận câu hỏi mới.")
            client.replyMessage(error_message, message_object, thread_id, thread_type, ttl=10000)
            print(f"DEBUG: Phiên chơi vẫn còn hiệu lực cho thread {thread_id}, còn {remaining} giây.")
            return
        else:
            active_games.pop(thread_id, None)
            print(f"DEBUG: Phiên chơi cũ cho thread {thread_id} đã hết hạn và được xoá.")
    send_question_auto(thread_id, thread_type, client)

def handle_vt_answer_command(message, message_object, thread_id, thread_type, author_id, client):
    print(f"DEBUG: handle_vt_answer_command() được gọi cho thread {thread_id} với message: {message}")
    client.sendReaction(message_object, "✅", thread_id, thread_type, reactionType=75)
    parts = message.split(maxsplit=1)
    if len(parts) < 2:
        error_message = Message(text="❌ Cú pháp không hợp lệ.\n👉 Vui lòng nhập: tlvt <đáp án>")
        client.replyMessage(error_message, message_object, thread_id, thread_type, ttl=DEFAULT_REPLY_TTL)
        print("DEBUG: Cú pháp sai trong handle_vt_answer_command()")
        return
    now = time.time()
    if thread_id not in active_games:
        error_message = Message(text="⚠️ Chưa có trò chơi nào đang hoạt động.\n👉 Hãy nhập vt để bắt đầu trò chơi.")
        client.replyMessage(error_message, message_object, thread_id, thread_type, ttl=DEFAULT_REPLY_TTL)
        print(f"DEBUG: Không có phiên chơi nào cho thread {thread_id}")
        return
    game_info = active_games[thread_id]
    elapsed = now - game_info["timestamp"]
    if elapsed >= GAME_VALID_SECONDS:
        active_games.pop(thread_id, None)
        error_message = Message(text="⌛ Câu hỏi đã hết thời gian hiệu lực.\n👉 Hãy nhập vt để bắt đầu trò chơi mới.")
        client.replyMessage(error_message, message_object, thread_id, thread_type, ttl=DEFAULT_REPLY_TTL)
        print(f"DEBUG: Phiên chơi cho thread {thread_id} đã hết hạn trong handle_vt_answer_command()")
        if auto_mode.get(thread_id, False):
            send_question_auto(thread_id, thread_type, client)
        return
    user_answer = parts[1].strip().lower()
    correct_answer = game_info["answer"]
    print(f"DEBUG: Đáp án người dùng: {user_answer} - Đáp án đúng: {correct_answer}")
    if user_answer == correct_answer:
        active_games.pop(thread_id, None)
        reply_text = "🎉 Quá đỉnh! Bạn đã trả lời rất chính xác.\n👉 Câu hỏi tiếp theo:"
        client.replyMessage(Message(text=reply_text), message_object, thread_id, thread_type, ttl=DEFAULT_REPLY_TTL)
        print(f"DEBUG: Người dùng trả lời đúng cho thread {thread_id}")
        if auto_mode.get(thread_id, False):
            send_question_auto(thread_id, thread_type, client)
    else:
        remaining = int(GAME_VALID_SECONDS - elapsed)
        reply_text = f"❌ Sai rồi, hãy thử lại. Câu hỏi còn hiệu lực trong {remaining} giây."
        client.replyMessage(Message(text=reply_text), message_object, thread_id, thread_type, ttl=5000)
        print(f"DEBUG: Người dùng trả lời sai cho thread {thread_id}")

def handle_stop_command(message, message_object, thread_id, thread_type, author_id, client):
    print(f"DEBUG: handle_stop_command() được gọi cho thread {thread_id}")
    auto_mode[thread_id] = False
    if thread_id in auto_timers:
        timer = auto_timers.pop(thread_id)
        timer.cancel()
        print(f"DEBUG: Huỷ timer cho thread {thread_id} trong handle_stop_command()")
    client.replyMessage(Message(text="🛑 Chế độ tự động gửi câu hỏi đã dừng."), message_object, thread_id, thread_type, ttl=DEFAULT_REPLY_TTL)

def get_mitaizl():
    return {
        'vt': handle_vt_command,
        'tlvt': handle_vt_answer_command,
        'vtstop': handle_stop_command
    }
