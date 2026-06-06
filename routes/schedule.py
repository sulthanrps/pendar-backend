from flask import Blueprint, request, jsonify
from config import supabase
from utils.auth_middleware import token_required

schedule_bp = Blueprint('schedule_bp', __name__)

@schedule_bp.route('', methods=['GET'])
@token_required
def get_schedules(current_user_id):
    try:
        # 1. Ambil data dari Supabase (cukup order berdasarkan deadline saja dulu)
        res = supabase.table('schedules')\
            .select('*')\
            .eq('user_id', current_user_id)\
            .eq('is_completed', False)\
            .execute()
        
        schedules = res.data
        
        # 2. Definisikan mapping prioritas agar bisa diurutkan secara numerik
        priority_map = {"High": 1, "Medium": 2, "Low": 3}
        
        # 3. Sort di Python menggunakan dua kunci (priority_map dulu, baru deadline)
        # x['priority'] diambil nilainya dari map, jika tidak ada (None) kasih nilai 4
        schedules.sort(key=lambda x: (priority_map.get(x.get('priority'), 4), x.get('deadline')))
        
        return jsonify({"data": schedules}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@schedule_bp.route('', methods=['POST'])
@token_required
def add_schedule(current_user_id):
    data = request.json
    try:
        new_schedule = {
            "user_id": current_user_id,
            "task_name": data.get("task_name"),
            "deadline": data.get("deadline"),
            "priority": data.get("priority", "Medium")
        }
        res = supabase.table('schedules').insert(new_schedule).execute()
        return jsonify({"message": "Jadwal berhasil ditambahkan!", "data": res.data[0]}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@schedule_bp.route('/<id>', methods=['PUT'])
@token_required
def update_schedule(current_user_id, id):
    data = request.json
    update_data = {}
    
    if "task_name" in data: update_data["task_name"] = data["task_name"]
    if "deadline" in data: update_data["deadline"] = data["deadline"]
    if "is_completed" in data: update_data["is_completed"] = data["is_completed"]
    if "priority" in data: update_data["priority"] = data["priority"]

    try:
        res = supabase.table('schedules').update(update_data).eq('id', id).eq('user_id', current_user_id).execute()
        if not res.data:
            return jsonify({"error": "Jadwal tidak ditemukan atau tidak memiliki akses"}), 404
        return jsonify({"message": "Jadwal berhasil diupdate!", "data": res.data[0]}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@schedule_bp.route('/<id>', methods=['DELETE'])
@token_required
def delete_schedule(current_user_id, id):
    try:
        res = supabase.table('schedules').delete().eq('id', id).eq('user_id', current_user_id).execute()
        
        if not res.data:
            return jsonify({"error": "Jadwal tidak ditemukan atau Anda tidak memiliki akses!"}), 404
            
        return jsonify({
            "message": "Jadwal berhasil dihapus.", 
            "deleted_id": id
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400