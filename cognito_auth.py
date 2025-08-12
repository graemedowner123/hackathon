#!/usr/bin/env python3

import boto3
import json
import base64
import hashlib
import hmac
import requests
from jose import jwt, JWTError
from datetime import datetime, timedelta
import os
from urllib.parse import urlencode, parse_qs, urlparse

class CognitoAuth:
    """AWS Cognito authentication handler for social media logins"""
    
    def __init__(self, region='us-east-1'):
        self.region = region
        self.user_pool_id = os.getenv('COGNITO_USER_POOL_ID')
        self.client_id = os.getenv('COGNITO_CLIENT_ID')
        self.client_secret = os.getenv('COGNITO_CLIENT_SECRET')
        self.domain = os.getenv('COGNITO_DOMAIN')
        self.redirect_uri = os.getenv('COGNITO_REDIRECT_URI', 'http://localhost:5000/auth/callback')
        
        # Initialize Cognito client
        self.cognito_client = boto3.client('cognito-idp', region_name=region)
        
        # JWKS URL for token verification
        self.jwks_url = f'https://cognito-idp.{region}.amazonaws.com/{self.user_pool_id}/.well-known/jwks.json'
        self.jwks = None
        
    def get_jwks(self):
        """Fetch JSON Web Key Set for token verification"""
        if not self.jwks:
            response = requests.get(self.jwks_url)
            self.jwks = response.json()
        return self.jwks
    
    def get_authorization_url(self, state=None):
        """Generate authorization URL for social login"""
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'scope': 'openid email profile',
            'redirect_uri': self.redirect_uri,
        }
        
        if state:
            params['state'] = state
            
        auth_url = f'https://{self.domain}/oauth2/authorize?{urlencode(params)}'
        return auth_url
    
    def get_social_login_url(self, provider, state=None):
        """Generate social provider specific login URL"""
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'scope': 'openid email profile',
            'redirect_uri': self.redirect_uri,
            'identity_provider': provider,
        }
        
        if state:
            params['state'] = state
            
        auth_url = f'https://{self.domain}/oauth2/authorize?{urlencode(params)}'
        return auth_url
    
    def exchange_code_for_tokens(self, authorization_code):
        """Exchange authorization code for access and ID tokens"""
        token_url = f'https://{self.domain}/oauth2/token'
        
        # Prepare the request
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'code': authorization_code,
            'redirect_uri': self.redirect_uri,
        }
        
        # Add client secret if available
        if self.client_secret:
            # Create client secret hash
            message = authorization_code + self.client_id
            dig = hmac.new(
                self.client_secret.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            ).digest()
            secret_hash = base64.b64encode(dig).decode()
            data['client_secret'] = self.client_secret
            data['secret_hash'] = secret_hash
        
        # Make the request
        response = requests.post(token_url, headers=headers, data=data)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Token exchange failed: {response.text}")
    
    def verify_token(self, token):
        """Verify and decode JWT token"""
        try:
            # Get JWKS
            jwks = self.get_jwks()
            
            # Decode token header to get key ID
            unverified_header = jwt.get_unverified_header(token)
            key_id = unverified_header['kid']
            
            # Find the correct key
            key = None
            for jwk in jwks['keys']:
                if jwk['kid'] == key_id:
                    key = jwk
                    break
            
            if not key:
                raise Exception('Unable to find appropriate key')
            
            # Verify and decode token
            payload = jwt.decode(
                token,
                key,
                algorithms=['RS256'],
                audience=self.client_id,
                issuer=f'https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}'
            )
            
            return payload
            
        except JWTError as e:
            raise Exception(f'Token verification failed: {str(e)}')
    
    def get_user_info(self, access_token):
        """Get user information using access token"""
        user_info_url = f'https://{self.domain}/oauth2/userInfo'
        
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        response = requests.get(user_info_url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get user info: {response.text}")
    
    def create_user_from_social(self, user_info, provider):
        """Create user data structure from social login info"""
        # Extract common fields
        email = user_info.get('email', '')
        given_name = user_info.get('given_name', user_info.get('name', '').split(' ')[0])
        family_name = user_info.get('family_name', user_info.get('name', '').split(' ')[-1] if ' ' in user_info.get('name', '') else 'User')
        
        # Handle provider-specific data
        if provider == 'Google':
            picture = user_info.get('picture', '')
            verified = user_info.get('email_verified', False)
        elif provider == 'Facebook':
            picture = user_info.get('picture', {}).get('data', {}).get('url', '') if isinstance(user_info.get('picture'), dict) else ''
            verified = True  # Facebook emails are generally verified
        elif provider == 'LoginWithAmazon':
            picture = ''
            verified = True
        else:
            picture = ''
            verified = user_info.get('email_verified', False)
        
        return {
            'email': email,
            'first_name': given_name,
            'last_name': family_name,
            'provider': provider,
            'provider_id': user_info.get('sub', ''),
            'picture': picture,
            'email_verified': verified,
            'social_login': True
        }
    
    def logout_url(self, logout_uri=None):
        """Generate logout URL"""
        if not logout_uri:
            logout_uri = self.redirect_uri.replace('/auth/callback', '/logout/complete')
        
        params = {
            'client_id': self.client_id,
            'logout_uri': logout_uri
        }
        
        return f'https://{self.domain}/logout?{urlencode(params)}'

# Cognito setup and configuration functions
def setup_cognito_user_pool():
    """Setup Cognito User Pool with social providers"""
    
    print("🔧 Setting up AWS Cognito User Pool for Social Authentication")
    print("=" * 60)
    
    # This would typically be done via AWS Console or CloudFormation
    # Here we provide the configuration that should be applied
    
    user_pool_config = {
        "PoolName": "p2p-lending-users",
        "Policies": {
            "PasswordPolicy": {
                "MinimumLength": 8,
                "RequireUppercase": False,
                "RequireLowercase": False,
                "RequireNumbers": False,
                "RequireSymbols": False
            }
        },
        "AutoVerifiedAttributes": ["email"],
        "UsernameAttributes": ["email"],
        "Schema": [
            {
                "Name": "email",
                "AttributeDataType": "String",
                "Required": True,
                "Mutable": True
            },
            {
                "Name": "given_name",
                "AttributeDataType": "String",
                "Required": False,
                "Mutable": True
            },
            {
                "Name": "family_name",
                "AttributeDataType": "String",
                "Required": False,
                "Mutable": True
            }
        ]
    }
    
    app_client_config = {
        "ClientName": "p2p-lending-web-client",
        "GenerateSecret": True,
        "ExplicitAuthFlows": [
            "ALLOW_USER_SRP_AUTH",
            "ALLOW_REFRESH_TOKEN_AUTH"
        ],
        "SupportedIdentityProviders": [
            "COGNITO",
            "Google",
            "Facebook",
            "LoginWithAmazon"
        ],
        "CallbackURLs": [
            "http://localhost:5000/auth/callback",
            "http://p2p-lending-prod.eba-qstjs52k.us-east-1.elasticbeanstalk.com/auth/callback"
        ],
        "LogoutURLs": [
            "http://localhost:5000/logout/complete",
            "http://p2p-lending-prod.eba-qstjs52k.us-east-1.elasticbeanstalk.com/logout/complete"
        ],
        "AllowedOAuthFlows": ["code"],
        "AllowedOAuthScopes": ["openid", "email", "profile"],
        "AllowedOAuthFlowsUserPoolClient": True
    }
    
    domain_config = {
        "Domain": "p2p-lending-auth",
        "CertificateArn": None  # Use Cognito's certificate
    }
    
    print("📋 User Pool Configuration:")
    print(json.dumps(user_pool_config, indent=2))
    print("\n📋 App Client Configuration:")
    print(json.dumps(app_client_config, indent=2))
    print("\n📋 Domain Configuration:")
    print(json.dumps(domain_config, indent=2))
    
    print("\n⚠️  Manual Setup Required:")
    print("1. Create User Pool in AWS Console with above configuration")
    print("2. Create App Client with above settings")
    print("3. Configure Domain for hosted UI")
    print("4. Set up Identity Providers (Google, Facebook, Amazon)")
    print("5. Update environment variables with pool ID, client ID, and secret")
    
    return user_pool_config, app_client_config, domain_config

if __name__ == "__main__":
    setup_cognito_user_pool()
