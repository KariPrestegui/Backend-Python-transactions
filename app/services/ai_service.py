import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.config import get_env
from app.models.request_log import RequestLog

logger = logging.getLogger(__name__)

OPENAI_API_KEY = get_env("OPENAI_API_KEY")


async def summarize_text(db: Session, text: str) -> dict:
    if OPENAI_API_KEY:
        summary, model_used = await _call_openai(text)
    else:
        summary, model_used = _simulate_summary(text), "simulated"

    # Persist the request/response
    log_entry = RequestLog(
        request_text=text,
        response_text=summary,
        model_used=model_used,
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)

    logger.info("Summarization logged as RequestLog %s", log_entry.id)
    return {
        "summary": summary,
        "model_used": model_used,
        "request_id": log_entry.id,
    }

async def _call_openai(text: str) -> tuple[str, str]:
    from openai import AsyncOpenAI


    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    model = "gpt-3.5-turbo"

    response = await client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant that creates concise summaries "
                    "Respond with only the summary, no extra commentary"
                ),
            },
            {
                "role": "user",
                "content": f"Please summarize the following text:\n\n{text}",
            },
        ],
        temperature=0.3,
        max_tokens=500,
    )

    summary = response.choices[0].message.content.strip()
    return summary, model



def _simulate_summary(text: str) -> str:
    words = text.split()
    word_count = len(words)

    if word_count <= 20:
        return f"[Simulated] The text discusses: {text[:200]}"

    first_chunk = " ".join(words[:25])
    last_chunk = " ".join(words[-15:])
    return (
        f"[Simulated Summary] This text contains {word_count} words. "
        f'It begins with: "{first_chunk}…" '
        f'and concludes with: "…{last_chunk}".'
    )
