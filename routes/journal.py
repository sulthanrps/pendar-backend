from flask import Blueprint, request, jsonify
from config import supabase
from utils.auth_middleware import token_required

journal_bp = Blueprint('journal_bp', __name__)

@journal_bp.route('/', methods=['GET'])
@token_required
def get_journals(current_user_id):
    try:
        res = supabase.table('journals').select('*').eq('user_id', current_user_id).order('created_at', desc=True).execute()
        return jsonify({"data": res.data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@journal_bp.route('/', methods=['POST'])
@token_required
def add_journal(current_user_id):
    data = request.json
    try:
        new_journal = {
            "user_id": current_user_id,
            "title": data.get("title"),
            "content": data.get("content"),
            "mood_emoji": data.get("mood_emoji")
        }
        res = supabase.table('journals').insert(new_journal).execute()
        return jsonify({"message": "Jurnal berhasil disimpan!", "data": res.data[0]}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@journal_bp.route('/<id>', methods=['PUT'])
@token_required
def update_journal(current_user_id, id):
    data = request.json
    update_data = {}
    
    if "title" in data: update_data["title"] = data["title"]
    if "content" in data: update_data["content"] = data["content"]

    try:
        res = supabase.table('journals').update(update_data).eq('id', id).eq('user_id', current_user_id).execute()
        if not res.data:
            return jsonify({"error": "Jurnal tidak ditemukan atau tidak memiliki akses"}), 404
        return jsonify({"message": "Jurnal berhasil diperbarui!", "data": res.data[0]}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@journal_bp.route('/<id>', methods=['DELETE'])
@token_required
def delete_journal(current_user_id, id):
    try:
        # Hapus jurnal berdasarkan ID jurnal DAN User ID yang sedang login
        res = supabase.table('journals').delete().eq('id', id).eq('user_id', current_user_id).execute()
        
        # Jika res.data kosong, berarti data tidak ada atau bukan milik user tersebut
        if not res.data:
            return jsonify({"error": "Jurnal tidak ditemukan atau Anda tidak memiliki akses!"}), 404
            
        return jsonify({
            "message": "Jurnal berhasil dihapus secara permanen.", 
            "deleted_id": id
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400