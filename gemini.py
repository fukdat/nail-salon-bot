import os
import base64
import httpx
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


async def verify_payment_screenshot(image_bytes: bytes) -> tuple[bool, str]:
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    payload = {
        "model": "llama-3.2-11b-vision-preview",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Это скриншот подтверждения оплаты через СБП или банковского перевода. "
                            "Определи: является ли это реальным подтверждением успешной оплаты? "
                            "Ответь строго в формате:\n"
                            "РЕЗУЛЬТАТ: ДА или НЕТ\n"
                            "ПРИЧИНА: краткое объяснение на русском (1-2 предложения)."
                        )
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_b64}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 200,
    }

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(GROQ_URL, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    text = data["choices"][0]["message"]["content"]
    is_valid = "РЕЗУЛЬТАТ: ДА" in text.upper()
    reason = ""
    for line in text.strip().split("\n"):
        if line.upper().startswith("ПРИЧИНА:"):
            reason = line.split(":", 1)[1].strip()
            break

    return is_valid, reason
