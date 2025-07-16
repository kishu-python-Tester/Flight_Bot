#!/usr/bin/env python3
"""
Test if asking the same question after successful booking still works
This tests the specific scenario the user mentioned
"""

import os
import sys
from models.conversation import SessionManager, ConversationState
from services.whatsapp_service import MockWhatsAppService
from services.llm_dialogue_manager import LLMDialogueManager
from services.ticket_parser_service import TicketParserService
from models.ticket_storage import ticket_storage

def test_post_booking_questions():
    """Test asking questions after successful booking"""
    print("🧪 Testing Post-Booking Question Scenario")
    print("=" * 45)
    
    phone_number = "+1234567890"
    print(f"📞 Testing with: {phone_number}")
    
    # Initialize services
    session_manager = SessionManager()
    whatsapp_service = MockWhatsAppService()
    dialogue_manager = LLMDialogueManager(whatsapp_service)
    session = session_manager.get_session(phone_number)
    
    # Clean start
    ticket_storage.clear_ticket_data(phone_number)
    session_manager.reset_session(phone_number)
    session = session_manager.get_session(phone_number)
    
    print("🧹 Cleaned all existing data")
    
    # Step 1: Simulate PDF upload and successful processing
    print(f"\n📄 STEP 1: Upload PDF and process")
    
    # Mock ticket data (what would come from PDF upload)
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
    
    mock_price_comparison = {
        'comparison_available': True,
        'ticket_price': 25000,
        'currency': 'INR',
        'best_system_price': 14000,
        'price_difference': 11000,
        'savings_percentage': 44.0,
        'recommendation': 'cheaper'
    }
    
    # Set up session like after PDF upload
    session.set_context('parsed_ticket', mock_ticket_info)
    session.set_context('price_comparison', mock_price_comparison)
    
    # Store persistently
    ticket_storage.store_ticket_data(
        phone_number=phone_number,
        ticket_info=mock_ticket_info,
        price_comparison=mock_price_comparison
    )
    
    print("   ✅ PDF upload simulated - ticket data set")
    
    # Step 2: Ask question (like "compare prices")
    print(f"\n💬 STEP 2: Ask question - 'compare prices'")
    
    response1 = dialogue_manager.process_message(session, "compare prices")
    
    has_price_info_1 = "₹" in response1 and "price" in response1.lower()
    has_error_1 = "not available" in response1.lower() or "error" in response1.lower()
    
    success_1 = has_price_info_1 and not has_error_1
    print(f"   First question: {'✅ SUCCESS' if success_1 else '❌ FAILED'}")
    
    if not success_1:
        print(f"   Response: {response1[:200]}...")
    
    # Step 3: Simulate successful booking
    print(f"\n🎫 STEP 3: Simulate successful booking")
    
    # Simulate booking with better price
    response_booking = dialogue_manager.process_message(session, "book with new price")
    booking_initiated = "office id" in response_booking.lower() or "office" in response_booking.lower()
    
    if booking_initiated:
        print("   📋 Booking initiated - collecting office ID")
        
        # Provide office ID
        response_office = dialogue_manager.process_message(session, "CORP-MUMBAI-001")
        booking_completed = "confirmed" in response_office.lower() or "pnr" in response_office.lower()
        
        if booking_completed:
            print("   ✅ Booking completed successfully")
            print(f"   Session state: {session.state}")
            
            # Check what data remains in session after booking
            session_ticket = session.get_context('parsed_ticket')
            session_comparison = session.get_context('price_comparison')
            
            print(f"   Session ticket data: {'✅ Present' if session_ticket else '❌ Missing'}")
            print(f"   Session comparison data: {'✅ Present' if session_comparison else '❌ Missing'}")
            
            # Check persistent storage
            stored_data = ticket_storage.get_ticket_data(phone_number)
            storage_ticket = stored_data.get('ticket_info') if stored_data else None
            storage_comparison = stored_data.get('price_comparison') if stored_data else None
            
            print(f"   Storage ticket data: {'✅ Present' if storage_ticket else '❌ Missing'}")
            print(f"   Storage comparison data: {'✅ Present' if storage_comparison else '❌ Missing'}")
            
        else:
            print(f"   ❌ Booking failed to complete")
            print(f"   Response: {response_office[:200]}...")
            return False
    else:
        print(f"   ❌ Booking failed to initiate")
        print(f"   Response: {response_booking[:200]}...")
        return False
    
    # Step 4: Ask the SAME question again after booking
    print(f"\n💬 STEP 4: Ask SAME question again - 'compare prices'")
    
    response2 = dialogue_manager.process_message(session, "compare prices")
    
    has_price_info_2 = "₹" in response2 and "price" in response2.lower()
    has_error_2 = "not available" in response2.lower() or "error" in response2.lower()
    
    success_2 = has_price_info_2 and not has_error_2
    print(f"   Second question: {'✅ SUCCESS' if success_2 else '❌ FAILED'}")
    
    if not success_2:
        print(f"   Response: {response2[:200]}...")
        print(f"   Full response: {response2}")
    
    # Step 5: Analysis
    print(f"\n📊 ANALYSIS")
    print("=" * 15)
    
    print(f"Before booking: {'✅ Worked' if success_1 else '❌ Failed'}")
    print(f"After booking:  {'✅ Worked' if success_2 else '❌ Failed'}")
    
    if success_1 and success_2:
        print(f"\n🎉 PERFECT! Questions work both before AND after booking")
        return True
    elif success_1 and not success_2:
        print(f"\n⚠️ ISSUE CONFIRMED! Questions work before booking but FAIL after booking")
        print(f"   This is the exact issue the user reported")
        return False
    elif not success_1:
        print(f"\n❌ Questions don't work even before booking - different issue")
        return False
    else:
        print(f"\n🤔 Unexpected scenario")
        return False

