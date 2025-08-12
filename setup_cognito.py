#!/usr/bin/env python3

import boto3
import json
import os
import sys

def create_cognito_user_pool():
    """Create Cognito User Pool for P2P Lending Platform"""
    
    print("🔧 Creating AWS Cognito User Pool for Social Authentication")
    print("=" * 60)
    
    # Initialize Cognito client
    cognito_client = boto3.client('cognito-idp', region_name='us-east-1')
    
    try:
        # Step 1: Create User Pool
        print("\n1. Creating User Pool...")
        
        user_pool_response = cognito_client.create_user_pool(
            PoolName='p2p-lending-users',
            Policies={
                'PasswordPolicy': {
                    'MinimumLength': 8,
                    'RequireUppercase': False,
                    'RequireLowercase': False,
                    'RequireNumbers': False,
                    'RequireSymbols': False,
                    'TemporaryPasswordValidityDays': 7
                }
            },
            AutoVerifiedAttributes=['email'],
            UsernameAttributes=['email'],
            UsernameConfiguration={
                'CaseSensitive': False
            },
            Schema=[
                {
                    'Name': 'email',
                    'AttributeDataType': 'String',
                    'Required': True,
                    'Mutable': True
                },
                {
                    'Name': 'given_name',
                    'AttributeDataType': 'String',
                    'Required': False,
                    'Mutable': True
                },
                {
                    'Name': 'family_name',
                    'AttributeDataType': 'String',
                    'Required': False,
                    'Mutable': True
                }
            ],
            VerificationMessageTemplate={
                'DefaultEmailOption': 'CONFIRM_WITH_CODE',
                'EmailMessage': 'Welcome to P2P Lending! Your verification code is {####}',
                'EmailSubject': 'P2P Lending - Verify your email'
            },
            EmailConfiguration={
                'EmailSendingAccount': 'COGNITO_DEFAULT'
            }
        )
        
        user_pool_id = user_pool_response['UserPool']['Id']
        print(f"✅ User Pool created: {user_pool_id}")
        
        # Step 2: Create User Pool Client
        print("\n2. Creating User Pool Client...")
        
        client_response = cognito_client.create_user_pool_client(
            UserPoolId=user_pool_id,
            ClientName='p2p-lending-web-client',
            GenerateSecret=True,
            RefreshTokenValidity=30,
            AccessTokenValidity=60,
            IdTokenValidity=60,
            TokenValidityUnits={
                'AccessToken': 'minutes',
                'IdToken': 'minutes',
                'RefreshToken': 'days'
            },
            ExplicitAuthFlows=[
                'ALLOW_USER_SRP_AUTH',
                'ALLOW_REFRESH_TOKEN_AUTH'
            ],
            SupportedIdentityProviders=[
                'COGNITO'
            ],
            CallbackURLs=[
                'http://localhost:5000/auth/callback',
                'https://p2p-lending-prod.eba-qstjs52k.us-east-1.elasticbeanstalk.com/auth/callback'
            ],
            LogoutURLs=[
                'http://localhost:5000/logout/complete',
                'https://p2p-lending-prod.eba-qstjs52k.us-east-1.elasticbeanstalk.com/logout/complete'
            ],
            AllowedOAuthFlows=['code'],
            AllowedOAuthScopes=['openid', 'email', 'profile'],
            AllowedOAuthFlowsUserPoolClient=True,
            PreventUserExistenceErrors='ENABLED'
        )
        
        client_id = client_response['UserPoolClient']['ClientId']
        client_secret = client_response['UserPoolClient']['ClientSecret']
        print(f"✅ User Pool Client created: {client_id}")
        
        # Step 3: Create User Pool Domain
        print("\n3. Creating User Pool Domain...")
        
        domain_name = f'p2p-lending-{user_pool_id.lower().replace("_", "-").replace("_", "-")}'
        
        try:
            domain_response = cognito_client.create_user_pool_domain(
                Domain=domain_name,
                UserPoolId=user_pool_id
            )
            print(f"✅ User Pool Domain created: {domain_name}.auth.us-east-1.amazoncognito.com")
            cognito_domain = f"{domain_name}.auth.us-east-1.amazoncognito.com"
        except Exception as e:
            if "Domain already exists" in str(e):
                print(f"⚠️  Domain already exists, using: {domain_name}.auth.us-east-1.amazoncognito.com")
                cognito_domain = f"{domain_name}.auth.us-east-1.amazoncognito.com"
            else:
                raise e
        
        # Step 4: Output configuration
        print(f"\n🎉 Cognito Setup Complete!")
        print(f"=" * 60)
        
        config = {
            'COGNITO_USER_POOL_ID': user_pool_id,
            'COGNITO_CLIENT_ID': client_id,
            'COGNITO_CLIENT_SECRET': client_secret,
            'COGNITO_DOMAIN': cognito_domain,
            'COGNITO_REDIRECT_URI': 'https://p2p-lending-prod.eba-qstjs52k.us-east-1.elasticbeanstalk.com/auth/callback'
        }
        
        print("📋 Environment Variables to Set:")
        for key, value in config.items():
            print(f"export {key}='{value}'")
        
        # Save to .env file
        with open('.env.cognito', 'w') as f:
            for key, value in config.items():
                f.write(f"{key}={value}\n")
        
        print(f"\n💾 Configuration saved to .env.cognito")
        
        print(f"\n📋 Next Steps:")
        print(f"1. Set up Identity Providers (Google, Facebook, Amazon) in AWS Console")
        print(f"2. Update User Pool Client to include social providers")
        print(f"3. Set environment variables in Elastic Beanstalk")
        print(f"4. Deploy updated application with Cognito integration")
        
        print(f"\n🔗 Useful URLs:")
        print(f"   • User Pool Console: https://console.aws.amazon.com/cognito/users/?region=us-east-1#/pool/{user_pool_id}")
        print(f"   • Hosted UI: https://{cognito_domain}/login?client_id={client_id}&response_type=code&scope=openid+email+profile&redirect_uri=http://localhost:5000/auth/callback")
        
        return config
        
    except Exception as e:
        print(f"❌ Error creating Cognito User Pool: {e}")
        return None

