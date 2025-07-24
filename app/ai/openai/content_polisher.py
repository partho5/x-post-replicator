# content_polisher.py

import openai
from typing import Optional
from ...config import config
from ...utils.logger import setup_logger
from .response_generator import generate_response

logger = setup_logger(__name__)


class ContentPolisher:
    def __init__(self):
        openai.api_key = config.openai_api_key
        self.client = openai.OpenAI(api_key=config.openai_api_key)

    async def polish_tweet_text(self, original_text: str, tweet_type: int) -> Optional[str]:
        """Polish tweet text using OpenAI API"""
        try:
            # Create appropriate prompt based on tweet type
            prompt = self._create_polish_prompt(original_text, tweet_type)

            # Use safe Unicode printing with utf-8 encoding
            print(f"original_text={original_text}".encode('utf-8', errors='replace').decode('utf-8'))
            print(f"tweet_type={tweet_type}")

            polished_text = generate_response(prompt, "You are an expert social media content creator.")
            print(f"polished_text={polished_text}")

            # Safe Unicode printing
            print(polished_text.encode('utf-8', errors='replace').decode('utf-8'))

            # Ensure the polished text is within Twitter's character limit
            # Use proper Unicode-aware length calculation
            if len(polished_text) > 280:
                polished_text = polished_text[:277] + "..."

            logger.info(f"Successfully polished tweet text")
            return polished_text

        except UnicodeEncodeError as e:
            logger.error(f"Unicode encoding error: {str(e)}")
            # Return original text if Unicode issues occur
            return original_text
        except Exception as e:
            logger.error(f"Error polishing tweet text: {str(e)}")
            return None

    def _create_polish_prompt(self, text: str, tweet_type: int) -> str:
        """Create appropriate prompt based on tweet type"""
        type_instructions = {
            1: "Transform this general tweet into a unique, engaging perspective while keeping the core message",
            2: "Rewrite this promotional content with fresh language and unique angles while maintaining professionalism",
            3: "Rephrase this news tweet with original insights and unique perspective while keeping it informative",
            4: "Reimagine this personal tweet with authentic, unique expression while maintaining the personal touch",
            5: "This is a retweet - create a unique commentary or perspective on the original content",
            6: "This is part of a thread - make it more coherent and engaging with unique insights"
        }

        instruction = type_instructions.get(tweet_type, "Transform this tweet into unique, engaging content")

        prompt = f"""
        {instruction}.

        Original tweet: "{text}"

        IMPORTANT: Create a COMPLETELY UNIQUE version that:
        - Has different wording and structure from the original
        - Uses fresh perspectives and unique angles
        - Avoids any direct copying or similar phrasing
        - Maintains the core message but expresses it differently
        - Uses original insights and commentary

        Rules:
        - Keep it under 280 characters
        - Make it significantly different from the original
        - Use unique language and structure
        - Don't use any hashtags in the tweet
        - Don't change any URLs or mentions
        - Support Unicode characters (emojis, international text)
        - Add your own unique perspective or commentary

        Return only the polished tweet text, nothing else.
        """

        return prompt