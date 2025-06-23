import requests
import time
from datetime import datetime

class WHATicketAPI:
    def __init__(self, base_url, token):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        self.rate_limit = 1.5
        self.last_send = 0

    def send_message(self, group_id, message, media_url=None):
        elapsed = time.time() - self.last_send
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        payload = {
            'chatId': group_id,
            'body': message
        }
        if media_url:
            payload['mediaUrl'] = media_url
            payload['mediaCaption'] = message
        try:
            response = requests.post(
                f'{self.base_url}/api/messages/send',
                headers=self.headers,
                json=payload,
                timeout=30
            )
            self.last_send = time.time()
            if response.status_code == 200:
                return True, response.json()
            return False, f"Error {response.status_code}: {response.text}"
        except Exception as e:
            return False, str(e)

    def get_group_info(self, group_id):
        try:
            response = requests.get(
                f'{self.base_url}/api/chats/{group_id}',
                headers=self.headers
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception:
            return None

    def validate_connection(self):
        try:
            response = requests.get(
                f'{self.base_url}/api/auth/refresh',
                headers=self.headers
            )
            return response.status_code == 200
        except Exception:
            return False
