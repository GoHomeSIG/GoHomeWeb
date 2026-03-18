"""
数据库初始化脚本
"""
import os
import sqlite3
from flask import Flask
from models.database import db, User, Checkin, Badge, Quote, AIQuote, BUILTIN_QUOTES
from werkzeug.security import generate_password_hash
from datetime import datetime


def init_db(app: Flask):
    """初始化数据库"""
    db.init_app(app)

    with app.app_context():
        # 创建所有表
        db.create_all()

        # 检查是否已有数据（避免重复初始化）
        user_count = User.query.count()
        if user_count == 0:
            print("数据库为空，正在初始化...")
            initialize_data()
        else:
            print(f"数据库已存在，共有 {user_count} 个用户")


def initialize_data():
    """初始化示例数据"""
    from models.database import db

    # 1. 添加内置话语
    for quote_data in BUILTIN_QUOTES:
        quote = Quote(
            id=quote_data['id'],
            content=quote_data['content'],
            category=quote_data['category'],
            is_custom=False
        )
        db.session.add(quote)

    # 2. 创建测试用户 (demo 用户)
    demo_user = User(
        id=1,
        username='demo',
        password_hash=generate_password_hash('demo123'),
        hometown='湖南长沙',
        current_city='北京',
        leave_home_date='2025-10-06',
        family_role='妈妈',
        nickname='娃',
        tone_style='唠叨型',
        created_at=datetime(2026, 3, 13, 23, 53, 16, 504415)
    )
    db.session.add(demo_user)

    # 3. 创建测试签到记录
    test_checkins = [
        {'checkin_date': '2026-03-13', 'checkin_time': '2026-03-13T09:30:16.504727', 'quote_content': '独在异乡为异客，每逢佳节倍思亲。', 'quote_category': '古诗'},
        {'checkin_date': '2026-03-12', 'checkin_time': '2026-03-12T09:30:16.504727', 'quote_content': '举头望明月，低头思故乡。', 'quote_category': '古诗'},
        {'checkin_date': '2026-03-11', 'checkin_time': '2026-03-11T09:30:16.504727', 'quote_content': '露从今夜白，月是故乡明。', 'quote_category': '古诗'},
        {'checkin_date': '2026-03-09', 'checkin_time': '2026-03-09T09:30:16.504727', 'quote_content': '此夜曲中闻折柳，何人不起故园情。', 'quote_category': '古诗'},
    ]

    for checkin_data in test_checkins:
        checkin = Checkin(
            user_id=1,
            checkin_date=checkin_data['checkin_date'],
            checkin_time=datetime.fromisoformat(checkin_data['checkin_time']),
            quote_content=checkin_data['quote_content'],
            quote_category=checkin_data['quote_category']
        )
        db.session.add(checkin)

    # 4. 创建测试徽章
    test_badge = Badge(
        user_id=1,
        badge_id='late_night',
        earned_at=datetime.fromisoformat('2026-03-17T10:50:23.450057')
    )
    db.session.add(test_badge)

    db.session.commit()
    print("初始化完成！")
    print(f"  - 内置话语：{len(BUILTIN_QUOTES)} 条")
    print(f"  - 测试用户：1 个 (demo)")
    print(f"  - 测试签到：{len(test_checkins)} 条")
    print(f"  - 测试徽章：1 个")


def get_db_path():
    """获取数据库文件路径"""
    # 优先使用环境变量
    db_path = os.environ.get('DATABASE_URL', '')

    if db_path.startswith('sqlite:///'):
        db_path = db_path[10:]  # 移除 sqlite:/// 前缀

    # 默认路径
    if not db_path:
        db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'homesignin.db')
        db_path = os.path.abspath(db_path)

    return db_path


def create_app():
    """创建 Flask 应用（用于独立运行迁移脚本）"""
    from config import SECRET_KEY, DATABASE_URL, SQLALCHEMY_TRACK_MODIFICATIONS

    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS
    app.secret_key = SECRET_KEY

    # 初始化数据库绑定
    db.init_app(app)

    return app


if __name__ == '__main__':
    app = create_app()
    init_db(app)
    print(f"数据库文件：{get_db_path()}")
