#!/usr/bin/env python3
"""
Test script for the new PDF ticket booking flow with office ID and PDF generation
"""

import os
import sys
import tempfile
from datetime import datetime
from models.conversation import SessionManager, ConversationState
from services.whatsapp_service import MockWhatsAppService
from services.llm_dialogue_manager import LLMDialogueManager
from services.pdf_generator_service import PDFGeneratorService

def test_pdf_booking_flow():
    """Test the complete PDF booking flow with office ID"""
    print("🧪 Testing PDF Ticket Booking Flow with Office ID")
    print("=" * 60)
    
    # Initialize services
    session_manager = SessionManager()
    whatsapp_service = MockWhatsAppService()
    dialogue_manager = LLMDialogueManager(whatsapp_service)
    
    # Test phone number
    phone_number = "+1234567890"
    
    print(f"🔄 Starting PDF booking flow for {phone_number}")
    print()
    
    # Step 1: User greets
    print("Step 1: User sends greeting")
    session = session_manager.get_session(phone_number)
    response = dialogue_manager.process_message(session, "hi")
    print(f"📱 Bot responds: {response[:100]}...")
    print(f"🔧 Session state: {session.state.value}")
    print("-" * 50)
    
    # Step 2: Simulate PDF ticket upload and analysis (mock parsed ticket data)
    print("Step 2: Simulating PDF ticket upload and analysis")
    
    # Mock parsed ticket data from a more expensive ticket
    mock_ticket_info = {
        'success': True,
        'flight_details': {
            'airline': 'Emirates',
            'flight_number': 'EK512',
            'origin_city': 'Delhi',
            'origin_airport': 'DEL',
            'destination_city': 'Dubai',
            'destination_airport': 'DXB',
            'departure_date': '2024-08-30',
            'departure_time': '11:30',
            'arrival_time': '14:15',
            'class_of_service': 'Business',
            'passenger_name': 'John Smith',
            'booking_reference': 'EK12345',
            'ticket_price': '₹25,000',
            'ticket_price_numeric': 25000,
            'currency': 'INR'
        },
        'confidence': 0.95
    }
    
    # Mock price comparison showing our system has better price
    mock_price_comparison = {
        'comparison_available': True,
        'ticket_price': 25000,
        'currency': 'INR',
        'best_system_price': 16000,
        'price_difference': 9000,
        'savings_percentage': 36.0,
        'comparable_flights': [
            {'airline': 'Emirates', 'flight_number': 'EK512', 'price': 16000, 'is_same_airline': True},
            {'airline': 'IndiGo', 'flight_number': '6E201', 'price': 14000, 'is_same_airline': False}
        ],
        'recommendation': 'cheaper'
    }
    
    # Set parsed ticket context in session
    session.set_context('parsed_ticket', mock_ticket_info)
    session.set_context('price_comparison', mock_price_comparison)
    
    print("✅ Mock ticket analyzed:")
    print(f"   Flight: Emirates EK512, Business Class")
    print(f"   Route: Delhi → Dubai")
    print(f"   User's Price: ₹25,000")
    print(f"   Our Best Price: ₹16,000")
    print(f"   Potential Savings: ₹9,000 (36%)")
    print("-" * 50)
    
    # Step 3: User requests booking with better price
    print("Step 3: User requests booking with better price")
    response = dialogue_manager.process_message(session, "book with new price")
    print(f"📱 Bot responds:")
    print(response)
    print(f"🔧 Session state: {session.state.value}")
    print("-" * 50)
    
    # Step 4: User provides office ID
    print("Step 4: User provides office ID")
    office_id = "CORP-MUMBAI-001"
    response = dialogue_manager.process_message(session, office_id)
    print(f"📱 Bot responds:")
    print(response)
    print(f"🔧 Session state: {session.state.value}")
    print("-" * 50)
    
    # Step 5: Check if PDF was generated
    print("Step 5: Checking PDF generation")
    pdf_path = session.get_data('pdf_path')
    new_booking = session.get_data('new_booking')
    
    if pdf_path and os.path.exists(pdf_path):
        print(f"✅ PDF ticket generated: {pdf_path}")
        print(f"   File size: {os.path.getsize(pdf_path)} bytes")
        
        if new_booking:
            print(f"✅ New booking data:")
            print(f"   PNR: {new_booking.get('pnr')}")
            print(f"   Office ID: {new_booking.get('office_id')}")
            print(f"   New Price: ₹{new_booking.get('ticket_price'):,}")
            print(f"   Savings: ₹{25000 - new_booking.get('ticket_price'):,}")
        
        # Clean up test PDF
        try:
            os.remove(pdf_path)
            print(f"✅ Test PDF cleaned up")
        except Exception as e:
            print(f"⚠️ Failed to clean up PDF: {e}")
    else:
        print("❌ PDF was not generated")
    
    print("-" * 50)
    
    # Step 6: Test PDF generator directly
    print("Step 6: Testing PDF generator directly")
    
    pdf_generator = PDFGeneratorService()
    
    test_booking_data = {
        'pnr': 'AB123X',
        'airline': 'Emirates',
        'flight_number': 'EK512',
        'origin_city': 'Delhi',
        'origin_airport': 'DEL',
        'destination_city': 'Dubai',
        'destination_airport': 'DXB',
        'departure_date': '2024-08-30',
        'departure_time': '11:30',
        'arrival_time': '14:15',
        'class_of_service': 'Business',
        'passenger_name': 'John Smith',
        'ticket_price': 16000,
        'currency': 'INR',
        'office_id': 'CORP-MUMBAI-001',
        'booking_date': datetime.now().strftime('%Y-%m-%d'),
        'booking_time': datetime.now().strftime('%H:%M')
    }
    
    test_pdf_path = pdf_generator.generate_ticket_pdf(test_booking_data)
    
    if test_pdf_path and os.path.exists(test_pdf_path):
        print(f"✅ Direct PDF generation successful: {test_pdf_path}")
        print(f"   File size: {os.path.getsize(test_pdf_path)} bytes")
        
        # Clean up
        try:
            os.remove(test_pdf_path)
            print(f"✅ Test PDF cleaned up")
        except Exception as e:
            print(f"⚠️ Failed to clean up test PDF: {e}")
    else:
        print("❌ Direct PDF generation failed")
    
    print("-" * 50)
    
    # Step 7: Test different booking scenarios
    print("Step 7: Testing edge cases")
    
    # Test invalid office ID
    session2 = session_manager.get_session("+9876543210")
    session2.set_state(ConversationState.COLLECT_OFFICE_ID)
    response = dialogue_manager.process_message(session2, "xx")  # Too short
    print(f"📝 Invalid office ID response: {response[:100]}...")
    
    # Test booking without price comparison
    session3 = session_manager.get_session("+5555555555")
    response = dialogue_manager.process_message(session3, "book with new price")
    print(f"📝 No price comparison response: {response[:100]}...")
    
    print("✅ Test completed!")
    print(f"📊 Final session data keys: {list(session.data.keys())}")
    print(f"📊 Final session context keys: {list(session.context.keys())}")

