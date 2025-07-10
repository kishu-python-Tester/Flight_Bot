import logging
import os
from flask import Flask, request, jsonify
from threading import Thread
import time

from config.settings import Config
from models.conversation import SessionManager
from services.whatsapp_service import WhatsAppService, MockWhatsAppService
from services.dialogue_manager import DialogueManager

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize services
session_manager = SessionManager()

# Use MockWhatsAppService for testing, real WhatsAppService for production
if Config.FLASK_ENV == 'development' or Config.WHATSAPP_TOKEN == 'your_whatsapp_token_here':
    whatsapp_service = MockWhatsAppService()
    logger.info("🧪 Using Mock WhatsApp Service for testing")
else:
    whatsapp_service = WhatsAppService()
    logger.info("📱 Using Real WhatsApp Service")

dialogue_manager = DialogueManager(whatsapp_service)

@app.route('/')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Flight Booking Chatbot',
        'version': '1.0',
        'active_sessions': session_manager.get_active_sessions_count()
    })

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    """Verify WhatsApp webhook"""
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    logger.info(f"Webhook verification attempt: mode={mode}, token={token}")
    
    verification_result = whatsapp_service.verify_webhook(mode, token, challenge)
    
    if verification_result:
        logger.info("✅ Webhook verified successfully")
        return verification_result
    else:
        logger.warning("❌ Webhook verification failed")
        return 'Verification failed', 403

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    """Handle incoming WhatsApp messages"""
    try:
        webhook_data = request.get_json()
        logger.info(f"📨 Received webhook: {webhook_data}")
        
        # Extract message data
        message_data = whatsapp_service.extract_message_from_webhook(webhook_data)
        
        if not message_data:
            logger.warning("⚠️ No message data found in webhook")
            return jsonify({'status': 'ok'})
        
        phone_number = message_data['phone_number']
        message_text = message_data['text']
        contact_name = message_data.get('contact_name', '')
        
        logger.info(f"📞 Message from {phone_number}: {message_text}")
        
        # Process message in separate thread to avoid timeout
        thread = Thread(target=process_message_async, args=(phone_number, message_text, contact_name))
        thread.start()
        
        return jsonify({'status': 'ok'})
        
    except Exception as e:
        logger.error(f"❌ Error handling webhook: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

def process_message_async(phone_number: str, message_text: str, contact_name: str = ''):
    """Process message asynchronously"""
    try:
        # Get or create session
        session = session_manager.get_session(phone_number)
        
        # Handle welcome message for new sessions
        if session.state.value == 'greeting' and session.get_context('last_message') is None:
            whatsapp_service.send_welcome_message(phone_number, contact_name)
            return
        
        # Process message through dialogue manager
        response = dialogue_manager.process_message(session, message_text)
        
        # Send response
        if response:
            whatsapp_service.send_text_message(phone_number, response)
        
        logger.info(f"✅ Message processed for {phone_number}")
        
    except Exception as e:
        logger.error(f"❌ Error processing message for {phone_number}: {e}")
        whatsapp_service.send_error_message(phone_number, 'general')

@app.route('/test', methods=['GET'])
def test_endpoint():
    """Test endpoint for manual testing"""
    return """
    <h1>🛫 Flight Booking Chatbot Test</h1>
    <h2>Test the chatbot by sending a POST request to /test with message data</h2>
    
    <h3>Example:</h3>
    <pre>
    curl -X POST http://localhost:5000/test \\
         -H "Content-Type: application/json" \\
         -d '{"phone_number": "+1234567890", "message": "I want to book a flight"}'
    </pre>
    
    <h3>Current Status:</h3>
    <ul>
        <li><strong>Active Sessions:</strong> """ + str(session_manager.get_active_sessions_count()) + """</li>
        <li><strong>Environment:</strong> """ + Config.FLASK_ENV + """</li>
        <li><strong>WhatsApp Service:</strong> """ + ("Mock" if isinstance(whatsapp_service, MockWhatsAppService) else "Real") + """</li>
    </ul>
    
    <h3>Test Conversation Flow:</h3>
    <ol>
        <li>Send: "I want to book a flight"</li>
        <li>Send: "Delhi"</li>
        <li>Send: "Dubai"</li>
        <li>Send: "July 15"</li>
        <li>Send: "1 adult"</li>
        <li>Send: "2" (to select flight option 2)</li>
        <li>Send: "John Doe, 10-May-1990, A1234567, Indian"</li>
        <li>Send: "Vegetarian meal and window seat"</li>
        <li>Send: "yes" (to confirm booking)</li>
    </ol>
    """

@app.route('/test', methods=['POST'])
def test_message():
    """Test endpoint for sending messages manually"""
    try:
        data = request.get_json()
        phone_number = data.get('phone_number', '+1234567890')
        message_text = data.get('message', '')
        
        if not message_text:
            return jsonify({'error': 'Message is required'}), 400
        
        logger.info(f"🧪 Test message from {phone_number}: {message_text}")
        
        # Process message
        session = session_manager.get_session(phone_number)
        response = dialogue_manager.process_message(session, message_text)
        
        # For mock service, also send the response
        if isinstance(whatsapp_service, MockWhatsAppService):
            whatsapp_service.send_text_message(phone_number, response)
        
        return jsonify({
            'status': 'success',
            'phone_number': phone_number,
            'message': message_text,
            'response': response,
            'session_state': session.state.value,
            'session_data': session.data
        })
        
    except Exception as e:
        logger.error(f"❌ Error in test endpoint: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/sessions', methods=['GET'])
def get_sessions():
    """Get information about active sessions"""
    try:
        sessions_info = []
        for phone_number, session in session_manager.sessions.items():
            sessions_info.append({
                'phone_number': phone_number,
                'state': session.state.value,
                'created_at': session.created_at.isoformat(),
                'last_activity': session.last_activity.isoformat(),
                'data': session.data
            })
        
        return jsonify({
            'active_sessions': len(sessions_info),
            'sessions': sessions_info
        })
        
    except Exception as e:
        logger.error(f"❌ Error getting sessions: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/sessions/<phone_number>', methods=['DELETE'])
def reset_session(phone_number: str):
    """Reset a specific session"""
    try:
        session_manager.reset_session(phone_number)
        logger.info(f"🔄 Session reset for {phone_number}")
        
        return jsonify({
            'status': 'success',
            'message': f'Session reset for {phone_number}'
        })
        
    except Exception as e:
        logger.error(f"❌ Error resetting session: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

def cleanup_sessions():
    """Background task to cleanup expired sessions"""
    while True:
        try:
            time.sleep(300)  # Run every 5 minutes
            session_manager.cleanup_expired_sessions(Config.SESSION_TIMEOUT // 60)
            logger.debug("🧹 Session cleanup completed")
        except Exception as e:
            logger.error(f"❌ Error in session cleanup: {e}")

if __name__ == '__main__':
    # Start session cleanup in background
    cleanup_thread = Thread(target=cleanup_sessions, daemon=True)
    cleanup_thread.start()
    
    logger.info(f"🚀 Starting Flight Booking Chatbot on port {Config.PORT}")
    logger.info(f"🔧 Environment: {Config.FLASK_ENV}")
    logger.info(f"📱 WhatsApp Service: {'Mock' if isinstance(whatsapp_service, MockWhatsAppService) else 'Real'}")
    
    if Config.FLASK_ENV == 'development':
        logger.info("💡 For testing, visit: http://localhost:5000/test")
        logger.info("💡 To test with curl:")
        logger.info("   curl -X POST http://localhost:5000/test -H 'Content-Type: application/json' -d '{\"phone_number\": \"+1234567890\", \"message\": \"I want to book a flight\"}'")
    
    app.run(
        host='0.0.0.0',
        port=Config.PORT,
        debug=Config.DEBUG
    ) 