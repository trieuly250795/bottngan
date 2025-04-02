import os
import time
import logging
import threading
from datetime import datetime
import pytz
import json
# Các import từ dự án của bạn
from config import API_KEY, SECRET_KEY, IMEI, SESSION_COOKIES, PREFIX
from mitaizl import CommandHandler
from zlapi import ZaloAPI, ZaloAPIException
from zlapi.models import Message, ThreadType, Mention, MultiMsgStyle, MessageStyle
from modules.bot_info import *
from modules.da import welcome
from undo.undo import UndoHandler  # Thư mục "undo" có file "undo.py"
from antispam_handler import AntiSpamHandler
from modules.autosend_on import start_auto
from modules.autosend_on2 import start_auto2

# Cấu hình logger thay vì in quá nhiều print
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Bot")

# Thiết lập timezone toàn cục (nếu bạn cần in thời gian cho Việt Nam)
vietnam_tz = pytz.timezone("Asia/Ho_Chi_Minh")

def apply_default_style(text):
    """
    Hàm tạo style mặc định áp dụng cho tin nhắn phản hồi người dùng.
    """
    base_length = len(text)
    adjusted_length = base_length + 100  # Tăng độ dài để phủ "dư" cho toàn bộ nội dung

    return MultiMsgStyle([
        MessageStyle(
            offset=0,
            length=adjusted_length,
            style="color",
            color="#db342e",
            auto_format=False,
        ),
        MessageStyle(
            offset=0,
            length=adjusted_length,
            style="bold",
            size="8",
            auto_format=False,
        ),
    ])
    
