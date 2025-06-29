from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import logging
from instagram_scraper_node import InstagramScraperNode, InstagramScraperNodeParams

# Configure logger
logger = logging.getLogger("uvicorn")

app = FastAPI()


# === Request Models ===

class HashtagRequest(BaseModel):
    hashtag: str
    posts_limit: int = Field(default=10, gt=0, le=100)
    include_comments: bool = False
    comments_per_post_limit: int = Field(default=10, gt=0, le=100)
    timeframe: Optional[str] = "Any time"


class KeywordRequest(BaseModel):
    keyword: str
    posts_limit: int = Field(default=10, gt=0, le=100)
    include_comments: bool = False
    comments_per_post_limit: int = Field(default=10, gt=0, le=100)
    timeframe: Optional[str] = "Any time"


class ProfileRequest(BaseModel):
    username: str
    posts_limit: int = Field(default=10, gt=0, le=100)
    include_comments: bool = False
    comments_per_post_limit: int = Field(default=10, gt=0, le=100)
    timeframe: Optional[str] = "Any time"


# === Endpoints ===

@app.post("/scrape/hashtag")
def scrape_hashtag(data: HashtagRequest):
    logger.info(f"Starting hashtag scrape for #{data.hashtag}")
    try:
        params = InstagramScraperNodeParams(
            search_type="Hashtag",
            search_term=data.hashtag,
            posts_limit=data.posts_limit,
            include_comments=data.include_comments,
            comments_per_post_limit=data.comments_per_post_limit,
            timeframe=data.timeframe
        )
        result = InstagramScraperNode(params).execute()
        logger.info("Hashtag scrape successful")
        return result
    except Exception as e:
        logger.error(f"Hashtag scrape failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scrape/keyword")
def scrape_keyword(data: KeywordRequest):
    logger.info(f"Starting keyword search for {data.keyword}")
    try:
        params = InstagramScraperNodeParams(
            search_type="Keyword Search",
            search_term=data.keyword,
            posts_limit=data.posts_limit,
            include_comments=data.include_comments,
            comments_per_post_limit=data.comments_per_post_limit,
            timeframe=data.timeframe
        )
        result = InstagramScraperNode(params).execute()
        logger.info("Keyword search successful")
        return result
    except Exception as e:
        logger.error(f"Keyword search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scrape/profile")
def scrape_profile(data: ProfileRequest):
    logger.info(f"Starting profile scrape for @{data.username}")
    try:
        params = InstagramScraperNodeParams(
            search_type="User Profile",
            search_term=data.username,
            posts_limit=data.posts_limit,
            include_comments=data.include_comments,
            comments_per_post_limit=data.comments_per_post_limit,
            timeframe=data.timeframe  # Now also passed to apply `onlyPostsNewerThan`
        )
        result = InstagramScraperNode(params).execute()
        logger.info("Profile scrape successful")
        return result
    except Exception as e:
        logger.error(f"Profile scrape failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
