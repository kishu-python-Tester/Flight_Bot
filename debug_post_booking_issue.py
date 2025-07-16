#!/usr/bin/env python3
"""
Debug script to understand why post-booking questions sometimes fail
Tests various scenarios to find the inconsistency
"""

import os
import sys
from models.conversation import SessionManager, ConversationState
from services.whatsapp_service import MockWhatsAppService
from services.llm_dialogue_manager import LLMDialogueManager
from models.ticket_storage import ticket_storage

def test_post_booking_consistency():
    """Test post-booking question consistency"""
    print("🔍 DEBUGGING POST-BOOKING CONSISTENCY ISSUE")
    print("=" * 50)
    
    phone_number = "+1234567890"
    
    # Initialize services
    session_manager = SessionManager()
    whatsapp_service = MockWhatsAppService()
    dialogue_manager = LLMDialogueManager(whatsapp_service)
    
    # Test multiple scenarios
    scenarios = [
        "compare prices",
        "price comparison", 
        "show prices",
        "check prices",
        "what about prices",
        "tell me prices",
        "price details"
    ]
    
    results = {}
    
    for i, question in enumerate(scenarios, 1):
        print(f"\n{'='*15} SCENARIO #{i} {'='*15}")
        print(f"Question: '{question}'")
        
        # Clean start for each test
        ticket_storage.clear_ticket_data(phone_number)
        session_manager.reset_session(phone_number)
        session = session_manager.get_session(phone_number)
        
        # Set up ticket data (like after PDF upload)
        mock_ticket_info = {
            'success': True,
            'flight_details': {
                'airline': 'Emirates',
                'flight_number': 'EK512',
                'origin_city': 'Delhi',
                'origin_airport': 'DEL',
                'destination_city': 'Dubai', 
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
        
        # Set session data
        session.set_context('parsed_ticket', mock_ticket_info)
        session.set_context('price_comparison', mock_price_comparison)
        
        # Store persistently
        ticket_storage.store_ticket_data(phone_number, mock_ticket_info, mock_price_comparison)
        
        print(f"   ✅ Ticket data set up")
        
        # Simulate completed booking state
        session.set_state(ConversationState.COMPLETED)
        print(f"   📋 State set to COMPLETED")
        
        # Test the question
        print(f"   💬 Testing question: '{question}'")
        
        # Check data before question
        has_ticket_before = bool(session.get_context('parsed_ticket'))
        has_comparison_before = bool(session.get_context('price_comparison'))
        
        print(f"   📱 Before question - Ticket: {'✅' if has_ticket_before else '❌'}, Comparison: {'✅' if has_comparison_before else '❌'}")
        
        # Test action detection
        action = dialogue_manager._detect_ticket_action(question)
        print(f"   🔍 Detected action: '{action}'")
        
        # Process the message
        response = dialogue_manager.process_message(session, question)
        
        # Check response quality
        is_booking_request = "which city" in response.lower() and "fly from" in response.lower()
        has_price_info = "₹" in response and "price" in response.lower()
        has_ticket_info = "ticket" in response.lower() or "flight" in response.lower()
        
        print(f"   📊 Response analysis:")
        print(f"      Is booking request: {'❌ YES' if is_booking_request else '✅ NO'}")
        print(f"      Has price info: {'✅ YES' if has_price_info else '❌ NO'}")
        print(f"      Has ticket info: {'✅ YES' if has_ticket_info else '❌ NO'}")
        
        # Check data after question
        has_ticket_after = bool(session.get_context('parsed_ticket'))
        has_comparison_after = bool(session.get_context('price_comparison'))
        
        print(f"   📱 After question - Ticket: {'✅' if has_ticket_after else '❌'}, Comparison: {'✅' if has_comparison_after else '❌'}")
        
        # Determine success
        success = not is_booking_request and (has_price_info or has_ticket_info)
        results[question] = {
            'success': success,
            'action_detected': action,
            'is_booking_request': is_booking_request,
            'response_snippet': response[:100]
        }
        
        print(f"   Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
        
        if not success:
            print(f"   Response: {response[:200]}...")
    
    # Summary
    print(f"\n📊 CONSISTENCY ANALYSIS")
    print("=" * 25)
    
    successful = sum(1 for r in results.values() if r['success'])
    total = len(results)
    
    print(f"Successful questions: {successful}/{total}")
    
    if successful == total:
        print(f"\n✅ CONSISTENT - All questions work")
    elif successful == 0:
        print(f"\n❌ COMPLETELY BROKEN - No questions work")
    else:
        print(f"\n⚠️ INCONSISTENT - Some work, some don't")
        
        print(f"\nWorking questions:")
        for q, r in results.items():
            if r['success']:
                print(f"   ✅ '{q}' - Action: {r['action_detected']}")
        
        print(f"\nFailing questions:")
        for q, r in results.items():
            if not r['success']:
                print(f"   ❌ '{q}' - Action: {r['action_detected']}")
                print(f"      Response: {r['response_snippet']}")
    
    return successful == total

def test_data_persistence():
    """Test if ticket data persists correctly"""
    print(f"\n🔍 TESTING DATA PERSISTENCE")
    print("=" * 30)
    
    phone_number = "+1234567891"
    session_manager = SessionManager()
    dialogue_manager = LLMDialogueManager(MockWhatsAppService())
    
    # Clean start
    ticket_storage.clear_ticket_data(phone_number)
    session_manager.reset_session(phone_number)
    session = session_manager.get_session(phone_number)
    
    # Set up data
    mock_ticket = {'success': True, 'flight_details': {'airline': 'Emirates'}}
    mock_comparison = {'comparison_available': True, 'ticket_price': 25000}
    
    # Test 1: Session data persistence
    print("   Test 1: Session data")
    session.set_context('parsed_ticket', mock_ticket)
    session.set_context('price_comparison', mock_comparison)
    
    # Change state to COMPLETED
    session.set_state(ConversationState.COMPLETED)
    
    # Check if data is still there
    ticket_still_there = bool(session.get_context('parsed_ticket'))
    comparison_still_there = bool(session.get_context('price_comparison'))
    
    print(f"      After state change - Ticket: {'✅' if ticket_still_there else '❌'}, Comparison: {'✅' if comparison_still_there else '❌'}")
    
    # Test 2: Storage data persistence
    print("   Test 2: Storage data")
    ticket_storage.store_ticket_data(phone_number, mock_ticket, mock_comparison)
    
    stored_data = ticket_storage.get_ticket_data(phone_number)
    storage_has_ticket = bool(stored_data and stored_data.get('ticket_info'))
    storage_has_comparison = bool(stored_data and stored_data.get('price_comparison'))
    
    print(f"      Storage - Ticket: {'✅' if storage_has_ticket else '❌'}, Comparison: {'✅' if storage_has_comparison else '❌'}")
    
    # Test 3: Data restoration
    print("   Test 3: Data restoration")
    session.set_context('parsed_ticket', None)  # Clear session
    session.set_context('price_comparison', None)
    
    # Try to restore
    response = dialogue_manager.process_message(session, "compare prices")
    
    # Check if data was restored
    restored_ticket = bool(session.get_context('parsed_ticket'))
    restored_comparison = bool(session.get_context('price_comparison'))
    
    print(f"      After restoration - Ticket: {'✅' if restored_ticket else '❌'}, Comparison: {'✅' if restored_comparison else '❌'}")
    
    return ticket_still_there and comparison_still_there and storage_has_ticket and storage_has_comparison

def test_action_detection():
    """Test ticket action detection"""
    print(f"\n🔍 TESTING ACTION DETECTION")
    print("=" * 25)
    
    dialogue_manager = LLMDialogueManager(MockWhatsAppService())
    
    test_phrases = [
        "compare prices",
        "price comparison", 
        "show prices",
        "check prices",
        "what about prices",
        "tell me prices",
        "price details",
        "how much does it cost",
        "what is the price",
        "compare with your system"
    ]
    
    print("   Testing action detection:")
    detected_actions = {}
    
    for phrase in test_phrases:
        action = dialogue_manager._detect_ticket_action(phrase)
        detected_actions[phrase] = action
        print(f"      '{phrase}' -> '{action}'")
    
    # Count how many were detected as compare_prices
    compare_price_count = sum(1 for action in detected_actions.values() if action == 'compare_prices')
    
    print(f"\n   Summary: {compare_price_count}/{len(test_phrases)} detected as 'compare_prices'")
    
    return compare_price_count > 0

if __name__ == "__main__":
    try:
        consistency_ok = test_post_booking_consistency()
        persistence_ok = test_data_persistence()
        detection_ok = test_action_detection()
        
        print(f"\n📋 FINAL DIAGNOSIS")
        print("=" * 20)
        print(f"Question consistency: {'✅ OK' if consistency_ok else '❌ ISSUES'}")
        print(f"Data persistence: {'✅ OK' if persistence_ok else '❌ ISSUES'}")
        print(f"Action detection: {'✅ OK' if detection_ok else '❌ ISSUES'}")
        
        if consistency_ok and persistence_ok and detection_ok:
            print(f"\n✅ ALL SYSTEMS WORKING - Issue might be elsewhere")
        else:
            print(f"\n❌ ISSUES FOUND - These need to be fixed:")
            if not consistency_ok:
                print(f"   - Post-booking questions inconsistent")
            if not persistence_ok:
                print(f"   - Data not persisting properly")
            if not detection_ok:
                print(f"   - Action detection not working")
        
    except Exception as e:
        print(f"\n❌ Debug error: {e}")
        import traceback
        traceback.print_exc() 