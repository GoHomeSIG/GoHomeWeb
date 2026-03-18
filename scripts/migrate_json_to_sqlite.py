"""
JSON 到 SQLite 数据迁移脚本

用法：
    python scripts/migrate_json_to_sqlite.py

功能：
    将现有的 JSON 数据文件迁移到 SQLite 数据库
"""
import os
import sys
import json
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from werkzeug.security import generate_password_hash
from models.database import db, User, Checkin, Badge, Quote, AIQuote, BUILTIN_QUOTES
from utils.db_init import get_db_path


def create_migration_app():
    """创建用于迁移的 Flask 应用"""
    from config import SECRET_KEY, DATABASE_URL, SQLALCHEMY_TRACK_MODIFICATIONS

    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS
    app.secret_key = SECRET_KEY

    # 初始化数据库绑定
    db.init_app(app)

    return app


def load_json_data(data_dir, filename):
    """加载 JSON 文件"""
    filepath = os.path.join(data_dir, filename)
    if not os.path.exists(filepath):
        print(f"警告：{filepath} 不存在")
        return None

    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def migrate_users(data_dir):
    """迁移用户数据"""
    print("\n=== 迁移用户数据 ===")

    users_file = os.path.join(data_dir, 'users.json')
    if not os.path.exists(users_file):
        print("  跳过：users.json 不存在")
        return 0

    with open(users_file, 'r', encoding='utf-8') as f:
        users_data = json.load(f)

    count = 0
    for user_id, user_data in users_data.items():
        # 检查用户是否已存在
        existing = db.session.get(User, int(user_id))
        if existing:
            print(f"  跳过已存在的用户：{user_data.get('username')} (ID: {user_id})")
            continue

        user = User(
            id=int(user_id),
            username=user_data.get('username', ''),
            password_hash=user_data.get('password_hash', ''),
            hometown=user_data.get('hometown', ''),
            current_city=user_data.get('current_city', ''),
            leave_home_date=user_data.get('leave_home_date'),
            family_role=user_data.get('family_role', '妈妈'),
            nickname=user_data.get('nickname', ''),
            tone_style=user_data.get('tone_style', '唠叨型'),
            created_at=datetime.fromisoformat(user_data['created_at']) if user_data.get('created_at') else datetime.utcnow()
        )
        db.session.add(user)
        count += 1
        print(f"  迁移用户：{user.username} (ID: {user.id})")

    return count


def migrate_checkins():
    """迁移签到数据"""
    print("\n=== 迁移签到数据 ===")

    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    checkins_file = os.path.join(data_dir, 'checkins.json')
    if not os.path.exists(checkins_file):
        print("  跳过：checkins.json 不存在")
        return 0

    with open(checkins_file, 'r', encoding='utf-8') as f:
        checkins_data = json.load(f)

    count = 0
    for user_id, user_checkins in checkins_data.items():
        for checkin_data in user_checkins:
            # 检查是否已存在（通过 user_id + checkin_date 唯一约束）
            existing = db.session.execute(
                db.select(Checkin).filter_by(
                    user_id=int(user_id),
                    checkin_date=checkin_data.get('checkin_date')
                )
            ).first()

            if existing:
                continue

            checkin = Checkin(
                user_id=int(user_id),
                checkin_date=checkin_data.get('checkin_date'),
                checkin_time=datetime.fromisoformat(checkin_data['checkin_time']) if checkin_data.get('checkin_time') else datetime.utcnow(),
                quote_content=checkin_data.get('quote_content'),
                quote_category=checkin_data.get('quote_category', '内置'),
                quote_dialect=checkin_data.get('quote_dialect')
            )
            db.session.add(checkin)
            count += 1

    print(f"  迁移签到记录：{count} 条")
    return count


def migrate_badges():
    """迁移徽章数据"""
    print("\n=== 迁移徽章数据 ===")

    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    badges_file = os.path.join(data_dir, 'badges.json')
    if not os.path.exists(badges_file):
        print("  跳过：badges.json 不存在")
        return 0

    with open(badges_file, 'r', encoding='utf-8') as f:
        badges_data = json.load(f)

    count = 0
    for user_id, user_badges in badges_data.items():
        for badge_data in user_badges:
            # 检查是否已存在
            existing = db.session.execute(
                db.select(Badge).filter_by(
                    user_id=int(user_id),
                    badge_id=badge_data.get('badge_id')
                )
            ).first()

            if existing:
                continue

            badge = Badge(
                user_id=int(user_id),
                badge_id=badge_data.get('badge_id'),
                earned_at=datetime.fromisoformat(badge_data['earned_at']) if badge_data.get('earned_at') else datetime.utcnow()
            )
            db.session.add(badge)
            count += 1

    print(f"  迁移徽章：{count} 个")
    return count


