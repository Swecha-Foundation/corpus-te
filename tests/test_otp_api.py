#!/usr/bin/env python3
"""
Test script for OTP Authentication API
"""

import requests
import json
import sys
from time import sleep

# API base URL
BASE_URL = "http://localhost:8000/api/v1/auth"

def test_send_otp():
    """Test sending OTP"""
    print("🔄 Testing OTP Send...")
    
    data = {
        "phone_number": "<PHONE_NUMBER>"  # Replace with a valid phone number
    }
    
    try:
        response = requests.post(f"{BASE_URL}/send-otp", json=data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ OTP sent successfully!")
            print(f"   Status: {result.get('status')}")
            print(f"   Message: {result.get('message')}")
            print(f"   Reference ID: {result.get('reference_id')}")
            return True
        else:
            print(f"❌ Failed to send OTP: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending OTP: {str(e)}")
        return False

def test_verify_otp(otp_code):
    """Test verifying OTP"""
    print(f"\n🔄 Testing OTP Verification with code: {otp_code}")
    
    data = {
        "phone_number": "<PHONE_NUMBER>",  # Replace with the same phone number used in send OTP
        "otp_code": otp_code
    }
    
    try:
        response = requests.post(f"{BASE_URL}/verify-otp", json=data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ OTP verified successfully!")
            print(f"   Access Token: {result.get('access_token')[:50]}...")
            print(f"   Token Type: {result.get('token_type')}")
            print(f"   User ID: {result.get('user_id')}")
            print(f"   Phone Number: {result.get('phone_number')}")
            return result.get('access_token')
        else:
            print(f"❌ Failed to verify OTP: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error verifying OTP: {str(e)}")
        return None

def test_resend_otp():
    """Test resending OTP"""
    print("\n🔄 Testing OTP Resend...")
    data = {
        "phone_number": "<PHONE_NUMBER>"
    }

    try:
        response = requests.post(f"{BASE_URL}/resend-otp", json=data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ OTP resent successfully!")
            print(f"   Status: {result.get('status')}")
            print(f"   Message: {result.get('message')}")
            print(f"   Reference ID: {result.get('reference_id')}")
            return True
        else:
            print(f"❌ Failed to resend OTP: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error resending OTP: {str(e)}")
        return False

def test_authenticated_endpoint(access_token):
    """Test accessing an authenticated endpoint"""
    print(f"\n🔄 Testing authenticated endpoint...")
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/me", headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Successfully accessed authenticated endpoint!")
            print(f"   User ID: {result.get('id')}")
            print(f"   Phone: {result.get('phone')}")
            print(f"   Name: {result.get('name')}")
            print(f"   Is Active: {result.get('is_active')}")
            return True
        else:
            print(f"❌ Failed to access authenticated endpoint: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error accessing authenticated endpoint: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🚀 OTP Authentication API Test")
    print("=" * 50)
    
    # Test 1: Send OTP
    if not test_send_otp():
        print("\n❌ OTP send failed. Exiting.")
        sys.exit(1)
    
    # Ask user for OTP code
    print(f"\n📱 Please check your phone for the OTP code.")
    otp_code = input("Enter the OTP code you received: ").strip()
    
    if not otp_code:
        print("❌ No OTP code provided. Exiting.")
        sys.exit(1)
    
    # Test 2: Verify OTP
    access_token = test_verify_otp(otp_code)
    if not access_token:
        print("\n❌ OTP verification failed. Exiting.")
        sys.exit(1)
    
    # Test 3: Access authenticated endpoint
    if not test_authenticated_endpoint(access_token):
        print("\n❌ Authenticated endpoint test failed.")
    
    # Test 4: Resend OTP (should be rate limited)
    print("\n⏰ Waiting a moment before testing resend...")
    sleep(2)
    test_resend_otp()
    
    print("\n🎉 OTP Authentication API test completed!")
    print("=" * 50)

if __name__ == "__main__":
    main()
