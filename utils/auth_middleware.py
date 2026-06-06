from functools import wraps
from flask import request, jsonify
from config import supabase 

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]
        
        if not token:
            return jsonify({'error': 'Akses ditolak: Token tidak ditemukan!'}), 401
        
        try:
            user_response = supabase.auth.get_user(token)
            current_user_id = user_response.user.id
        except Exception as e:
            return jsonify({'error': 'Token tidak valid atau kedaluwarsa!', 'details': str(e)}), 401
        
        return f(current_user_id, *args, **kwargs)
    
    return decorated