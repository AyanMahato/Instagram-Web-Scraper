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

def test_missing_api_key(monkeypatch, basic_params):
    monkeypatch.delenv("INSTAGRAM_SCRAPER_API_KEY", raising=False)
    monkeypatch.setenv("INSTAGRAM_SCRAPER_ACTOR_ID", "dummy")
    with pytest.raises(Exception, match="API key not found"):
        InstagramScraperNode(basic_params)

def test_missing_actor_id(monkeypatch, basic_params):
    monkeypatch.setenv("INSTAGRAM_SCRAPER_API_KEY", "token")
    monkeypatch.delenv("INSTAGRAM_SCRAPER_ACTOR_ID", raising=False)
    with pytest.raises(Exception, match="Actor ID not set"):
        InstagramScraperNode(basic_params)

@patch("instagram_scraper_node.requests.post")
def test_actor_start_failure(mock_post, mock_env, basic_params):
    mock_post.return_value.status_code = 400
    mock_post.return_value.text = "Bad Request"
    node = InstagramScraperNode(basic_params)
    with pytest.raises(Exception, match="Apify API error: 400"):
        node.execute()

@patch("instagram_scraper_node.requests.post")
def test_no_data_returned(mock_post, mock_env, basic_params):
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = []
    node = InstagramScraperNode(basic_params)
    result = node.execute()
    assert isinstance(result, dict)
    assert "posts" in result
    assert isinstance(result["posts"], list)
    assert len(result["posts"]) == 0

@patch("instagram_scraper_node.requests.post")
def test_basic_hashtag_scrape(mock_post, mock_env, basic_params):
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = [
        {
            "url": "https://insta.com/p/abc",
            "ownerUsername": "user123",
            "ownerFollowers": 1234,
            "caption": "caption here",
            "timestamp": "2024-06-01T00:00:00",
            "likesCount": 20,
            "commentsCount": 3,
            "imageUrls": ["https://cdn.com/pic.jpg"],
            "comments": []
        }
    ]
    node = InstagramScraperNode(basic_params)
    result = node.execute()
    assert "posts" in result
    assert result["posts"][0]["ownerUsername"] == "user123"

@patch("instagram_scraper_node.requests.post")
def test_user_profile_scrape(mock_post, mock_env):
    params = InstagramScraperNodeParams(
        search_type="User Profile",
        search_term="user42",
        posts_limit=3,
        include_comments=True,
        comments_per_post_limit=2
    )

    mock_post.side_effect = [
        MagicMock(status_code=200, json=lambda: [
            {
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
            }
        ]),
        MagicMock(status_code=200, json=lambda: [
            {
                "username": "user42",
                "followers": 15000,
                "following": 800,
                "postsCount": 50,
                "bio": "Traveler & Foodie",
                "externalUrl": "http://example.com"
            }
        ])
    ]

    node = InstagramScraperNode(params)
    result = node.execute()
    assert "profile" in result
    assert "posts" in result
    assert result["profile"]["username"] == "user42"
    assert result["posts"][0]["ownerUsername"] == "user42"
    assert result["posts"][0]["comments"][0]["text"] == "Nice shot!"
