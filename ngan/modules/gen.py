import subprocess
import json
import logging
from zlapi.models import *
 
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

GEMINI_API_KEY = "AIzaSyCkG7NfjnfBQ4ovfLW7uAFl6V8WDmgt7dg"
api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={GEMINI_API_KEY}"

des = {
    'version': "1.0.0",
    'credits': "Hiển",
    'description': "Trò chuyện với AI"
}

def ask_gemini(content, message_object, thread_id, thread_type, client):
    try:
        request_data = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": content
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 2048,
                "responseMimeType": "text/plain"
            }
        }

        result = subprocess.run(
            ['curl', '-X', 'POST', api_url,
             '-H', 'Content-Type: application/json',
             '-d', json.dumps(request_data)],
            capture_output=True, text=True
        )

        if result.returncode != 0:
            raise Exception(f"curl failed with return code {result.returncode}")

        response_data = json.loads(result.stdout)

        if not result.stdout or 'candidates' not in response_data:
            logging.error(response_data)
            gemini_response = "API không trả về dữ liệu mong đợi."
        else:
            gemini_response = response_data['candidates'][0]['content']['parts'][0]['text']

        if not gemini_response.strip():
            gemini_response = "Gen không có gì để nói."

        message_to_send = Message(text=f"> Gemini AI: {gemini_response}")
        client.replyMessage(message_to_send, message_object, thread_id, thread_type)
        client.sendReaction(message_object, 'YES', thread_id, thread_type)
    except Exception as e:
        logging.error(f"Lỗi khi gọi API: {str(e)}")
        client.sendReaction(message_object, '🚫', thread_id, thread_type)

def handle_genz_command(message, message_object, thread_id, thread_type, author_id, client):
    text = message.split()

    if len(text) < 2:
        client.sendReaction(message_object, 'OK', thread_id, thread_type)
        error_message = Message(text="Vui lòng nhập câu hỏi để trò chuyện cùng Gemini AI.")
        client.sendMessage(error_message, thread_id, thread_type)
        return

    content = " ".join(text[1:])

    ask_gemini(content, message_object, thread_id, thread_type, client)

def get_mitaizl():
    return {
        'gen': handle_genz_command
    }