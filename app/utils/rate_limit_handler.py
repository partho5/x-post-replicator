# utils/rate_limit_handler.py

import tweepy
import requests
from typing import Optional, Dict, Any
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class RateLimitHandler:
    """Handles Twitter/X API rate limits and 429 errors"""
    
    @staticmethod
    def is_rate_limit_error(error) -> bool:
        """Check if the error is a rate limit error (429)"""
        if isinstance(error, tweepy.TooManyRequests):
            return True
        elif isinstance(error, tweepy.errors.TooManyRequests):
            return True
        elif hasattr(error, 'response') and error.response:
            return error.response.status_code == 429
        elif isinstance(error, requests.exceptions.HTTPError):
            return error.response.status_code == 429
        return False
    
    @staticmethod
    def get_rate_limit_info(error) -> Dict[str, Any]:
        """Extract rate limit information from error"""
        rate_limit_info = {
            "is_rate_limit": False,
            "reset_time": None,
            "remaining_requests": None,
            "limit": None,
            "retry_after": None
        }
        
        if RateLimitHandler.is_rate_limit_error(error):
            rate_limit_info["is_rate_limit"] = True
            
            # Try to extract reset time from headers
            if hasattr(error, 'response') and error.response:
                headers = error.response.headers
                rate_limit_info["reset_time"] = headers.get('x-rate-limit-reset')
                rate_limit_info["remaining_requests"] = headers.get('x-rate-limit-remaining')
                rate_limit_info["limit"] = headers.get('x-rate-limit-limit')
                rate_limit_info["retry_after"] = headers.get('retry-after')
            
            # For tweepy specific errors
            if hasattr(error, 'response') and hasattr(error.response, 'headers'):
                headers = error.response.headers
                rate_limit_info["reset_time"] = headers.get('x-rate-limit-reset')
                rate_limit_info["remaining_requests"] = headers.get('x-rate-limit-remaining')
                rate_limit_info["limit"] = headers.get('x-rate-limit-limit')
                rate_limit_info["retry_after"] = headers.get('retry-after')
        
        return rate_limit_info
    
    @staticmethod
    def log_rate_limit_error(error, operation: str = "API call"):
        """Log rate limit error with detailed information"""
        rate_limit_info = RateLimitHandler.get_rate_limit_info(error)
        
        if rate_limit_info["is_rate_limit"]:
            logger.error(f"🚫 RATE LIMIT HIT during {operation}")
            logger.error(f"   Reset time: {rate_limit_info['reset_time']}")
            logger.error(f"   Remaining requests: {rate_limit_info['remaining_requests']}")
            logger.error(f"   Limit: {rate_limit_info['limit']}")
            logger.error(f"   Retry after: {rate_limit_info['retry_after']} seconds")
            logger.error(f"   Error details: {str(error)}")
        else:
            logger.error(f"❌ API ERROR during {operation}: {str(error)}")
    
    @staticmethod
    def should_retry_after_rate_limit(error) -> bool:
        """Determine if we should retry after a rate limit error"""
        rate_limit_info = RateLimitHandler.get_rate_limit_info(error)
        
        if not rate_limit_info["is_rate_limit"]:
            return False
        
        # Don't retry if we don't have retry-after info
        if not rate_limit_info["retry_after"]:
            return False
        
        # Don't retry if retry-after is too long (more than 15 minutes)
        try:
            retry_after = int(rate_limit_info["retry_after"])
            if retry_after > 900:  # 15 minutes
                logger.warning(f"Rate limit retry time too long ({retry_after}s), skipping retry")
                return False
            return True
        except (ValueError, TypeError):
            return False 