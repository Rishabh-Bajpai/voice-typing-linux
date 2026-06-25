import os
import requests

SYSTEM_PROMPTS = {
    "grammar": (
        "You are a text cleaner. Fix grammar, punctuation, and capitalization "
        "in the following text. Do not change the meaning, word choice, or structure "
        "beyond what's needed for correctness. Return only the corrected text."
    ),
    "translate": (
        "You are a translator. Translate the following text into {language}. "
        "Preserve the meaning, tone, and formatting. Return only the translated text."
    ),
}


def llm_process(text, action="off", instruction=None):
    if action == "off" or not text:
        return text

    import voice_dictation as vd

    base_url = (vd.OPENAI_BASE_URL or os.getenv("OPENAI_BASE_URL", "")).rstrip("/")
    model = vd.OPENAI_CHAT_MODEL_ID or os.getenv("OPENAI_CHAT_MODEL_ID", "")
    api_key = vd.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", "")

    if not base_url or not model:
        print("[LLM] Missing OPENAI_BASE_URL or OPENAI_CHAT_MODEL_ID", flush=True)
        return text

    if action == "grammar":
        system = SYSTEM_PROMPTS["grammar"]
    elif action == "translate":
        lang = instruction or "Hindi"
        system = SYSTEM_PROMPTS["translate"].format(language=lang)
    elif action == "custom":
        system = instruction or "Fix the grammar and improve clarity."
    else:
        return text

    try:
        resp = requests.post(
            f"{base_url}/chat/completions",
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": text},
                ],
                "temperature": 0.1,
            },
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=15,
        )
        resp.raise_for_status()
        result = resp.json()["choices"][0]["message"]["content"].strip()
        return result
    except Exception as e:
        print(f"[LLM] Error: {e}", flush=True)
        return text
