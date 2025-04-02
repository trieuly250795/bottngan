from config import API_KEY, SECRET_KEY, IMEI, SESSION_COOKIES,PREFIX
from mitaizl import CommandHandler
from zlapi import ZaloAPI
from zlapi.models import Message
from modules.bot_info import *
from modules.da import welcome
from colorama import Fore, Style, init

init(autoreset=True)

class Client(ZaloAPI):
    def __init__(self, api_key, secret_key, imei, session_cookies):
        super().__init__(api_key, secret_key, imei=imei, session_cookies=session_cookies)
        handle_bot_admin(self)
        self.version = 1.1
        self.me_name = "Bot by A Sin"
        self.date_update = "26/9/2024"
        self.command_handler = CommandHandler(self)
    def onEvent(self,event_data,event_type):
        welcome(self,event_data,event_type)
    def onMessage(self, mid, author_id, message, message_object, thread_id, thread_type):
        print(f"{Fore.GREEN}{Style.BRIGHT}------------------------------\n"
              f"**Message Details:**\n"
              f"- **Message:** {Style.BRIGHT}{message} {Style.NORMAL}\n"
              f"- **Author ID:** {Fore.MAGENTA}{Style.BRIGHT}{author_id} {Style.NORMAL}\n"
              f"- **Thread ID:** {Fore.YELLOW}{Style.BRIGHT}{thread_id}{Style.NORMAL}\n"
              f"- **Thread Type:** {Fore.BLUE}{Style.BRIGHT}{thread_type}{Style.NORMAL}\n"
              f"- **Message Object:** {Fore.RED}{Style.BRIGHT}{message_object}{Style.NORMAL}\n"
              f"{Fore.GREEN}{Style.BRIGHT}------------------------------\n"
              )
        allowed_thread_ids = get_allowed_thread_ids()
        if thread_id in allowed_thread_ids and thread_type == ThreadType.GROUP and not is_admin(author_id):
            handle_check_profanity(self, author_id, thread_id, message_object, thread_type, message)
        try:
            if isinstance(message,str):
                if message == f"{PREFIX}":
                    self.send(Message(text=f"Dùng {PREFIX}menu để biết rõ hơn"),thread_id,thread_type)
                    return
                self.command_handler.handle_command(message, author_id, message_object, thread_id, thread_type)
        except:
            pass

if __name__ == "__main__":
    client = Client(API_KEY, SECRET_KEY, IMEI, SESSION_COOKIES)
    client.listen(thread=True,delay=0)
