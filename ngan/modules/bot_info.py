import json, re, time, threading
from threading import Thread
from zlapi import ZaloAPI
from zlapi.models import *
import regex as re  # Cần cài đặt thư viện 'regex' (pip install regex)

SETTING_FILE, CONFIG_FILE = 'setting.json', 'config.json'
URL_REGEX = re.compile(r'http[s]?://(?:[a-zA-Z0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
# Biểu thức regex để kiểm tra chuỗi chỉ chứa emoji (có thể tùy chỉnh thêm)
EMOJI_PATTERN = re.compile(r'^(?:\p{Emoji}|\p{Extended_Pictographic})+$')
# Global cache dùng để kiểm tra nội dung tin nhắn trùng lặp
last_message_cache = {}
last_message_cache_lock = threading.Lock()  # Thêm lock cho biến toàn cục này

# -----------------------------------------
# Lớp SettingsManager: Quản lý việc đọc/ghi file settings
# -----------------------------------------
class SettingsManager:
    def __init__(self, filename=SETTING_FILE):
        self.filename = filename
        self.lock = threading.RLock()  # Sử dụng RLock để hỗ trợ giao dịch cập nhật nhiều bước
        self._cache = None

    def load(self):
        with self.lock:
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    self._cache = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                self._cache = {}
            return self._cache

    def save(self):
        with self.lock:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=4)

    def atomic_update(self, update_fn):
        """Thực hiện cập nhật settings dưới 1 giao dịch duy nhất"""
        with self.lock:
            self.load()  # Tải settings hiện tại
            update_fn(self._cache)  # Thực hiện các thay đổi qua hàm callback
            self.save()

    def get(self, key, default=None):
        with self.lock:
            self.load()
            return self._cache.get(key, default)

    def update(self, key, value):
        self.atomic_update(lambda s: s.update({key: value}))

    def setdefault(self, key, default):
        with self.lock:
            self.load()
            result = self._cache.setdefault(key, default)
            self.save()
            return result

    def delete_key(self, key):
        with self.lock:
            self.load()
            if key in self._cache:
                del self._cache[key]
                self.save()

# Tạo instance settings_manager
settings_manager = SettingsManager()

def read_settings():
    return settings_manager.load()

def write_settings(s):
    # Ghi đè toàn bộ settings (đã được cập nhật qua giao dịch atomic nếu cần)
    settings_manager.atomic_update(lambda cache: cache.update(s))

def load_message_log():
    return read_settings().get("message_log", {})

def save_message_log(log):
    def updater(s):
        s["message_log"] = log
    settings_manager.atomic_update(updater)

def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            return config.get('imei'), config.get('cookies')
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"Error: File {CONFIG_FILE} không tồn tại hoặc định dạng không hợp lệ.")
        return None, None

# -----------------------------------------
# Các hàm xử lý tin nhắn
# -----------------------------------------
def extract_message_text(msg_obj):
    if msg_obj.msgType == 'chat.sticker':
        return ""
    c = msg_obj.content
    return c.get('title', "") if isinstance(c, dict) else (c if isinstance(c, str) else "")

get_content_message = extract_message_text

def is_url_in_message(msg_obj):
    return bool(URL_REGEX.search(extract_message_text(msg_obj)))

# -----------------------------------------
# Hàm kiểm soát spam (dựa trên message_log)
# -----------------------------------------
def is_spamming(author_id, thread_id):
    max_msgs, time_win, min_int = 5, 5, 5
    log = load_message_log()
    key = f"{thread_id}_{author_id}"
    now = time.time()
    user_data = log.get(key, {"last_message_time": 0, "message_times": []})
    lt = user_data["last_message_time"]
    times = [t for t in user_data["message_times"] if now - t <= time_win]
    if now - lt < min_int and sum(1 for t in times if now - t <= min_int) >= 10:
        return True
    times.append(now)
    user_data.update({"last_message_time": now, "message_times": times})
    log[key] = user_data
    save_message_log(log)
    return len(times) > max_msgs

# -----------------------------------------
# Các hàm quản lý admin, nhóm, từ cấm
# -----------------------------------------
def is_admin(author_id):
    return author_id in read_settings().get("admin_bot", [])

def handle_bot_admin(bot):
    s = read_settings()
    admin_bot = s.get("admin_bot", [])
    if bot.uid not in admin_bot:
        admin_bot.append(bot.uid)
        s['admin_bot'] = admin_bot
        write_settings(s)
        print(f"Đã thêm {get_user_name_by_id(bot, bot.uid)} (ID: {bot.uid}) vào danh sách Admin BOT.")

def get_allowed_thread_ids():
    return read_settings().get('allowed_threads', [])

def toggle_group(bot, thread_id, enable=True):
    s = read_settings()
    allowed = s.get('allowed_threads', [])
    group = bot.fetchGroupInfo(thread_id).gridInfoMap[thread_id]
    if enable:
        if thread_id in allowed:
            return f"⚠ Group {group.name} đã được bật trước đó."
        allowed.append(thread_id)
        s['allowed_threads'] = allowed
        write_settings(s)
        return f"👥 Group: {group.name}\n🆔 ID: {thread_id}\n✅ Bot đã được bật trong nhóm"
    else:
        if thread_id not in allowed:
            return f"⚠ Group {group.name} chưa được kích hoạt."
        allowed.remove(thread_id)
        s['allowed_threads'] = allowed
        write_settings(s)
        return f"👥 Group: {group.name}\n🆔 ID: {thread_id}\n🔴 Bot đã được tắt trong nhóm"

def add_forbidden_word(word):
    s = read_settings()
    words = s.get('forbidden_words', [])
    if word not in words:
        words.append(word)
        s['forbidden_words'] = words
        write_settings(s)
        return f"🟢 Từ '{word}' đã được thêm vào danh sách từ cấm."
    return f"⚠️ Từ '{word}' đã tồn tại trong danh sách từ cấm."

def remove_forbidden_word(word):
    s = read_settings()
    words = s.get('forbidden_words', [])
    if word in words:
        words.remove(word)
        s['forbidden_words'] = words
        write_settings(s)
        return f"✅ Từ '{word}' đã được xóa khỏi danh sách từ cấm."
    return f"❌ Từ '{word}' không có trong danh sách từ cấm."

def is_forbidden_word(word):
    return word in read_settings().get('forbidden_words', [])

def setup_bot_on(bot, thread_id):
    group = bot.fetchGroupInfo(thread_id).gridInfoMap[thread_id]
    admin_ids = group.adminIds.copy()
    if group.creatorId not in admin_ids:
        admin_ids.append(group.creatorId)
    if bot.uid in admin_ids:
        s = read_settings()
        s.setdefault('group_admins', {})[thread_id] = admin_ids
        write_settings(s)
        return f"⚙️ Cấu hình: 🟢 BẬT\n👥 Nhóm: {group.name} (ID: {thread_id})\n✅ Bot đã được quyền cấm người dùng"
    return f"⚙️ Cấu hình: 🔴 TẮT\n👥 Nhóm: {group.name} (ID: {thread_id})\n❌ Bạn không có quyền quản trị nhóm này!"

