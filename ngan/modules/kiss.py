
from zlapi import ZaloAPI
from zlapi.models import *
import time
from concurrent.futures import ThreadPoolExecutor
import threading
import random
import os
def ping(message, message_object, thread_id, thread_type, author_id, self):
        start_time = time.time()
        reply_message = Message("Ảnh kiss của bạn đây >.<...💋")
        self.replyMessage(reply_message, message_object, thread_id, thread_type)

        end_time = time.time()
        ping_time = end_time - start_time

        image_dir = "kiss"
        image_files = [f for f in os.listdir(image_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]
        random_image = random.choice(image_files)
        image_path = os.path.join(image_dir, random_image)

        text = f"💋Bờ môi em thật quyến rũ, anh muốn chạm vào nó bằng đôi môi của anh lên chiếc lưỡi mọng nước của em!!!!: {ping_time:.2f}ms"
        self.sendLocalImage(imagePath=image_path, thread_id=thread_id, thread_type=thread_type, message=Message(text))

def get_mitaizl():
    return {
        'kiss': ping
    }