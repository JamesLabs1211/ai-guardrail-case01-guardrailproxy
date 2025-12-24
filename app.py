import os
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from calypsoai import CalypsoAI

CALYPSOAI_URL = os.getenv("CALYPSOAI_URL", "<ai-guardrail-url>")
CALYPSOAI_TOKEN = os.getenv("CALYPSOAI_TOKEN")
CALYPSOAI_PROJECT_ID = os.getenv("CALYPSOAI_PROJECT_ID")  
DEFAULT_PROVIDER = os.getenv("DEFAULT_PROVIDER")  

if not CALYPSOAI_TOKEN:
    raise RuntimeError("CALYPSOAI_TOKEN must be set")

cai = CalypsoAI(url=CALYPSOAI_URL, token=CALYPSOAI_TOKEN)
app = FastAPI()

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: list[Message]
    model: str | None = None      
    provider: str | None = None   
    project: str | None = None
    max_tokens: int | None = 256

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/v1/chat/completions")
async def chat(req: ChatRequest):
    provider = req.provider or req.model or DEFAULT_PROVIDER
    if not provider and not (req.project or CALYPSOAI_PROJECT_ID):
        raise HTTPException(status_code=400, detail="provider/model or project must be set")

    user_prompt = next((m.content for m in reversed(req.messages) if m.role == "user"), "")

    send_kwargs = {}
    if provider:
        send_kwargs["provider"] = provider
    else:
        send_kwargs["project"] = req.project or CALYPSOAI_PROJECT_ID

    # Call Calypso AI Guardrail ONLY
    result = cai.prompts.send(user_prompt, **send_kwargs)
    data = result.model_dump()

    guardrail_result = data.get("result", {})
    outcome = guardrail_result.get("outcome")

    if outcome == "cleared":
        assistant_text = guardrail_result.get("response", "")
    else:
        calypso_type = str(data.get("type", "")).lower()
        label = "Response" if calypso_type == "response" else "Prompt"
        assistant_text = (
            f"{label} Rejected\n\n"
            f"The requested {label} was rejected by F5 AI Guardrail because it violated "
            "the company's AI security policy."
        )

    return {
        "id": data.get("id", "guardrail-gw"),
        "object": "chat.completion",
        "created": int(time.time()),
        "model": provider or "guardrail",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": assistant_text},
                "finish_reason": "stop",
            }
        ],
        "usage": data.get("usage", None),
    }