def setup_bot_off(bot, thread_id):
    group = bot.fetchGroupInfo(thread_id).gridInfoMap[thread_id]
    s = read_settings()
    if s.get('group_admins', {}).pop(thread_id, None) is not None:
        write_settings(s)
        return f"⚙️ Cấu hình: 🔴 TẮT\n👥 {group.name}\n🆔 ID: {thread_id}"
    return f"⚙️ Cấu hình: 🔴 TẮT\n👥 {group.name}\n🆔 ID: {thread_id}\n❌ Không tìm thấy cấu hình quản trị cho nhóm này"

def check_admin_group(bot, thread_id):
    group = bot.fetchGroupInfo(thread_id).gridInfoMap[thread_id]
    admin_ids = group.adminIds.copy()
    if group.creatorId not in admin_ids:
        admin_ids.append(group.creatorId)
    s = read_settings()
    s.setdefault('group_admins', {})[thread_id] = admin_ids
    write_settings(s)
    return bot.uid in admin_ids

def get_ban_link_status(thread_id):
    return read_settings().get('ban_link', {}).get(thread_id, False)

def is_user_muted(author_id, thread_id):
    s = read_settings()
    now = time.time()
    for user in s.get("muted_users", []):
        if user["author_id"] == author_id and user["thread_id"] == thread_id and now < user["muted_until"]:
            return True
    return False

# -----------------------------------------
# Các hàm quản lý cấm media và link
# -----------------------------------------
def set_media_ban(thread_id, media_type, status):
    settings = read_settings()
    key = f"ban_{media_type}"
    group_settings = settings.get(key, {})
    if group_settings.get(thread_id) == status:
        return f"⚠ {media_type.capitalize()} đã được {'bật' if status else 'tắt'} trước đó."
    group_settings[thread_id] = status
    settings[key] = group_settings
    write_settings(settings)
    return f"✅ Đã {'bật' if status else 'tắt'} cấm {media_type} trong nhóm."

def set_ban_link(thread_id, status):
    settings = read_settings()
    group_settings = settings.get('ban_link', {})
    if group_settings.get(thread_id) == status:
        return f"⚠ Link đã được {'cấm' if status else 'cho phép'} trước đó."
    group_settings[thread_id] = status
    settings['ban_link'] = group_settings
    write_settings(settings)
    return f"✅ Đã {'cấm' if status else 'cho phép'} gửi link trong nhóm."

def is_image_message(msg_obj):
    return msg_obj.msgType == "chat.photo"

def is_video_message(msg_obj):
    return msg_obj.msgType == "chat.video.msg"

def is_sticker_message(msg_obj):
    return msg_obj.msgType == "chat.sticker"

def is_gif_message(msg_obj):
    return msg_obj.msgType == "chat.gif"

def is_file_message(msg_obj):
    return msg_obj.msgType in ["chat.file", "share.file", "chat.attachment", "chat.doc"]

def is_voice_message(msg_obj):
    return msg_obj.msgType == "chat.voice"

def is_emoji_message(msg_obj):
    content = extract_message_text(msg_obj).strip()
    if content and EMOJI_PATTERN.fullmatch(content):
        return True
    return False

SEX_KEYWORDS = ["sex", "nude", "porn", "xxx"]

def is_sex_image(msg_obj):
    caption = extract_message_text(msg_obj)
    for keyword in SEX_KEYWORDS:
        if keyword.lower() in caption.lower():
            return True
    return False

def handle_media_content(bot, author_id, thread_id, msg_obj, thread_type):
    if author_id == bot.uid:
        return
    if is_admin(author_id):
        return    
    if is_user_muted(author_id, thread_id):
        bot.deleteGroupMsg(msg_obj.msgId, author_id, msg_obj.cliMsgId, thread_id)
        return        
    s = read_settings()
    if author_id in s.get("excluded_users", []):
        return        
    settings = read_settings()
    if settings.get("ban_image", {}).get(thread_id, False) and is_image_message(msg_obj):
        bot.deleteGroupMsg(msg_obj.msgId, author_id, msg_obj.cliMsgId, thread_id)
        return True
    if settings.get("ban_video", {}).get(thread_id, False) and is_video_message(msg_obj):
        bot.deleteGroupMsg(msg_obj.msgId, author_id, msg_obj.cliMsgId, thread_id)
        return True
    if settings.get("ban_sticker", {}).get(thread_id, False) and is_sticker_message(msg_obj):
        bot.deleteGroupMsg(msg_obj.msgId, author_id, msg_obj.cliMsgId, thread_id)
        return True
    if settings.get("ban_gif", {}).get(thread_id, False) and is_gif_message(msg_obj):
        bot.deleteGroupMsg(msg_obj.msgId, author_id, msg_obj.cliMsgId, thread_id)
        return True
    if settings.get("ban_sex", {}).get(thread_id, False) and is_image_message(msg_obj) and is_sex_image(msg_obj):
        bot.deleteGroupMsg(msg_obj.msgId, author_id, msg_obj.cliMsgId, thread_id)
        return True
    if settings.get("ban_file", {}).get(thread_id, False) and is_file_message(msg_obj):
        bot.deleteGroupMsg(msg_obj.msgId, author_id, msg_obj.cliMsgId, thread_id)
        return True
    if settings.get("ban_voice", {}).get(thread_id, False) and is_voice_message(msg_obj):
        bot.deleteGroupMsg(msg_obj.msgId, author_id, msg_obj.cliMsgId, thread_id)
        return True
    if settings.get("ban_emoji", {}).get(thread_id, False) and is_emoji_message(msg_obj):
        bot.deleteGroupMsg(msg_obj.msgId, author_id, msg_obj.cliMsgId, thread_id)
        return True
    return False

# -----------------------------------------
# Các hàm cài đặt chế độ cấm tin nhắn dài, nội dung trùng lặp, tag người dùng
# -----------------------------------------
def set_longmsg_ban(thread_id, status):
    settings = read_settings()
    key = "ban_longmsg"
    group_settings = settings.get(key, {})
    if group_settings.get(thread_id) == status:
        return f"⚠ Chế độ cấm tin nhắn quá dài đã được {'bật' if status else 'tắt'} trước đó."
    group_settings[thread_id] = status
    settings[key] = group_settings
    write_settings(settings)
    return f"✅ Đã {'bật' if status else 'tắt'} cấm tin nhắn quá dài trong nhóm."

def set_duplicate_ban(thread_id, status):
    settings = read_settings()
    key = "ban_duplicate"
    group_settings = settings.get(key, {})
    if group_settings.get(thread_id) == status:
        return f"⚠ Chế độ cấm nội dung trùng lặp đã được {'bật' if status else 'tắt'} trước đó."
    group_settings[thread_id] = status
    settings[key] = group_settings
    write_settings(settings)
    return f"✅ Đã {'bật' if status else 'tắt'} cấm nội dung trùng lặp trong nhóm."

def set_tag_ban(thread_id, status):
    settings = read_settings()
    key = "ban_tag"
    group_settings = settings.get(key, {})
    if group_settings.get(thread_id) == status:
        return f"⚠ Chế độ cấm tag người dùng đã được {'bật' if status else 'tắt'} trước đó."
    group_settings[thread_id] = status
    settings[key] = group_settings
    write_settings(settings)
    return f"✅ Đã {'bật' if status else 'tắt'} cấm tag người dùng trong nhóm."

