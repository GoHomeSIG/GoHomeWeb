from flask import Blueprint, jsonify, session
from routes.auth import login_required
from models.database import db, User, Badge

badges_bp = Blueprint('badges', __name__)


@badges_bp.route('/api/badges')
@login_required
def api_list():
    """API: 获取用户勋章列表"""
    user = db.session.get(User, session['user_id'])
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404

    badges = db.session.execute(
        db.select(Badge)
        .filter_by(user_id=user.id)
        .order_by(Badge.earned_at.desc())
    ).scalars().all()

    result = []
    for badge in badges:
        badge_dict = badge.to_dict()
        result.append({
            'id': badge.badge_id,
            'badge_id': badge.badge_id,
            'name': badge_dict.get('badge_name', ''),
            'description': badge_dict.get('badge_description', ''),
            'category': badge_dict.get('badge_category', ''),
            'earned_at': badge_dict.get('earned_at')
        })

    return jsonify({
        'success': True,
        'badges': result
    })


@badges_bp.route('/api/badges/definitions')
@login_required
def api_definitions():
    """API: 获取所有勋章定义"""
    # 按分类组织
    categories = {
        'time': {'name': '时间里程碑', 'badges': []},
        'streak': {'name': '签到连续', 'badges': []},
        'special': {'name': '特殊成就', 'badges': []},
    }

    for badge_id, definition in Badge.BADGE_DEFINITIONS.items():
        category = definition.get('category', 'special')
        categories[category]['badges'].append({
            'id': badge_id,
            'name': definition['name'],
            'description': definition['description'],
            'category': category
        })

    return jsonify({
        'success': True,
        'categories': categories
    })
