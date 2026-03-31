import os
import base64
import httpx
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
)


async def verify_payment_screenshot(image_bytes: bytes) -> tuple[bool, str]:
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            "Это скриншот подтверждения оплаты через СБП или банковского перевода. "
                            "Определи: является ли это реальным подтверждением успешной оплаты? "
                            "Ответь строго в формате:\n"
                            "РЕЗУЛЬТАТ: ДА или НЕТ\n"
                            "ПРИЧИНА: краткое объяснение на русском (1-2 предложения)."
                        )
                    },
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": image_b64
                        }
                    }
                ]
            }
        ]
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(GEMINI_URL, json=payload)
        response.raise_for_status()
        data = response.json()

    text = data["candidates"][0]["content"]["parts"][0]["text"]
    is_valid = "РЕЗУЛЬТАТ: ДА" in text.upper()
    reason = ""
    for line in text.strip().split("\n"):
        if line.upper().startswith("ПРИЧИНА:"):
            reason = line.split(":", 1)[1].strip()
            break

    return is_valid, reason
