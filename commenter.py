import os
import re
import openai
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("GPT_MODEL", "gpt-4.1-nano")
MODERATION_ENABLED = os.getenv("MODERATION", "on").lower() != "off"


def moderate(text: str) -> bool:
    """Return True if text passes OpenAI moderation."""
    if not MODERATION_ENABLED:
        return True
    response = openai.Moderation.create(input=text)
    flagged = response["results"][0]["flagged"]
    return not flagged

def generate_comment(post_text: str) -> str:
    """
    Generate a short, positive, professional LinkedIn comment (≤30 words, ≤2 emojis).
    """
    if MODERATION_ENABLED and not moderate(post_text):
        raise ValueError("Post content flagged by moderation")
    prompt = (
        "Write a short, positive, professional LinkedIn comment (≤30 words, ≤2 emojis) "
        "in response to this post:\n\n\"\"\"\n"
        f"{post_text}\n"
        "\"\"\""
    )
    completion = openai.ChatCompletion.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful assistant that writes professional LinkedIn comments."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=60,
    )
    comment = completion.choices[0].message.content.strip()
    if MODERATION_ENABLED and not moderate(comment):
        raise ValueError("Generated comment flagged by moderation")
    return comment 