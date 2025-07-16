import requests
import json
import logging
from typing import Dict, List, Optional
from config.settings import Config
import os

logger = logging.getLogger(__name__)

class WhatsAppService:
    def __init__(self):
        self.api_url = Config.get_whatsapp_api_url()
        self.access_token = Config.WHATSAPP_TOKEN
        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    def send_text_message(self, phone_number: str, message: str) -> bool:
        """Send a text message via WhatsApp"""
        try:
            payload = {
                "messaging_product": "whatsapp",
                "to": phone_number,
                "type": "text",
                "text": {
                    "body": message
                }
            }
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                data=json.dumps(payload)
            )
            
            if response.status_code == 200:
                logger.info(f"Message sent successfully to {phone_number}")
                return True
            else:
                logger.error(f"Failed to send message: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {e}")
            return False
    
    def send_interactive_list(self, phone_number: str, header: str, body: str, 
                             footer: str, button_text: str, sections: List[Dict]) -> bool:
        """Send an interactive list message"""
        try:
            payload = {
                "messaging_product": "whatsapp",
                "to": phone_number,
                "type": "interactive",
                "interactive": {
                    "type": "list",
                    "header": {
                        "type": "text",
                        "text": header
                    },
                    "body": {
                        "text": body
                    },
                    "footer": {
                        "text": footer
                    },
                    "action": {
                        "button": button_text,
                        "sections": sections
                    }
                }
            }
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                data=json.dumps(payload)
            )
            
            if response.status_code == 200:
                logger.info(f"Interactive list sent successfully to {phone_number}")
                return True
            else:
                logger.error(f"Failed to send interactive list: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending WhatsApp interactive list: {e}")
            return False
    
    def send_interactive_buttons(self, phone_number: str, header: str, body: str,
                                footer: str, buttons: List[Dict]) -> bool:
        """Send an interactive buttons message"""
        try:
            payload = {
                "messaging_product": "whatsapp",
                "to": phone_number,
                "type": "interactive",
                "interactive": {
                    "type": "button",
                    "header": {
                        "type": "text",
                        "text": header
                    },
                    "body": {
                        "text": body
                    },
                    "footer": {
                        "text": footer
                    },
                    "action": {
                        "buttons": buttons
                    }
                }
            }
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                data=json.dumps(payload)
            )
            
            if response.status_code == 200:
                logger.info(f"Interactive buttons sent successfully to {phone_number}")
                return True
            else:
                logger.error(f"Failed to send interactive buttons: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending WhatsApp interactive buttons: {e}")
            return False
    
    def extract_message_from_webhook(self, webhook_data: Dict) -> Optional[Dict]:
        """Extract message data from WhatsApp webhook"""
        try:
            entry = webhook_data.get('entry', [])
            if not entry:
                return None
            
            changes = entry[0].get('changes', [])
            if not changes:
                return None
            
            value = changes[0].get('value', {})
            messages = value.get('messages', [])
            
            if not messages:
                return None
            
            message = messages[0]
            message_type = message.get('type')
            
            # Extract contact info
            contacts = value.get('contacts', [])
            contact_name = ''
            if contacts:
                profile = contacts[0].get('profile', {})
                contact_name = profile.get('name', '')
            
            # Base message data
            message_data = {
                'phone_number': message.get('from'),
                'message_id': message.get('id'),
                'timestamp': message.get('timestamp'),
                'type': message_type,
                'text': '',
                'interactive': message.get('interactive', {}),
                'contact_name': contact_name
            }
            
            # Handle different message types
            if message_type == 'text':
                message_data['text'] = message.get('text', {}).get('body', '')
            elif message_type == 'document':
                # Handle document uploads (PDFs)
                document = message.get('document', {})
                message_data.update({
                    'document': {
                        'id': document.get('id'),
                        'filename': document.get('filename', 'document'),
                        'mime_type': document.get('mime_type'),
                        'sha256': document.get('sha256'),
                        'caption': document.get('caption', '')
                    }
                })
                message_data['text'] = document.get('caption', '')  # Use caption as text
            
            return message_data
            
        except Exception as e:
            logger.error(f"Error extracting message from webhook: {e}")
            return None
    
    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """Verify WhatsApp webhook"""
        if mode == "subscribe" and token == Config.WHATSAPP_VERIFY_TOKEN:
            logger.info("Webhook verified successfully")
            return challenge
        else:
            logger.warning("Webhook verification failed")
            return None
    
    def format_flight_options_list(self, flights: List[Dict]) -> List[Dict]:
        """Format flight options as WhatsApp interactive list sections"""
        if not flights:
            return []
        
        sections = [{
            "title": "Available Flights",
            "rows": []
        }]
        
        for i, flight in enumerate(flights[:10], 1):  # Limit to 10 options
            # Handle both Flight objects and dictionaries
            if hasattr(flight, 'airline'):
                # Flight object
                row = {
                    "id": f"flight_{i}",
                    "title": f"{flight.airline} - ₹{flight.price:,}",
                    "description": f"{flight.departure_time} → {flight.arrival_time} ({flight.duration})"
                }
            else:
                # Dictionary
                row = {
                    "id": f"flight_{i}",
                    "title": f"{flight['airline']} - ₹{flight['price']:,}",
                    "description": f"{flight['departure_time']} → {flight['arrival_time']} ({flight['duration']})"
                }
            sections[0]["rows"].append(row)
        
        return sections
    
    def format_confirmation_buttons(self) -> List[Dict]:
        """Format confirmation buttons for booking"""
        return [
            {
                "type": "reply",
                "reply": {
                    "id": "confirm_booking",
                    "title": "✅ Confirm Booking"
                }
            },
            {
                "type": "reply",
                "reply": {
                    "id": "cancel_booking",
                    "title": "❌ Cancel"
                }
            }
        ]
    
    def format_ssr_buttons(self) -> List[Dict]:
        """Format special service request buttons"""
        return [
            {
                "type": "reply",
                "reply": {
                    "id": "add_ssr",
                    "title": "➕ Add Requests"
                }
            },
            {
                "type": "reply",
                "reply": {
                    "id": "no_ssr",
                    "title": "⏭️ Skip"
                }
            }
        ]
    
    def send_typing_indicator(self, phone_number: str) -> bool:
        """Send typing indicator to show bot is processing"""
        try:
            payload = {
                "messaging_product": "whatsapp",
                "to": phone_number,
                "type": "text",
                "text": {
                    "body": "⏳ Processing..."
                }
            }
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                data=json.dumps(payload)
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error sending typing indicator: {e}")
            return False
    
    def send_welcome_message(self, phone_number: str, contact_name: str = '') -> bool:
        """Send welcome message to new users"""
        greeting = f"Hello {contact_name}!" if contact_name else "Hello!"
        
        message = f"""✈️ *Welcome to Flight Booking Assistant!* {greeting}

I'm here to help you book flights quickly and easily. Just tell me where you want to go!

*Examples:*
• "I want to book a flight"
• "Flight to Dubai"
• "Book flight from Delhi to Mumbai"

*What can I help you with today?* 🛫"""
        
        return self.send_text_message(phone_number, message)
    
    def send_error_message(self, phone_number: str, error_type: str = 'general') -> bool:
        """Send appropriate error message"""
        error_messages = {
            'general': "❌ Something went wrong. Please try again or contact support.",
            'invalid_input': "🤔 I didn't understand that. Could you please rephrase?",
            'no_flights': "❌ No flights found for your search. Try different dates or destinations.",
            'booking_failed': "❌ Booking failed. Please try again or contact support.",
            'city_not_found': "🏙️ City not found. Please check spelling or try a major city nearby.",
            'invalid_date': "📅 Invalid date. Please provide a future date.",
            'passenger_limit': "👥 Passenger limit exceeded. Maximum 9 passengers allowed.",
            'invalid_pdf': "📄 Invalid PDF file. Please upload a valid flight ticket in PDF format.",
            'pdf_parsing_failed': "❌ Unable to read your ticket. Please try uploading a clearer PDF file."
        }
        
        message = error_messages.get(error_type, error_messages['general'])
        return self.send_text_message(phone_number, message)
    
    def download_media_file(self, media_id: str) -> Optional[bytes]:
        """Download media file from WhatsApp by media ID"""
        try:
            # Get media URL
            media_url_endpoint = f"https://graph.facebook.com/v18.0/{media_id}"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            
            # Get media URL
            response = requests.get(media_url_endpoint, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"Failed to get media URL: {response.status_code} - {response.text}")
                return None
            
            media_data = response.json()
            media_download_url = media_data.get('url')
            
            if not media_download_url:
                logger.error("No download URL found in media response")
                return None
            
            # Download the actual file
            download_response = requests.get(media_download_url, headers=headers)
            
            if download_response.status_code == 200:
                logger.info(f"Successfully downloaded media file: {media_id}")
                return download_response.content
            else:
                logger.error(f"Failed to download media: {download_response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading media file: {e}")
            return None
    
    def is_pdf_document(self, document_info: Dict) -> bool:
        """Check if the uploaded document is a PDF"""
        mime_type = document_info.get('mime_type', '')
        filename = document_info.get('filename', '')
        
        return (mime_type == 'application/pdf' or 
                filename.lower().endswith('.pdf'))
    
    def send_pdf_processing_message(self, phone_number: str) -> bool:
        """Send message indicating PDF is being processed"""
        message = """📄 *PDF Ticket Received!*

🔄 *Processing your flight ticket...*
⏳ *This may take a few seconds*

I'll extract your flight details and compare prices with our system! ✈️"""
        
        return self.send_text_message(phone_number, message)

    def send_pdf_document(self, phone_number: str, pdf_path: str, caption: str = "") -> bool:
        """Send PDF document via WhatsApp"""
        try:
            # First, upload the media to WhatsApp
            media_id = self._upload_media_file(pdf_path)
            if not media_id:
                logger.error("Failed to upload PDF to WhatsApp")
                return False
            
            # Send document message
            payload = {
                "messaging_product": "whatsapp",
                "to": phone_number,
                "type": "document",
                "document": {
                    "id": media_id,
                    "caption": caption,
                    "filename": os.path.basename(pdf_path)
                }
            }
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                data=json.dumps(payload)
            )
            
            if response.status_code == 200:
                logger.info(f"PDF document sent successfully to {phone_number}")
                return True
            else:
                logger.error(f"Failed to send PDF document: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending PDF document: {e}")
            return False
    
    def _upload_media_file(self, file_path: str) -> Optional[str]:
        """Upload media file to WhatsApp and get media ID"""
        try:
            upload_url = f"https://graph.facebook.com/v18.0/{Config.WHATSAPP_PHONE_NUMBER_ID}/media"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            
            # Determine MIME type
            mime_type = 'application/pdf'
            if file_path.lower().endswith('.pdf'):
                mime_type = 'application/pdf'
            
            with open(file_path, 'rb') as file:
                files = {
                    'file': (os.path.basename(file_path), file, mime_type)
                }
                data = {
                    'messaging_product': 'whatsapp'
                }
                
                response = requests.post(upload_url, headers=headers, files=files, data=data)
                
                if response.status_code == 200:
                    result = response.json()
                    media_id = result.get('id')
                    logger.info(f"Media uploaded successfully: {media_id}")
                    return media_id
                else:
                    logger.error(f"Failed to upload media: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error uploading media file: {e}")
            return None

