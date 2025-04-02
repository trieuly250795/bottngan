import sys, os

from config import ADMIN
from zlapi.models import Message, MultiMsgStyle, MessageStyle

ADMIN_ID = ADMIN

des = {
    'version': "1.0.0",
    'credits': "Dzi",
    'description': "Restart lại bot"
}

def is_admin(author_id):
    return author_id == ADMIN_ID

def handle_reset_command(message, message_object, thread_id, thread_type, author_id, client):
    if not is_admin(author_id):
        msg = "Chỉ có chủ tao mới được reset tao nha mày"
        styles = MultiMsgStyle([
            MessageStyle(offset=0, length=len(msg), style="color", color="#db342e", auto_format=False),
            MessageStyle(offset=0, length=len(msg), style="bold", size="16", auto_format=False)
        ])
        client.replyMessage(Message(text=msg, style=styles), message_object, thread_id, thread_type)
        action = "❎"
        client.sendReaction(message_object, action, thread_id, thread_type, reactionType=97)
        
        return

    try:
        msg = f"🆘 Bot Mya đã nhận lệnh khởi động lại thành công!\n🔂Đang load [PREFIX]..."
        style = MultiMsgStyle([
            MessageStyle(offset=0, length=len(msg), style="color", color="#db342e", auto_format=False),
            MessageStyle(offset=0, length=len(msg), style="bold", size="16", auto_format=False)
        ])
        client.replyMessage(Message(text=msg, style=style), message_object, thread_id, thread_type, ttl=12000)
        action = "⭕"
        client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)

        python = sys.executable
        os.execl(python, python, *sys.argv)

    except Exception as e:
        msg = f"• Đã xảy ra lỗi khi restart bot: {str(e)}"
        styles = MultiMsgStyle([
            MessageStyle(offset=0, length=len(msg), style="color", color="#db342e", auto_format=False),
            MessageStyle(offset=0, length=len(msg), style="font", size="16", auto_format=False)
        ])
        client.replyMessage(Message(text=msg, style=styles), message_object, thread_id, thread_type)

def get_mitaizl():
    return {
        'rs': handle_reset_command
    }