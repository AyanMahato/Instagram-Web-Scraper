from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from instagram_scraper_node import InstagramScraperNode, InstagramScraperNodeParams
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

# Logger
logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.INFO)

# Create FastAPI app
app = FastAPI(title="Instagram Scraper API", version="1.0")

# Optional: enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check route
@app.get("/health")
async def health():
    logger.info("Health OK")
    return {"status": "ok"}

# Main scraping route
@app.post("/scrape")
async def scrape_instagram(params: InstagramScraperNodeParams, request: Request):
    logger.info("Incoming request from %s with params: %s", request.client.host, params.dict())
    try:
        scraper = InstagramScraperNode(params)
        result = scraper.execute()
        logger.info("Scraping completed successfully.")
        return JSONResponse(content=result, status_code=200)
    except Exception as e:
        logger.exception("Scraping failed.")
        raise e