# -----------------------------------------
# Xử lý vi phạm: spam, từ cấm và các chế độ cấm bổ sung
# -----------------------------------------
def handle_check_profanity(bot, author_id, thread_id, msg_obj, thread_type, message):
    if author_id == bot.uid:
       return
    if is_admin(author_id):
       return        
    if is_user_muted(author_id, thread_id):
        bot.deleteGroupMsg(msg_obj.msgId, author_id, msg_obj.cliMsgId, thread_id)
        return        
    def send_response():
        s = read_settings()
        if author_id in s.get("excluded_users", []):
            return
        admin_ids = s.get('group_admins', {}).get(thread_id, [])
        if bot.uid not in admin_ids:
            return
        if is_spamming(author_id, thread_id):
            bot.kickUsersInGroup(author_id, thread_id)
            bot.blockUsersInGroup(author_id, thread_id)
            return
        if get_ban_link_status(thread_id) and is_url_in_message(msg_obj):
            bot.deleteGroupMsg(msg_obj.msgId, author_id, msg_obj.cliMsgId, thread_id)
            return
        if not isinstance(message, str):
            return
        txt = message
        group_admin_ids = s.get('group_admins', {}).get(thread_id, [])
        if not (is_admin(author_id) or author_id in group_admin_ids):
            if s.get("ban_longmsg", {}).get(thread_id, False):
                threshold_long = 200
                if len(txt) > threshold_long:
                    bot.deleteGroupMsg(msg_obj.msgId, author_id, msg_obj.cliMsgId, thread_id)
                    return
            if s.get("ban_duplicate", {}).get(thread_id, False):
                duplicate_window = 60
                key = f"last_msg_{thread_id}_{author_id}"
                with last_message_cache_lock:
                    last_info = last_message_cache.get(key, {"msg": "", "time": 0})
                    current_time = time.time()
                    if current_time - last_info["time"] < duplicate_window and \
                       last_info["msg"].strip().lower() == txt.strip().lower():
                        bot.deleteGroupMsg(msg_obj.msgId, author_id, msg_obj.cliMsgId, thread_id)
                        return
                    last_message_cache[key] = {"msg": txt, "time": current_time}
            if s.get("ban_tag", {}).get(thread_id, False):
                if hasattr(msg_obj, "mentions") and msg_obj.mentions:
                    bot.deleteGroupMsg(msg_obj.msgId, author_id, msg_obj.cliMsgId, thread_id)
                    return
        forbidden = s.get('forbidden_words', [])
        violations = s.get('violations', {})
        rules = s.get("rules", {})
        now = int(time.time())
        word_rule = rules.get("word", {"threshold": 3, "duration": 30})
        thresh, dur = word_rule["threshold"], word_rule["duration"]
        if any(word.lower() in txt.lower() for word in forbidden):
            bot.deleteGroupMsg(msg_obj.msgId, author_id, msg_obj.cliMsgId, thread_id)
            user_v = violations.setdefault(author_id, {}).setdefault(thread_id, {"profanity_count": 0, "spam_count": 0, "penalty_level": 0})
            user_v["profanity_count"] += 1
            count = user_v["profanity_count"]
            if count >= thresh:
                user_v["penalty_level"] += 1
                s.setdefault("muted_users", []).append({
                    "author_id": author_id,
                    "thread_id": thread_id,
                    "reason": txt,
                    "muted_until": now + 60 * dur
                })
                write_settings(s)
                resp = f"❌ Bạn đã vượt quá {thresh} lần vi phạm và bị mute {dur} phút.\nℹ️ Nội dung: '{txt}'"
                bot.replyMessage(Message(text=resp), msg_obj, thread_id=thread_id, thread_type=thread_type, ttl=60000)
                return
            elif count == thresh - 1:
                resp = f"⚠️ Cảnh báo: {count}/{thresh} lần vi phạm. Nếu tái phạm, bạn sẽ bị mute {dur} phút.\nℹ️ Nội dung: '{txt}'"
                bot.replyMessage(Message(text=resp), msg_obj, thread_id=thread_id, thread_type=thread_type, ttl=100000)
            else:
                resp = f"⚠️ Bạn đã vi phạm {count}/{thresh} lần. Hãy kiểm soát lời nói!"
                bot.replyMessage(Message(text=resp), msg_obj, thread_id=thread_id, thread_type=thread_type, ttl=10000)
            write_settings(s)
    Thread(target=send_response).start()

# -----------------------------------------
# Các hàm hiển thị thông tin
# -----------------------------------------
def get_user_name_by_id(bot, author_id):
    try:
        return bot.fetchUserInfo(author_id).changed_profiles[author_id].displayName
    except:
        return "Unknown User"

def print_muted_users_in_group(bot, thread_id):
    s = read_settings()
    now = int(time.time())
    muted = [{
        "author_id": u['author_id'],
        "name": get_user_name_by_id(bot, u['author_id']),
        "minutes_left": (u['muted_until'] - now) // 60,
        "reason": u['reason']
    } for u in s.get("muted_users", []) if u['thread_id'] == thread_id and u['muted_until'] > now]
    muted.sort(key=lambda x: x['minutes_left'])
    if muted:
        return ("🔒 Danh sách thành viên bị mute:\n" +
                "\n".join(f"{i}. {u['name']} - {u['minutes_left']} phút - Lý do: {u['reason']}" for i, u in enumerate(muted, 1)))
    else:
        return "✅ Nhóm này không có thành viên bị mute!"

def print_blocked_users_in_group(bot, thread_id):
    s = read_settings()
    blocked = s.get("block_user_group", {}).get(thread_id, {}).get("blocked_users", [])
    lst = [{"author_id": uid, "name": get_user_name_by_id(bot, uid)} for uid in blocked]
    lst.sort(key=lambda x: x['name'])
    if lst:
        return ("🚫 Danh sách thành viên bị chặn:\n" +
                "\n".join(f"{i}. {u['name']} (ID: {u['author_id']})" for i, u in enumerate(lst, 1)))
    else:
        return "✅ Không có thành viên nào bị chặn trong nhóm!"

def add_users_to_ban_list(bot, author_ids, thread_id, reason):
    s = read_settings()
    now = int(time.time())
    muted = s.get("muted_users", [])
    violations = s.get("violations", {})
    dur = s.get("rules", {}).get("word", {}).get("duration", 30)
    resp = ""
    for uid in author_ids:
        uname = get_user_name_by_id(bot, uid)
        if not any(m["author_id"] == uid and m["thread_id"] == thread_id for m in muted):
            muted.append({"author_id": uid, "thread_id": thread_id, "reason": reason, "muted_until": now + 60 * dur})
        violations.setdefault(uid, {}).setdefault(thread_id, {"profanity_count": 0, "spam_count": 0, "penalty_level": 0})
        violations[uid][thread_id]["profanity_count"] += 1
        violations[uid][thread_id]["penalty_level"] += 1
        resp += f"⛔ {uname} đã bị cấm phát ngôn {dur} phút!\n"
    s["muted_users"], s["violations"] = muted, violations
    write_settings(s)
    return resp

def remove_users_from_ban_list(bot, author_ids, thread_id):
    s = read_settings()
    muted = s.get("muted_users", [])
    violations = s.get("violations", {})
    resp = ""
    for uid in author_ids:
        uname = get_user_name_by_id(bot, uid)
        new_muted = [m for m in muted if not (m["author_id"] == uid and m["thread_id"] == thread_id)]
        removed = len(muted) != len(new_muted)
        muted = new_muted
        if uid in violations and thread_id in violations[uid]:
            del violations[uid][thread_id]
            if not violations[uid]:
                del violations[uid]
            removed = True
        resp += f"✅ {uname} đã được gỡ cấm phát ngôn!\n" if removed else f"⚠️ {uname} không có trong danh sách cấm!\n"
    s["muted_users"], s["violations"] = muted, violations
    write_settings(s)
    return resp