# Mock WhatsApp service for testing without actual WhatsApp API
class MockWhatsAppService(WhatsAppService):
    def __init__(self):
        super().__init__()
        self.sent_messages = []  # Store sent messages for testing
    
    def send_text_message(self, phone_number: str, message: str) -> bool:
        """Mock send text message"""
        self.sent_messages.append({
            'phone_number': phone_number,
            'type': 'text',
            'message': message,
            'timestamp': None
        })
        print(f"📱 MOCK MESSAGE TO {phone_number}:")
        print(f"💬 {message}")
        print("─" * 50)
        return True
    
    def send_interactive_list(self, phone_number: str, header: str, body: str,
                             footer: str, button_text: str, sections: List[Dict]) -> bool:
        """Mock send interactive list"""
        self.sent_messages.append({
            'phone_number': phone_number,
            'type': 'interactive_list',
            'header': header,
            'body': body,
            'footer': footer,
            'button_text': button_text,
            'sections': sections
        })
        print(f"📱 MOCK INTERACTIVE LIST TO {phone_number}:")
        print(f"📋 Header: {header}")
        print(f"💬 Body: {body}")
        print(f"👆 Button: {button_text}")
        print("─" * 50)
        return True
    
    def send_interactive_buttons(self, phone_number: str, header: str, body: str,
                                footer: str, buttons: List[Dict]) -> bool:
        """Mock send interactive buttons"""
        self.sent_messages.append({
            'phone_number': phone_number,
            'type': 'interactive_buttons',
            'header': header,
            'body': body,
            'footer': footer,
            'buttons': buttons
        })
        print(f"📱 MOCK INTERACTIVE BUTTONS TO {phone_number}:")
        print(f"📋 Header: {header}")
        print(f"💬 Body: {body}")
        print(f"🔘 Buttons: {len(buttons)} options")
        print("─" * 50)
        return True 