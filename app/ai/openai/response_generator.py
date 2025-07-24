# response_generator.py
from ...config import config
from .openai_client import get_chat_completion
from .utils import clean_response

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def generate_response(prompt, system_message="You are a helpful assistant."):
    #return prompt+"--"+system_message
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": prompt}
    ]
    try:
        raw_response, usage = get_chat_completion(
            messages=messages,
            model=config.OPENAI_MODEL,
            temperature=config.OPENAI_TEMPERATURE,
            max_tokens=config.OPENAI_MAX_TOKENS
        )
        return clean_response(raw_response)
    except RuntimeError as e:
        # Optionally log the error here
        return f"[Error] {str(e)}"