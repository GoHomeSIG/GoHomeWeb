from flask import Blueprint, jsonify, request, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from models.database import db, User, Checkin, Badge, AIQuote
from routes.auth import login_required
from routes.dashboard import get_checkin_stats

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/login', methods=['POST'])
def login():
    """登录 API"""
    data = request.get_json()
    username = data.get('username', '').strip() if data else ''
    password = data.get('password', '') if data else ''

    if not username or not password:
        return jsonify({'success': False, 'message': '用户名和密码不能为空'})

    user = db.session.execute(
        db.select(User).filter_by(username=username)
    ).first()

    if not user or not check_password_hash(user[0].password_hash, password):
        return jsonify({'success': False, 'message': '用户名或密码错误'})

    user = user[0]
    session['user_id'] = user.id
    session['username'] = user.username

    return jsonify({
        'success': True,
        'user': user.to_dict()
    })


@api_bp.route('/register', methods=['POST'])
def register():
    """注册 API"""
    data = request.get_json()
    username = data.get('username', '').strip() if data else ''
    password = data.get('password', '') if data else ''
    hometown = data.get('hometown', '').strip() if data else ''
    current_city = data.get('current_city', '').strip() if data else ''
    leave_home_date = data.get('leave_home_date', '')
    family_role = data.get('family_role', '妈妈')
    nickname = data.get('nickname', '').strip()
    tone_style = data.get('tone_style', '唠叨型')

    if not username or not password:
        return jsonify({'success': False, 'message': '用户名和密码不能为空'})

    if len(username) < 3:
        return jsonify({'success': False, 'message': '用户名至少需要 3 个字符'})

    if len(password) < 6:
        return jsonify({'success': False, 'message': '密码至少需要 6 个字符'})

    # 检查用户名是否已存在
    existing = db.session.execute(
        db.select(User).filter_by(username=username)
    ).first()

    if existing:
        return jsonify({'success': False, 'message': '该用户名已被注册'})

    user = User(
        username=username,
        password_hash=generate_password_hash(password),
        hometown=hometown,
        current_city=current_city,
        leave_home_date=leave_home_date,
        family_role=family_role,
        nickname=nickname,
        tone_style=tone_style
    )
    db.session.add(user)
    db.session.commit()

    return jsonify({'success': True})


@api_bp.route('/logout', methods=['GET'])
def logout():
    """登出 API"""
    session.clear()
    return jsonify({'success': True})


@api_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    """获取用户资料 API"""
    user = db.session.get(User, session['user_id'])
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'})

    return jsonify({
        'success': True,
        'user': user.to_dict()
    })


@api_bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    """更新用户资料 API"""
    data = request.get_json()
    user = db.session.get(User, session['user_id'])
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'})

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


@api_bp.route('/checkin', methods=['POST'])
@login_required
def do_checkin():
    """签到 API"""
    user = db.session.get(User, session['user_id'])
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'})

    today = datetime.now().strftime('%Y-%m-%d')

    # 检查今天是否已经签到
    existing = db.session.execute(
        db.select(Checkin).filter_by(user_id=user.id, checkin_date=today)
    ).first()

    if existing:
        return jsonify({
            'success': False,
            'message': '今天已经签到过了'
        })

    return jsonify({
        'success': False,
        'message': '请使用 /api/checkin 端点进行签到'
    })


@api_bp.route('/checkin/status', methods=['GET'])
@login_required
def checkin_status():
    """获取签到状态 API"""
    user = db.session.get(User, session['user_id'])
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'})

    stats = get_checkin_stats(user)
    today = datetime.now().strftime('%Y-%m-%d')

    has_checked_in = db.session.execute(
        db.select(Checkin).filter_by(user_id=user.id, checkin_date=today)
    ).first() is not None

    return jsonify({
        'success': True,
        'has_checked_in_today': has_checked_in,
        'stats': stats
    })


@api_bp.route('/checkin/history', methods=['GET'])
@login_required
def checkin_history():
    """获取签到历史 API"""
    user = db.session.get(User, session['user_id'])
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'})

    checkins = db.session.execute(
        db.select(Checkin)
        .filter_by(user_id=user.id)
        .order_by(Checkin.checkin_time.desc())
    ).scalars().all()

    return jsonify({
        'success': True,
        'checkins': [c.to_dict() for c in checkins]
    })
