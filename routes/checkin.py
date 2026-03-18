from flask import Blueprint, jsonify, request, session
from datetime import datetime
from models.database import db, User, Checkin, Badge, AIQuote
from routes.auth import login_required
from routes.dashboard import get_checkin_stats
from config import AI_API_KEY, AI_API_BASE_URL, AI_MODEL

checkin_bp = Blueprint('checkin', __name__)


@checkin_bp.route('/api/checkin/status', methods=['GET'])
@login_required
def get_checkin_status():
    """获取签到状态 API"""
    user = db.session.get(User, session['user_id'])
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404

    stats = get_checkin_stats(user)
    today = datetime.now().strftime('%Y-%m-%d')

    # 检查今天是否已签到
    checkin_today = db.session.execute(
        db.select(Checkin).filter_by(user_id=user.id, checkin_date=today)
    ).first()

    return jsonify({
        'success': True,
        'has_checked_in_today': checkin_today is not None,
        'stats': stats,
        'last_checkin': {
            'checkin_date': stats.get('last_checkin_date', '')
        } if stats.get('last_checkin_date') else None
    })


@checkin_bp.route('/api/checkin', methods=['POST'])
@login_required
def do_checkin():
    """签到打卡 API"""
    user = db.session.get(User, session['user_id'])
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404

    today = datetime.now().strftime('%Y-%m-%d')

    # 检查今天是否已签到
    existing = db.session.execute(
        db.select(Checkin).filter_by(user_id=user.id, checkin_date=today)
    ).first()

    if existing:
        return jsonify({
            'success': False,
            'message': '今天已经签到过了'
        }), 400

    new_badges = []  # 记录新解锁的徽章

    # 检查特殊成就徽章
    checkin_time = datetime.now()

    # 深夜未眠徽章 (凌晨 2 点后)
    if checkin_time.hour >= 2:
        badge = add_badge(user.id, 'late_night')
        if badge:
            new_badges.append(Badge.get_definition('late_night'))

    # 早起鸟儿徽章 (早上 6 点前)
    elif checkin_time.hour < 6:
        badge = add_badge(user.id, 'early_bird')
        if badge:
            new_badges.append(Badge.get_definition('early_bird'))

    # 优先尝试 AI 生成家人问候
    quote_content = None
    quote_dialect = ''
    if AI_API_KEY:
        try:
            from utils.ai_hometown_generator import AIHometownGenerator
            generator = AIHometownGenerator(
                api_key=AI_API_KEY,
                base_url=AI_API_BASE_URL,
                model=AI_MODEL
            )
            user_info = {
                'hometown': user.hometown,
                'current_city': getattr(user, 'current_city', ''),
                'family_role': getattr(user, 'family_role', '妈妈'),
                'nickname': getattr(user, 'nickname', '娃'),
                'tone_style': getattr(user, 'tone_style', '唠叨型'),
            }
            ai_result = generator.generate_family_greeting(user_info)
            if ai_result:
                quote_content = ai_result['content']
                quote_dialect = ai_result.get('dialect', '')
                # 保存 AI 问候记录
                ai_quote = AIQuote(
                    user_id=user.id,
                    content=quote_content,
                    family_role=user_info['family_role'],
                    dialect=quote_dialect
                )
                db.session.add(ai_quote)
        except Exception as e:
            print(f"AI 生成失败：{e}")

    # 如果 AI 生成失败，使用内置话语
    if not quote_content:
        from utils.quote_generator import QuoteGenerator
        quote = QuoteGenerator.get_random_quote(user.id)
        quote_content = quote['content']

    # 创建签到记录
    checkin = Checkin(
        user_id=user.id,
        checkin_date=today,
        checkin_time=datetime.now(),
        quote_content=quote_content,
        quote_category='AI 生成' if AI_API_KEY and quote_content else '内置',
        quote_dialect=quote_dialect
    )
    db.session.add(checkin)

    # 检查时间里程碑徽章
    days_away = get_days_away_from_home(user)
    time_badges = {
        1: 'day_1', 7: 'day_7', 30: 'day_30',
        100: 'day_100', 180: 'day_180', 365: 'day_365'
    }
    for threshold, badge_id in time_badges.items():
        if days_away == threshold:
            badge = add_badge(user.id, badge_id)
            if badge:
                new_badges.append(Badge.get_definition(badge_id))

    # 检查连续签到徽章
    stats = get_checkin_stats(user)
    streak_badges = {
        3: 'streak_3', 7: 'streak_7', 15: 'streak_15',
        30: 'streak_30', 100: 'streak_100'
    }
    for threshold, badge_id in streak_badges.items():
        if stats['current_streak'] == threshold:
            badge = add_badge(user.id, badge_id)
            if badge:
                new_badges.append(Badge.get_definition(badge_id))

    db.session.commit()

    # 返回结果
    result = {
        'success': True,
        'checkin_date': today,
        'stats': stats,
        'new_badges': new_badges
    }

    if quote_content:
        result['quote'] = {
            'content': quote_content,
            'category': 'AI 生成' if AI_API_KEY else '内置',
            'dialect': quote_dialect
        }

    return jsonify(result)


@checkin_bp.route('/api/checkin/history', methods=['GET'])
@login_required
def get_checkin_history():
    """获取签到历史 API"""
    user = db.session.get(User, session['user_id'])
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404

    checkins = db.session.execute(
        db.select(Checkin)
        .filter_by(user_id=user.id)
        .order_by(Checkin.checkin_time.desc())
    ).scalars().all()

    return jsonify({
        'success': True,
        'checkins': [c.to_dict() for c in checkins]
    })


def add_badge(user_id, badge_id):
    """给用户添加徽章（如果未获得）"""
    existing = db.session.execute(
        db.select(Badge).filter_by(user_id=user_id, badge_id=badge_id)
    ).first()

    if existing:
        return None

    badge = Badge(user_id=user_id, badge_id=badge_id)
    db.session.add(badge)
    return badge


def get_days_away_from_home(user):
    """计算离家天数"""
    if not user.leave_home_date:
        return 0
    try:
        leave_date = datetime.strptime(user.leave_home_date, '%Y-%m-%d')
        return (datetime.now() - leave_date).days
    except ValueError:
        return 0
