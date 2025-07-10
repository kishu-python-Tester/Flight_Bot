#!/usr/bin/env python3
"""
Debug test script for the flight booking chatbot
"""

from models.conversation import SessionManager, ConversationState
from services.whatsapp_service import MockWhatsAppService
from services.dialogue_manager import DialogueManager
from services.intent_service import IntentService

def debug_intent_detection():
    """Debug intent detection step by step"""
    print("🔍 Debugging Intent Detection")
    print("=" * 50)
    
    intent_service = IntentService()
    
    # Test city extraction
    test_messages = [
        "I want to book a flight",
        "Delhi", 
        "Dubai",
        "from Delhi to Dubai",
        "I want to fly from Delhi to Dubai"
    ]
    
    for msg in test_messages:
        print(f"\n🔍 Message: '{msg}'")
        
        # Test intent detection
        is_flight_intent = intent_service.detect_flight_booking_intent(msg)
        print(f"  ✈️ Flight intent detected: {is_flight_intent}")
        
        # Test city extraction
        cities = intent_service.extract_cities(msg)
        print(f"  🏙️ Cities found: {[city['name'] + ' (' + city['iata'] + ')' for city in cities]}")
        
        # Test date extraction
        date = intent_service.extract_date(msg)
        print(f"  📅 Date found: {date}")
        
        # Test passenger count
        passengers = intent_service.extract_passenger_count(msg)
        print(f"  👥 Passengers: {passengers}")

def debug_conversation_flow():
    """Debug the conversation flow step by step"""
    print("\n\n🔍 Debugging Conversation Flow")
    print("=" * 50)
    
    session_manager = SessionManager()
    whatsapp_service = MockWhatsAppService()
    dialogue_manager = DialogueManager(whatsapp_service)
    
    phone_number = "+1234567890"
    session = session_manager.get_session(phone_number)
    
    print(f"Initial state: {session.state.value}")
    print(f"Initial data: {session.data}")
    
    # Step 1: Flight booking intent
    print(f"\n📝 Step 1: Processing 'I want to book a flight'")
    response1 = dialogue_manager.process_message(session, "I want to book a flight")
    print(f"Response: {response1}")
    print(f"State: {session.state.value}")
    print(f"Data: {session.data}")
    
    # Step 2: Source city
    print(f"\n📝 Step 2: Processing 'Delhi'")
    response2 = dialogue_manager.process_message(session, "Delhi")
    print(f"Response: {response2}")
    print(f"State: {session.state.value}")
    print(f"Data: {session.data}")
    
    # Step 3: Destination city
    print(f"\n📝 Step 3: Processing 'Dubai'")
    response3 = dialogue_manager.process_message(session, "Dubai")
    print(f"Response: {response3}")
    print(f"State: {session.state.value}")
    print(f"Data: {session.data}")

def test_flight_search():
    """Test flight search directly"""
    print("\n\n🔍 Testing Flight Search")
    print("=" * 50)
    
    from services.flight_service import FlightService
    
    flight_service = FlightService()
    
    # Test flight search
    flights = flight_service.search_flights(
        origin="DEL",
        destination="DXB", 
        date="2025-07-15",
        adults=1,
        children=0,
        infants=0
    )
    
    print(f"Found {len(flights)} flights:")
    for i, flight in enumerate(flights, 1):
        print(f"  {i}. {flight.airline} {flight.flight_id} - ₹{flight.price:,}")

if __name__ == "__main__":
    debug_intent_detection()
    debug_conversation_flow()
    test_flight_search() 