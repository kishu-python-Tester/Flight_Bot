import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # WhatsApp API Configuration
    WHATSAPP_TOKEN = os.getenv('WHATSAPP_TOKEN', 'your_whatsapp_token_here')
    WHATSAPP_PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID', 'your_phone_number_id')
    WHATSAPP_VERIFY_TOKEN = os.getenv('WHATSAPP_VERIFY_TOKEN', 'flight_booking_verify_token')
    
    # Google AI Configuration
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', 'your_google_api_key_here')
    
    # Application Configuration
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    PORT = int(os.getenv('PORT', 5000))
    
    # Session Configuration
    SESSION_TIMEOUT = 1800  # 30 minutes
    
    # Mock Data Configuration
    MOCK_API_DELAY = 1  # Simulate API response delay
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    @staticmethod
    def get_whatsapp_api_url():
        return f"https://graph.facebook.com/v18.0/{Config.WHATSAPP_PHONE_NUMBER_ID}/messages" 