class Client(ZaloAPI):
    def __init__(self, api_key, secret_key, imei, session_cookies):
        super().__init__(api_key, secret_key, imei=imei, session_cookies=session_cookies)
        # Áp dụng các thiết lập cho bot (nếu có)
        handle_bot_admin(self)

        # Thông tin chung
        self.version = 1.1
        self.me_name = "MAIN FIX BY ROSY"
        self.date_update = "25/01/2025"

        # Khởi tạo các handler
        self.command_handler = CommandHandler(self)
        self.undo_handler = UndoHandler()
        self.antispam_handler = AntiSpamHandler()

        # Khởi tạo cache cho file JSON và thông tin chủ bot
        self._banned_users = None
        self._banned_users_time = 0
        self._banned_groups = None
        self._banned_groups_time = 0
        self._cache_interval = 60  # thời gian cache (giây)
        self._bot_owner_info = None
        self._bot_owner_info_time = 0
        self._bot_owner_ttl = 300  # thời gian cache thông tin chủ bot (giây)

    def get_banned_users(self):
        """Lấy danh sách banned_users từ file với cơ chế cache."""
        current_time = time.time()
        if self._banned_users is None or (current_time - self._banned_users_time > self._cache_interval):
            try:
                with open("banned_users.json", "r", encoding="utf-8") as f:
                    self._banned_users = json.load(f)
            except Exception as e:
                logger.error("Lỗi tải banned_users.json: " + str(e))
                self._banned_users = []
            self._banned_users_time = current_time
        return self._banned_users

    def get_banned_groups(self):
        """Lấy danh sách banned_groups từ file với cơ chế cache."""
        current_time = time.time()
        if self._banned_groups is None or (current_time - self._banned_groups_time > self._cache_interval):
            try:
                with open("banned_groups.json", "r", encoding="utf-8") as f:
                    self._banned_groups = json.load(f)
            except Exception as e:
                logger.error("Lỗi tải banned_groups.json: " + str(e))
                self._banned_groups = []
            self._banned_groups_time = current_time
        return self._banned_groups

    def get_bot_owner_info(self, target_user_id):
        """Lấy và cache thông tin chủ bot để giảm số lần gọi API."""
        current_time = time.time()
        if self._bot_owner_info is None or (current_time - self._bot_owner_info_time > self._bot_owner_ttl):
            try:
                user_info_response = self.fetchUserInfo(target_user_id)
                self._bot_owner_info = user_info_response.changed_profiles.get(str(target_user_id))
            except Exception as e:
                logger.error(f"Lỗi khi fetchUserInfo của chủ bot: {e}")
                self._bot_owner_info = None
            self._bot_owner_info_time = current_time
        return self._bot_owner_info

    def onEvent(self, event_data, event_type):
        # Hàm welcome hay các hàm khác tùy ý
        welcome(self, event_data, event_type)

    def onMessage(self, mid, author_id, message, message_object, thread_id, thread_type):
        """
        Hàm xử lý khi có tin nhắn đến.
        """
        # Bỏ qua tin nhắn do chính bot gửi
        if author_id == self.uid:
            return

       # Kiểm tra và xử lý tin nhắn media (ảnh/video)
        if handle_media_content(self, author_id, thread_id, message_object, thread_type):
            return 

        # --- Bỏ qua tin nhắn từ những người dùng bị cấm theo tệp banned_users.json ---
        banned_users_list = self.get_banned_users()
        banned_user_ids = [user["user_id"] for user in banned_users_list]
        if author_id in banned_user_ids:
            return

        # --- Bỏ qua tin nhắn từ những nhóm bị cấm theo tệp banned_groups.json ---
        if thread_type == ThreadType.GROUP:
            banned_groups_list = self.get_banned_groups()
            banned_group_ids = [group["group_id"] for group in banned_groups_list]
            if thread_id in banned_group_ids:
                return

        # Lấy dName (tên hiển thị) nếu có
        dname_value = getattr(message_object, "dName", "Không có giá trị")

        # Lấy thời gian hiện tại (theo múi giờ Việt Nam)
        now_str = datetime.now(vietnam_tz).strftime("%H:%M:%S %d/%m/%Y")

        # Log đơn giản
        logger.info(f"[{now_str}] Msg from {dname_value}({author_id}) in {thread_type}-{thread_id}: {message}")

        # ---- Xử lý thu hồi tin nhắn (Undo) và lưu tin nhắn ngay sau đó ----
        self.process_message(message_object, thread_id, thread_type)
        # ---------------------------------------------------------------

        # Xử lý tin nhắn riêng (private message)
        if thread_type == ThreadType.USER:
            user_msg = message.strip().lower()  # Chuyển về chữ thường để so sánh

            # Danh sách các từ khóa không muốn gửi auto_reply (ngoài 1,2,3,4)
            skip_auto_reply_keywords = ["vdtt","2c","5c","@all","acclq","alo","amlich","api","atk","stklag","stop","atknamegr","atkstk","attack","autolink","autosend_on","ban","banggia","addbgroup","delbgroup","listbgroup","bantho","addban","delban","listban","bc","menubc","bcua","bclichsu","block","unblock","boi","booba","bot","bott","calc","canva","cap","card","cmd","cmdl","cos18","cover","csplay","welcome","deptrai","dhbc","tl","dhbcstop","dhbc2","tl2","dhbcstop2","dich","dinhgiasdt","ngaunhien","doan","doc","down","duyetmem","fb","`","gai1","gai2","gay","gen","getidbylink","getlink","getvoice","girl","gr","grid","group","haha","help","hentai","hotclip","i4","i5","imgur","jav","join","kb","kiss","lamnetanh","leave","lea","listfriends","listgroups","listmembers","love","addgroup","delgroup","listgroup","maqr","media","menu","menu1","menu2","menu3","menu4","menu5","menu9","menuad","mlem","day","mya","net","onMessage","nhai","note","nude","otaku","phatnguoi","phongthuy","pin","play_on","play_off","pollwar","qr","qrcode","random","renamecmd","rm","sory","rs","scanqr","scantext","scl","scllist","scload","sendtoall","sendanh","sendids","sendl","sendl2","sendlink","sendnhom","sendstk","senduser","sexy","sharecode","sms","sos","spamsms","spamtodo","stk","stkmoi","stktn","sys","tagall","tagallmem","tagmem","stkk2","tdgr","teach","text","thinh","thoitiet","tiktokinfo","time","todogr","todouser","tt","ttinfo","tx","menutx","txiu","soi","xemphientruoc","dsnohu","dudoan","lichsu","tygia","uid","unlock","vd18","vd19","vdgai","vdtt","vdx","viewcode","voice","vt","tlvt","vtstop","warpoll","wiki","xoa","xxxhub","yt","up","zl"]

            if user_msg == "1":
                reply_text = "📞 Vui lòng bấm vào danh thiếp ở trên để liên hệ chủ bot "
                self.sendMessage(
                    Message(text=reply_text, style=apply_default_style(reply_text)),
                    thread_id,
                    thread_type
                )
            elif user_msg == "2":
                reply_text = "📞 Vui lòng bấm vào danh thiếp ở trên để liên hệ chủ bot"
                self.sendMessage(
                    Message(text=reply_text, style=apply_default_style(reply_text)),
                    thread_id,
                    thread_type
                )
            elif user_msg == "3":
                reply_text = "ℹ️ Nhập lệnh menu để xem menu chính , từ menu chính nhập tiếp lệnh để xem menu con \n 💡 Soạn help + tên lệnh để xem mô tả lệnh và cách sử dụng "
                self.sendMessage(
                    Message(text=reply_text, style=apply_default_style(reply_text)),
                    thread_id,
                    thread_type
                )
            elif user_msg == "4":
                reply_text = "📞 Nếu có ý tưởng khác vui lòng liên hệ chủ bot để hợp tác , danh thiếp ở trên "
                self.sendMessage(
                    Message(text=reply_text, style=apply_default_style(reply_text)),
                    thread_id,
                    thread_type
                )
            elif user_msg in skip_auto_reply_keywords:
                # Không làm gì khi tin nhắn nằm trong danh sách skip_auto_reply_keywords
                pass
            else:
                # Nếu không phải 1, 2, 3, 4 và cũng không phải các từ khóa trong skip_auto_reply_keywords
                # => Gửi auto_reply
                auto_reply = (
    "         BOT ROSY  \n"
    "━━━━━━━━━━━━━\n"
    "❗ Tôi là bot chat được cài đặt để tự động gửi tin nhắn.\n"
    "❓ Vui lòng nhập số (1-4) để chọn:\n"
    "---------------------------------\n"
    "1️⃣  Xin slot\n"
    "2️⃣  Mua map\n"
    "3️⃣  Sử dụng bot\n"
    "4️⃣  Yêu cầu khác\n"
)

                self.sendMessage(
                    Message(text=auto_reply, style=apply_default_style(auto_reply)),
                    author_id,
                    ThreadType.USER,
                )
                logger.info(f"Đã gửi phản hồi tự động cho người dùng {author_id}")
                
                # Gửi business card kèm theo tin nhắn chào
                target_user_id = 2670654904430771575
                user_info_response = self.fetchUserInfo(target_user_id)
                user_info = user_info_response.changed_profiles.get(str(target_user_id))
                if not user_info:
                    msg_text = "Không thể lấy thông tin người dùng."
                    self.sendMessage(
                        Message(text=msg_text, style=apply_default_style(msg_text)),
                        thread_id,
                        thread_type
                    )
                else:
                    avatarUrl = user_info.avatar
                    if not avatarUrl:
                        msg_text = "Người dùng này không có ảnh đại diện."
                        self.sendMessage(
                            Message(text=msg_text, style=apply_default_style(msg_text)),
                            thread_id,
                            thread_type
                        )
                    else:
                        self.sendBusinessCard(
                            userId=target_user_id,
                            qrCodeUrl=avatarUrl,
                            thread_id=thread_id,
                            thread_type=thread_type
                        )

        # Kiểm tra nhóm được phép
        allowed_thread_ids = get_allowed_thread_ids()
        if thread_type == ThreadType.GROUP and thread_id in allowed_thread_ids:
            # Kiểm duyệt nội dung, ví dụ profanity
            handle_check_profanity(self, author_id, thread_id, message_object, thread_type, message)

        # Chống spam
        if self.antispam_handler.is_antispam_enabled(thread_id):
            if self.antispam_handler.check_and_handle_spam(self, author_id, thread_id, message_object, thread_type):
                return  # Nếu tin nhắn bị xác định là spam, dừng xử lý tiếp

        # Lệnh bật/tắt antispam
        if isinstance(message, str) and message.startswith(f"{PREFIX}antispam"):
            self.antispam_handler.toggle_antispam(self, message, message_object, thread_id, thread_type)

        # Xử lý lệnh khác (command)
        if isinstance(message, str):
            self.command_handler.handle_command(message, author_id, message_object, thread_id, thread_type)

    def process_message(self, message_object, thread_id, thread_type):
        """
        Xử lý tin nhắn ngay khi nhận được.
        Nếu tin nhắn là sự kiện thu hồi (chat.undo) thì sẽ truy xuất nội dung tin nhắn đã lưu trước đó
        và hiển thị lại nội dung đó theo đúng định dạng.
        Sau đó, lưu lại tin nhắn để hỗ trợ các lần thu hồi sau.
        """
        if message_object.msgType == 'chat.undo':
            cliMsgId = str(message_object.content.get('cliMsgId', ''))
            saved_message = self.undo_handler.get_message(cliMsgId)
            if saved_message:
                formatted_time = time.strftime("%H:%M:%S %d/%m/%Y", time.localtime())
                mention_text = "@Member"
                # Tạo mention với độ dài của mention_text
                mention = Mention(message_object.uidFrom, length=len(mention_text), offset=0)

                if 'href' in saved_message['content']:
                    href = saved_message['content']['href']
                    if 'stk' in href:
                        catId = saved_message['content']['catId']
                        stk_id = saved_message['content']['id']
                        self.sendsticker(stk_id, catId, thread_id, thread_type)
                    elif 'jpg' in href or 'png' in href:
                        image_file = self.undo_handler.download_image(href)
                        self.sendLocalImage(image_file, thread_id=thread_id, thread_type=thread_type, ttl=30000)
                        os.remove(image_file)
                        undo_text = f"{mention_text}\n\n🖼️ Hình ảnh đã bị thu hồi\n{href}\n\n⏰ Thời gian: {formatted_time}"
                        self.replyMessage(
                            Message(text=undo_text, style=apply_default_style(undo_text), mention=mention),
                            message_object,
                            thread_id,
                            thread_type,
                            ttl=30000
                        )
                    elif 'video' in href:
                        undo_text = f"{mention_text}\n\n📹 Video đã bị thu hồi\n{href}\n\n⏰ Thời gian: {formatted_time}"
                        self.replyMessage(
                            Message(text=undo_text, style=apply_default_style(undo_text), mention=mention),
                            message_object,
                            thread_id,
                            thread_type,
                            ttl=30000
                        )
                        self.sendRemoteVideo(href, thread_id=thread_id, thread_type=thread_type, ttl=30000)
                    elif 'voice' in href:
                        undo_text = f"{mention_text}\nVoice đã bị thu hồi:\n{href}\nThời gian: {formatted_time}"
                        self.replyMessage(
                            Message(text=undo_text, style=apply_default_style(undo_text), mention=mention),
                            message_object,
                            thread_id,
                            thread_type,
                            ttl=30000
                        )
                        self.sendRemoteVoice(href, thread_id=thread_id, thread_type=thread_type, ttl=30000)
                else:
                    content = saved_message['content']
                    undo_text = (
    f"{mention_text}\n\n"
    "⚠️ Tin nhắn đã được thu hồi\n"
    "──────────────────────\n"
    f"💬 Nội dung: {content}\n"
    "──────────────────────\n"
    f"🕒 Thời gian: {formatted_time}"
)

                    self.replyMessage(
                        Message(text=undo_text, style=apply_default_style(undo_text), mention=mention),
                        message_object,
                        thread_id,
                        thread_type,
                        ttl=30000
                    )
            else:
                logger.info(f"Không tìm thấy nội dung tin nhắn với cliMsgId: {cliMsgId}")
        # Sau khi xử lý undo, lưu tin nhắn để hỗ trợ các lần thu hồi sau
        self.undo_handler.save_message(message_object)

    def kick_member_from_group(self, user_id, thread_id):
        """
        Ví dụ hàm kick thành viên khỏi nhóm.
        """
        if user_id == self.uid:
            return
        try:
            response = self.blockUsersInGroup(user_id, thread_id)
            if response.get('status') == 'success':
                kick_text = "Bạn đã bị kick khỏi nhóm vì vi phạm nội quy hoặc spam."
                self.sendMessage(
                    Message(text=kick_text, style=apply_default_style(kick_text)),
                    user_id,
                    ThreadType.USER,
                )
                logger.info(f"Đã kick thành viên {user_id} khỏi nhóm {thread_id}")
            else:
                logger.error(f"Lỗi khi kick thành viên {user_id} khỏi nhóm {thread_id}")
        except ZaloAPIException as e:
            logger.error(f"Lỗi ZaloAPIException khi kick: {e}")
        except Exception as e:
            logger.error(f"Lỗi không xác định khi kick: {e}")


