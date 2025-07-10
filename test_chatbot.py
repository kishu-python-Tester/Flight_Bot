#!/usr/bin/env python3
"""
Simple test script for the flight booking chatbot
"""

from models.conversation import SessionManager, ConversationState
from services.whatsapp_service import MockWhatsAppService
from services.dialogue_manager import DialogueManager

def test_complete_booking_flow():
    """Test the complete booking workflow"""
    print("🧪 Testing Flight Booking Chatbot")
    print("=" * 50)
    
    # Initialize services
    session_manager = SessionManager()
    whatsapp_service = MockWhatsAppService()
    dialogue_manager = DialogueManager(whatsapp_service)
    
    # Test conversation flow
    phone_number = "+1234567890"
    test_messages = [
        "I want to book a flight",
        "Delhi",
        "Dubai", 
        "July 15",
        "1 adult",
        "2",  # Select flight option 2
        "John Doe, 10-May-1990, A1234567, Indian",
        "Vegetarian meal and window seat",
        "yes"  # Confirm booking
    ]
    
    print(f"🔄 Starting conversation for {phone_number}")
    print()
    
    for i, message in enumerate(test_messages, 1):
        print(f"Step {i}: User sends: '{message}'")
        
        # Get session
        session = session_manager.get_session(phone_number)
        
        # Process message
        response = dialogue_manager.process_message(session, message)
        
        print(f"📱 Bot responds:")
        print(response)
        print(f"🔧 Session state: {session.state.value}")
        print("-" * 50)
    
    print("✅ Test completed!")
    print(f"📊 Final session data: {session.data}")

if __name__ == "__main__":
    test_complete_booking_flow() 