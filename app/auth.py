import jwt
import requests
from flask import request, jsonify
from functools import wraps

SUPABASE_PROJECT_ID = 'pnvmksvuwvvrdqqjsyqf'
SUPABASE_JWT_SECRET_URL = 'https://pnvmksvuwvvrdqqjsyqf.supabase.co/auth/v1/keys'

def get_jwt_public_key():
    res = requests.get(SUPABASE_JWT_SECRET_URL)
    jwks = res.json()
    return jwt.algorithms.RSAAlgorithm.from_jwk(jwks['keys'][0])

def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.replace('Bearer ', '')

        try:
            payload = jwt.decode(token, get_jwt_public_key(), algorithms=['RS256'], audience='authenticated')
            request.user = {
                "sub": payload.get("sub"),
                "email": payload.get("email") 
            }
        except Exception as e:
            return jsonify({'error': 'Unauthorized', 'details': str(e)}), 401

        return f(*args, **kwargs)
    return wrapper