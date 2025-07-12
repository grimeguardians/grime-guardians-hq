#!/usr/bin/env python3
"""
GoHighLevel OAuth Token Refresh
Refresh the expired OAuth token using the refresh token
"""

import asyncio
import aiohttp
import json
from datetime import datetime

# OAuth configuration from .env
CLIENT_ID = "685b47db98d007215e2760c0-mcblfc4t"
CLIENT_SECRET = "4605b435-fbd7-428c-a9bc-fea05f9ba975"
REFRESH_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdXRoQ2xhc3MiOiJMb2NhdGlvbiIsImF1dGhDbGFzc0lkIjoiZzNnSk5kRVNOdzlTclY3TnBqSmwiLCJzb3VyY2UiOiJJTlRFR1JBVElPTiIsInNvdXJjZUlkIjoiNjg1YjQ3ZGI5OGQwMDcyMTVlMjc2MGMwLW1jYmxmYzR0IiwiY2hhbm5lbCI6Ik9BVVRIIiwicHJpbWFyeUF1dGhDbGFzc0lkIjoiZzNnSk5kRVNOdzlTclY3TnBqSmwiLCJvYXV0aE1ldGEiOnsic2NvcGVzIjpbImNvbnZlcnNhdGlvbnMvbWVzc2FnZS5yZWFkb25seSIsImNvbnZlcnNhdGlvbnMvbWVzc2FnZS53cml0ZSIsImNvbnRhY3RzLnJlYWRvbmx5IiwiY29udGFjdHMud3JpdGUiLCJjb252ZXJzYXRpb25zLnJlYWRvbmx5IiwiY29udmVyc2F0aW9ucy53cml0ZSIsImxvY2F0aW9ucy5yZWFkb25seSJdLCJjbGllbnQiOiI2ODViNDdkYjk4ZDAwNzIxNWUyNzYwYzAiLCJ2ZXJzaW9uSWQiOiI2ODViNDdkYjk4ZDAwNzIxNWUyNzYwYzAiLCJjbGllbnRLZXkiOiI2ODViNDdkYjk4ZDAwNzIxNWUyNzYwYzAtbWNibGZjNHQifSwiaWF0IjoxNzUwOTE5MjEzLjkzNywiZXhwIjoxNzgyNDU1MjEzLjkzNywidW5pcXVlSWQiOiJkMTRjZDZlYy05NjBjLTRjZDUtODEyNi0wOWIzZmE4NzFlMTYiLCJ2IjoiMiJ9.QKLdRNnC9sPHZmD6qTFPeqv3MxfEmIWNRjhNVLP0q2t6RqhlWP5iQ1JGKnPzOJjaEvOLSFuOW1ZUGa87n-45no8Kzd1SioFhsFUPBv0b94dcMsD-RLEiXaGn92LaTEHjLPSH6AsTCOWC3iJpyc9g52iQjU10vdJnPznXbBGVmrkubw_CLv8eO76VL5aD0QqXvbxSkbEcUelfAKqx1iXaZFlqhgsS24ZZamc2o6iajswg7wEJ0YWrDEF8kafjdmM7y5u32nd2QpfcQS1B0lRACVji9SoJX_hzIDqTB60G3XiTMIORr3udNXW7PARNvJSISBS_bM6cIGk1yfoQG0HgZeg4_x2Yx2denmLswt_WFPwyE23RQ1bENgYXILiFz7xG3cDefQQDKR875Vh9mwwObBe49RVxb9ziFrsA2BAXLEA6mwkM9Gqf_wtiwtKSU3TvlqEdtUWJt66CRlQwXqWwmz0jqtdJ8z0AAW2KJvBhym_ijva0CTH02HQ8kfPi-IL1SAI7pHQzO_iCDVzMQ2lO8z7EaLoKh3xYDyU19lb2Wa2WtmI9lGshGKJcpbmqQl3Uj8OMxR9pm3nvLZWgtMaO3PthED_olg68sixugYMzNnHxAqThDy2OOuC7agaR4ETxoebABl_xlF3AttM9KguTd42UzOV4UyYSjEbTTFsouM"

