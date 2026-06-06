from flask import Blueprint, request, jsonify
from config import supabase

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    try:
        auth_res = supabase.auth.sign_up({
            "email": data.get('email'),
            "password": data.get('password')
        })
        user_id = auth_res.user.id

        profile_data = {
            "id": user_id,
            "full_name": data.get('full_name'),
            "institution": data.get('institution')
        }
        supabase.table('profiles').insert(profile_data).execute()

        return jsonify({"message": "Registrasi berhasil!", "data": profile_data}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    try:
        auth_res = supabase.auth.sign_in_with_password({
            "email": data.get('email'),
            "password": data.get('password')
        })
        return jsonify({
            "message": "Login berhasil.",
            "data": {
                "access_token": auth_res.session.access_token,
                "user_id": auth_res.user.id
            }
        }), 200
    except Exception as e:
        return jsonify({"error": "Email atau password salah."}), 401