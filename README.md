# 115 文件整理 Web 工具

独立的 115 网盘文件整理系统，支持 115 Cookie、TMDB 识别、高级正则重命名、洗版预览、人工确认执行、操作日志和回滚。

## 第一版边界

- 不依赖 MoviePilot。
- 不包含 Docker。
- 不包含多用户登录。
- 不包含定时任务。
- 不自动删除旧文件。

## 安全原则

- 默认只生成预览，不执行真实 115 操作。
- 所有改名、移动、洗版都需要用户在预览页确认。
- 115 Cookie 和 TMDB API Key 脱敏显示，不写入日志。
- 回滚只针对本工具记录过且当前仍可反向操作的文件。

## 后端开发

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .[dev]
python -c "import fastapi, sqlalchemy, pydantic; print('backend deps ok')"
```

Task 1 阶段仅验证依赖导入；有测试用例后再运行 `pytest`。
后续 Task 2 创建 `app/main.py` 后再运行：

```powershell
pytest
uvicorn app.main:app --reload
```

## 前端开发

```powershell
cd frontend
npm install
npm run dev
```
