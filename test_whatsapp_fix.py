#!/usr/bin/env python3
"""
Quick test to verify WhatsApp API fix
"""

import os
import sys
from dotenv import load_dotenv
from services.whatsapp_service import WhatsAppService

load_dotenv()

def test_whatsapp_fix():
    """Test if WhatsApp API is working after token update"""
    print("🧪 Testing WhatsApp API Fix")
    print("=" * 30)
    
    # Check token
    token = os.getenv('WHATSAPP_TOKEN', '')
    print(f"📋 Token Length: {len(token)} chars")
    print(f"📋 Token starts with: {token[:20]}..." if token else "❌ No token")
    
    # Initialize WhatsApp service
    try:
        whatsapp_service = WhatsAppService()
        print("✅ WhatsApp service initialized")
        
        # Test basic configuration
        print(f"📱 Phone ID: {os.getenv('WHATSAPP_PHONE_NUMBER_ID')}")
        
        # NOTE: We won't actually send a message in the test
        # Instead, we'll just verify the service can be created
        print("✅ Configuration appears valid")
        print("\n💡 To fully test:")
        print("   1. Update WHATSAPP_TOKEN in .env")
        print("   2. Restart your Flask app")
        print("   3. Send a test message via WhatsApp")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    test_whatsapp_fix() 