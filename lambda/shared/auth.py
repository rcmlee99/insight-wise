import os
import jwt
import requests
from typing import Dict, Any
from jwt.algorithms import RSAAlgorithm

# Cache for the public key
_public_key = None

def get_public_key() -> str:
    """Get the public key from Cognito for JWT verification"""
    global _public_key
    if _public_key is None:
        # For test environment, use a simple key
        if os.environ.get('TESTING'):
            _public_key = 'test-key'
        else:
            user_pool_id = os.environ['USER_POOL_ID']
            region = user_pool_id.split('_')[0]
            url = f'https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json'
            response = requests.get(url)
            jwks = response.json()
            # Use the first key in the key set
            key_data = jwks['keys'][0]
            _public_key = RSAAlgorithm.from_jwk(key_data)
    return _public_key

def verify_token(token: str) -> Dict[str, Any]:
    """Verify the JWT token from Cognito"""
    try:
        # Get the public key
        public_key = get_public_key()

        if os.environ.get('TESTING'):
            # In test environment, use HS256 and simpler verification
            decoded = jwt.decode(
                token,
                public_key,
                algorithms=['HS256'],
                audience=os.environ['CLIENT_ID']
            )
        else:
            # In production, use RS256 and full verification
            decoded = jwt.decode(
                token,
                public_key,
                algorithms=['RS256'],
                audience=os.environ['CLIENT_ID']
            )
        return decoded
    except jwt.InvalidTokenError as e:
        raise ValueError(f"Invalid token: {str(e)}")