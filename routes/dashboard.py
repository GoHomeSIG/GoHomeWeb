from flask import Blueprint, jsonify, session, request
from datetime import datetime, timedelta
from models.database import db, User, Checkin, Badge
from routes.auth import login_required

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
def get_dashboard():
    """获取仪表盘数据"""
    user = db.session.get(User, session['user_id'])
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404

    stats = get_checkin_stats(user)
    days_away = get_days_away_from_home(user)

    # 获取最近 7 天的签到情况
    week_calendar = get_week_calendar(user)

    # 获取最后一次签到
    last_checkin = get_last_checkin(user)

    # 获取用户徽章数量
    badge_count = db.session.query(Badge).filter_by(user_id=user.id).count()

    return jsonify({
        'success': True,
        'data': {
            'user': user.to_dict(),
            'stats': stats,
            'days_away': days_away,
            'week_calendar': week_calendar,
            'last_checkin': last_checkin,
            'badge_count': badge_count
        }
    })


def get_checkin_stats(user):
    """获取签到统计"""
    checkins = db.session.execute(
        db.select(Checkin)
        .filter_by(user_id=user.id)
        .order_by(Checkin.checkin_date.desc())
    ).scalars().all()

    total_days = len(checkins)

    if total_days == 0:
        return {
            'total_days': 0,
            'current_streak': 0,
            'longest_streak': 0
        }

    # 计算连续签到
    dates = [c.checkin_date for c in checkins]
    current_streak = calculate_current_streak(dates)
    longest_streak = calculate_longest_streak(dates)

    return {
        'total_days': total_days,
        'current_streak': current_streak,
        'longest_streak': longest_streak
    }


def calculate_current_streak(dates):
    """计算当前连续签到天数"""
    if not dates:
        return 0

    today = datetime.now().date()
    streak = 0
    expected_date = today

    for date_str in sorted(dates, reverse=True):
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            if date == expected_date or date == expected_date - timedelta(days=1):
                streak += 1
                expected_date = date - timedelta(days=1)
            else:
                break
        except:
            continue

    # 如果今天没签到，当前连续为 0
    if dates[0] != today.strftime('%Y-%m-%d'):
        return 0

    return streak


def calculate_longest_streak(dates):
    """计算最长连续签到天数"""
    if not dates:
        return 0

    sorted_dates = sorted(dates)
    longest = 1
    current = 1

    for i in range(1, len(sorted_dates)):
        prev = datetime.strptime(sorted_dates[i-1], '%Y-%m-%d').date()
        curr = datetime.strptime(sorted_dates[i], '%Y-%m-%d').date()
        diff = (curr - prev).days

        if diff == 1:
            current += 1
            longest = max(longest, current)
        elif diff > 1:
            current = 1

    return longest


def get_days_away_from_home(user):
    """计算离家天数"""
    if not user.leave_home_date:
        return 0
    try:
        leave_date = datetime.strptime(user.leave_home_date, '%Y-%m-%d')
        return (datetime.now() - leave_date).days
    except ValueError:
        return 0


def get_week_calendar(user):
    """生成最近 7 天的日历"""
    checkins = db.session.execute(
        db.select(Checkin.checkin_date)
        .filter_by(user_id=user.id)
    ).scalars().all()

    recent_dates = set(checkins)

    today = datetime.now().date()
    week_calendar = []
    weekdays = ['一', '二', '三', '四', '五', '六', '日']

    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        week_calendar.append({
            'date': date_str,
            'day': date.strftime('%m/%d'),
            'weekday': weekdays[date.weekday()],
            'checked': date_str in recent_dates
        })

    return week_calendar


def get_last_checkin(user):
    """获取最后一次签到记录"""
    checkin = db.session.execute(
        db.select(Checkin)
        .filter_by(user_id=user.id)
        .order_by(Checkin.checkin_time.desc())
    ).scalars().first()

    if not checkin:
        return None

    return {
        'checkin_date': checkin.checkin_date,
        'checkin_time': checkin.checkin_time.isoformat(),
        'quote_content': checkin.quote_content
    }


@dashboard_bp.route('/profile')
@login_required
def get_profile():
    """获取个人资料"""
    user = db.session.get(User, session['user_id'])
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404

    stats = get_checkin_stats(user)
    days_away = get_days_away_from_home(user)

    return jsonify({
        'success': True,
        'user': user.to_dict(),
        'stats': stats,
        'days_away': days_away
    })


@dashboard_bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    """更新个人资料"""
    data = request.get_json()
    user = db.session.get(User, session['user_id'])
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404

    # 更新字段
    if 'hometown' in data:
        user.hometown = data['hometown']
    if 'current_city' in data:
        user.current_city = data['current_city']
    if 'leave_home_date' in data:
        user.leave_home_date = data['leave_home_date']
    if 'family_role' in data:
        user.family_role = data['family_role']
    if 'nickname' in data:
        user.nickname = data['nickname']
    if 'tone_style' in data:
        user.tone_style = data['tone_style']

    db.session.commit()

    return jsonify({'success': True, 'user': user.to_dict()})
