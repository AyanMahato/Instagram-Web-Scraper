import pytest
from unittest.mock import patch, MagicMock
from instagram_scraper_node import InstagramScraperNode, InstagramScraperNodeParams

@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("INSTAGRAM_SCRAPER_API_KEY", "test_token")
    monkeypatch.setenv("INSTAGRAM_SCRAPER_ACTOR_ID", "apify/instagram-scraper")

@pytest.fixture
def basic_params():
    return InstagramScraperNodeParams(
        search_type="Hashtag",
        search_term="test",
        posts_limit=5,
        include_comments=False,
        comments_per_post_limit=10
    )

def test_missing_api_key(monkeypatch):
    monkeypatch.delenv("INSTAGRAM_SCRAPER_API_KEY", raising=False)
    monkeypatch.setenv("INSTAGRAM_SCRAPER_ACTOR_ID", "dummy")
    with pytest.raises(Exception, match="Missing Apify API key"):
        InstagramScraperNode(basic_params)

def test_missing_actor_id(monkeypatch):
    monkeypatch.setenv("INSTAGRAM_SCRAPER_API_KEY", "token")
    monkeypatch.delenv("INSTAGRAM_SCRAPER_ACTOR_ID", raising=False)
    with pytest.raises(Exception, match="Missing Actor ID"):
        InstagramScraperNode(basic_params)

@patch("instagram_scraper_node.requests.post")
def test_actor_start_failure(mock_post, mock_env, basic_params):
    mock_post.return_value.status_code = 400
    mock_post.return_value.text = "Bad Request"
    node = InstagramScraperNode(basic_params)
    with pytest.raises(Exception, match="Failed to start Apify actor"):
        node.execute()

@patch("instagram_scraper_node.requests.post")
@patch("instagram_scraper_node.requests.get")
def test_actor_timeout(mock_get, mock_post, mock_env, basic_params):
    mock_post.return_value.status_code = 201
    mock_post.return_value.json.return_value = {"data": {"id": "run123"}}
    mock_get.return_value.json.return_value = {"data": {"status": "RUNNING"}}
    node = InstagramScraperNode(basic_params)
    with patch("time.sleep", return_value=None):
        with pytest.raises(Exception, match="Timeout: Apify actor run did not finish within 60 seconds"):
            node.execute()

@patch("instagram_scraper_node.requests.post")
@patch("instagram_scraper_node.requests.get")
def test_actor_failure(mock_get, mock_post, mock_env, basic_params):
    mock_post.return_value.status_code = 201
    mock_post.return_value.json.return_value = {"data": {"id": "run123"}}
    mock_get.return_value.json.return_value = {"data": {"status": "FAILED"}}
    node = InstagramScraperNode(basic_params)
    with patch("time.sleep", return_value=None):
        with pytest.raises(Exception, match="Apify actor run failed"):
            node.execute()

@patch("instagram_scraper_node.requests.post")
@patch("instagram_scraper_node.requests.get")
def test_no_data(mock_get, mock_post, mock_env, basic_params):
    mock_post.return_value.status_code = 201
    mock_post.return_value.json.return_value = {"data": {"id": "run123"}}
    mock_get.side_effect = [
        MagicMock(json=lambda: {"data": {"status": "SUCCEEDED", "defaultDatasetId": "dataset123"}}),
        MagicMock(json=lambda: [])
    ]
    node = InstagramScraperNode(basic_params)
    with pytest.raises(Exception, match="No data returned from Apify dataset"):
        node.execute()

@patch("instagram_scraper_node.requests.post")
@patch("instagram_scraper_node.requests.get")
def test_basic_hashtag_scrape(mock_get, mock_post, mock_env, basic_params):
    mock_post.return_value.status_code = 201
    mock_post.return_value.json.return_value = {"data": {"id": "run123"}}
    mock_get.side_effect = [
        MagicMock(json=lambda: {"data": {"status": "SUCCEEDED", "defaultDatasetId": "dataset123"}}),
        MagicMock(json=lambda: [{
            "url": "https://insta.com/p/abc",
            "ownerUsername": "user123",
            "ownerFollowers": 1234,
            "caption": "caption here",
            "timestamp": "2024-06-01T00:00:00",
            "likesCount": 20,
            "commentsCount": 3,
            "imageUrls": ["https://cdn.com/pic.jpg"],
            "comments": []
        }])
    ]
    node = InstagramScraperNode(basic_params)
    result = node.execute()
    assert result["instagram_results"][0]["author_username"] == "user123"

@patch("instagram_scraper_node.requests.post")
@patch("instagram_scraper_node.requests.get")
def test_user_profile_scrape(mock_get, mock_post, mock_env):
    params = InstagramScraperNodeParams(
        search_type="User Profile",
        search_term="user42",
        posts_limit=3,
        include_comments=True,
        comments_per_post_limit=2
    )
    mock_post.return_value.status_code = 201
    mock_post.return_value.json.return_value = {"data": {"id": "run321"}}
    mock_get.side_effect = [
        MagicMock(json=lambda: {"data": {"status": "SUCCEEDED", "defaultDatasetId": "d123"}}),
        MagicMock(json=lambda: [{
            "username": "user42",
            "followers": 15000,
            "following": 800,
            "postsCount": 50,
            "bio": "Traveler & Foodie",
            "externalUrl": "http://example.com",
            "latestPosts": [{
                "url": "https://insta.com/p/xyz",
                "ownerUsername": "user42",
                "ownerFollowers": 15000,
                "caption": "Amazing view",
                "timestamp": "2024-05-10T10:00:00",
                "likesCount": 500,
                "commentsCount": 10,
                "imageUrls": ["https://cdn.com/view.jpg"],
                "comments": [{
                    "ownerUsername": "commenter",
                    "text": "Nice shot!",
                    "timestamp": "2024-05-10T12:00:00"
                }]
            }]
        }])
    ]
    node = InstagramScraperNode(params)
    result = node.execute()
    profile = result["instagram_results"]
    assert profile["username"] == "user42"
    assert len(profile["recent_posts"]) == 1
    assert profile["recent_posts"][0]["comments"][0]["comment_text"] == "Nice shot!"
