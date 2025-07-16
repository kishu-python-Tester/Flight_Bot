#!/usr/bin/env python3
"""
Real-time session tester to debug the exact user scenario
Run this to test your specific case and see detailed debugging info
"""

import os
import sys
import json
from datetime import datetime
from models.conversation import SessionManager, ConversationState
from services.whatsapp_service import MockWhatsAppService
from services.llm_dialogue_manager import LLMDialogueManager
from models.ticket_storage import ticket_storage

class RealTimeSessionTester:
    def __init__(self):
        self.session_manager = SessionManager()
        self.whatsapp_service = MockWhatsAppService()
        self.dialogue_manager = LLMDialogueManager(self.whatsapp_service)
        self.phone_number = "+1234567890"  # Your test number
        
    def log(self, message, level="INFO"):
        """Enhanced logging with timestamps"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] {level}: {message}")
    
    def show_session_state(self, session, label=""):
        """Show complete session state"""
        print(f"\n📊 SESSION STATE {label}")
        print("=" * 30)
        print(f"   Phone: {session.phone_number}")
        print(f"   State: {session.state}")
        print(f"   Retry Count: {session.get_retry_count()}")
        
        # Show context data
        parsed_ticket = session.get_context('parsed_ticket')
        price_comparison = session.get_context('price_comparison')
        
        print(f"   Parsed Ticket: {'✅ Present' if parsed_ticket else '❌ Missing'}")
        print(f"   Price Comparison: {'✅ Present' if price_comparison else '❌ Missing'}")
        
        if parsed_ticket:
            flight_details = parsed_ticket.get('flight_details', {})
            print(f"      Flight: {flight_details.get('airline', 'N/A')} {flight_details.get('flight_number', 'N/A')}")
            print(f"      Route: {flight_details.get('origin_airport', 'N/A')} → {flight_details.get('destination_airport', 'N/A')}")
        
        if price_comparison:
            available = price_comparison.get('comparison_available', False)
            print(f"      Comparison Available: {'✅' if available else '❌'}")
            if available:
                print(f"      User Price: ₹{price_comparison.get('ticket_price', 0):,}")
                print(f"      System Price: ₹{price_comparison.get('best_system_price', 0):,}")
        
        # Show booking data
        booking_data = {
            'source_city': session.get_data('source_city'),
            'destination_city': session.get_data('destination_city'), 
            'departure_date': session.get_data('departure_date'),
            'selected_flight': session.get_data('selected_flight'),
            'pnr': session.get_data('pnr')
        }
        
        has_booking_data = any(v for v in booking_data.values())
        if has_booking_data:
            print(f"   Booking Data: ✅ Present")
            for key, value in booking_data.items():
                if value:
                    print(f"      {key}: {value}")
        else:
            print(f"   Booking Data: ❌ None")
    
    def show_storage_state(self):
        """Show persistent storage state"""
        print(f"\n💾 STORAGE STATE")
        print("=" * 20)
        
        stored_data = ticket_storage.get_ticket_data(self.phone_number)
        if stored_data:
            print(f"   Stored Data: ✅ Present")
            
            ticket_info = stored_data.get('ticket_info')
            price_comparison = stored_data.get('price_comparison')
            
            if ticket_info:
                print(f"   Stored Ticket: ✅ Present")
                flight_details = ticket_info.get('flight_details', {})
                print(f"      Flight: {flight_details.get('airline', 'N/A')} {flight_details.get('flight_number', 'N/A')}")
            
            if price_comparison:
                available = price_comparison.get('comparison_available', False)
                print(f"   Stored Comparison: {'✅ Available' if available else '❌ Not available'}")
                if available:
                    print(f"      Prices: ₹{price_comparison.get('ticket_price', 0):,} vs ₹{price_comparison.get('best_system_price', 0):,}")
        else:
            print(f"   Stored Data: ❌ None")
    
    def test_action_detection(self, message):
        """Test action detection for a message"""
        print(f"\n🔍 ACTION DETECTION TEST")
        print("=" * 25)
        print(f"   Message: '{message}'")
        
        action = self.dialogue_manager._detect_ticket_action(message)
        print(f"   Detected Action: '{action}'")
        
        # Test various price-related phrases
        price_phrases = ['compare prices', 'price comparison', 'show prices', 'check prices', 'what about prices']
        print(f"   Would these be detected?")
        for phrase in price_phrases:
            detected = self.dialogue_manager._detect_ticket_action(phrase)
            match = "✅" if detected == 'compare_prices' else "❌"
            print(f"      '{phrase}' -> '{detected}' {match}")
        
        return action
    
    def simulate_your_scenario(self):
        """Simulate the exact scenario you're experiencing"""
        print(f"🧪 SIMULATING YOUR REAL SCENARIO")
        print("=" * 40)
        
        # Step 1: Clean start
        self.log("Starting clean session")
        ticket_storage.clear_ticket_data(self.phone_number)
        self.session_manager.reset_session(self.phone_number)
        session = self.session_manager.get_session(self.phone_number)
        
        self.show_session_state(session, "- INITIAL")
        
        # Step 2: Simulate PDF upload (like what you did)
        self.log("Simulating PDF upload and processing")
        
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
        
        # Set session data (like after PDF processing)
        session.set_context('parsed_ticket', mock_ticket_info)
        session.set_context('price_comparison', mock_price_comparison)
        
        # Store persistently
        ticket_storage.store_ticket_data(
            phone_number=self.phone_number,
            ticket_info=mock_ticket_info,
            price_comparison=mock_price_comparison
        )
        
        self.show_session_state(session, "- AFTER PDF UPLOAD")
        self.show_storage_state()
        
        # Step 3: First question (before booking)
        self.log("Testing first question - should work")
        
        first_question = "compare prices"
        self.test_action_detection(first_question)
        
        response1 = self.dialogue_manager.process_message(session, first_question)
        
        has_price_info_1 = "₹" in response1 and "price" in response1.lower()
        is_booking_request_1 = "which city" in response1.lower() and "fly from" in response1.lower()
        
        print(f"\n📱 FIRST QUESTION RESULT:")
        print(f"   Question: '{first_question}'")
        print(f"   Has price info: {'✅' if has_price_info_1 else '❌'}")
        print(f"   Is booking request: {'❌ YES' if is_booking_request_1 else '✅ NO'}")
        print(f"   Response length: {len(response1)} chars")
        
        if is_booking_request_1:
            print(f"   ❌ PROBLEM: First question failed!")
            print(f"   Response: {response1[:200]}...")
            return False
        
        # Step 4: Simulate successful booking
        self.log("Simulating successful booking process")
        
        # Book with better price
        booking_response = self.dialogue_manager.process_message(session, "book with new price")
        print(f"   Booking initiated: {'✅' if 'office' in booking_response.lower() else '❌'}")
        
        # Provide office ID
        office_response = self.dialogue_manager.process_message(session, "CORP-MUMBAI-001")
        booking_completed = "confirmed" in office_response.lower() or "pnr" in office_response.lower()
        print(f"   Booking completed: {'✅' if booking_completed else '❌'}")
        
        if booking_completed:
            self.show_session_state(session, "- AFTER BOOKING")
            
            # Step 5: Ask the SAME question again (your issue)
            self.log("Testing SAME question after booking - this is where your issue happens")
            
            second_question = "compare prices"  # Same question
            self.test_action_detection(second_question)
            
            response2 = self.dialogue_manager.process_message(session, second_question)
            
            has_price_info_2 = "₹" in response2 and "price" in response2.lower()
            is_booking_request_2 = "which city" in response2.lower() and "fly from" in response2.lower()
            
            print(f"\n📱 SECOND QUESTION RESULT (THE ISSUE):")
            print(f"   Question: '{second_question}'")
            print(f"   Has price info: {'✅' if has_price_info_2 else '❌'}")
            print(f"   Is booking request: {'❌ YES' if is_booking_request_2 else '✅ NO'}")
            print(f"   Response length: {len(response2)} chars")
            
            if is_booking_request_2:
                print(f"   ❌ CONFIRMED: This is your issue!")
                print(f"   Response: {response2[:300]}...")
                
                # Show what went wrong
                self.show_session_state(session, "- AFTER SECOND QUESTION")
                self.show_storage_state()
                
                return False
            else:
                print(f"   ✅ Working correctly!")
                return True
        else:
            print(f"   ❌ Booking failed - cannot test post-booking scenario")
            return False
    
    def interactive_test(self):
        """Interactive test where you can type your actual questions"""
        print(f"\n💬 INTERACTIVE TEST MODE")
        print("=" * 30)
        print("Type the exact questions you're asking in WhatsApp")
        print("Type 'quit' to exit, 'reset' to start over")
        
        # Set up session like after your PDF upload
        session = self.session_manager.get_session(self.phone_number)
        
        # Your ticket data
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
        session.set_state(ConversationState.COMPLETED)  # After booking
        
        ticket_storage.store_ticket_data(self.phone_number, mock_ticket_info, mock_price_comparison)
        
        print("✅ Session set up (ticket uploaded, booking completed)")
        
        while True:
            try:
                user_input = input("\n💬 Your question: ").strip()
                
                if user_input.lower() == 'quit':
                    break
                elif user_input.lower() == 'reset':
                    session.set_state(ConversationState.COMPLETED)
                    session.set_context('parsed_ticket', mock_ticket_info)
                    session.set_context('price_comparison', mock_price_comparison)
                    print("🔄 Session reset")
                    continue
                
                if not user_input:
                    continue
                
                # Test the question
                action = self.dialogue_manager._detect_ticket_action(user_input)
                print(f"🔍 Detected action: '{action}'")
                
                response = self.dialogue_manager.process_message(session, user_input)
                
                # Analyze response
                is_booking = "which city" in response.lower() and "fly from" in response.lower()
                has_prices = "₹" in response
                
                print(f"\n📱 Response:")
                print(response)
                
                print(f"\n📊 Analysis:")
                print(f"   Is booking request: {'❌ YES' if is_booking else '✅ NO'}")
                print(f"   Has price info: {'✅ YES' if has_prices else '❌ NO'}")
                
                if is_booking:
                    print("   ⚠️ This is the issue you're experiencing!")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error: {e}")

def main():
    tester = RealTimeSessionTester()
    
    print("🔍 REAL-TIME SESSION TESTER")
    print("=" * 35)
    print("This will test your exact scenario and show what's happening")
    
    try:
        # Test the scenario
        success = tester.simulate_your_scenario()
        
        print(f"\n📋 SCENARIO TEST RESULT")
        print("=" * 25)
        
        if success:
            print("✅ Your scenario works correctly!")
            print("   The issue might be:")
            print("   - Different wording in your real questions")
            print("   - Different session state")
            print("   - Timing issues")
        else:
            print("❌ Issue reproduced!")
            print("   This confirms the problem you're experiencing")
        
        # Offer interactive testing
        print(f"\n💡 Want to test with your exact questions?")
        choice = input("Type 'yes' for interactive mode: ").strip().lower()
        
        if choice in ['yes', 'y']:
            tester.interactive_test()
    
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 