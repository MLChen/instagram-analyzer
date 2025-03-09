from flask import Blueprint, render_template
from app.database.models import Following, FollowHistory
from datetime import datetime

web = Blueprint('web', __name__)

@web.route('/')
def index():
    """首頁 - 顯示追蹤統計和單向追蹤清單"""
    # 獲取統計數據
    total_following = Following.query.filter_by(current_status=True).count()
    mutual_following = Following.query.filter_by(
        current_status=True,
        follows_me=True
    ).count()
    one_way_following = Following.query.filter_by(
        current_status=True,
        follows_me=False
    ).count()

    # 獲取單向追蹤清單
    one_way_users = Following.query.filter_by(
        current_status=True,
        follows_me=False
    ).order_by(Following.first_seen.desc()).all()

    # 獲取最近的變動記錄
    recent_changes = FollowHistory.query.order_by(
        FollowHistory.event_date.desc()
    ).limit(10).all()

    return render_template('dashboard.html',
        total_following=total_following,
        mutual_following=mutual_following,
        one_way_following=one_way_following,
        one_way_users=one_way_users,
        recent_changes=recent_changes,
        current_time=datetime.now()
    )

@web.route('/history')
def history():
    """歷史記錄頁面"""
    changes = FollowHistory.query.order_by(
        FollowHistory.event_date.desc()
    ).all()
    
    return render_template('history.html',
        changes=changes,
        current_time=datetime.now()
    )
