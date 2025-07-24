# media_handler.py

import os
import httpx
import aiofiles
from typing import List, Optional
from urllib.parse import urlparse
from ..config import config
from ..utils.logger import setup_logger
from ..utils.helpers import get_tweet_media_dir

logger = setup_logger(__name__)


class MediaHandler:
    def __init__(self):
        self.timeout = config.media_download_timeout

    async def download_tweet_media(self, tweet_id: str, media_urls: List[str]) -> List[str]:
        """Download all media files for a tweet"""
        if not media_urls:
            return []

        media_dir = get_tweet_media_dir(tweet_id)
        os.makedirs(media_dir, exist_ok=True)

        downloaded_paths = []

        for i, url in enumerate(media_urls):
            try:
                file_path = await self._download_single_media(url, media_dir, f"media_{i}")
                if file_path:
                    downloaded_paths.append(file_path)
                    logger.info(f"Downloaded media: {file_path}")
            except Exception as e:
                logger.error(f"Failed to download media {url}: {str(e)}")
                continue

        logger.info(f"Downloaded {len(downloaded_paths)} media files for tweet {tweet_id}")
        return downloaded_paths

    async def _download_single_media(self, url: str, media_dir: str, filename_prefix: str) -> Optional[str]:
        """Download a single media file"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()

                # Determine file extension from URL or content type
                extension = self._get_file_extension(url, response.headers.get('content-type'))
                filename = f"{filename_prefix}{extension}"
                file_path = os.path.join(media_dir, filename)

                async with aiofiles.open(file_path, 'wb') as f:
                    await f.write(response.content)

                return file_path

        except Exception as e:
            logger.error(f"Error downloading {url}: {str(e)}")
            return None

    def _get_file_extension(self, url: str, content_type: Optional[str] = None) -> str:
        """Determine file extension from URL or content type"""
        # Try to get extension from URL
        parsed_url = urlparse(url)
        path = parsed_url.path
        if '.' in path:
            return os.path.splitext(path)[1]

        # Try to get extension from content type
        if content_type:
            if 'image/jpeg' in content_type or 'image/jpg' in content_type:
                return '.jpg'
            elif 'image/png' in content_type:
                return '.png'
            elif 'image/gif' in content_type:
                return '.gif'
            elif 'video/mp4' in content_type:
                return '.mp4'

        # Default extension
        return '.jpg'

    def get_media_files(self, tweet_id: str) -> List[str]:
        """Get list of downloaded media files for a tweet"""
        media_dir = get_tweet_media_dir(tweet_id)
        if not os.path.exists(media_dir):
            return []

        files = []
        for filename in os.listdir(media_dir):
            file_path = os.path.join(media_dir, filename)
            if os.path.isfile(file_path):
                files.append(file_path)

        return files