#!/usr/bin/env python3
"""
WhatsApp Business API Diagnostic Script
Helps identify and troubleshoot API permission issues
"""

import os
import sys
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_whatsapp_api():
    """Test WhatsApp Business API configuration"""
    print("🔍 WhatsApp Business API Diagnostic Tool")
    print("=" * 50)
    
    # Get configuration
    token = os.getenv('WHATSAPP_TOKEN', '')
    phone_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID', '')
    verify_token = os.getenv('WHATSAPP_VERIFY_TOKEN', '')
    
    print(f"📋 Configuration Check:")
    print(f"   Token Present: {'✅ Yes' if token else '❌ No'}")
    print(f"   Token Length: {len(token)} chars")
    print(f"   Phone ID: {phone_id}")
    print(f"   Verify Token: {verify_token}")
    print("-" * 50)
    
    if not token or not phone_id:
        print("❌ Missing required configuration!")
        print("\n📝 Required Environment Variables:")
        print("   WHATSAPP_TOKEN=your_access_token")
        print("   WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id")
        return False
    
    # Test 1: Check Phone Number Details
    print("🧪 Test 1: Phone Number Information")
    phone_url = f"https://graph.facebook.com/v18.0/{phone_id}"
    headers = {'Authorization': f'Bearer {token}'}
    
    try:
        response = requests.get(phone_url, headers=headers)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Phone number accessible")
            print(f"   Display Name: {data.get('display_phone_number', 'N/A')}")
            print(f"   Verified: {data.get('verified_name', 'N/A')}")
        else:
            print(f"   ❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False
    
    print("-" * 50)
    
    # Test 2: Check App Permissions
    print("🧪 Test 2: App Permissions Check")
    me_url = "https://graph.facebook.com/v18.0/me"
    
    try:
        response = requests.get(me_url, headers=headers)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("   ✅ App accessible")
            print(f"   App ID: {data.get('id', 'N/A')}")
            print(f"   App Name: {data.get('name', 'N/A')}")
        else:
            print(f"   ❌ Error: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    print("-" * 50)
    
    # Test 3: Check Messaging Permissions
    print("🧪 Test 3: Messaging Permissions")
    
    # Try to get phone number info with messaging scope
    messaging_url = f"https://graph.facebook.com/v18.0/{phone_id}/phone_numbers"
    
    try:
        response = requests.get(messaging_url, headers=headers)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Messaging permissions active")
        elif response.status_code == 403:
            print("   ❌ Missing messaging permissions")
            print("   💡 Solution: Add whatsapp_business_messaging permission")
        else:
            print(f"   ⚠️ Response: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    print("-" * 50)
    
    # Test 4: Token Validation
    print("🧪 Test 4: Token Validation")
    
    # Check token info
    token_url = f"https://graph.facebook.com/v18.0/me?access_token={token}"
    
    try:
        response = requests.get(token_url)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Token is valid")
        elif response.status_code == 401:
            print("   ❌ Token is invalid or expired")
            print("   💡 Solution: Generate new access token")
        else:
            print(f"   ⚠️ Response: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    print("-" * 50)
    
    return True

def show_troubleshooting_guide():
    """Show comprehensive troubleshooting guide"""
    print("\n🛠️ TROUBLESHOOTING GUIDE")
    print("=" * 50)
    
    print("\n📋 Common Issues & Solutions:")
    
    print("\n1. ❌ Token Expired")
    print("   Solution: Generate new access token")
    print("   Steps:")
    print("   • Go to Facebook Developers Console")
    print("   • Navigate to your app > WhatsApp > Getting Started")
    print("   • Generate new temporary token (24hrs) or permanent token")
    print("   • Update WHATSAPP_TOKEN in .env file")
    
    print("\n2. ❌ Missing Permissions")
    print("   Required permissions:")
    print("   • whatsapp_business_messaging")
    print("   • whatsapp_business_management")
    print("   Solution: Add permissions in App Review")
    
    print("\n3. ❌ Phone Number Not Verified")
    print("   Solution:")
    print("   • Verify phone number in Meta Business account")
    print("   • Complete WhatsApp Business API setup")
    print("   • Ensure phone number is added to app")
    
    print("\n4. ❌ Webhook Configuration")
    print("   Check:")
    print("   • Webhook URL is accessible")
    print("   • Verify token matches WHATSAPP_VERIFY_TOKEN")
    print("   • SSL certificate is valid")
    
    print("\n5. ❌ Rate Limits")
    print("   • Check if you've exceeded message limits")
    print("   • Wait and retry")
    print("   • Consider upgrading plan")
    
    print("\n📱 Development vs Production:")
    print("   Development: Limited to 5 phone numbers")
    print("   Production: Requires app review and approval")
    
    print("\n🔗 Useful Links:")
    print("   • Meta for Developers: https://developers.facebook.com/")
    print("   • WhatsApp Business API Docs: https://developers.facebook.com/docs/whatsapp/")
    print("   • Cloud API Setup: https://developers.facebook.com/docs/whatsapp/cloud-api/")

def quick_fix_guide():
    """Show quick fix steps"""
    print("\n⚡ QUICK FIX STEPS")
    print("=" * 30)
    
    print("\n1. 🔄 Regenerate Access Token:")
    print("   • Go to: https://developers.facebook.com/apps/")
    print("   • Select your app > WhatsApp > API Setup")
    print("   • Generate new token")
    print("   • Copy token to .env file")
    
    print("\n2. 🔧 Update Environment:")
    print("   • Edit .env file")
    print("   • Replace WHATSAPP_TOKEN with new token")
    print("   • Restart Flask application")
    
    print("\n3. ✅ Test Configuration:")
    print("   • Run this script again")
    print("   • Test with simple message")
    
    print(f"\n4. 📋 Current Token Info:")
    token = os.getenv('WHATSAPP_TOKEN', '')
    if token:
        print(f"   Token starts with: {token[:20]}...")
        print(f"   Token length: {len(token)} characters")
        print(f"   Likely expires: Within 24 hours (if temporary)")
    else:
        print("   ❌ No token found in environment")

if __name__ == "__main__":
    try:
        success = test_whatsapp_api()
        show_troubleshooting_guide()
        quick_fix_guide()
        
        if success:
            print("\n✅ Diagnostic completed successfully!")
        else:
            print("\n❌ Configuration issues detected!")
            
    except Exception as e:
        print(f"\n❌ Diagnostic failed: {e}")
        import traceback
        traceback.print_exc() 