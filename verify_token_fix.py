#!/usr/bin/env python3
"""
Immediate WhatsApp Token Verification
Run this after updating your WHATSAPP_TOKEN in .env
"""

import os
import sys
import requests
from dotenv import load_dotenv

def verify_token_fix():
    """Quickly verify if new token is working"""
    print("⚡ Quick WhatsApp Token Verification")
    print("=" * 40)
    
    # Reload environment variables
    load_dotenv(override=True)
    
    token = os.getenv('WHATSAPP_TOKEN', '')
    phone_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID', '668182639718247')
    
    print(f"📋 Token length: {len(token)} characters")
    print(f"📱 Phone ID: {phone_id}")
    print(f"🔑 Token preview: {token[:30]}..." if len(token) > 30 else "❌ No token found")
    print("-" * 40)
    
    if not token:
        print("❌ No token found! Please update .env file.")
        return False
    
    # Quick token test
    print("🧪 Testing token validity...")
    
    headers = {'Authorization': f'Bearer {token}'}
    test_url = f"https://graph.facebook.com/v18.0/{phone_id}"
    
    try:
        response = requests.get(test_url, headers=headers, timeout=10)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS! Token is working!")
            print(f"📞 Phone: {data.get('display_phone_number', 'N/A')}")
            print(f"✅ Verified: {data.get('verified_name', 'N/A')}")
            print("\n🎉 Your WhatsApp API is now functional!")
            print("🚀 You can now test your PDF booking flow!")
            return True
            
        elif response.status_code == 401:
            print("❌ STILL EXPIRED: Token is still invalid")
            print("💡 Solution: Generate a newer token from Facebook Developers")
            error_data = response.json().get('error', {})
            print(f"📝 Error: {error_data.get('message', 'Unknown error')}")
            
        elif response.status_code == 403:
            print("❌ PERMISSION DENIED: Token lacks required permissions")
            print("💡 Solution: Add whatsapp_business_messaging permission")
            
        else:
            print(f"⚠️ UNEXPECTED RESPONSE: {response.status_code}")
            print(f"📝 Response: {response.text}")
            
        return False
        
    except requests.exceptions.Timeout:
        print("⏱️ REQUEST TIMEOUT: Check internet connection")
        return False
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def show_next_steps():
    """Show what to do after successful verification"""
    print("\n🎯 NEXT STEPS:")
    print("1. ✅ Restart your Flask application")
    print("2. ✅ Test PDF booking flow with test script")
    print("3. ✅ Send test WhatsApp message")
    print("\n📝 Commands to run:")
    print("   python3 app.py                    # Start your app")
    print("   python3 test_booking_flow.py      # Test PDF booking")
    print("\n🔄 If you want to avoid daily token renewal:")
    print("   Generate a permanent system user token (see guide)")

def quick_curl_test():
    """Show curl command for manual testing"""
    token = os.getenv('WHATSAPP_TOKEN', '')
    phone_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID', '668182639718247')
    
    if token:
        print(f"\n🔧 Manual Test Command:")
        print(f"curl -X GET 'https://graph.facebook.com/v18.0/{phone_id}' \\")
        print(f"  -H 'Authorization: Bearer {token[:50]}...'")

if __name__ == "__main__":
    try:
        success = verify_token_fix()
        
        if success:
            show_next_steps()
        else:
            print("\n❌ Token verification failed!")
            print("📖 Check: whatsapp_token_renewal_guide.md")
            quick_curl_test()
            
    except Exception as e:
        print(f"❌ Verification script failed: {e}")
        import traceback
        traceback.print_exc() 