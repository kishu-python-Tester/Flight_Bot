#!/usr/bin/env python3
"""
WhatsApp Media Upload Fix
Diagnoses and fixes media upload token issues specifically
"""

import os
import sys
import requests
import tempfile
from dotenv import load_dotenv

def test_media_upload_permissions():
    """Test media upload specifically"""
    print("🎯 WhatsApp Media Upload Diagnostic")
    print("=" * 40)
    
    load_dotenv(override=True)
    
    token = os.getenv('WHATSAPP_TOKEN', '')
    phone_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID', '668182639718247')
    
    print(f"📱 Phone ID: {phone_id}")
    print(f"🔑 Token length: {len(token)} chars")
    
    # Test 1: Basic phone number access (should work)
    print("\n🧪 Test 1: Basic Phone Access")
    basic_url = f"https://graph.facebook.com/v18.0/{phone_id}"
    headers = {'Authorization': f'Bearer {token}'}
    
    try:
        response = requests.get(basic_url, headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Basic access works")
        else:
            print(f"   ❌ Basic access failed: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False
    
    # Test 2: Media endpoint access
    print("\n🧪 Test 2: Media Endpoint Access")
    media_url = f"https://graph.facebook.com/v18.0/{phone_id}/media"
    
    try:
        # Just test GET to see if endpoint is accessible
        response = requests.get(media_url, headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Media endpoint accessible")
        elif response.status_code == 405:
            print("   ✅ Media endpoint exists (Method Not Allowed is expected for GET)")
        elif response.status_code == 401:
            print("   ❌ Media endpoint: Token expired/invalid")
            print("   💡 Need to regenerate token")
            return False
        elif response.status_code == 403:
            print("   ❌ Media endpoint: Permission denied")
            print("   💡 Need whatsapp_business_messaging permission")
            return False
        else:
            print(f"   ⚠️ Unexpected: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False
    
    # Test 3: Create test file for upload
    print("\n🧪 Test 3: Test Media Upload")
    
    try:
        # Create a small test text file (not PDF to avoid complexity)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write("WhatsApp Media Upload Test")
            temp_file_path = temp_file.name
        
        # Try to upload
        upload_headers = {'Authorization': f'Bearer {token}'}
        
        with open(temp_file_path, 'rb') as file:
            files = {
                'file': ('test.txt', file, 'text/plain')
            }
            data = {
                'messaging_product': 'whatsapp'
            }
            
            upload_response = requests.post(media_url, headers=upload_headers, files=files, data=data)
            print(f"   Upload Status: {upload_response.status_code}")
            
            if upload_response.status_code == 200:
                print("   ✅ Media upload successful!")
                result = upload_response.json()
                media_id = result.get('id')
                print(f"   📄 Media ID: {media_id}")
                return True
            elif upload_response.status_code == 401:
                print("   ❌ Upload failed: Token expired")
                error_data = upload_response.json().get('error', {})
                print(f"   📝 Error: {error_data.get('message', 'Unknown')}")
                return False
            elif upload_response.status_code == 403:
                print("   ❌ Upload failed: Permission denied")
                print("   💡 Solution: Add whatsapp_business_messaging permission")
                return False
            else:
                print(f"   ❌ Upload failed: {upload_response.text}")
                return False
                
        # Clean up test file
        os.unlink(temp_file_path)
        
    except Exception as e:
        print(f"   ❌ Upload test exception: {e}")
        return False

def show_media_upload_solutions():
    """Show solutions for media upload issues"""
    print("\n🛠️ MEDIA UPLOAD SOLUTIONS")
    print("=" * 30)
    
    print("\n1. 🔄 Token Regeneration (Most Common)")
    print("   • Generate new token from Facebook Developers")
    print("   • Ensure token has media upload permissions")
    print("   • Use permanent system user token")
    
    print("\n2. ✅ Required Permissions")
    print("   • whatsapp_business_messaging")
    print("   • whatsapp_business_management")
    print("   • pages_messaging (if using Page)")
    
    print("\n3. 🔧 Alternative: Mock PDF Sending")
    print("   • For testing: Skip actual PDF sending")
    print("   • Just generate PDF and show success message")
    print("   • Good for development phase")
    
    print("\n4. 📋 Manual Token Test")
    token = os.getenv('WHATSAPP_TOKEN', '')
    phone_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID', '668182639718247')
    
    print(f"   curl -X POST 'https://graph.facebook.com/v18.0/{phone_id}/media' \\")
    print(f"     -H 'Authorization: Bearer {token[:50]}...' \\")
    print(f"     -F 'messaging_product=whatsapp' \\")
    print(f"     -F 'file=@test.txt'")

def create_mock_pdf_mode():
    """Create a development mode that skips PDF sending"""
    print("\n💡 TEMPORARY WORKAROUND")
    print("=" * 25)
    
    print("For immediate testing, you can:")
    print("1. ✅ Generate PDFs locally (working)")
    print("2. ✅ Show booking confirmation (working)")
    print("3. ⏭️ Skip WhatsApp PDF sending (temporarily)")
    print("4. 🔄 Fix token and enable PDF sending later")
    
    print("\n📝 Quick fix: Set environment variable")
    print("   SKIP_PDF_SENDING=true")
    print("   This will generate PDFs but not send via WhatsApp")

if __name__ == "__main__":
    try:
        success = test_media_upload_permissions()
        
        if success:
            print("\n✅ Media upload is working!")
            print("🎉 PDF booking flow should work completely!")
        else:
            print("\n❌ Media upload needs fixing")
            show_media_upload_solutions()
            create_mock_pdf_mode()
            
    except Exception as e:
        print(f"❌ Diagnostic failed: {e}")
        import traceback
        traceback.print_exc() 