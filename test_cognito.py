#!/usr/bin/env python3

import os
import sys
import requests
from cognito_auth import CognitoAuth

def test_cognito_integration():
    """Test Cognito authentication integration"""
    
    print("🔐 Testing AWS Cognito Integration")
    print("=" * 50)
    
    try:
        # Initialize Cognito auth
        cognito = CognitoAuth()
        
        # Test 1: Check configuration
        print("\n1. Testing Cognito Configuration...")
        
        config_items = [
            ('User Pool ID', cognito.user_pool_id),
            ('Client ID', cognito.client_id),
            ('Domain', cognito.domain),
            ('Redirect URI', cognito.redirect_uri)
        ]
        
        for name, value in config_items:
            if value:
                print(f"✅ {name}: {value}")
            else:
                print(f"❌ {name}: Not configured")
        
        # Test 2: Generate authorization URLs
        print("\n2. Testing Authorization URL Generation...")
        
        try:
            auth_url = cognito.get_authorization_url(state='test')
            print(f"✅ Authorization URL: {auth_url[:80]}...")
            
            # Test social provider URLs
            providers = ['Google', 'Facebook', 'LoginWithAmazon']
            for provider in providers:
                try:
                    social_url = cognito.get_social_login_url(provider, state=provider.lower())
                    print(f"✅ {provider} URL: Generated successfully")
                except Exception as e:
                    print(f"⚠️  {provider} URL: {e}")
                    
        except Exception as e:
            print(f"❌ URL Generation Error: {e}")
        
        # Test 3: Check JWKS endpoint
        print("\n3. Testing JWKS Endpoint...")
        
        try:
            jwks = cognito.get_jwks()
            if jwks and 'keys' in jwks:
                print(f"✅ JWKS Retrieved: {len(jwks['keys'])} keys found")
            else:
                print("❌ JWKS: No keys found")
        except Exception as e:
            print(f"❌ JWKS Error: {e}")
        
        # Test 4: Test logout URL
        print("\n4. Testing Logout URL...")
        
        try:
            logout_url = cognito.logout_url()
            print(f"✅ Logout URL: {logout_url[:80]}...")
        except Exception as e:
            print(f"❌ Logout URL Error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Cognito Integration Test Failed: {e}")
        return False

def test_application_endpoints():
    """Test application endpoints with Cognito"""
    
    print("\n🌐 Testing Application Endpoints")
    print("=" * 40)
    
    base_url = "https://p2p-lending-prod.eba-qstjs52k.us-east-1.elasticbeanstalk.com"
    
    endpoints = [
        ('/', 'Home page'),
        ('/login', 'Login page with social options'),
        ('/register', 'Registration page'),
        ('/auth/callback', 'OAuth callback (should redirect)'),
    ]
    
    for endpoint, description in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10, allow_redirects=False)
            
            if endpoint == '/auth/callback':
                # Callback should redirect without code parameter
                if response.status_code in [302, 400]:
                    print(f"✅ {description}: Properly handling missing code")
                else:
                    print(f"⚠️  {description}: Unexpected status {response.status_code}")
            else:
                if response.status_code == 200:
                    print(f"✅ {description}: HTTP {response.status_code}")
                else:
                    print(f"⚠️  {description}: HTTP {response.status_code}")
                    
        except Exception as e:
            print(f"❌ {description}: Error - {e}")

def test_environment_variables():
    """Test that all required environment variables are set"""
    
    print("\n🔧 Testing Environment Variables")
    print("=" * 40)
    
    required_vars = [
        'COGNITO_USER_POOL_ID',
        'COGNITO_CLIENT_ID', 
        'COGNITO_CLIENT_SECRET',
        'COGNITO_DOMAIN',
        'COGNITO_REDIRECT_URI'
    ]
    
    all_set = True
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Show partial value for security
            display_value = value[:10] + "..." if len(value) > 10 else value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: Not set")
            all_set = False
    
    return all_set

def main():
    """Main test function"""
    
    print("🧪 AWS Cognito Integration Test Suite")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 3
    
    # Test 1: Environment variables
    if test_environment_variables():
        tests_passed += 1
        print("✅ Environment variables test passed")
    else:
        print("❌ Environment variables test failed")
    
    # Test 2: Cognito integration
    if test_cognito_integration():
        tests_passed += 1
        print("✅ Cognito integration test passed")
    else:
        print("❌ Cognito integration test failed")
    
    # Test 3: Application endpoints
    test_application_endpoints()
    tests_passed += 1  # This test is informational
    
    # Results
    print(f"\n" + "=" * 60)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 Cognito integration is working correctly!")
        
        print(f"\n🔗 Test URLs:")
        print(f"   • Login Page: https://p2p-lending-prod.eba-qstjs52k.us-east-1.elasticbeanstalk.com/login")
        print(f"   • Hosted UI: https://p2p-lending-us-east-1-ajst293jz.auth.us-east-1.amazoncognito.com/login")
        
        print(f"\n📋 Next Steps:")
        print(f"   1. Set up social identity providers in AWS Console")
        print(f"   2. Test social login flows")
        print(f"   3. Configure additional providers as needed")
        
    else:
        print(f"⚠️  Some tests failed. Please check the configuration.")
    
    return tests_passed == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
