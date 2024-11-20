import streamlit as st
import sys
import os
import requests
import json
import re
from typing import Tuple, List, Dict
from dataclasses import dataclass
from pathlib import Path
import logging
from urllib.parse import urlencode

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class VideoVariant:
    """Represents a video variant with different bitrate and quality"""
    bitrate: int
    url: str
    content_type: str

class TwitterAPIError(Exception):
    """Custom exception for Twitter API related errors"""
    pass

class TwitterAPIClient:
    """A client for interacting with the Twitter/X API.
    This class handles authentication and API interactions with Twitter/X platform,
    including bearer token retrieval, guest token authentication, and tweet data fetching.
    Attributes:
        BASE_URL (str): Base URL for Twitter's GraphQL API
        ACTIVATE_URL (str): URL for guest token activation
        MAINJS_URL (str): URL for Twitter's main JavaScript file containing bearer token
        session (requests.Session): Session object for making HTTP requests
        bearer_token (str): Bearer token for API authentication
        guest_token (str): Guest token for API authentication
    Methods:
        authenticate(): Obtains necessary authentication tokens
        get_tweet_details(tweet_id): Retrieves detailed information about a specific tweet
    Raises:
        TwitterAPIError: When API requests fail or authentication fails
        requests.RequestException: When HTTP requests fail
    Example:
        client = TwitterAPIClient()
        client.authenticate()
        tweet_data = client.get_tweet_details("1234567890")
    """
    """Handles authentication and API interactions with Twitter"""
    
    BASE_URL = "https://api.x.com/graphql/OoJd6A50cv8GsifjoOHGfg"
    ACTIVATE_URL = "https://api.twitter.com/1.1/guest/activate.json"
    MAINJS_URL = "https://abs.twimg.com/responsive-web/client-web/main.165ee22a.js"
    
    def __init__(self):
        self.session = requests.Session()
        self.bearer_token = None
        self.guest_token = None
        self._setup_session()
        
    def _setup_session(self):
        """Setup basic headers for request session"""
        self.session.headers.update({
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:84.0) Gecko/20100101 Firefox/84.0",
            "accept": "*/*",
            "accept-language": "de,en-US;q=0.7,en;q=0.3",
            "accept-encoding": "gzip, deflate, br",
            "te": "trailers",
        })

    def authenticate(self):
        """Get authentication tokens"""
        self.bearer_token = self._get_bearer_token()
        self.guest_token = self._get_guest_token()
        
        # Update session headers with tokens
        self.session.headers.update({
            "authorization": f"Bearer {self.bearer_token}",
            "x-guest-token": self.guest_token
        })

    def _get_bearer_token(self) -> str:
        """Extract bearer token from main.js"""
        try:
            response = self.session.get(self.MAINJS_URL)
            response.raise_for_status()
            
            bearer_tokens = re.findall(r'AAAAAAAAA[^"]+', response.text)
            if not bearer_tokens:
                raise TwitterAPIError("Could not find bearer token in main.js")
                
            return bearer_tokens[0]
            
        except requests.RequestException as e:
            logger.error(f"Failed to get bearer token: {e}")
            raise TwitterAPIError(f"Failed to get bearer token: {e}")

    def _get_guest_token(self) -> str:
        """Get guest token using bearer token"""
        try:
            self.session.headers.update({"authorization": f"Bearer {self.bearer_token}"})
            response = self.session.post(self.ACTIVATE_URL)
            response.raise_for_status()
            
            return response.json()["guest_token"]
            
        except requests.RequestException as e:
            logger.error(f"Failed to get guest token: {e}")
            raise TwitterAPIError(f"Failed to get guest token: {e}")
            
    def get_tweet_details(self, tweet_id: str) -> dict:
        """Get tweet details from Twitter API"""
        try:
            url = self._build_tweet_detail_url(tweet_id)
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to get tweet details: {e}")
            raise TwitterAPIError(f"Failed to get tweet details: {e}")

    def _build_tweet_detail_url(self, tweet_id: str) -> str:
        """Build the URL for tweet details API"""
        return f"{self.BASE_URL}/TweetResultByRestId?variables=%7B%22tweetId%22%3A%22{tweet_id}%22%2C%22withCommunity%22%3Afalse%2C%22includePromotedContent%22%3Afalse%2C%22withVoice%22%3Afalse%7D&features=%7B%22creator_subscriptions_tweet_preview_api_enabled%22%3Atrue%2C%22communities_web_enable_tweet_community_results_fetch%22%3Atrue%2C%22c9s_tweet_anatomy_moderator_badge_enabled%22%3Atrue%2C%22articles_preview_enabled%22%3Atrue%2C%22responsive_web_edit_tweet_api_enabled%22%3Atrue%2C%22graphql_is_translatable_rweb_tweet_is_translatable_enabled%22%3Atrue%2C%22view_counts_everywhere_api_enabled%22%3Atrue%2C%22longform_notetweets_consumption_enabled%22%3Atrue%2C%22responsive_web_twitter_article_tweet_consumption_enabled%22%3Atrue%2C%22tweet_awards_web_tipping_enabled%22%3Afalse%2C%22creator_subscriptions_quote_tweet_preview_enabled%22%3Afalse%2C%22freedom_of_speech_not_reach_fetch_enabled%22%3Atrue%2C%22standardized_nudges_misinfo%22%3Atrue%2C%22tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled%22%3Atrue%2C%22rweb_video_timestamps_enabled%22%3Atrue%2C%22longform_notetweets_rich_text_read_enabled%22%3Atrue%2C%22longform_notetweets_inline_media_enabled%22%3Atrue%2C%22rweb_tipjar_consumption_enabled%22%3Atrue%2C%22responsive_web_graphql_exclude_directive_enabled%22%3Atrue%2C%22verified_phone_label_enabled%22%3Afalse%2C%22responsive_web_graphql_skip_user_profile_image_extensions_enabled%22%3Afalse%2C%22responsive_web_graphql_timeline_navigation_enabled%22%3Atrue%2C%22responsive_web_enhance_cards_enabled%22%3Afalse%7D&fieldToggles=%7B%22withArticleRichContentState%22%3Atrue%2C%22withArticlePlainText%22%3Afalse%2C%22withGrokAnalyze%22%3Afalse%2C%22withDisallowedReplyControls%22%3Afalse%7D"


