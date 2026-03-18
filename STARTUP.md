# 思乡签到 - 快速启动指南

## 方式一：使用启动脚本（推荐）

```bash
# 安装依赖
./start.sh

# 然后手动启动后端和前端（见下方）
```

## 方式二：手动启动

### 1. 安装依赖

**后端：**
```bash
pip3 install -r requirements.txt
```

**前端：**
```bash
cd frontend
npm install
```

### 2. 启动服务

需要打开**两个终端**：

**终端 1 - 启动后端：**
```bash
python3 app.py
```
后端将在 http://localhost:5001 启动

**终端 2 - 启动前端：**
```bash
cd frontend
npm run dev
```
前端将在 http://localhost:3000 启动

### 3. 访问应用

打开浏览器访问：**http://localhost:3000**

## 测试账号

| 用户名 | 密码 |
|--------|------|
| `demo` | `demo123` |

## 常见问题

### Q: 端口被占用怎么办？
**A:** 可以通过环境变量修改端口：
```bash
# 修改后端端口
PORT=5002 python3 app.py

# 修改前端端口
cd frontend
VITE_PORT=3001 npm run dev
```

### Q: 如何初始化数据库？
**A:** 首次启动时自动初始化。如需重新初始化，删除 `data/homesignin.db` 后重启后端即可。

### Q: 如何迁移原有的 JSON 数据？
**A:** 运行迁移脚本：
```bash
python3 scripts/migrate_json_to_sqlite.py
```

### Q: AI 功能如何使用？
**A:** 复制 `.env.example` 为 `.env`，配置相应的 API Key 即可。