def migrate_quotes():
    """迁移话语数据"""
    print("\n=== 迁移话语数据 ===")

    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    quotes_file = os.path.join(data_dir, 'quotes.json')
    if not os.path.exists(quotes_file):
        print("  跳过：quotes.json 不存在")
        return 0, 0

    with open(quotes_file, 'r', encoding='utf-8') as f:
        quotes_data = json.load(f)

    builtin_count = 0
    custom_count = 0

    # 迁移内置话语（如果数据库中还没有）
    existing_builtin = db.session.query(Quote).filter_by(is_custom=False).count()
    if existing_builtin == 0 and 'built_in' in quotes_data:
        for quote_data in quotes_data['built_in']:
            quote = Quote(
                id=quote_data.get('id'),
                content=quote_data.get('content'),
                category=quote_data.get('category', '个人'),
                is_custom=False
            )
            db.session.add(quote)
            builtin_count += 1
        print(f"  迁移内置话语：{builtin_count} 条")

    # 迁移用户自定义话语
    if 'custom' in quotes_data:
        for user_id, user_quotes in quotes_data['custom'].items():
            for quote_data in user_quotes:
                quote = Quote(
                    content=quote_data.get('content'),
                    category=quote_data.get('category', '个人'),
                    is_custom=True,
                    user_id=int(user_id)
                )
                db.session.add(quote)
                custom_count += 1

    if custom_count > 0:
        print(f"  迁移自定义话语：{custom_count} 条")

    return builtin_count, custom_count


def migrate_ai_quotes():
    """迁移 AI 问候数据"""
    print("\n=== 迁移 AI 问候数据 ===")

    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    ai_quotes_file = os.path.join(data_dir, 'ai_quotes.json')
    if not os.path.exists(ai_quotes_file):
        print("  跳过：ai_quotes.json 不存在")
        return 0

    with open(ai_quotes_file, 'r', encoding='utf-8') as f:
        ai_quotes_data = json.load(f)

    count = 0
    for user_id, user_quotes in ai_quotes_data.items():
        for quote_data in user_quotes:
            quote = AIQuote(
                user_id=int(user_id),
                content=quote_data.get('content'),
                family_role=quote_data.get('family_role'),
                dialect=quote_data.get('dialect'),
                created_at=datetime.fromisoformat(quote_data['created_at']) if quote_data.get('created_at') else datetime.utcnow()
            )
            db.session.add(quote)
            count += 1

    print(f"  迁移 AI 问候：{count} 条")
    return count


def verify_migration():
    """验证迁移结果"""
    print("\n=== 验证迁移结果 ===")

    user_count = db.session.query(User).count()
    checkin_count = db.session.query(Checkin).count()
    badge_count = db.session.query(Badge).count()
    builtin_quote_count = db.session.query(Quote).filter_by(is_custom=False).count()
    custom_quote_count = db.session.query(Quote).filter_by(is_custom=True).count()
    ai_quote_count = db.session.query(AIQuote).count()

    print(f"  用户数：{user_count}")
    print(f"  签到记录：{checkin_count}")
    print(f"  徽章：{badge_count}")
    print(f"  内置话语：{builtin_quote_count}")
    print(f"  自定义话语：{custom_quote_count}")
    print(f"  AI 问候：{ai_quote_count}")

    return {
        'users': user_count,
        'checkins': checkin_count,
        'badges': badge_count,
        'builtin_quotes': builtin_quote_count,
        'custom_quotes': custom_quote_count,
        'ai_quotes': ai_quote_count
    }


def main():
    """主函数"""
    print("=" * 50)
    print("JSON 到 SQLite 数据迁移")
    print("=" * 50)

    # 确定数据目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    data_dir = os.path.join(project_root, 'data')

    print(f"\n数据目录：{data_dir}")
    print(f"数据库文件：{get_db_path()}")

    # 创建应用
    app = create_migration_app()

    with app.app_context():
        # 创建表
        print("\n=== 创建数据库表 ===")
        db.create_all()
        print("  表创建完成")

        # 备份现有 JSON 数据
        backup_dir = os.path.join(data_dir, 'backup_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
        print(f"\n=== 备份 JSON 数据到 {backup_dir} ===")
        os.makedirs(backup_dir, exist_ok=True)

        for filename in ['users.json', 'checkins.json', 'badges.json', 'quotes.json', 'ai_quotes.json']:
            src = os.path.join(data_dir, filename)
            if os.path.exists(src):
                import shutil
                shutil.copy2(src, os.path.join(backup_dir, filename))
                print(f"  已备份：{filename}")

        # 执行迁移
        stats_before = verify_migration()

        print("\n=== 开始迁移 ===")
        migrate_users(data_dir)
        migrate_checkins()
        migrate_badges()
        migrate_quotes()
        migrate_ai_quotes()

        # 提交事务
        print("\n=== 提交事务 ===")
        db.session.commit()
        print("  提交完成")

        # 验证迁移
        stats_after = verify_migration()

        # 总结
        print("\n" + "=" * 50)
        print("迁移完成！")
        print("=" * 50)
        print(f"\n备份位置：{backup_dir}")
        print("\n数据统计:")
        for key, count in stats_after.items():
            print(f"  {key}: {count}")


if __name__ == '__main__':
    main()
