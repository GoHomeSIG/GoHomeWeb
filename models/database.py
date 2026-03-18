"""
数据库模块 - SQLite 存储层
"""
import os
import json
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import Optional, List


class Base(DeclarativeBase):
    """数据库模型基类"""
    pass


# 初始化 SQLAlchemy
db = SQLAlchemy(model_class=Base)


class User(Base):
    """用户模型"""
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(nullable=False)
    hometown: Mapped[Optional[str]] = mapped_column(default='')
    current_city: Mapped[Optional[str]] = mapped_column(default='')
    leave_home_date: Mapped[Optional[str]] = mapped_column()  # YYYY-MM-DD format
    family_role: Mapped[Optional[str]] = mapped_column(default='妈妈')
    nickname: Mapped[Optional[str]] = mapped_column(default='')
    tone_style: Mapped[Optional[str]] = mapped_column(default='唠叨型')
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    checkins: Mapped[List["Checkin"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    badges: Mapped[List["Badge"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    custom_quotes: Mapped[List["Quote"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    ai_quotes: Mapped[List["AIQuote"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'username': self.username,
            'hometown': self.hometown or '',
            'current_city': self.current_city or '',
            'leave_home_date': self.leave_home_date,
            'family_role': self.family_role or '妈妈',
            'nickname': self.nickname or '',
            'tone_style': self.tone_style or '唠叨型',
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Checkin(Base):
    """签到记录模型"""
    __tablename__ = 'checkins'
    __table_args__ = (
        UniqueConstraint('user_id', 'checkin_date', name='uq_user_date'),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    checkin_date: Mapped[str] = mapped_column(nullable=False)  # YYYY-MM-DD format
    checkin_time: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    quote_content: Mapped[Optional[str]] = mapped_column()
    quote_category: Mapped[Optional[str]] = mapped_column(default='内置')
    quote_dialect: Mapped[Optional[str]] = mapped_column()

    # 关系
    user: Mapped["User"] = relationship(back_populates="checkins")

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'checkin_date': self.checkin_date,
            'checkin_time': self.checkin_time.isoformat() if self.checkin_time else None,
            'quote_content': self.quote_content,
            'quote_category': self.quote_category,
            'quote_dialect': self.quote_dialect
        }


class Badge(Base):
    """用户徽章模型"""
    __tablename__ = 'badges'
    __table_args__ = (
        UniqueConstraint('user_id', 'badge_id', name='uq_user_badge'),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    badge_id: Mapped[str] = mapped_column(nullable=False)
    earned_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # 关系
    user: Mapped["User"] = relationship(back_populates="badges")

    # 徽章定义
    BADGE_DEFINITIONS = {
        # 时间里程碑系列
        'day_1': {'name': '🌱 初来乍到', 'description': '离开家乡的第一天', 'category': 'time'},
        'day_7': {'name': '📅 七日维新', 'description': '坚持了一周', 'category': 'time'},
        'day_30': {'name': '🌙 满月之约', 'description': '离家一个月了', 'category': 'time'},
        'day_100': {'name': '🔄 百日征程', 'description': '百日纪念', 'category': 'time'},
        'day_180': {'name': '💫 半年光阴', 'description': '半年过去了', 'category': 'time'},
        'day_365': {'name': '🏆 一年归期', 'description': '离家一整年', 'category': 'time'},

        # 签到连续系列
        'streak_3': {'name': '🔥 三日热', 'description': '开始上瘾了', 'category': 'streak'},
        'streak_7': {'name': '⚡ 周冠军', 'description': '坚持一周！', 'category': 'streak'},
        'streak_15': {'name': '🌟 半月谈', 'description': '半个月不间断', 'category': 'streak'},
        'streak_30': {'name': '💪 月全勤', 'description': '整月打卡', 'category': 'streak'},
        'streak_100': {'name': '👑 签到之王', 'description': '传奇！', 'category': 'streak'},

        # 特殊成就系列
        'late_night': {'name': '🌙 深夜未眠', 'description': '这么晚还没睡', 'category': 'special'},
        'early_bird': {'name': '🌅 早起鸟儿', 'description': '起得真早', 'category': 'special'},
        'quote_master': {'name': '📝 思乡达人', 'description': '文采斐然', 'category': 'special'},
    }

    def to_dict(self):
        """转换为字典"""
        definition = self.BADGE_DEFINITIONS.get(self.badge_id, {})
        return {
            'id': self.id,
            'user_id': self.user_id,
            'badge_id': self.badge_id,
            'badge_name': definition.get('name', ''),
            'badge_description': definition.get('description', ''),
            'badge_category': definition.get('category', ''),
            'earned_at': self.earned_at.isoformat() if self.earned_at else None
        }

    @classmethod
    def get_definition(cls, badge_id: str):
        """获取徽章定义"""
        return cls.BADGE_DEFINITIONS.get(badge_id)


class Quote(Base):
    """话语模型（用户自定义）"""
    __tablename__ = 'quotes'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    content: Mapped[str] = mapped_column(nullable=False)
    category: Mapped[str] = mapped_column(default='个人')
    is_custom: Mapped[bool] = mapped_column(default=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # 关系
    user: Mapped["User"] = relationship(back_populates="custom_quotes")

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'content': self.content,
            'category': self.category,
            'is_custom': self.is_custom,
            'user_id': self.user_id
        }


class AIQuote(Base):
    """AI 生成的问候语模型"""
    __tablename__ = 'ai_quotes'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    content: Mapped[str] = mapped_column(nullable=False)
    family_role: Mapped[Optional[str]] = mapped_column()
    dialect: Mapped[Optional[str]] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # 关系
    user: Mapped["User"] = relationship(back_populates="ai_quotes")

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'content': self.content,
            'family_role': self.family_role,
            'dialect': self.dialect,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# 内置话语数据
BUILTIN_QUOTES = [
    {"id": 1, "content": "独在异乡为异客，每逢佳节倍思亲。", "category": "古诗"},
    {"id": 2, "content": "举头望明月，低头思故乡。", "category": "古诗"},
    {"id": 3, "content": "露从今夜白，月是故乡明。", "category": "古诗"},
    {"id": 4, "content": "春风又绿江南岸，明月何时照我还。", "category": "古诗"},
    {"id": 5, "content": "此夜曲中闻折柳，何人不起故园情。", "category": "古诗"},
    {"id": 6, "content": "故乡的歌是一支清远的笛，总在有月亮的晚上响起。", "category": "现代"},
    {"id": 7, "content": "故乡是游子心中的根，走得再远也割不断。", "category": "现代"},
    {"id": 8, "content": "每一朵游子的心中，都藏着一朵故乡的云。", "category": "现代"},
    {"id": 9, "content": "想家的时候，月亮是最圆的。", "category": "现代"},
    {"id": 10, "content": "世界上最暖的地方，是回家的路。", "category": "现代"},
    {"id": 11, "content": "胃知道回家的路，味蕾记得妈妈的味道。", "category": "现代"},
    {"id": 12, "content": "长大后才明白，最奢侈的不是远方，而是回家的车票。", "category": "现代"},
    {"id": 13, "content": "每次视频里看到父母的笑脸，都忍不住红了眼眶。", "category": "亲情"},
    {"id": 14, "content": "妈妈说：别担心，家里都好。可我知道，她最想说的是：你回来吧。", "category": "亲情"},
    {"id": 15, "content": "父亲的背影，是我见过最沉默的牵挂。", "category": "亲情"},
    {"id": 16, "content": "电话那头永远问不够的：吃饭了吗？穿暖了吗？什么时候回来？", "category": "亲情"},
    {"id": 17, "content": "小时候想逃离的地方，如今成了最想回去的地方。", "category": "感悟"},
    {"id": 18, "content": "原来，乡愁是一张小小的车票，我在这头，母亲在那头。", "category": "现代"},
    {"id": 19, "content": "城市越大，越容易迷路；离家越远，越容易想家。", "category": "感悟"},
    {"id": 20, "content": "打拼的路上，总有一盏灯为你而亮，那是家的方向。", "category": "感悟"},
]
