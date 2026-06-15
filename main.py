import os, httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

OR_KEY = os.environ.get("OPENROUTER_API_KEY", "")

# 依優先順序排列的免費模型，第一個失敗自動換下一個
FREE_MODELS = [
    "openrouter/owl-alpha",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "openai/gpt-oss-120b:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "moonshotai/kimi-k2:free",
    "meta-llama/llama-4-maverick:free",
]

class ReviewRequest(BaseModel):
    system: str
    user: str

@app.get("/")
def health():
    return {"status": "ok", "models": FREE_MODELS}

@app.post("/review")
async def review(req: ReviewRequest):
    if not OR_KEY:
        raise HTTPException(500, "Server: OPENROUTER_API_KEY not set")

    last_error = ""
    async with httpx.AsyncClient(timeout=120) as client:
        for model in FREE_MODELS:
            try:
                resp = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {OR_KEY}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://ifp-review.app",
                        "X-Title": "IFP Test Report Review",
                    },
                    json={
                        "model": model,
                        "max_tokens": 4000,
                        "messages": [
                            {"role": "system", "content": req.system},
                            {"role": "user",   "content": req.user},
                        ],
                    },
                )
                data = resp.json()

                # 429 rate limit → 換下一個
                if resp.status_code == 429:
                    last_error = f"{model}: rate limited"
                    continue

                text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                if text and text.strip():
                    return {"result": text, "model": model}

                err = data.get("error", {}).get("message", "empty response")
                last_error = f"{model}: {err}"

            except Exception as e:
                last_error = f"{model}: {e}"

    raise HTTPException(502, f"All models failed. Last error: {last_error}")
