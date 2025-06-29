# Instagram Scraper API

A FastAPI-based microservice to scrape Instagram posts and profiles using the [Apify Instagram Scraper](https://apify.com/apify/instagram-scraper) actor. Easily fetch posts by hashtag or retrieve public user profiles along with recent posts and optional comments.

---

## 🚀 Features

- 🔍 Scrape Instagram posts by hashtag  
- 👤 Scrape Instagram user profiles and posts  
- 💬 Optionally include recent comments  
- 🧠 Timeframe filtering (last 24 hours to last 6 months)  
- ⚙️ Built with FastAPI

---

## 📦 Requirements

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 🛠️ Environment Variables

Create a `.env` file with the following keys:

```env
INSTAGRAM_SCRAPER_API_KEY=your_apify_api_token
INSTAGRAM_SCRAPER_ACTOR_ID=apify~instagram-scraper
```

You can obtain your API token and actor ID from [apify.com](https://apify.com).

---

## 🧪 Example Payloads

### Hashtag Scrape

`POST /scrape`

```json
{
  "search_type": "Hashtag",
  "search_term": "nature",
  "posts_limit": 2,
  "include_comments": false,
  "comments_per_post_limit": 3
}
```

### User Profile Scrape

`POST /scrape`

```json
{
  "search_type": "User Profile",
  "search_term": "natgeo",
  "posts_limit": 2,
  "include_comments": false,
  "comments_per_post_limit": 3
}
```

---

## 📡 API Endpoints

### `GET /health`

Health check endpoint.

```json
{ "status": "ok" }
```

---

### `POST /scrape`

Scrape Instagram content using Apify.

#### Request Body

| Field                     | Type      | Required | Description                                 |
|--------------------------|-----------|----------|---------------------------------------------|
| `search_type`            | string    | ✅        | `"Hashtag"` or `"User Profile"`             |
| `search_term`            | string    | ✅        | Hashtag (e.g., `"nature"`) or username      |
| `posts_limit`            | integer   | ✅        | Number of posts to fetch (0–1000)           |
| `include_comments`       | boolean   | ✅        | Include post comments                       |
| `comments_per_post_limit`| integer   | ✅        | Max comments per post (0–200)               |
| `timeframe`              | string    | ❌        | `"Last 24 hours"`, `"Last 7 days"`, etc.    |
| `location`               | string    | ❌        | Optional location constraint                |

## 🧪 Testing

Run the test suite using `pytest`:

```bash
pytest
```

---

## 📦 Deployment

Use `uvicorn` to serve the API:

```bash
uvicorn main:app --reload
```

---

## 🔒 Disclaimer

This tool uses publicly available actors on Apify and is intended for ethical use only. Do **not** use it to violate Instagram’s [terms of service](https://help.instagram.com/581066165581870).

---

## 🧑‍💻 Author

Made for internal automation or personal analytics. Contributions and PRs are welcome!
