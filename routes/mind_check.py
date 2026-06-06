from flask import Blueprint, request, jsonify
from config import supabase
from utils.auth_middleware import token_required
from utils.ml_predictor import MindCheckPredictor

mind_check_bp = Blueprint('mind_check_bp', __name__)

predictor = MindCheckPredictor()

@mind_check_bp.route('', methods=['POST'])
@token_required
def create_mind_check(current_user_id):
    data = request.json
    
    raw_input = {
        "mental_health_index": data.get('mental_health_index', 1),
        "depression_score": data.get('depression_score', 0),
        "anxiety_score": data.get('anxiety_score', 0),
        "stress_score": data.get('stress_score', 0),
        "sleep_hours": data.get('sleep_hours', 0),
        "study_hours": data.get('study_hours', 0)
    }

    try:
        result = predictor.predict(raw_input)
        
        msg = "It looks like you're reaching your limit. Please prioritize rest." if result['is_burnout'] else "You're doing great! Your focus is high today."

        db_payload = {
            "user_id": current_user_id,
            "mental_health_index": raw_input["mental_health_index"],
            "depression_score": raw_input["depression_score"],
            "anxiety_score": raw_input["anxiety_score"],
            "stress_score": raw_input["stress_score"],
            "sleep_hours": raw_input["sleep_hours"],
            "study_hours": raw_input["study_hours"],
            "focus_level_pct": result['focus_level_pct'],
            "burnout_level_pct": result['burnout_level_pct'],
            "is_burnout": result['is_burnout']
        }
        res = supabase.table('mind_checks').insert(db_payload).execute()
        
        return jsonify({
            "message": "Mind check analysis completed successfully.",
            "data": {
                "id": res.data[0]['id'],
                "created_at": res.data[0]['created_at'],
                "analysis_result": {
                    "focus_level_pct": result['focus_level_pct'],
                    "burnout_level_pct": result['burnout_level_pct'],
                    "analysis_message": msg,
                    "is_burnout": result['is_burnout']
                }
            }
        }), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 422
    except Exception as e:
        return jsonify({"error": f"Terjadi kesalahan pada server: {str(e)}"}), 500
    
@mind_check_bp.route('', methods=['GET'])
@token_required
def get_mind_checks(current_user_id):
    """
    Mengambil riwayat mind check milik user yang sedang login, 
    diurutkan dari yang paling baru.
    """
    try:
        res = supabase.table('mind_checks')\
            .select('*')\
            .eq('user_id', current_user_id)\
            .order('created_at', desc=True)\
            .execute()
            
        return jsonify({
            "message": "Berhasil mengambil riwayat mind check",
            "data": res.data
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Terjadi kesalahan saat mengambil data: {str(e)}"}), 500