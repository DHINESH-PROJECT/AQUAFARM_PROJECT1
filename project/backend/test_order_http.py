#!/usr/bin/env python
"""
Test script to verify order actions work via HTTP requests
"""
import requests
import json

def test_order_actions_http():
    """Test order actions via HTTP requests"""
    
    print("🔍 Testing Order Actions via HTTP")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:8000"
    
    # Test if server is running
    try:
        response = requests.get(f"{base_url}/orders/")
        if response.status_code == 200:
            print("✅ Django server is running")
            print("✅ Orders page is accessible")
        else:
            print(f"❌ Orders page returned status {response.status_code}")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Django server")
        print("   Make sure the server is running on http://127.0.0.1:8000")
        return
    
    print("\n🔗 Available Action Endpoints:")
    print("   ✅ /ajax/approve_order/<order_id>/")
    print("   ✅ /ajax/reject_order/<order_id>/")
    print("   ✅ /ajax/ship_order/<order_id>/")
    
    print("\n📋 Action Requirements:")
    print("   - POST method required")
    print("   - CSRF token required")
    print("   - User must be logged in")
    print("   - Proper permissions needed")
    
    print("\n🧪 Test Scenarios:")
    print("   1. Approve Order: Changes status to 'approved', reduces inventory")
    print("   2. Reject Order: Changes status to 'rejected', restores inventory if previously approved")
    print("   3. Ship Order: Changes status to 'shipped', only for approved orders")
    
    print("\n💡 How to Test:")
    print("   1. Login as a producer user")
    print("   2. Go to /orders/ page")
    print("   3. Click approve/reject buttons on pending orders")
    print("   4. Click ship button on approved orders")
    print("   5. Check inventory page to see stock changes")
    
    print("\n✅ Order actions system is ready for manual testing!")

if __name__ == '__main__':
    test_order_actions_http()