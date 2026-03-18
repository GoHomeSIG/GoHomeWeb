from flask import Blueprint, jsonify, request, session
from routes.auth import login_required
from models.database import db, User, Quote
from utils.quote_generator import QuoteGenerator

quotes_bp = Blueprint('quotes', __name__)


@quotes_bp.route('/api/quotes')
@login_required
def get_quotes():
    """API: 获取话语列表"""
    user = db.session.get(User, session['user_id'])
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404

    # 获取内置话语
    builtin_quotes = db.session.execute(
        db.select(Quote).filter_by(is_custom=False)
    ).scalars().all()

    # 获取用户自定义话语
    custom_quotes = db.session.execute(
        db.select(Quote).filter_by(is_custom=True, user_id=user.id)
    ).scalars().all()

    all_quotes = []
    for q in builtin_quotes:
        all_quotes.append({
            'id': q.id,
            'content': q.content,
            'category': q.category,
            'is_custom': False
        })

    for q in custom_quotes:
        all_quotes.append({
            'id': q.id,
            'content': q.content,
            'category': q.category,
            'is_custom': True
        })

    return jsonify({
        'success': True,
        'quotes': all_quotes
    })


@quotes_bp.route('/api/quotes', methods=['POST'])
@login_required
def add_quote():
    """API: 添加自定义话语"""
    data = request.get_json()
    content = data.get('content', '').strip() if data else ''
    category = data.get('category', '个人').strip() if data else ''

    if not content:
        return jsonify({'success': False, 'message': '话语内容不能为空'}), 400

    if len(content) > 100:
        return jsonify({'success': False, 'message': '话语内容不能超过 100 字'}), 400

    user = db.session.get(User, session['user_id'])

    quote = Quote(
        content=content,
        category=category,
        is_custom=True,
        user_id=user.id
    )
    db.session.add(quote)
    db.session.commit()

    return jsonify({
        'success': True,
        'quote': {
            'id': quote.id,
            'content': quote.content,
            'category': quote.category,
            'is_custom': quote.is_custom
        }
    })


@quotes_bp.route('/api/quotes/<int:quote_id>', methods=['DELETE'])
@login_required
def delete_quote(quote_id):
    """API: 删除自定义话语"""
    user = db.session.get(User, session['user_id'])
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404

    # 查找话语
    quote = db.session.get(Quote, quote_id)
    if not quote:
        return jsonify({'success': False, 'message': '话语不存在'}), 404

    # 只能删除自己的话语
    if quote.user_id != user.id:
        return jsonify({'success': False, 'message': '无权删除他人的话语'}), 403

    db.session.delete(quote)
    db.session.commit()

    return jsonify({'success': True})


@quotes_bp.route('/api/quotes/categories')
@login_required
def get_categories():
    """API: 获取所有分类"""
    categories = QuoteGenerator.get_all_categories()
    return jsonify({
        'success': True,
        'categories': categories
    })