class TwitterVideoDownloader:
    """Main class for downloading Twitter videos"""
    
    def __init__(self):
        self.api_client = TwitterAPIClient()
        
    def download_video(self, tweet_url: str, output_dir: Path = None):
        """
        Download video from a tweet URL
        
        Args:
            tweet_url: URL of the tweet containing video
            output_dir: Directory to save the video (optional)
        """
        try:
            # Setup authentication
            self.api_client.authenticate()
            
            # Get tweet details
            tweet_id = self._extract_tweet_id(tweet_url)
            tweet_data = self.api_client.get_tweet_details(tweet_id)
            
            # Extract video variants
            video_variants = self._extract_video_variants(tweet_data)
            if not video_variants:
                raise ValueError("No video found in tweet")
                
            # Download videos
            self._download_video_variants(video_variants, tweet_id, output_dir)

            return video_variants, tweet_id
            
        except Exception as e:
            logger.error(f"Failed to download video: {e}")
            raise

    @staticmethod
    def _extract_tweet_id(tweet_url: str) -> str:
        """Extract tweet ID from tweet URL"""
        tweet_id = re.findall(r'(?<=status/)\d+', tweet_url)
        if not tweet_id:
            raise ValueError(f"Could not parse tweet ID from URL: {tweet_url}")
        return tweet_id[0]
    
    @staticmethod
    def _extract_video_variants(tweet_data: dict) -> List[VideoVariant]:
        """Extract video variants from tweet data"""
        try:
            media = tweet_data["data"]["tweetResult"]["result"]["legacy"]["entities"]["media"][0]
            variants = media["video_info"]["variants"]
            
            return [
                VideoVariant(
                    bitrate=variant.get("bitrate", 0),
                    url=variant["url"],
                    content_type=variant["content_type"]
                )
                for variant in variants
                if variant["content_type"] == "video/mp4"
            ]
        except (KeyError, IndexError) as e:
            logger.error(f"Failed to extract video variants: {e}")
            raise ValueError("Could not find video information in tweet data")

    def _download_video_variants(
        self,
        variants: List[VideoVariant],
        tweet_id: str,
        output_dir: Path = None
    ):
        """
        Download all video variants
        
        Args:
            variants: List of video variants to download
            tweet_id: ID of the tweet
            output_dir: Directory to save videos (optional)
        """
        output_dir = output_dir or Path.cwd()
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for variant in variants:
            output_path = output_dir / f"tweet_{tweet_id}_{variant.bitrate}.mp4"
            self._download_file(variant.url, output_path)
            logger.info(f"Downloaded video: {output_path}")

    @staticmethod
    def _download_file(url: str, output_path: Path):
        """
        Download file from URL with progress tracking
        
        Args:
            url: URL of the file to download
            output_path: Path where to save the file
        """
        try:
            with requests.get(url, stream=True) as response:
                response.raise_for_status()
                total_size = int(response.headers.get('content-length', 0))
                block_size = 8192
                
                with open(output_path, 'wb') as f:
                    if total_size == 0:
                        f.write(response.content)
                    else:
                        downloaded = 0
                        for chunk in response.iter_content(chunk_size=block_size):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                percentage = int((downloaded / total_size) * 100)
                                if percentage % 10 == 0:  # Log every 10%
                                    logger.info(f"Download progress: {percentage}%")
                                    
        except requests.RequestException as e:
            logger.error(f"Failed to download file: {e}")
            if output_path.exists():
                output_path.unlink()  # Delete partially downloaded file
            raise



st.title("Twitter Video Downloader")
st.write("Enter a tweet URL to download the video")

tweet_url = st.text_input("Tweet URL")
output_dir = Path.cwd()

if st.button("Start Parse"):
    try:
        downloader = TwitterVideoDownloader()
        video_variants, tweet_id = downloader.download_video(tweet_url)
        
        st.success("Video downloaded successfully!")
        
        # 为每个 MP4 视频生成一个下载按钮
        for i, variant in enumerate(video_variants):
            file_path = f"tweet_{tweet_id}_{variant.bitrate}.mp4"
            
            # 提供下载按钮
            with open(file_path, "rb") as file:
                st.download_button(
                    label=f"{file_path}",
                    data=file,
                    file_name=file_path,
                    mime="video/mp4"
                )
    except Exception as e:
        st.error(f"Download Error: {e}")


