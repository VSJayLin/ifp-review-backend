# IFP Test Report Review — Backend

FastAPI proxy server: 接收前端 HTML 的審核請求，轉發到 OpenRouter，
OpenRouter API Key 存在 Render 環境變數，前端看不到。

## 部署步驟

### 1. 把這個資料夾推上 GitHub

```bash
git init
git add .
git commit -m "init"
git remote add origin https://github.com/你的帳號/ifp-review-backend.git
git push -u origin main
```

### 2. Render 建立 Web Service

1. 登入 https://render.com
2. New → Web Service → Connect GitHub → 選這個 repo
3. 設定：
   - **Name**：ifp-review-backend（隨意）
   - **Runtime**：Python 3
   - **Build Command**：`pip install -r requirements.txt`
   - **Start Command**：`uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**：Free
4. Environment Variables → Add：
   - Key：`OPENROUTER_API_KEY`
   - Value：你的 OpenRouter API Key（sk-or-v1-...）
5. Create Web Service → 等待部署完成（約 2 分鐘）

### 3. 取得 Render URL

部署完成後會看到：`https://ifp-review-backend-xxxx.onrender.com`

把這個 URL 填入前端 HTML 的 `BACKEND_URL` 變數即可。

### 4. OpenRouter API Key 取得方式

1. 前往 https://openrouter.ai
2. 登入 → API Keys → Create Key
3. 免費，不需要信用卡

## 使用的免費模型（依優先順序）

1. openrouter/owl-alpha（1M context，目前評測最強）
2. nvidia/nemotron-3-super-120b-a12b:free（120B，1M context）
3. openai/gpt-oss-120b:free（120B，131K context）
4. nvidia/nemotron-3-ultra-550b-a55b:free（550B，1M context）
5. moonshotai/kimi-k2:free（fallback）
6. meta-llama/llama-4-maverick:free（fallback）

模型失敗時自動換下一個。

## 注意事項

- Render 免費方案閒置 15 分鐘後 spin down，第一次請求需等 30～60 秒冷啟動
- OpenRouter 免費模型限制：20 req/min，200 req/day（6 人輕度使用足夠）