def test_alternative_booking_phrases():
    """Test different ways users might request booking"""
    print("\n🧪 Testing Alternative Booking Phrases")
    print("=" * 50)
    
    session_manager = SessionManager()
    whatsapp_service = MockWhatsAppService()
    dialogue_manager = LLMDialogueManager(whatsapp_service)
    
    # Mock session with ticket and price comparison
    phone_number = "+1111111111"
    session = session_manager.get_session(phone_number)
    
    mock_ticket_info = {
        'success': True,
        'flight_details': {
            'airline': 'Air India',
            'flight_number': 'AI131',
            'origin_city': 'Mumbai',
            'origin_airport': 'BOM',
            'destination_city': 'Dubai',
            'destination_airport': 'DXB',
            'departure_date': '2024-09-15',
            'departure_time': '09:45',
            'arrival_time': '12:30',
            'class_of_service': 'Economy',
            'passenger_name': 'Sarah Ahmed',
            'booking_reference': 'AI98765',
            'ticket_price': '₹13,800',
            'ticket_price_numeric': 13800,
            'currency': 'INR'
        }
    }
    
    mock_price_comparison = {
        'comparison_available': True,
        'ticket_price': 13800,
        'best_system_price': 12500,
        'price_difference': 1300,
        'savings_percentage': 9.4,
        'recommendation': 'cheaper'
    }
    
    session.set_context('parsed_ticket', mock_ticket_info)
    session.set_context('price_comparison', mock_price_comparison)
    
    # Test various booking phrases
    test_phrases = [
        "go ahead with booking",
        "proceed",
        "book it",
        "yes book",
        "book now",
        "book cheaper",
        "book with system"
    ]
    
    for phrase in test_phrases:
        session_copy = session_manager.get_session(f"+{hash(phrase) % 1000000000}")
        session_copy.set_context('parsed_ticket', mock_ticket_info)
        session_copy.set_context('price_comparison', mock_price_comparison)
        
        response = dialogue_manager.process_message(session_copy, phrase)
        
        if "Office ID" in response:
            print(f"✅ '{phrase}' - Correctly detected booking intent")
        else:
            print(f"❌ '{phrase}' - Failed to detect booking intent")
    
    print("✅ Alternative phrases test completed!")

if __name__ == "__main__":
    # Add current directory to Python path for imports
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    try:
        test_pdf_booking_flow()
        test_alternative_booking_phrases()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc() 