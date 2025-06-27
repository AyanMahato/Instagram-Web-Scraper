import pytest
from unittest.mock import patch, MagicMock
from instagram_scraper_node import InstagramScraperNode, InstagramScraperNodeParams

@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("INSTAGRAM_SCRAPER_API_KEY", "test_token")
    monkeypatch.setenv("INSTAGRAM_SCRAPER_ACTOR_ID", "apify/instagram-scraper")

@pytest.fixture
def default_params():
    return InstagramScraperNodeParams(
        search_type="Hashtag",
        search_term="test",
        posts_limit=5,
        include_comments=False,
        comments_per_post_limit=10
    )

def test_invalid_api_key(monkeypatch):
    monkeypatch.delenv("INSTAGRAM_SCRAPER_API_KEY", raising=False)
    monkeypatch.setenv("INSTAGRAM_SCRAPER_ACTOR_ID", "dummy_id")
    with pytest.raises(Exception, match="Missing Apify API key"):
        InstagramScraperNode(InstagramScraperNodeParams(
            search_type="Hashtag",
            search_term="test",
            posts_limit=5,
            comments_per_post_limit=10
        ))

def test_invalid_actor_id(monkeypatch):
    monkeypatch.setenv("INSTAGRAM_SCRAPER_API_KEY", "test_token")
    monkeypatch.delenv("INSTAGRAM_SCRAPER_ACTOR_ID", raising=False)
    with pytest.raises(Exception, match="Missing Actor ID"):
        InstagramScraperNode(InstagramScraperNodeParams(
            search_type="Hashtag",
            search_term="test",
            posts_limit=5,
            comments_per_post_limit=10
        ))

@patch("instagram_scraper_node.requests.post")
@patch("instagram_scraper_node.requests.get")
def test_successful_execute(mock_get, mock_post, mock_env, default_params):
    mock_post.return_value.status_code = 201
    mock_post.return_value.json.return_value = {"data": {"id": "run123"}}

    mock_get.side_effect = [
        MagicMock(json=lambda: {
            "data": {
                "status": "SUCCEEDED",
                "defaultDatasetId": "dataset123"
            }
        }),
        MagicMock(json=lambda: [{
            "url": "https://insta.com/post1",
            "ownerUsername": "user1",
            "ownerFollowers": 1000,
            "caption": "test caption",
            "timestamp": "2024-06-01T12:00:00",
            "likesCount": 100,
            "commentsCount": 5,
            "imageUrls": ["https://img.com/1.jpg"],
            "comments": []
        }])
    ]

    node = InstagramScraperNode(default_params)
    result = node.execute()

    assert "instagram_results" in result
    assert isinstance(result["instagram_results"], list)
    assert len(result["instagram_results"]) == 1
    assert result["instagram_results"][0]["author_username"] == "user1"

@patch("instagram_scraper_node.requests.post")
@patch("instagram_scraper_node.requests.get")
def test_no_results_error(mock_get, mock_post, mock_env, default_params):
    mock_post.return_value.status_code = 201
    mock_post.return_value.json.return_value = {"data": {"id": "run123"}}

    mock_get.side_effect = [
        MagicMock(json=lambda: {
            "data": {
                "status": "SUCCEEDED",
                "defaultDatasetId": "dataset123"
            }
        }),
        MagicMock(json=lambda: [])
    ]

    node = InstagramScraperNode(default_params)
    with pytest.raises(Exception, match="No data returned from Apify dataset"):
        node.execute()
