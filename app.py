from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
import httpx
import os

app = FastAPI()

BOT_TOKEN = os.getenv("BOT_TOKEN", "8644154655:AAFv3PZV6JYuNKBUp0WYYyLydCT-Q2zAAfc")
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID", "-1003955690487"))
INTERNAL_WEBHOOK_SECRET = os.getenv("INTERNAL_WEBHOOK_SECRET", "super-secret-key")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"


class CheckUserRequest(BaseModel):
    user_id: int


async def get_chat_member(chat_id: int, user_id: int) -> dict:
    url = f"{TELEGRAM_API}/getChatMember"
    payload = {
        "chat_id": chat_id,
        "user_id": user_id
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(url, json=payload)
        data = response.json()

    if not data.get("ok"):
        raise RuntimeError(
            f"Telegram error_code={data.get('error_code')}, "
            f"description={data.get('description')}"
        )

    return data["result"]


def is_allowed_status(status: str) -> bool:
    # Участником считаем обычного участника, админа и владельца
    return status in {"member", "administrator", "creator"}


@app.post("/check-user")
async def check_user(
    body: CheckUserRequest,
    x_webhook_secret: str | None = Header(default=None)
):
    if x_webhook_secret != INTERNAL_WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        member = await get_chat_member(GROUP_CHAT_ID, body.user_id)
        status = member.get("status", "unknown")

        return {
            "ok": True,
            "user_id": body.user_id,
            "in_group": status in {"member", "administrator", "creator"},
            "status": status
        }

    except Exception as e:
        return {
            "ok": False,
            "user_id": body.user_id,
            "in_group": False,
            "error": str(e)
        }