async def refresh_oauth_token():
    """Refresh the GoHighLevel OAuth token."""
    print("🔄 Refreshing GoHighLevel OAuth Token")
    print("=" * 50)
    
    token_url = "https://services.leadconnectorhq.com/oauth/token"
    
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
        "user_type": "Location"
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    try:
        print(f"🔗 Requesting token refresh from: {token_url}")
        print(f"📋 Grant type: refresh_token")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(token_url, data=data, headers=headers) as response:
                status = response.status
                response_data = await response.json()
                
                if status == 200:
                    print(f"✅ Token refresh successful!")
                    
                    # Extract new tokens
                    new_access_token = response_data.get("access_token")
                    new_refresh_token = response_data.get("refresh_token")
                    expires_in = response_data.get("expires_in", 86400)  # Default 24 hours
                    
                    # Calculate expiry timestamp
                    new_expiry = int(datetime.now().timestamp() + expires_in) * 1000
                    
                    print(f"🎯 New Access Token: {new_access_token[:50]}...")
                    print(f"🔄 New Refresh Token: {new_refresh_token[:50]}...")
                    print(f"⏰ Expires in: {expires_in} seconds ({expires_in/3600:.1f} hours)")
                    print(f"📅 Expiry timestamp: {new_expiry}")
                    
                    # Generate .env update instructions
                    print("\n" + "=" * 50)
                    print("📝 UPDATE YOUR .ENV FILE:")
                    print("=" * 50)
                    print(f"HIGHLEVEL_OAUTH_ACCESS_TOKEN={new_access_token}")
                    print(f"HIGHLEVEL_OAUTH_REFRESH_TOKEN={new_refresh_token}")
                    print(f"HIGHLEVEL_TOKEN_EXPIRY={new_expiry}")
                    
                    # Test the new token
                    print("\n🧪 Testing new token...")
                    await test_new_token(new_access_token)
                    
                    return {
                        "success": True,
                        "access_token": new_access_token,
                        "refresh_token": new_refresh_token,
                        "expiry": new_expiry
                    }
                    
                else:
                    print(f"❌ Token refresh failed: {status}")
                    print(f"💬 Error: {response_data}")
                    return {"success": False, "error": response_data}
                    
    except Exception as e:
        print(f"💥 Exception during token refresh: {e}")
        return {"success": False, "error": str(e)}

async def test_new_token(access_token):
    """Test the new access token."""
    location_id = "g3gJNdESNw9SrV7NpjJl"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Version": "2021-07-28"
    }
    
    # Test a simple endpoint
    test_url = f"https://services.leadconnectorhq.com/contacts/?locationId={location_id}&limit=1"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(test_url, headers=headers) as response:
                status = response.status
                
                if status == 200:
                    data = await response.json()
                    print(f"✅ New token test successful!")
                    print(f"   Retrieved {len(data.get('contacts', []))} contacts")
                    return True
                else:
                    error = await response.text()
                    print(f"❌ New token test failed: {status}")
                    print(f"   Error: {error[:100]}...")
                    return False
                    
    except Exception as e:
        print(f"💥 Token test exception: {e}")
        return False

async def main():
    """Main token refresh process."""
    print("🔧 GoHighLevel OAuth Token Refresh Utility")
    print("=" * 60)
    
    # Check current token status
    current_expiry = 1751005613973 / 1000
    current_time = datetime.now().timestamp()
    
    if current_time > current_expiry:
        hours_expired = (current_time - current_expiry) / 3600
        print(f"⚠️  Current token expired {hours_expired:.1f} hours ago")
    else:
        hours_left = (current_expiry - current_time) / 3600
        print(f"ℹ️  Current token expires in {hours_left:.1f} hours")
    
    print("\n🔄 Attempting token refresh...")
    
    result = await refresh_oauth_token()
    
    if result["success"]:
        print("\n🎉 TOKEN REFRESH SUCCESSFUL!")
        print("\n📋 Next Steps:")
        print("1. Update your .env file with the new tokens above")
        print("2. Restart any running services")
        print("3. Test Discord commands: 'Ask Ava about schedule' or 'Ask Dean about analytics'")
        print("\n🚀 Your CRM integration will now work with Ava, Dean, and Emma!")
        return 0
    else:
        print("\n❌ TOKEN REFRESH FAILED")
        print("\n🔧 Troubleshooting:")
        print("1. Check if refresh token is still valid")
        print("2. Verify OAuth app settings in GoHighLevel")
        print("3. Regenerate OAuth credentials if needed")
        return 1

if __name__ == '__main__':
    exit_code = asyncio.run(main())
    exit(exit_code)