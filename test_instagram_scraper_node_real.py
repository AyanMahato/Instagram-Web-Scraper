import os
from instagram_scraper_node import InstagramScraperNode, InstagramScraperNodeParams

def test_real_hashtag_scrape():
    params = InstagramScraperNodeParams(
        search_type="Hashtag",
        search_term="nature",
        posts_limit=2,
        include_comments=False,
        comments_per_post_limit=3
    )
    node = InstagramScraperNode(params)
    result = node.execute()

    assert "instagram_results" in result
    assert isinstance(result["instagram_results"], list)
    assert len(result["instagram_results"]) > 0
