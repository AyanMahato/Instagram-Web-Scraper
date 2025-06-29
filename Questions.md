#Questions

I started to search for the apis and found some promising ones but they are paid after limited tokens or results. Is it ok to use those or use a headless scraper like selenium?

Do I need to make an API or a frontend for a user to test?

# Comments

1. **ERROR**: *Field input.searchType must be equal to one of the allowed values: "user", "hashtag", "place"*

I believe we need to change `search_type_map = {"Hashtag": "hashtag", "User Profile": "user"}`

2. The scrape is getting none of the image/video URLs for posts, and also some missing information for user profile. For example this is a response for `input_params = {"search_type":"User Profile", "search_term":"espn", "posts_limit":"10", "comments_per_post_limit":10}`

```json
{
  "instagram_results": {
    "username": "espnnl",
    "follower_count": 0,
    "following_count": 0,
    "post_count": 13191,
    "bio_text": "nl/'",
    "recent_posts": [
      {
        "post_url": "https://www.instagram.com/p/DLc7-OEoe1V/",
        "author_username": "espnnl",
        "author_fol\n 𝐃𝐨𝐧𝐞 𝐝𝐞𝐚𝐥: Antoni Milambo verlaat Feyenoord en tekent voor vijf jaar bij Brentford.": "timestamp",
        "like_count": 10990,
        "comment_count": 72,
        "view_count": "None",
        "media_urls": [],
        "image_urls": [],
        "commen\ninstagram.com/p/DLc3T7YIPEL/": "author_username': 'espnnl",
        "author_follower_count": 0,
        "post_content": "👶 Aangenaam, Ge\n2010 😨",
        "timestamp": "datetime.datetime(2025"
      },
      ...
    ]
  }
}
```

3. When scraping for hashtags it only returns the list of hashtags, rather than posts with the hashtag. This is the output for `input_params = {"search_type":"Hashtag", "search_term":"#sanfrancisco", "posts_limit":"10", "comments_per_post_limit":10`

```json
{
  "instagram_results": [
    {
      "post_url": "https://www.instagram.com/explore/tags/sanfranciscoweed/",
      "author_username": "None",
      "author_follower_count": 0,
      "post_content": "",
      "timestamp": "None",
      "like_count": 0,
      "comment_count": 0,
      "view_count": "None",
      "media_urls": [],
      "image_urls": [],
      "comments": []
    },
    {
      "post_url": "https://www.instagram.com/explore/tags/sanfranciscodemacor%c3%ads",
      "author_username": "None",
      "author_follower_count": 0,
      "post_content": "",
      "timestamp": "None",
      "like_count": 0,
      "comment_count": 0,
      "view_count": "None",
      "media_urls": [],
      "image_urls": [],
      "comments": []
    },
    {
      "post_url": "https://www.instagram.com/explore/tags/sanfrancisco",
      "author_username": "None",
      "author_follower_count": 0,
      "post_content": "",
      "timestamp": "None",
      "like_count": 0,
      "comment_count": 0,
      "view_count": "None",
      "media_urls": [],
      "image_urls": [],
      "comments": []
    },
    ...
  ]
}
```

4. It is also not getting any comments, but for initial iteration that's not a huge requirement so it's okay

5. Also when scraping for profiles it is never getting the exact profile name I am looking for - e.g., if I input "espn" it is scraping "espnnl", not sure if this is API issue or something to fix in the code itself

6. Small note: any reason to not use the `apify-client` python package and instead use requests?