"""
Reddit Service — Monitor subreddits and manage engagement via PRAW.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

import asyncpraw
import config

logger = logging.getLogger(__name__)


class RedditClient:
    """Async Reddit client wrapper around asyncpraw."""

    def __init__(self):
        self.reddit: Optional[asyncpraw.Reddit] = None

    async def connect(self):
        """Initialize the Reddit connection."""
        if not config.REDDIT_CLIENT_ID:
            logger.warning("Reddit credentials not configured — skipping Reddit")
            return

        self.reddit = asyncpraw.Reddit(
            client_id=config.REDDIT_CLIENT_ID,
            client_secret=config.REDDIT_CLIENT_SECRET,
            username=config.REDDIT_USERNAME,
            password=config.REDDIT_PASSWORD,
            user_agent=config.REDDIT_USER_AGENT,
        )
        logger.info(f"Reddit connected as u/{config.REDDIT_USERNAME}")

    async def close(self):
        """Close the Reddit connection."""
        if self.reddit:
            await self.reddit.close()

    async def search_posts(
        self,
        subreddit: str,
        query: str,
        sort: str = "relevance",
        time_filter: str = "week",
        limit: int = 10,
    ) -> list[dict]:
        """Search for relevant posts in a subreddit."""
        if not self.reddit:
            return []

        try:
            sub = await self.reddit.subreddit(subreddit)
            posts = []
            async for post in sub.search(query, sort=sort, time_filter=time_filter, limit=limit):
                posts.append({
                    "id": post.id,
                    "title": post.title,
                    "body": post.selftext[:1000] if post.selftext else "",
                    "url": f"https://reddit.com{post.permalink}",
                    "subreddit": subreddit,
                    "score": post.score,
                    "num_comments": post.num_comments,
                    "created_utc": datetime.fromtimestamp(post.created_utc, tz=timezone.utc).isoformat(),
                    "author": str(post.author) if post.author else "[deleted]",
                })
            return posts
        except Exception as e:
            logger.error(f"Reddit search failed in r/{subreddit}: {e}")
            return []

    async def get_hot_posts(
        self,
        subreddit: str,
        limit: int = 25,
    ) -> list[dict]:
        """Get hot posts from a subreddit."""
        if not self.reddit:
            return []

        try:
            sub = await self.reddit.subreddit(subreddit)
            posts = []
            async for post in sub.hot(limit=limit):
                if post.stickied:
                    continue
                posts.append({
                    "id": post.id,
                    "title": post.title,
                    "body": post.selftext[:1000] if post.selftext else "",
                    "url": f"https://reddit.com{post.permalink}",
                    "subreddit": subreddit,
                    "score": post.score,
                    "num_comments": post.num_comments,
                    "created_utc": datetime.fromtimestamp(post.created_utc, tz=timezone.utc).isoformat(),
                    "author": str(post.author) if post.author else "[deleted]",
                })
            return posts
        except Exception as e:
            logger.error(f"Reddit hot posts failed for r/{subreddit}: {e}")
            return []

    async def get_new_posts(
        self,
        subreddit: str,
        limit: int = 25,
    ) -> list[dict]:
        """Get new posts from a subreddit — best for finding questions to answer."""
        if not self.reddit:
            return []

        try:
            sub = await self.reddit.subreddit(subreddit)
            posts = []
            async for post in sub.new(limit=limit):
                posts.append({
                    "id": post.id,
                    "title": post.title,
                    "body": post.selftext[:1000] if post.selftext else "",
                    "url": f"https://reddit.com{post.permalink}",
                    "subreddit": subreddit,
                    "score": post.score,
                    "num_comments": post.num_comments,
                    "created_utc": datetime.fromtimestamp(post.created_utc, tz=timezone.utc).isoformat(),
                    "author": str(post.author) if post.author else "[deleted]",
                })
            return posts
        except Exception as e:
            logger.error(f"Reddit new posts failed for r/{subreddit}: {e}")
            return []

    async def post_comment(
        self,
        post_id: str,
        comment_text: str,
    ) -> Optional[str]:
        """Post a comment on a Reddit post. Returns the comment ID."""
        if not self.reddit:
            return None

        try:
            submission = await self.reddit.submission(id=post_id)
            comment = await submission.reply(comment_text)
            logger.info(f"Posted comment on {post_id}: {comment.id}")
            return comment.id
        except Exception as e:
            logger.error(f"Reddit comment failed on {post_id}: {e}")
            return None

    async def get_account_info(self) -> dict:
        """Get info about the authenticated Reddit account."""
        if not self.reddit:
            return {}

        try:
            me = await self.reddit.user.me()
            return {
                "username": me.name,
                "karma": me.link_karma + me.comment_karma,
                "link_karma": me.link_karma,
                "comment_karma": me.comment_karma,
                "created_utc": datetime.fromtimestamp(me.created_utc, tz=timezone.utc).isoformat(),
                "is_verified": me.has_verified_email,
            }
        except Exception as e:
            logger.error(f"Reddit account info failed: {e}")
            return {}
