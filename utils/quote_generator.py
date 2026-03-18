import random
from models.database import db, Quote


class QuoteGenerator:
    """思乡话语生成器"""

    @staticmethod
    def get_random_quote(user_id=None):
        """获取随机一句思乡话语"""
        # 优先从内置话语中获取
        builtin_quotes = db.session.execute(
            db.select(Quote).filter_by(is_custom=False)
        ).scalars().all()

        if builtin_quotes:
            quote = random.choice(builtin_quotes)
            return {
                'id': quote.id,
                'content': quote.content,
                'category': quote.category
            }

        # 如果没有内置话语，返回默认
        return {
            'id': 0,
            'content': '家，是心中永远的港湾。',
            'category': '默认'
        }

    @staticmethod
    def get_quote_by_id(quote_id):
        """根据 ID 获取话语"""
        quote = db.session.get(Quote, quote_id)
        if quote:
            return {
                'id': quote.id,
                'content': quote.content,
                'category': quote.category
            }
        return None

    @staticmethod
    def get_quotes_by_category(category, user_id=None):
        """按分类获取话语"""
        quotes = db.session.execute(
            db.select(Quote).filter_by(category=category, is_custom=False)
        ).scalars().all()

        return [{
            'id': q.id,
            'content': q.content,
            'category': q.category
        } for q in quotes]

    @staticmethod
    def get_all_categories():
        """获取所有分类"""
        result = db.session.execute(
            db.select(Quote.category)
            .filter_by(is_custom=False)
            .distinct()
        ).scalars().all()
        return list(result)
