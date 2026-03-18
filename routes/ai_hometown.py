from flask import Blueprint, request, jsonify, session
from routes.auth import login_required
from models.database import db, User, Quote
from config import AI_API_KEY, AI_API_BASE_URL, AI_MODEL

ai_hometown_bp = Blueprint('ai_hometown', __name__)


def get_generator():
    """获取 AI 生成器实例"""
    if not AI_API_KEY:
        return None
    from utils.ai_hometown_generator import AIHometownGenerator
    return AIHometownGenerator(
        api_key=AI_API_KEY,
        base_url=AI_API_BASE_URL,
        model=AI_MODEL
    )


@ai_hometown_bp.route('/api/ai-quote/generate', methods=['POST'])
@login_required
def generate():
    """API: 生成 AI 思乡话语"""
    generator = get_generator()

    if not generator:
        return jsonify({
            'success': False,
            'message': '请先配置 API Key'
        }), 503

    data = request.get_json()
    location = data.get('location', '').strip() if data else ''
    category = data.get('category', 'daily')

    if not location:
        return jsonify({
            'success': False,
            'message': '请输入家乡地点'
        }), 400

    # 生成话语
    result = generator.generate(location, category)

    if result:
        return jsonify({
            'success': True,
            'data': result
        })
    else:
        return jsonify({
            'success': False,
            'message': '生成失败，请稍后重试'
        }), 500


@ai_hometown_bp.route('/api/ai-quote/generate-batch', methods=['POST'])
@login_required
def generate_batch():
    """API: 批量生成 AI 思乡话语"""
    generator = get_generator()

    if not generator:
        return jsonify({
            'success': False,
            'message': '请先配置 API Key'
        }), 503

    data = request.get_json()
    location = data.get('location', '').strip() if data else ''

    if not location:
        return jsonify({
            'success': False,
            'message': '请输入家乡地点'
        }), 400

    # 批量生成
    results = generator.generate_batch(location)

    if results:
        return jsonify({
            'success': True,
            'data': results
        })
    else:
        return jsonify({
            'success': False,
            'message': '生成失败，请稍后重试'
        }), 500


@ai_hometown_bp.route('/api/ai-quote/save', methods=['POST'])
@login_required
def save_quote():
    """API: 保存 AI 生成的话语"""
    data = request.get_json()
    content = data.get('content', '').strip() if data else ''
    category = data.get('category', 'AI 生成').strip()

    if not content:
        return jsonify({
            'success': False,
            'message': '话语内容不能为空'
        }), 400

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
            'category': quote.category
        }
    })


@ai_hometown_bp.route('/api/ai-quote/history')
@login_required
def get_history():
    """API: 获取 AI 生成历史"""
    user = db.session.get(User, session['user_id'])
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404

    # 获取用户的所有自定义话语
    quotes = db.session.execute(
        db.select(Quote)
        .filter_by(user_id=user.id, is_custom=True)
        .order_by(Quote.created_at.desc())
    ).scalars().all()

    ai_categories = ['AI 生成', '饮食关怀', '天气问候', '节日思念', '日常问候', '思乡诗句', '童年回忆']
    ai_quotes = [q.to_dict() for q in quotes if q.category in ai_categories]

    return jsonify({
        'success': True,
        'quotes': ai_quotes
    })


@ai_hometown_bp.route('/api/ai-quote/categories')
@login_required
def get_categories():
    """API: 获取可用的生成分类"""
    generator = get_generator()
    categories = []
    if generator:
        categories = generator.get_available_categories()

    return jsonify({
        'success': True,
        'categories': categories
    })
