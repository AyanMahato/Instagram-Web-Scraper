import os
import time
import requests
import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv(".env")

class Comment(BaseModel):
    author_username: str
    comment_text: str
    timestamp: datetime.datetime

class Post(BaseModel):
    post_url: str
    author_username: str
    author_follower_count: int
    post_content: str
    timestamp: datetime.datetime
    like_count: int
    comment_count: int
    view_count: Optional[int] = None
    media_urls: List[str]
    comments: List[Comment] = []

class Profile(BaseModel):
    username: str
    follower_count: int
    following_count: int
    post_count: int
    bio_text: Optional[str] = None
    external_url: Optional[str] = None
    recent_posts: List[Post]

class InstagramScraperNodeParams(BaseModel):
    search_type: Literal['Hashtag', 'Keyword Search', 'User Profile']
    search_term: str
    posts_limit: int = Field(default=100, gt=0, le=1000)
    timeframe: Literal['Last 24 hours', 'Last 7 days', 'Last 30 days', 'Last 6 months', 'Any time'] = 'Any time'
    include_comments: bool = False
    comments_per_post_limit: int = Field(default=20, gt=0, le=200)
    location: Optional[str] = None

class InstagramScraperNode:
    def __init__(self, params: InstagramScraperNodeParams):
        self.params = params
        self.api_key = os.getenv("INSTAGRAM_SCRAPER_API_KEY")
        self.actor_id = os.getenv("INSTAGRAM_SCRAPER_ACTOR_ID")

        if not self.api_key:
            raise Exception("Missing Apify API key")
        if not self.actor_id:
            raise Exception("Missing Actor ID")

    def execute(self) -> dict:
        search_type_map = {
            "Hashtag": "hashtag",
            "Keyword Search": "keyword",
            "User Profile": "profile"
        }
        search_type = search_type_map[self.params.search_type]

        payload = {
            "searchType": search_type,
            "search": self.params.search_term,
            "resultsLimit": self.params.posts_limit,
            "addComments": self.params.include_comments,
            "commentsLimit": self.params.comments_per_post_limit,
        }

        run_url = f"https://api.apify.com/v2/acts/{self.actor_id}/runs"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        response = requests.post(run_url, headers=headers, json=payload)
        if response.status_code != 201:
            raise Exception(f"Failed to start Apify actor. Response: {response.text}")

        run_id = response.json().get("data", {}).get("id")
        if not run_id:
            raise Exception("No run ID returned by Apify actor.")

        status_url = f"https://api.apify.com/v2/actor-runs/{run_id}"
        for _ in range(60):
            status_response = requests.get(status_url, headers=headers).json()
            status = status_response['data']['status']
            if status == 'SUCCEEDED':
                dataset_id = status_response['data']['defaultDatasetId']
                break
            elif status == 'FAILED':
                raise Exception("Apify actor run failed.")
            time.sleep(5)
        else:
            raise Exception("Timeout: Apify actor run did not finish within 60 seconds.")

        data_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?format=json&clean=1"
        data = requests.get(data_url, headers=headers).json()

        if not data:
            raise Exception("No data returned from Apify dataset.")

        results = []
        for item in data:
            if self.params.search_type == "User Profile":
                profile = Profile(
                    username=item['username'],
                    follower_count=item.get('followers', 0),
                    following_count=item.get('following', 0),
                    post_count=item.get('postsCount', 0),
                    bio_text=item.get('bio', ''),
                    external_url=item.get('externalUrl'),
                    recent_posts=[]
                )
                for post in item.get('latestPosts', []):
                    profile.recent_posts.append(self._parse_post(post))
                return {"instagram_results": profile.dict()}
            else:
                results.append(self._parse_post(item).dict())

        return {"instagram_results": results}

    def _parse_post(self, post):
        comments = []
        for c in post.get('comments', [])[:self.params.comments_per_post_limit]:
            comments.append(Comment(
                author_username=c.get('ownerUsername', 'unknown'),
                comment_text=c.get('text', ''),
                timestamp=datetime.datetime.fromisoformat(c.get('timestamp'))
            ))

        return Post(
            post_url=post.get('url'),
            author_username=post.get('ownerUsername'),
            author_follower_count=post.get('ownerFollowers', 0),
            post_content=post.get('caption', ''),
            timestamp=datetime.datetime.fromisoformat(post.get('timestamp')),
            like_count=post.get('likesCount', 0),
            comment_count=post.get('commentsCount', 0),
            view_count=post.get('videoViewCount'),
            media_urls=post.get('imageUrls', []),
            comments=comments
        )