def block_users_from_group(bot, author_ids, thread_id):
    s = read_settings()
    s.setdefault("block_user_group", {}).setdefault(thread_id, {"blocked_users": []})
    blocked = []
    for uid in author_ids:
        uname = get_user_name_by_id(bot, uid)
        bot.blockUsersInGroup(uid, thread_id)
        if uid not in s["block_user_group"][thread_id]["blocked_users"]:
            s["block_user_group"][thread_id]["blocked_users"].append(uid)
        blocked.append(uname)
    write_settings(s)
    if blocked:
        return f"🚫 {', '.join(blocked)} đã bị chặn khỏi nhóm!"
    else:
        return "✅ Không có ai bị chặn khỏi nhóm!"

def unblock_users_from_group(bot, author_ids, thread_id):
    s = read_settings()
    unblocked = []
    if thread_id in s.get("block_user_group", {}):
        blocked = s["block_user_group"][thread_id]["blocked_users"]
        for uid in author_ids:
            uname = get_user_name_by_id(bot, uid)
            if uid in blocked:
                bot.unblockUsersInGroup(uid, thread_id)
                blocked.remove(uid)
                unblocked.append(uname)
        if not blocked:
            del s["block_user_group"][thread_id]
        write_settings(s)
    if unblocked:
        return f"✅ {', '.join(unblocked)} đã được bỏ chặn khỏi nhóm"
    else:
        return "🚫 Không có ai bị chặn trong nhóm"

def kick_users_from_group(bot, uids, thread_id):
    resp = ""
    for uid in uids:
        try:
            bot.kickUsersInGroup(uid, thread_id)
            bot.blockUsersInGroup(uid, thread_id)
            resp += f"✅ Đã kick {get_user_name_by_id(bot, uid)} khỏi nhóm thành công\n"
        except Exception:
            resp += f"🚫 Không thể kick {get_user_name_by_id(bot, uid)} khỏi nhóm\n"
    return resp

def extract_uids_from_mentions(msg_obj):
    return [m["uid"] for m in msg_obj.mentions if "uid" in m]

def add_admin(bot, author_id, mentioned_uids, s):
    admin_bot = s.get("admin_bot", [])
    resp = ""
    for uid in mentioned_uids:
        if author_id not in admin_bot:
            resp = "🚫 Bạn không có quyền sử dụng lệnh này!"
        elif uid not in admin_bot:
            admin_bot.append(uid)
            resp = f"✅ Đã thêm {get_user_name_by_id(bot, uid)} vào danh sách Admin BOT"
        else:
            resp = f"⚠️ {get_user_name_by_id(bot, uid)} đã có trong danh sách Admin BOT"
    s["admin_bot"] = admin_bot
    write_settings(s)
    return resp

def remove_admin(bot, author_id, mentioned_uids, s):
    admin_bot = s.get("admin_bot", [])
    resp = ""
    for uid in mentioned_uids:
        if author_id not in admin_bot:
            resp = "⛔ Bạn không có quyền sử dụng lệnh này!"
        elif uid in admin_bot:
            admin_bot.remove(uid)
            resp = f"✅ Đã xóa {get_user_name_by_id(bot, uid)} khỏi danh sách Admin BOT"
        else:
            resp = f"⚠️ {get_user_name_by_id(bot, uid)} không có trong danh sách Admin BOT"
    s["admin_bot"] = admin_bot
    write_settings(s)
    return resp

def list_forbidden_groups(bot):
    s = read_settings()
    ban_keys = ['ban_link', 'ban_image', 'ban_video', 'ban_sticker', 'ban_gif',
                'ban_longmsg', 'ban_duplicate', 'ban_tag', 'ban_sex',
                'ban_file', 'ban_voice', 'ban_emoji']
    groups = {}
    for key in ban_keys:
        ban_dict = s.get(key, {})
        for thread_id, status in ban_dict.items():
            if status:
                groups.setdefault(thread_id, []).append(key)
    allowed = s.get('allowed_threads', [])
    for thread_id in allowed:
        groups.setdefault(thread_id, []).append("✅ Bot")
    group_admins = s.get('group_admins', {})
    for thread_id in group_admins:
        groups.setdefault(thread_id, []).append("⚙️ Bot setup")
    if not groups:
        return "Không có nhóm nào được bật các cài đặt."
    result = "📋 Danh sách nhóm bật các cài đặt:\n"
    for thread_id, commands in groups.items():
        try:
            group = bot.fetchGroupInfo(thread_id).gridInfoMap[thread_id]
            group_name = group.name
        except Exception:
            group_name = "Unknown"
        result += f"\n👥 Nhóm: {group_name}\n🆔 ID: {thread_id}\n⚙️ Các cài đặt bật: {', '.join(commands)}\n"
    return result

