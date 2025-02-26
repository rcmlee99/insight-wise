import os
import jwt
import logging
from typing import Dict, Any
from jwt.algorithms import RSAAlgorithm
import requests

logger = logging.getLogger(__name__)

# Cache for the public key
_public_key = None

def get_public_key() -> str:
    """Get the public key from Cognito for JWT verification"""
    global _public_key
    if _public_key is None:
        is_testing = os.environ.get('TESTING', '').lower() == 'true'
        logger.debug(f"get_public_key called, is_testing={is_testing}")

        if is_testing:
            _public_key = 'test-key'
            logger.debug("Using test key")
        else:
            try:
                logger.debug("Fetching public key from Cognito")
                user_pool_id = os.environ['USER_POOL_ID']
                region = user_pool_id.split('_')[0]
                url = f'https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json'

                logger.debug(f"Making request to {url}")
                response = requests.get(url)
                jwks = response.json()
                # Use the first key in the key set
                key_data = jwks['keys'][0]
                _public_key = RSAAlgorithm.from_jwk(key_data)
                logger.debug("Successfully fetched public key")
            except Exception as e:
                logger.error(f"Error fetching public key: {str(e)}")
                raise
    return _public_key

def verify_token(token: str) -> Dict[str, Any]:
    """Verify the JWT token from Cognito"""
    try:
        # Get the public key
        public_key = get_public_key()
        is_testing = os.environ.get('TESTING', '').lower() == 'true'

        if is_testing:
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