from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
import asyncio
import json
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from playwright.async_api import Page, BrowserContext


async def main():

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://www.ziprecruiter.com/Search-Software-Engineer-Jobs",
            config=CrawlerRunConfig(
                magic=True,  # Simplifies a lot of interaction
                remove_overlay_elements=True,
                page_timeout=60000
            )
        )
        print(result.markdown)
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())