# -----------------------------------------
# Hàm xử lý lệnh của BOT
# -----------------------------------------
def handle_bot_command(message, msg_obj, thread_id, thread_type, author_id, bot):
    if "bott" in msg_obj.content.lower():
        bot.sendReaction(msg_obj, "✅", thread_id, thread_type, reactionType=75)
    parts = msg_obj.content.split()
    if len(parts) == 1:
         response = (
            "🇧 🇴 🇹 & 🇨 🇴 🇲 🇲 🇦 🇳 🇩\n\n"
            "-------------------------------------\n"
            "📌 Cài đặt & Quản lý:\n"
            "-------------------------------------\n"
            "📑 𝗯𝗼𝘁 𝗶𝗻𝗳𝗼 — Bật/tắt bot trong nhóm\n"
            "⚙️ 𝗯𝗼𝘁 𝗼𝗻/𝗼𝗳𝗳 — Bật/tắt bot trong nhóm\n"
            "👑 𝗯𝗼𝘁 𝗮𝗱𝗺𝗶𝗻 𝗮𝗱𝗱/𝗿𝗲𝗺𝗼𝘃𝗲/𝗹𝗶𝘀𝘁 — Quản lý Admin BOT\n"
            "📜 𝗯𝗼𝘁 𝗻𝗼𝗶𝗾𝘂𝘆 — Xem nội quy nhóm\n"
            "-------------------------------------\n"
            "🚨 Kiểm soát thành viên:\n"
            "-------------------------------------\n"
            "🔇 𝗯𝗼𝘁 𝗯𝗮𝗻/𝘂𝗻𝗯𝗮𝗻/𝗹𝗶𝘀𝘁 — Khóa/mở mõm thành viên\n"
            "🚫 𝗯𝗼𝘁 𝗸𝗶𝗰𝗸 @𝘂𝘀𝗲𝗿 — Loại thành viên khỏi nhóm\n"
            "🚫 𝗯𝗼𝘁 𝗯𝗹𝗼𝗰𝗸/𝘂𝗻𝗯𝗹𝗼𝗰𝗸/𝗹𝗶𝘀𝘁 — Chặn/mở chặn thành viên\n"
            "-------------------------------------\n"
            "🔍 Bảo vệ & Lọc nội dung:\n"
            "-------------------------------------\n"
            "🔗 𝗯𝗼𝘁 𝗹𝗶𝗻𝗸 𝗼𝗻/𝗼𝗳𝗳 — Cấm/cho phép gửi link\n"
            "🖼️ 𝗯𝗼𝘁 𝗶𝗺𝗮𝗴𝗲 𝗼𝗻/𝗼𝗳𝗳 — Cấm/cho phép gửi ảnh\n"
            "🎥 𝗯𝗼𝘁 𝘃𝗶𝗱𝗲𝗼 𝗼𝗻/𝗼𝗳𝗳 — Cấm/cho phép gửi video\n"
            "💬 𝗯𝗼𝘁 𝘀𝘁𝗶𝗰𝗸𝗲𝗿 𝗼𝗻/𝗼𝗳𝗳 — Cấm/cho phép gửi sticker\n"
            "🎞️ 𝗯𝗼𝘁 𝗴𝗶𝗳 𝗼𝗻/𝗼𝗳𝗳 — Cấm/cho phép gửi GIF\n"
            "📁 𝗯𝗼𝘁 𝗳𝗶𝗹𝗲 𝗼𝗻/𝗼𝗳𝗳 — Cấm/cho phép gửi file\n"
            "🎤 𝗯𝗼𝘁 𝘃𝗼𝗶𝗰𝗲 𝗼𝗻/𝗼𝗳𝗳 — Cấm/cho phép gửi voice\n"
            "😀 𝗯𝗼𝘁 𝗲𝗺𝗼𝗷𝗶 𝗼𝗻/𝗼𝗳𝗳 — Cấm/cho phép gửi emoji\n"
            "⏱️ 𝗯𝗼𝘁 𝗹𝗼𝗻𝗴𝗺𝘀𝗴 𝗼𝗻/𝗼𝗳𝗳 — Cấm/cho phép gửi tin nhắn quá dài\n"
            "📑 𝗯𝗼𝘁 𝗱𝘂𝗽𝗹𝗶𝗰𝗮𝘁𝗲 𝗼𝗻/𝗼𝗳𝗳 — Cấm/cho phép gửi nội dung trùng lặp\n"
            "🏷️ 𝗯𝗼𝘁 𝘁𝗮𝗴 𝗼𝗻/𝗼𝗳𝗳 — Cấm/cho phép tag người dùng\n"
            "🔞 𝗯𝗼𝘁 𝗮𝘀𝗲𝘅 𝗼𝗻/𝗼𝗳𝗳 — Cấm/cho phép ảnh 18+\n"
            "📷 𝗯𝗼𝘁 𝗮𝗹𝗹 𝗼𝗻/𝗼𝗳𝗳 — Bật/tắt đồng loạt tất cả các chức năng\n"
            "🏷️ 𝗯𝗼𝘁 𝘀𝗸𝗶𝗽 𝗮𝗱𝗱/𝗿𝗲𝗺𝗼𝘃𝗲/𝗹𝗶𝘀𝘁 — Bỏ qua xử phạt cho người dùng\n"
            "-------------------------------------\n"
            "📋 𝗯𝗼𝘁 𝗯𝗮𝗻𝗹𝗶𝘀𝘁 — Xem cấu hình cấm hiện tại\n"
            "📋 𝗯𝗼𝘁 𝗴𝗿𝗼𝘂𝗽𝗯𝗮𝗻𝗹𝗶𝘀𝘁 — Xem danh sách nhóm bật các lệnh cấm\n"
         )
         bot.replyMessage(Message(text=response), msg_obj, thread_id=thread_id, thread_type=thread_type, ttl=25000)
         return
    if parts[1].lower() == 'info':
         response = (
            "THÔNG TIN BOT\n"
            "--------------\n"
            "🆙 Phiên bản         - Mới nhất\n"
            "📅 Ngày cập nhật     - 29/10/2024\n"
            "👑 Admin             - ROSY\n"
            "📖 Hướng dẫn         - /bot help\n"
            "⏳ Thời gian phản hồi - 1s\n"
            "⚡ Tổng lệnh hỗ trợ   - 160\n"
            "💻 Công nghệ          - Python, ZaloAPI\n"
            "🔒 Chế độ bảo vệ      - Link, Image, Video, Sticker, GIF, Sex, File, Voice, Emoji, Tin nhắn dài, Tag\n"
            "👥 Nhóm kích hoạt     - [Số nhóm]\n"
            "📢 Thông báo         - Mới mỗi giờ\n"
            "💬 Hỗ trợ            - support@example.com\n"
            "🌐 Website           - www.botrosy.com\n"
            "📝 Ghi chú           - Team ROSY phát triển\n"
            "Chúc bạn một ngày tuyệt vời! 😊"
         )
         bot.replyMessage(Message(text=response), msg_obj, thread_id=thread_id, thread_type=thread_type, ttl=25000)
         return
    if not is_admin(author_id):
         bot.replyMessage(Message(text="⛔ Bạn không có quyền sử dụng lệnh này!"), msg_obj, thread_id=thread_id, thread_type=thread_type, ttl=25000)
         return

    def send_bot_response():
        try:
            parts = msg_obj.content.split()
            if len(parts) == 1:
                response = (
                    "🇧 🇴 🇹 & 🇨 🇴 🇲 🇲 🇦 🇳 🇩\n"
                    "-------------------------------------\n"
                    "📌 Cài đặt & Quản lý:\n"
                    "-------------------------------------\n"
                    "📑 𝗯𝗼𝘁 𝗶𝗻𝗳𝗼 — Bật/tắt bot trong nhóm\n"
                    "⚙️ 𝗯𝗼𝘁 𝗼𝗻/𝗼𝗳𝗳 — Bật/tắt bot trong nhóm\n"
                    "👤 𝗯𝗼𝘁 𝗮𝗱𝗺𝗶𝗻 𝗮𝗱𝗱/𝗿𝗲𝗺𝗼𝘃𝗲/𝗹𝗶𝘀𝘁 — Quản lý Admin BOT\n"
                    "📜 𝗯𝗼𝘁 𝗻𝗼𝗶𝗾𝘂𝘆 — Xem nội quy nhóm\n"
                    "-------------------------------------\n"
                    "🚨 Kiểm soát thành viên:\n"
                    "-------------------------------------\n"
                    "🔇 𝗯𝗼𝘁 𝗯𝗮𝗻/𝘂𝗻𝗯𝗮𝗻/𝗹𝗶𝘀𝘁 — Khóa/mở mõm thành viên\n"
                    "🚫 𝗯𝗼𝘁 𝗸𝗶𝗰𝗸 @𝘂𝘀𝗲𝗿 — Loại thành viên khỏi nhóm\n"
                    "🚫 𝗯𝗼𝘁 𝗯𝗹𝗼𝗰𝗸/𝘂𝗻𝗯𝗹𝗼𝗰𝗸/𝗹𝗶𝘀𝘁 — Chặn/mở chặn thành viên\n"
                    "-------------------------------------\n"
                    "🔍 Bảo vệ & Lọc nội dung:\n"
                    "-------------------------------------\n"
                    "🔗 𝗯𝗼𝘁 𝗹𝗶𝗻𝗸 𝗼𝗻/𝗼𝗳𝗳 — Cấm/cho phép gửi link\n"
                    "🖼️ 𝗯𝗼𝘁 𝗶𝗺𝗮𝗴𝗲 𝗼𝗻/𝗼𝗳𝗳 — Cấm/cho phép gửi ảnh\n"
                    "🎥 𝗯𝗼𝘁 𝘃𝗶𝗱𝗲𝗼 𝗼𝗻/𝗼𝗳𝗳 — Cấm/cho phép gửi video\n"
                    "💬 𝗯𝗼𝘁 𝘀𝘁𝗶𝗰𝗸𝗲𝗿 𝗼𝗻/𝗼𝗳𝗳 — Cấm/cho phép gửi sticker\n"
                    "🎞️ 𝗯𝗼𝘁 𝗴𝗶𝗳 𝗼𝗻/𝗼𝗳𝗳 — Cấm/cho phép gửi GIF\n"
                    "📁 𝗯𝗼𝘁 𝗳𝗶𝗹𝗲 𝗼𝗻/𝗼𝗳𝗳 — Cấm/cho phép gửi file\n"
                    "🎤 𝗯𝗼𝘁 𝘃𝗼𝗶𝗰𝗲 𝗼𝗻/𝗼𝗳𝗳 — Cấm/cho phép gửi voice\n"
                    "😀 𝗯𝗼𝘁 𝗲𝗺𝗼𝗷𝗶 𝗼𝗻/𝗼𝗳𝗳 — Cấm/cho phép gửi emoji\n"
                    "⏱️ 𝗯𝗼𝘁 𝗹𝗼𝗻𝗴𝗺𝘀𝗴 𝗼𝗻/𝗼𝗳𝗳 — Cấm/cho phép gửi tin nhắn quá dài\n"
                    "📑 𝗯𝗼𝘁 𝗱𝘂𝗽𝗹𝗶𝗰𝗮𝘁𝗲 𝗼𝗻/𝗼𝗳𝗳 — Cấm/cho phép gửi nội dung trùng lặp\n"
                    "🏷️ 𝗯𝗼𝘁 𝘁𝗮𝗴 𝗼𝗻/𝗼𝗳𝗳 — Cấm/cho phép tag người dùng\n"
                    "🔞 𝗯𝗼𝘁 𝗮𝘀𝗲𝘅 𝗼𝗻/𝗼𝗳𝗳 — Cấm/cho phép ảnh 18+\n"
                    "📷 𝗯𝗼𝘁 𝗮𝗹𝗹 𝗼𝗻/𝗼𝗳𝗳 — Bật/tắt đồng loạt tất cả các chức năng\n"
                    "🏷️ 𝗯𝗼𝘁 𝘀𝗸𝗶𝗽 𝗮𝗱𝗱/𝗿𝗲𝗺𝗼𝘃𝗲/𝗹𝗶𝘀𝘁 — Bỏ qua xử phạt cho người dùng\n"
                    "-------------------------------------\n"
                    "📋 𝗯𝗼𝘁 𝗯𝗮𝗻𝗹𝗶𝘀𝘁 — Xem cấu hình cấm hiện tại\n"
                    "📋 𝗯𝗼𝘁 𝗴𝗿𝗼𝘂𝗽𝗯𝗮𝗻𝗹𝗶𝘀𝘁 — Xem danh sách nhóm bật các lệnh cấm\n"
                )
            else:
                act = parts[1].lower()
                if act == 'on':
                    if thread_type != ThreadType.GROUP:
                        response = "⚠ Lệnh này chỉ dùng trong nhóm!"
                    else:
                        response = toggle_group(bot, thread_id, True)
                elif act == 'off':
                    if thread_type != ThreadType.GROUP:
                        response = "⚠ Lệnh này chỉ dùng trong nhóm!"
                    else:
                        response = toggle_group(bot, thread_id, False)
                elif act == 'info':
                    response = (
                        "📌 Thông tin BOT\n"
                        "🆙 Phiên bản: Mới nhất\n"
                        "📅 Ngày cập nhật: 29/10/2024\n"
                        "👑 Admin: ROSY\n"
                        "📖 Cách dùng: /bot help\n"
                        "⏳ Thời gian phản hồi: 1s\n"
                        "⚡ Tổng lệnh hỗ trợ: 160\n"
                    )
                elif act == 'admin':
                    if len(parts) < 3:
                        response = "⚠ Cú pháp: bot admin [add/remove/list] @user"
                    else:
                        s = read_settings()
                        admin_bot = s.get("admin_bot", [])
                        sub = parts[2].lower()
                        if sub == 'add':
                            if len(parts) < 4:
                                response = "⚠ Cú pháp: bot admin add @user"
                            else:
                                uids = extract_uids_from_mentions(msg_obj)
                                response = add_admin(bot, author_id, uids, s)
                        elif sub == 'remove':
                            if len(parts) < 4:
                                response = "⚠ Cú pháp: bot admin remove @user"
                            else:
                                uids = extract_uids_from_mentions(msg_obj)
                                response = remove_admin(bot, author_id, uids, s)
                        elif sub == 'list':
                            response = ("📋 Danh sách Admin BOT:\n" +
                                        "\n".join(f"{i}. {get_user_name_by_id(bot, uid)} (ID: {uid})" 
                                                  for i, uid in enumerate(admin_bot, 1))
                                       ) if admin_bot else "⚠️ Không có Admin BOT nào."
                        else:
                            response = f"⚠️ Lệnh bot admin {sub} không được hỗ trợ."
                elif act == 'setup':
                    if len(parts) < 3:
                        response = "⚠ Cú pháp: bot setup on/off"
                    else:
                        sub = parts[2].lower()
                        if sub == 'on':
                            response = setup_bot_on(bot, thread_id)
                        elif sub == 'off':
                            response = setup_bot_off(bot, thread_id)
                        else:
                            response = f"⚠ Lệnh bot setup {sub} không được hỗ trợ."
                elif act == 'link':
                    if len(parts) < 3:
                        response = "⚠ Cú pháp: bot link on/off"
                    else:
                        sub = parts[2].lower()
                        if sub == 'on':
                            response = set_ban_link(thread_id, True)
                        elif sub == 'off':
                            response = set_ban_link(thread_id, False)
                        else:
                            response = "⚠ Cú pháp: bot link on/off"
                elif act == 'word':
                    if len(parts) < 3:
                        response = "⚠ Cú pháp: bot word add/remove/list [từ khóa]"
                    else:
                        sub = parts[2].lower()
                        if sub == 'list':
                            s = read_settings()
                            words = s.get('forbidden_words', [])
                            response = "📋 Danh sách từ cấm:\n" + "\n".join(f"- {w}" for w in words) if words else "✅ Không có từ cấm nào."
                        elif sub == 'add':
                            if len(parts) < 4:
                                response = "⚠ Cú pháp: bot word add <từ khóa>"
                            else:
                                word = ' '.join(parts[3:])
                                response = add_forbidden_word(word)
                        elif sub == 'remove':
                            if len(parts) < 4:
                                response = "⚠ Cú pháp: bot word remove <từ khóa>"
                            else:
                                word = ' '.join(parts[3:])
                                response = remove_forbidden_word(word)
                        else:
                            response = f"⚠ Lệnh bot word {sub} không được hỗ trợ."
                elif act == 'image':
                    if len(parts) < 3:
                        response = "⚠ Cú pháp: bot image on/off"
                    else:
                        toggle = parts[2].lower()
                        if toggle in ['on', 'off']:
                            status = (toggle == 'on')
                            response = set_media_ban(thread_id, 'image', status)
                        else:
                            response = "⚠ Cú pháp: bot image on/off"
                elif act == 'video':
                    if len(parts) < 3:
                        response = "⚠ Cú pháp: bot video on/off"
                    else:
                        toggle = parts[2].lower()
                        if toggle in ['on', 'off']:
                            status = (toggle == 'on')
                            response = set_media_ban(thread_id, 'video', status)
                        else:
                            response = "⚠ Cú pháp: bot video on/off"
                elif act == 'sticker':
                    if len(parts) < 3:
                        response = "⚠ Cú pháp: bot sticker on/off"
                    else:
                        toggle = parts[2].lower()
                        if toggle in ['on', 'off']:
                            status = (toggle == 'on')
                            response = set_media_ban(thread_id, 'sticker', status)
                        else:
                            response = "⚠ Cú pháp: bot sticker on/off"
                elif act == 'gif':
                    if len(parts) < 3:
                        response = "⚠ Cú pháp: bot gif on/off"
                    else:
                        toggle = parts[2].lower()
                        if toggle in ['on', 'off']:
                            status = (toggle == 'on')
                            response = set_media_ban(thread_id, 'gif', status)
                        else:
                            response = "⚠ Cú pháp: bot gif on/off"
                elif act == 'asex':
                    if len(parts) < 3:
                        response = "⚠ Cú pháp: bot asex on/off"
                    else:
                        toggle = parts[2].lower()
                        if toggle in ['on', 'off']:
                            status = (toggle == 'on')
                            response = set_media_ban(thread_id, 'sex', status)
                        else:
                            response = "⚠ Cú pháp: bot asex on/off"
                elif act == 'file':
                    if len(parts) < 3:
                        response = "⚠ Cú pháp: bot file on/off"
                    else:
                        toggle = parts[2].lower()
                        if toggle in ['on', 'off']:
                            status = (toggle == 'on')
                            response = set_media_ban(thread_id, 'file', status)
                        else:
                            response = "⚠ Cú pháp: bot file on/off"
                elif act == 'voice':
                    if len(parts) < 3:
                        response = "⚠ Cú pháp: bot voice on/off"
                    else:
                        toggle = parts[2].lower()
                        if toggle in ['on', 'off']:
                            status = (toggle == 'on')
                            response = set_media_ban(thread_id, 'voice', status)
                        else:
                            response = "⚠ Cú pháp: bot voice on/off"
                elif act == 'emoji':
                    if len(parts) < 3:
                        response = "⚠ Cú pháp: bot emoji on/off"
                    else:
                        toggle = parts[2].lower()
                        if toggle in ['on', 'off']:
                            status = (toggle == 'on')
                            response = set_media_ban(thread_id, 'emoji', status)
                        else:
                            response = "⚠ Cú pháp: bot emoji on/off"
                # Phần thêm cho duplicate:
                elif act == 'duplicate':
                    if len(parts) < 3:
                        response = "⚠ Cú pháp: bot duplicate on/off"
                    else:
                        toggle = parts[2].lower()
                        if toggle in ['on', 'off']:
                            status = (toggle == 'on')
                            response = set_duplicate_ban(thread_id, status)
                        else:
                            response = "⚠ Cú pháp: bot duplicate on/off"
                elif act == 'all':
                    if thread_type != ThreadType.GROUP:
                        response = "⚠ Lệnh này chỉ dùng trong nhóm!"
                    elif len(parts) < 3:
                        response = "⚠ Cú pháp: bot all on/off"
                    else:
                        toggle = parts[2].lower()
                        if toggle not in ['on', 'off']:
                            response = "⚠ Cú pháp: bot all on/off"
                        else:
                            status = (toggle == 'on')
                            responses = []
                            group_response = toggle_group(bot, thread_id, status)
                            responses.append("Bot: " + group_response)
                            if status:
                                setup_response = setup_bot_on(bot, thread_id)
                            else:
                                setup_response = setup_bot_off(bot, thread_id)
                            responses.append("⚙️ Setup: " + setup_response)
                            link_response = set_ban_link(thread_id, status)
                            responses.append("🔗 Link: " + link_response)
                            media_icons = {
                                'image': '🖼️',
                                'video': '🎥',
                                'sticker': '💬',
                                'gif': '🎞️',
                                'sex': '🔞',
                                'file': '📄',
                                'voice': '🎤',
                                'emoji': '😀'
                            }
                            for media in ['image', 'video', 'sticker', 'gif', 'sex', 'file', 'voice', 'emoji']:
                                res = set_media_ban(thread_id, media, status)
                                icon = media_icons.get(media, '')
                                responses.append(f"{icon} {media.capitalize()}: " + res)
                            res = set_longmsg_ban(thread_id, status)
                            responses.append("🗨️ Tin nhắn dài: " + res)
                            res = set_duplicate_ban(thread_id, status)
                            responses.append("📑 Nội dung trùng lặp: " + res)
                            res = set_tag_ban(thread_id, status)
                            responses.append("🏷 Tag người dùng: " + res)
                            response = "\n".join(responses)
                elif act == 'banlist':
                    s = read_settings()
                    config_str = "📋 *Cài đặt cấm hiện tại của nhóm:*\n\n"
                    allowed_threads = s.get("allowed_threads", [])
                    bot_status = "✅" if thread_id in allowed_threads else "❌"
                    config_str += f" 🤖 Bot: {bot_status}\n"
                    group_admins = s.get("group_admins", {})
                    setup_status = "✅" if thread_id in group_admins else "❌"
                    config_str += f" ⚙️ Bot setup: {setup_status}\n"
                    ban_link = s.get("ban_link", {}).get(thread_id, False)
                    link_status = "✅" if ban_link else "❌"
                    config_str += f" 🔗 Gửi link: {link_status}\n"
                    ban_image = s.get("ban_image", {}).get(thread_id, False)
                    image_status = "✅" if ban_image else "❌"
                    config_str += f" 🖼️ Gửi ảnh: {image_status}\n"
                    ban_video = s.get("ban_video", {}).get(thread_id, False)
                    video_status = "✅" if ban_video else "❌"
                    config_str += f" 🎥 Gửi video: {video_status}\n"
                    ban_sticker = s.get("ban_sticker", {}).get(thread_id, False)
                    sticker_status = "✅" if ban_sticker else "❌"
                    config_str += f" 💬 Sticker: {sticker_status}\n"
                    ban_gif = s.get("ban_gif", {}).get(thread_id, False)
                    gif_status = "✅" if ban_gif else "❌"
                    config_str += f" 🎞️ GIF: {gif_status}\n"
                    ban_file = s.get("ban_file", {}).get(thread_id, False)
                    file_status = "✅" if ban_file else "❌"
                    config_str += f" 📄 File: {file_status}\n"
                    ban_voice = s.get("ban_voice", {}).get(thread_id, False)
                    voice_status = "✅" if ban_voice else "❌"
                    config_str += f" 🎤 Voice: {voice_status}\n"
                    ban_emoji = s.get("ban_emoji", {}).get(thread_id, False)
                    emoji_status = "✅" if ban_emoji else "❌"
                    config_str += f" 😀 Emoji: {emoji_status}\n"
                    ban_longmsg = s.get("ban_longmsg", {}).get(thread_id, False)
                    longmsg_status = "✅" if ban_longmsg else "❌"
                    config_str += f" ⏱️ Tin nhắn dài: {longmsg_status}\n"
                    ban_duplicate = s.get("ban_duplicate", {}).get(thread_id, False)
                    duplicate_status = "✅" if ban_duplicate else "❌"
                    config_str += f" 📑 Nội dung trùng lặp: {duplicate_status}\n"
                    ban_tag = s.get("ban_tag", {}).get(thread_id, False)
                    tag_status = "✅" if ban_tag else "❌"
                    config_str += f" 🏷️ Tag người dùng: {tag_status}\n"
                    ban_sex = s.get("ban_sex", {}).get(thread_id, False)
                    sex_status = "✅" if ban_sex else "❌"
                    config_str += f" 🔞 Ảnh sex: {sex_status}\n"
                    response = config_str
                elif act == 'noiquy':
                    s = read_settings()
                    rules = s.get("rules", {})
                    word_rule = rules.get("word", {"threshold": 3, "duration": 30})
                    group = bot.fetchGroupInfo(thread_id).gridInfoMap[thread_id]
                    response = (f"✅ Nội quy đã được áp dụng\n📌 Nhóm: {group.name}\n📌 ID: {thread_id}\n"
                                f"✅ Cấm sủa trong nhóm\n✅ Vi phạm {word_rule['threshold']} lần sẽ bị khoá mõm {word_rule['duration']} phút\n"
                                f"✅ Nếu tái phạm 2 lần sẽ bị loại khỏi nhóm"
                               ) if s.get('group_admins', {}).get(thread_id) else (
                                f"⛔ Nội quy chưa được áp dụng\n📌 Nhóm: {group.name}\n📌 ID: {thread_id}\n"
                                f"⛔ Lý do: Chưa bật bot setup hoặc bot không giữ key nhóm"
                               )
                elif act == 'ban':
                    if len(parts) < 3:
                        response = "⚠ Cú pháp: bot ban/unban/list [@user]"
                    else:
                        sub = parts[2].lower()
                        if sub == 'list':
                            response = print_muted_users_in_group(bot, thread_id)
                        else:
                            if thread_type != ThreadType.GROUP or not check_admin_group(bot, thread_id):
                                response = "⚠ Lệnh này chỉ dùng trong nhóm với quyền phù hợp!"
                            else:
                                uids = extract_uids_from_mentions(msg_obj)
                                response = add_users_to_ban_list(bot, uids, thread_id, "Quản trị viên cấm")
                elif act == 'unban':
                    if len(parts) < 3:
                        response = "⚠ Cú pháp: bot unban [@user]"
                    else:
                        if thread_type != ThreadType.GROUP:
                            response = "⚠ Lệnh này chỉ dùng trong nhóm!"
                        else:
                            uids = extract_uids_from_mentions(msg_obj)
                            response = remove_users_from_ban_list(bot, uids, thread_id)
                elif act == 'block':
                    if len(parts) < 3:
                        response = "⚠ Cú pháp: bot block/unblock/list [@user]"
                    else:
                        sub = parts[2].lower()
                        if sub == 'list':
                            response = print_blocked_users_in_group(bot, thread_id)
                        else:
                            if thread_type != ThreadType.GROUP or not check_admin_group(bot, thread_id):
                                response = "⚠ Lệnh này chỉ dùng trong nhóm với quyền phù hợp!"
                            else:
                                uids = extract_uids_from_mentions(msg_obj)
                                response = block_users_from_group(bot, uids, thread_id)
                elif act == 'unblock':
                    if len(parts) < 3:
                        response = "⚠ Cú pháp: bot unblock [UID1,UID2,...]"
                    else:
                        if thread_type != ThreadType.GROUP:
                            response = "⚠ Lệnh này chỉ dùng trong nhóm!"
                        else:
                            uids = [uid.strip() for uid in parts[2].split(',') if uid.strip()]
                            response = unblock_users_from_group(bot, uids, thread_id) if uids else "⚠ Không có UID hợp lệ!"
                elif act == 'kick':
                    if len(parts) < 3:
                        response = "⚠ Cú pháp: bot kick [@user]"
                    else:
                        if thread_type != ThreadType.GROUP or not check_admin_group(bot, thread_id):
                            response = "⚠ Lệnh này chỉ dùng trong nhóm với quyền phù hợp!"
                        else:
                            uids = extract_uids_from_mentions(msg_obj)
                            response = kick_users_from_group(bot, uids, thread_id)
                elif act == 'rule':
                    if len(parts) < 5:
                        response = "⚠ Cú pháp: bot rule word [số lần] [số phút]"
                    else:
                        try:
                            thresh, dur = int(parts[3]), int(parts[4])
                        except ValueError:
                            response = "⚠ Số lần và số phút phải là số nguyên!"
                        else:
                            s = read_settings()
                            rule_type = parts[2].lower()
                            if rule_type not in ["word", "spam"]:
                                response = "⚠ Lệnh bot rule không hỗ trợ loại này! Ví dụ: bot rule word 3 30"
                            else:
                                if thread_type != ThreadType.GROUP:
                                    response = "⚠ Lệnh này chỉ dùng trong nhóm!"
                                else:
                                    s.setdefault("rules", {})[rule_type] = {"threshold": thresh, "duration": dur}
                                    write_settings(s)
                                    response = f"✅ Cập nhật nội quy: Vi phạm {thresh} lần sẽ bị phạt {dur} phút!"
                elif act == 'groupbanlist':
                    response = list_forbidden_groups(bot)
                elif act == 'skip':
                    if len(parts) < 3:
                        response = "⚠ Cú pháp: bot skip add/remove/list @user"
                    else:
                        sub = parts[2].lower()
                        s = read_settings()
                        excluded_users = s.get("excluded_users", [])
                        if sub == 'list':
                            response = ("📋 Danh sách người dùng được loại trừ:\n" +
                                        "\n".join(f"- {get_user_name_by_id(bot, uid)} (ID: {uid})" for uid in excluded_users)
                                       ) if excluded_users else "✅ Không có ai được loại trừ."
                        elif sub == 'add':
                            if len(parts) < 4:
                                response = "⚠ Cú pháp: bot skip add @user"
                            else:
                                uids = extract_uids_from_mentions(msg_obj)
                                for uid in uids:
                                    if uid not in excluded_users:
                                        excluded_users.append(uid)
                                s["excluded_users"] = excluded_users
                                write_settings(s)
                                response = f"✅ Đã thêm {len(uids)} người vào danh sách loại trừ."
                        elif sub == 'remove':
                            if len(parts) < 4:
                                response = "⚠ Cú pháp: bot skip remove @user"
                            else:
                                uids = extract_uids_from_mentions(msg_obj)
                                excluded_users = [uid for uid in excluded_users if uid not in uids]
                                s["excluded_users"] = excluded_users
                                write_settings(s)
                                response = f"✅ Đã xóa {len(uids)} người khỏi danh sách loại trừ."
                        else:
                            response = f"⚠️ Lệnh bot skip {sub} không được hỗ trợ."
                else:
                    response = f"🛑 Lệnh [bot {act}] không được hỗ trợ."
            if response:
                bot.replyMessage(Message(text=response), msg_obj, thread_id=thread_id, thread_type=thread_type, ttl=25000)
        except Exception as e:
            print(f"Error: {e}")
            bot.replyMessage(Message(text="⚠ Đã xảy ra lỗi"), msg_obj, thread_id=thread_id, thread_type=thread_type, ttl=20000)
    Thread(target=send_bot_response).start()

def get_mitaizl():
    return {'bott': handle_bot_command}
