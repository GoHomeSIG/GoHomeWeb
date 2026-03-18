# 后端重构设计文档

## 概述

将 HomeSignin 项目从混合架构重构为纯前后端分离架构，并将数据存储从 JSON 文件迁移到 SQLite。

## 当前架构问题

### 1. 前后端混合
- `templates/` 目录包含 14 个 HTML 模板文件
- `static/` 目录包含 CSS/JS 静态资源
- Routes 中 `render_template` 调用混合了前后端逻辑
- 同时存在 Vue 3 前端和 Flask 模板两套 UI 系统

### 2. JSON 存储局限性
- 无事务支持，并发写入可能丢失数据
- 无查询优化，全表扫描效率低
- 无外键约束，数据完整性依赖代码维护
- 数据迁移/备份困难

## 目标架构

```
┌─────────────────┐     REST API      ┌─────────────────┐
│   Vue 3 SPA     │ ◄──────────────► │   Flask Backend │
│   (frontend/)   │    JSON Response  │   (Pure API)    │
└─────────────────┘                   └────────┬────────┘
                                               │
                                        ┌─────▼─────┐
                                        │  SQLite   │
                                        │ Database  │
                                        └───────────┘
```

## 实施步骤

### 第一阶段：数据库设计与迁移

#### 1.1 数据库 Schema 设计

**users 表**
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    hometown TEXT,
    current_city TEXT,
    leave_home_date DATE,
    family_role TEXT DEFAULT '妈妈',
    nickname TEXT,
    tone_style TEXT DEFAULT '唠叨型',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**checkins 表**
```sql
CREATE TABLE checkins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    checkin_date DATE NOT NULL,
    checkin_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    quote_content TEXT,
    quote_category TEXT DEFAULT '内置',
    quote_dialect TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, checkin_date)
);
```

**badges 表**
```sql
CREATE TABLE badges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    badge_id TEXT NOT NULL,
    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, badge_id)
);
```

**quotes 表**
```sql
CREATE TABLE quotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    category TEXT NOT NULL,
    is_custom BOOLEAN DEFAULT FALSE,
    user_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);
```

**ai_quotes 表**
```sql
CREATE TABLE ai_quotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    family_role TEXT,
    dialect TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

#### 1.2 数据库工具类

创建 `utils/database.py`：
- 数据库初始化
- 连接管理
- 迁移脚本支持

#### 1.3 数据迁移脚本

创建 `scripts/migrate_json_to_sqlite.py`：
- 读取现有 JSON 数据
- 转换并插入 SQLite
- 验证数据完整性

### 第二阶段：后端 API 重构

#### 2.1 删除模板相关代码

- 删除 `templates/` 目录
- 删除 `static/` 目录
- 移除 routes 中所有 `render_template` 调用
- 移除 `flash` 调用（改为 API 响应）

#### 2.2 Route 改造清单

| 文件 | 当前函数 | 改造方式 |
|------|----------|----------|
| `auth.py` | `index()` | 删除（首页由前端处理） |
| `auth.py` | `register()` | 保留 API，移除模板渲染 |
| `auth.py` | `login()` | 保留 API，移除模板渲染 |
| `auth.py` | `logout()` | 保持 API |
| `dashboard.py` | `index()` | 删除（由前端 Vue 路由处理） |
| `dashboard.py` | `profile()` | 删除（由前端 Vue 路由处理） |
| `checkin.py` | `do_checkin()` | 删除（已有 `/api/checkin`） |
| `checkin.py` | `history()` | 删除（已有 `/api/checkin/history`） |

#### 2.3 新增/完善 API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/dashboard` | GET | 获取仪表盘数据（统计、周历等） |
| `/api/badges` | GET | 获取用户徽章列表 |
| `/api/quotes` | GET | 获取话语列表 |
| `/api/quotes` | POST | 添加自定义话语 |
| `/api/ai-quote/generate` | POST | AI 生成思乡话语 |

### 第三阶段：前端适配

#### 3.1 API 客户端更新

- 更新 `frontend/src/api/` 调用
- 统一错误处理
- 添加响应拦截器

#### 3.2 路由完善

- 确保所有前端路由正常工作
- 添加 404 页面处理

### 第四阶段：清理与验证

#### 4.1 清理工作

- 删除废弃的模板文件
- 删除废弃的静态资源
- 更新依赖配置

#### 4.2 验证清单

- [ ] 所有 API 端点测试通过
- [ ] 前端功能正常运行
- [ ] 数据迁移完整
- [ ] 单元测试通过
- [ ] 部署配置更新

## 技术选型

### SQLite 配置

- 使用 Flask-SQLAlchemy 作为 ORM
- 使用 Alembic 管理数据库迁移
- 开发环境：本地 SQLite 文件
- 生产环境：可无缝切换到 PostgreSQL

### 依赖更新

**requirements.txt 新增：**
```
Flask-SQLAlchemy>=3.0
SQLAlchemy>=2.0
Flask-Migrate>=4.0
```

## 数据迁移策略

1. **备份现有 JSON 数据**
2. **创建 SQLite 数据库**
3. **运行迁移脚本导入数据**
4. **验证数据完整性**
5. **保留 JSON 文件作为备份（不删除）**

## 风险与缓解

| 风险 | 缓解措施 |
|------|----------|
| 数据丢失 | 迁移前完整备份 JSON 文件 |
| API 不兼容 | 保持现有 API 响应格式 |
| 前端功能异常 | 完整测试所有前端页面 |
| 并发问题 | SQLite 支持事务，优于 JSON |

## 时间估算

- 第一阶段（数据库）：2-3 小时
- 第二阶段（后端重构）：3-4 小时
- 第三阶段（前端适配）：1-2 小时
- 第四阶段（验证测试）：1-2 小时

**总计：7-11 小时**
