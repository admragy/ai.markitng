"""WhatsApp Business API Integration"""
import os
import logging
try:
    import httpx
    HAS_HTTPX = True
except:
    HAS_HTTPX = False

logger = logging.getLogger(__name__)

class WhatsAppService:
    def __init__(self):
        self.api_key = os.getenv('WHATSAPP_API_KEY')
        self.phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        self.api_base = f"https://graph.facebook.com/v18.0/{self.phone_number_id}"
    
    async def send_message(self, to_phone: str, message: str):
        if not self.api_key or not HAS_HTTPX:
            return {'success': False, 'error': 'WhatsApp not configured'}
        phone = ''.join(filter(str.isdigit, to_phone))
        if len(phone) == 10:
            phone = '20' + phone
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/messages",
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                    json={"messaging_product": "whatsapp", "to": phone, "type": "text", "text": {"body": message}},
                    timeout=30.0
                )
                return {'success': response.status_code == 200, 'data': response.json()}
        except Exception as e:
            return {'success': False, 'error': str(e)}