def run_bot():
    """
    Hàm chạy bot với cơ chế retry (exponential backoff) để tránh lặp liên tục gây OOM.
    """
    backoff = 5        # Thời gian chờ ban đầu (giây)
    max_backoff = 60   # Giới hạn tối đa
    while True:
        try:
            # Khởi tạo client
            client = Client(API_KEY, SECRET_KEY, IMEI, SESSION_COOKIES)

            # Khởi chạy tính năng auto send (nếu có)
            threading.Thread(target=start_auto, args=(client,), daemon=True).start()

            # Khởi chạy tính năng tự động gửi link
            threading.Thread(target=start_auto2, args=(client,), daemon=True).start()

            # Gửi tin nhắn thông báo bot khởi động vào một nhóm
            thread_id = "643794532760252296"
            now_str = datetime.now(vietnam_tz).strftime("%H:%M:%S %d/%m/%Y")
            message_content = (
                f"✅ BOT ĐÃ KHỞI ĐỘNG THÀNH CÔNG!\n"
                f"🆔 ID Bot: {client.uid}\n"
                f"🕒 Thời gian: {now_str}\n"
                f"Bot đang lắng nghe tin nhắn..."
            )
            client.sendMessage(Message(text=message_content), thread_id, ThreadType.GROUP)

            # Bắt đầu lắng nghe
            client.listen(thread=True, delay=0)

            # Nếu listen() kết thúc bình thường, thoát vòng lặp
            break

        except Exception as e:
            logger.error(f"Bot bị ngắt kết nối: {e}")
            # Tăng dần thời gian chờ trước khi khởi động lại
            time.sleep(backoff)
            backoff = min(backoff * 2, max_backoff)


if __name__ == "__main__":
    run_bot()
