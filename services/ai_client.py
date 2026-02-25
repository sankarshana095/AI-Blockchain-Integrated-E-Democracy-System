import os
import json
from openai import OpenAI


GROK_API_KEY = os.getenv("GROK_API_KEY")

MODEL_NAME = "grok-4-1-fast-reasoning"
class AIClientError(Exception):
    pass


def _get_client():
    if not GROK_API_KEY:
        raise AIClientError("GROK_API_KEY not configured")

    return OpenAI(
        api_key=GROK_API_KEY,
        base_url="https://api.x.ai/v1"
    )


# -------- POLICY ANALYSIS (JSON OUTPUT) --------
def run_policy_analysis(prompt: str) -> dict:
    try:
        client = _get_client()

        response = client.chat.completions.create(
            model=MODEL_NAME,
            temperature=0.2,
            messages=[
                {
                    "role": "system",
                    "content": "You are a policy analysis AI. Always respond with valid JSON only."
                },
                {"role": "user", "content": prompt}
            ]
        )

        content = response.choices[0].message.content.strip()
        return json.loads(content)

    except Exception as e:
        raise AIClientError(f"Grok AI error: {str(e)}")


# -------- COMMENT REPLY (TEXT OUTPUT) --------
def run_comment_reply(prompt: str) -> str:
    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=MODEL_NAME,
            temperature=0.3,
            messages=[
                {
                    "role": "system",
                    "content": "You generate concise, helpful civic discussion replies."
                },
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        raise AIClientError(f"Grok AI error: {str(e)}")