def test_different_post_booking_questions():
    """Test different types of questions after booking"""
    print(f"\n🔍 Testing Different Post-Booking Questions")
    print("=" * 45)
    
    phone_number = "+1234567891"  # Different number for clean test
    
    # Set up the same scenario
    session_manager = SessionManager()
    whatsapp_service = MockWhatsAppService()
    dialogue_manager = LLMDialogueManager(whatsapp_service)
    session = session_manager.get_session(phone_number)
    
    # Mock data
    mock_ticket_info = {
        'success': True,
        'flight_details': {
            'airline': 'Emirates',
            'flight_number': 'EK512',
            'origin_airport': 'DEL',
            'destination_airport': 'DXB',
            'departure_date': '2024-08-30'
        }
    }
    
    mock_price_comparison = {
        'comparison_available': True,
        'ticket_price': 25000,
        'best_system_price': 14000,
        'price_difference': 11000,
        'recommendation': 'cheaper'
    }
    
    session.set_context('parsed_ticket', mock_ticket_info)
    session.set_context('price_comparison', mock_price_comparison)
    ticket_storage.store_ticket_data(phone_number, mock_ticket_info, mock_price_comparison)
    
    # Complete a booking to set COMPLETED state
    session.set_state(ConversationState.COMPLETED)
    
    print(f"   Session state: {session.state}")
    
    # Test different questions
    questions = [
        "compare prices",
        "price comparison",
        "search similar flights",
        "book new flight",
        "show me flight details"
    ]
    
    results = {}
    
    for question in questions:
        print(f"\n   Testing: '{question}'")
        response = dialogue_manager.process_message(session, question)
        
        # Check if response is helpful
        has_error = "not available" in response.lower() or "error" in response.lower()
        has_content = len(response) > 50  # Reasonable response length
        
        success = not has_error and has_content
        results[question] = success
        
        print(f"      Result: {'✅ Works' if success else '❌ Failed'}")
        if not success:
            print(f"      Response: {response[:100]}...")
    
    # Summary
    working_questions = sum(1 for success in results.values() if success)
    total_questions = len(questions)
    
    print(f"\n   Summary: {working_questions}/{total_questions} questions work after booking")
    
    return working_questions == total_questions

if __name__ == "__main__":
    try:
        print("🔍 TESTING POST-BOOKING QUESTION SCENARIO")
        print("=" * 50)
        
        main_test_ok = test_post_booking_questions()
        different_questions_ok = test_different_post_booking_questions()
        
        print(f"\n📋 FINAL RESULTS")
        print("=" * 20)
        print(f"Main scenario (compare prices): {'✅ Works' if main_test_ok else '❌ Broken'}")
        print(f"Different questions: {'✅ Work' if different_questions_ok else '❌ Issues'}")
        
        if main_test_ok and different_questions_ok:
            print(f"\n✅ ALL GOOD! Questions work fine after booking")
            print(f"   Your issue should be resolved")
        elif not main_test_ok:
            print(f"\n❌ CONFIRMED ISSUE! Questions fail after booking")
            print(f"   This needs to be fixed")
        else:
            print(f"\n⚠️ MIXED RESULTS - some questions work, others don't")
            
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc() 