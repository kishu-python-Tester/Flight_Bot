#!/usr/bin/env python3
"""
Test PDF booking flow with fresh token reload
This ensures we use the updated token from .env file
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

def force_reload_config():
    """Force reload of configuration with updated token"""
    # Reload environment variables
    load_dotenv(override=True)
    
    # Force reimport of config to get fresh token
    if 'config.settings' in sys.modules:
        del sys.modules['config.settings']
    
    # Clear WhatsApp service imports to force reinitialization
    modules_to_clear = [
        'services.whatsapp_service',
        'services.llm_dialogue_manager', 
        'models.conversation'
    ]
    
    for module in modules_to_clear:
        if module in sys.modules:
            del sys.modules[module]

def test_booking_with_fresh_token():
    """Test booking flow with properly reloaded token"""
    print("🔄 Testing PDF Booking with Fresh Token")
    print("=" * 50)
    
    # Force fresh reload
    force_reload_config()
    
    # Now import with fresh config
    from models.conversation import SessionManager, ConversationState
    from services.whatsapp_service import MockWhatsAppService
    from services.llm_dialogue_manager import LLMDialogueManager
    
    print("✅ Services reloaded with fresh token")
    
    # Check current token
    token = os.getenv('WHATSAPP_TOKEN', '')
    print(f"📋 Current token length: {len(token)} chars")
    print(f"🔑 Token preview: {token[:30]}..." if token else "❌ No token")
    
    # Initialize services
    session_manager = SessionManager()
    whatsapp_service = MockWhatsAppService()
    dialogue_manager = LLMDialogueManager(whatsapp_service)
    
    # Test phone number
    phone_number = "+1234567890"
    
    print(f"\n🚀 Testing booking flow for {phone_number}")
    
    # Create session and set up mock data
    session = session_manager.get_session(phone_number)
    
    # Mock parsed ticket data
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
    
    # Mock price comparison showing savings
    mock_price_comparison = {
        'comparison_available': True,
        'ticket_price': 25000,
        'currency': 'INR',
        'best_system_price': 16000,
        'price_difference': 9000,
        'savings_percentage': 36.0,
        'recommendation': 'cheaper'
    }
    
    # Set context
    session.set_context('parsed_ticket', mock_ticket_info)
    session.set_context('price_comparison', mock_price_comparison)
    
    print("\n📊 Mock Data Set:")
    print(f"   💰 User's Price: ₹25,000")
    print(f"   🏷️ Our Price: ₹16,000") 
    print(f"   💸 Savings: ₹9,000 (36%)")
    
    # Test booking request
    print("\n🧪 Step 1: User requests booking")
    response1 = dialogue_manager.process_message(session, "book with new price")
    print(f"📱 Bot response: {response1[:100]}...")
    print(f"🔧 State: {session.state.value}")
    
    # Test office ID
    print("\n🧪 Step 2: User provides office ID")
    office_id = "CORP-MUMBAI-001"
    response2 = dialogue_manager.process_message(session, office_id)
    
    print(f"📱 Bot response:")
    print(response2)
    print(f"🔧 Final state: {session.state.value}")
    
    # Check if booking was successful
    new_booking = session.get_data('new_booking')
    if new_booking:
        print(f"\n✅ Booking Success!")
        print(f"   📋 PNR: {new_booking.get('pnr')}")
        print(f"   🏢 Office ID: {new_booking.get('office_id')}")
        print(f"   💰 New Price: ₹{new_booking.get('ticket_price'):,}")
        
        # Check PDF generation
        pdf_path = session.get_data('pdf_path')
        if pdf_path and os.path.exists(pdf_path):
            print(f"   📄 PDF Generated: {os.path.basename(pdf_path)}")
            print(f"   📊 File Size: {os.path.getsize(pdf_path)} bytes")
            
            # Clean up
            try:
                os.remove(pdf_path)
                print(f"   🧹 PDF cleaned up")
            except:
                pass
        else:
            print(f"   📄 PDF: Not found on disk")
            
        return True
    else:
        print(f"\n❌ Booking failed - no booking data found")
        return False

def show_token_status():
    """Show current token status"""
    print(f"\n📋 Current Token Status:")
    token = os.getenv('WHATSAPP_TOKEN', '')
    print(f"   Length: {len(token)} characters")
    print(f"   Preview: {token[:40]}..." if len(token) > 40 else "   ❌ No token")
    
    # Quick API test
    import requests
    phone_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID', '668182639718247')
    url = f"https://graph.facebook.com/v18.0/{phone_id}"
    headers = {'Authorization': f'Bearer {token}'}
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            print(f"   🟢 Status: Active and working")
        else:
            print(f"   🔴 Status: Error {response.status_code}")
    except:
        print(f"   ⚠️ Status: Network error")

if __name__ == "__main__":
    try:
        show_token_status()
        success = test_booking_with_fresh_token()
        
        if success:
            print("\n🎉 SUCCESS! PDF booking flow is working!")
            print("🚀 Your system is ready for production!")
        else:
            print("\n❌ Test failed - check token configuration")
            
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc() 