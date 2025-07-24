# tweet_types.py

from enum import IntEnum


class TweetTypes(IntEnum):
    GENERAL = 1
    PROMOTIONAL = 2
    NEWS = 3
    PERSONAL = 4
    RETWEET = 5
    THREAD = 6

    @classmethod
    def get_name(cls, value: int) -> str:
        """Get descriptive name for tweet type"""
        names = {
            1: "GENERAL",
            2: "PROMOTIONAL",
            3: "NEWS",
            4: "PERSONAL",
            5: "RETWEET",
            6: "THREAD"
        }
        return names.get(value, "UNKNOWN")

    @property
    def UPPERCASE_NAMES(self) -> dict:
        return {
            1: "GENERAL",
            2: "PROMOTIONAL",
            3: "NEWS",
            4: "PERSONAL",
            5: "RETWEET",
            6: "THREAD"
        }