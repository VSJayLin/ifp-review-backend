import os, httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=".*",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
MODEL = "gemini-2.0-flash"

class ReviewRequest(BaseModel):
    system: str
    user: str

@app.get("/")
def health():
    return {"status": "ok", "model": MODEL}

@app.post("/review")
async def review(req: ReviewRequest):
    if not GEMINI_KEY:
        raise HTTPException(500, "Server: GEMINI_API_KEY not set")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            url,
            headers={"x-goog-api-key": GEMINI_KEY},
            json={
                "system_instruction": {"parts": [{"text": req.system}]},
                "contents": [{"role": "user", "parts": [{"text": req.user}]}],
                "generationConfig": {"maxOutputTokens": 8192, "temperature": 0.1}
            }
        )

    data = resp.json()

    if resp.status_code == 401 or resp.status_code == 403:
        raise HTTPException(401, f"Gemini API Key 無效：{data.get('error',{}).get('message','')}")
    if resp.status_code == 429:
        raise HTTPException(429, "Gemini 每分鐘額度已用完，請稍後再試。")
    if resp.status_code != 200:
        raise HTTPException(502, f"Gemini API 錯誤 {resp.status_code}：{data.get('error',{}).get('message', str(data)[:300])}")

    text = (data.get("candidates") or [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
    if not text.strip():
        raise HTTPException(502, "Gemini 回傳空白結果，請重試。")

    return {"result": text, "model": MODEL}