def setup_identity_providers(user_pool_id, client_id):
    """Setup social identity providers"""
    
    print(f"\n🔧 Setting up Identity Providers")
    print(f"=" * 40)
    
    print(f"⚠️  Manual Setup Required in AWS Console:")
    print(f"1. Go to Cognito User Pool: {user_pool_id}")
    print(f"2. Navigate to 'Sign-in experience' > 'Federated identity provider sign-in'")
    print(f"3. Add Identity Providers:")
    
    providers = {
        'Google': {
            'setup_url': 'https://console.developers.google.com/',
            'callback_url': f'https://p2p-lending-{user_pool_id.lower().replace("_", "-")}.auth.us-east-1.amazoncognito.com/oauth2/idpresponse',
            'scopes': 'openid email profile'
        },
        'Facebook': {
            'setup_url': 'https://developers.facebook.com/',
            'callback_url': f'https://p2p-lending-{user_pool_id.lower().replace("_", "-")}.auth.us-east-1.amazoncognito.com/oauth2/idpresponse',
            'scopes': 'public_profile email'
        },
        'Amazon': {
            'setup_url': 'https://developer.amazon.com/loginwithamazon/console/site/lwa/overview.html',
            'callback_url': f'https://p2p-lending-{user_pool_id.lower().replace("_", "-")}.auth.us-east-1.amazoncognito.com/oauth2/idpresponse',
            'scopes': 'profile'
        }
    }
    
    for provider, config in providers.items():
        print(f"\n   {provider}:")
        print(f"   • Setup URL: {config['setup_url']}")
        print(f"   • Callback URL: {config['callback_url']}")
        print(f"   • Scopes: {config['scopes']}")
    
    print(f"\n4. Update User Pool Client to include social providers")
    print(f"5. Test the integration")

def main():
    """Main setup function"""
    
    try:
        # Create Cognito User Pool
        config = create_cognito_user_pool()
        
        if config:
            # Setup identity providers (manual steps)
            setup_identity_providers(config['COGNITO_USER_POOL_ID'], config['COGNITO_CLIENT_ID'])
            
            print(f"\n🎯 Setup Summary:")
            print(f"✅ Cognito User Pool created and configured")
            print(f"✅ User Pool Client created with OAuth settings")
            print(f"✅ Domain configured for hosted UI")
            print(f"✅ Environment variables generated")
            print(f"⚠️  Social providers require manual setup")
            
            return True
        else:
            return False
            
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
