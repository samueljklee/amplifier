"""
Fetcher core functionality.

Fetches top Hacker News posts and comments using HN API.
"""

import asyncio
from typing import Any

import httpx

from amplifier.utils.logger import get_logger

logger = get_logger(__name__)


class Fetcher:
    """Fetches data from Hacker News API."""

    BASE_URL = "https://hacker-news.firebaseio.com/v0"

    async def fetch_top_posts(self, limit: int = 20) -> list[dict[str, Any]]:
        """Fetch top HN posts with their comments.

        Args:
            limit: Number of top posts to fetch

        Returns:
            List of post dictionaries with metadata and top comments
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Get top story IDs
                response = await client.get(f"{self.BASE_URL}/topstories.json")
                response.raise_for_status()
                story_ids = response.json()[:limit]

                logger.info(f"Fetching details for {len(story_ids)} stories...")

                # Fetch each story with comments
                posts = []
                for idx, story_id in enumerate(story_ids, 1):
                    try:
                        post = await self._fetch_story_with_comments(client, story_id)
                        if post:
                            posts.append(post)
                            logger.info(f"  [{idx}/{len(story_ids)}] {post['title'][:60]}...")
                    except Exception as e:
                        logger.warning(f"Failed to fetch story {story_id}: {e}")
                        continue

                    # Rate limiting
                    await asyncio.sleep(0.1)

                return posts

        except Exception as e:
            logger.error(f"Failed to fetch top posts: {e}")
            return []

    async def _fetch_story_with_comments(self, client: httpx.AsyncClient, story_id: int) -> dict[str, Any] | None:
        """Fetch a single story with its top comments.

        Args:
            client: HTTP client
            story_id: Story ID to fetch

        Returns:
            Story dictionary with metadata and comments, or None if failed
        """
        try:
            # Fetch story details
            response = await client.get(f"{self.BASE_URL}/item/{story_id}.json")
            response.raise_for_status()
            story = response.json()

            if not story or story.get("type") != "story":
                return None

            # Extract key fields
            post = {
                "id": story.get("id"),
                "title": story.get("title", ""),
                "url": story.get("url", ""),
                "score": story.get("score", 0),
                "by": story.get("by", ""),
                "time": story.get("time", 0),
                "descendants": story.get("descendants", 0),
                "text": story.get("text", ""),
                "comments": [],
            }

            # Fetch top comments (first 5)
            comment_ids = story.get("kids", [])[:5]
            for comment_id in comment_ids:
                try:
                    comment_response = await client.get(f"{self.BASE_URL}/item/{comment_id}.json")
                    comment_response.raise_for_status()
                    comment = comment_response.json()

                    if comment and comment.get("text"):
                        post["comments"].append(
                            {
                                "by": comment.get("by", ""),
                                "text": comment.get("text", ""),
                                "time": comment.get("time", 0),
                            }
                        )

                    await asyncio.sleep(0.05)  # Rate limiting
                except Exception:
                    continue

            return post

        except Exception as e:
            logger.warning(f"Failed to fetch story {story_id}: {e}")
            return None
