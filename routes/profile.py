from flask import Blueprint, request, jsonify
from config import supabase
from utils.auth_middleware import token_required

profile_bp = Blueprint('profile_bp', __name__)

@profile_bp.route('/', methods=['GET'])
@token_required
def get_profile(current_user_id):
    try:
        res = supabase.table('profiles').select('*').eq('id', current_user_id).execute()
        if not res.data:
            return jsonify({"error": "Profil tidak ditemukan"}), 404
            
        return jsonify({"data": res.data[0]}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@profile_bp.route('/', methods=['PUT'])
@token_required
def update_profile(current_user_id):
    data = request.json
    update_data = {}
    
    if "full_name" in data: update_data["full_name"] = data["full_name"]
    if "avatar_url" in data: update_data["avatar_url"] = data["avatar_url"]
    if "institution" in data: update_data["institution"] = data["institution"]

    try:
        res = supabase.table('profiles').update(update_data).eq('id', current_user_id).execute()
        return jsonify({"message": "Profil berhasil diperbarui", "data": res.data[0]}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500