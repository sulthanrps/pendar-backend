from flask import Blueprint, jsonify
from config import supabase
from utils.auth_middleware import token_required
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard_bp', __name__)

@dashboard_bp.route('/', methods=['GET'])
@token_required
def get_dashboard(current_user_id):
    try:
        profile_res = supabase.table('profiles').select('full_name').eq('id', current_user_id).execute()
        user_name = profile_res.data[0]['full_name'].split()[0] if profile_res.data else "User"

        seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
        mind_checks_res = supabase.table('mind_checks')\
            .select('burnout_level_pct')\
            .eq('user_id', current_user_id)\
            .gte('created_at', seven_days_ago)\
            .execute()
        
        scores = [row['burnout_level_pct'] for row in mind_checks_res.data]
        if scores:
            avg_burnout = sum(scores) / len(scores)
            mood_percentage = round(120 - avg_burnout)
            mood_label = "You're feeling good this week" if mood_percentage >= 70 else "Take time to rest this week"
        else:
            mood_percentage = 0
            mood_label = "No data yet. Do your first Mind Check today!"
        
        journal_res = supabase.table('journals')\
            .select('id, created_at, content, mood_emoji')\
            .eq('user_id', current_user_id)\
            .order('created_at', desc=True)\
            .limit(1)\
            .execute()

        schedule_res = supabase.table('schedules')\
            .select('id, task_name, deadline')\
            .eq('user_id', current_user_id)\
            .eq('is_completed', False)\
            .order('deadline')\
            .limit(2)\
            .execute()

        return jsonify({
            "data": {
                "user_greeting": f"Good Morning, {user_name}",
                "mood_journey": {
                    "percentage": mood_percentage,
                    "label": mood_label
                },
                "recent_journal": journal_res.data[0] if journal_res.data else None,
                "upcoming_priorities": schedule_res.data
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500