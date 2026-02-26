"""arXiv paper fetcher module."""

import asyncio
import datetime
from typing import Optional

from paper_tracker.fetcher.arxiv import ArxivFetcher, Paper
from paper_tracker.fetcher.filter import PaperFilter

__all__ = ["ArxivFetcher", "PaperFilter", "fetch_papers"]


async def fetch_papers(
    categories: list[str],
    keywords: Optional[list[str]] = None,
    limit: int = 100,
    date: Optional[datetime.date] = None,
) -> list[Paper]:
    """Fetch papers from arXiv.

    Args:
        categories: List of arXiv categories (e.g., ["cs.AI", "cs.LG"])
        keywords: Optional list of keywords to filter by
        limit: Maximum number of papers to fetch
        date: Date to fetch papers for (defaults to today)

    Returns:
        List of Paper objects
    """
    fetcher = ArxivFetcher()
    try:
        papers = await fetcher.fetch_papers(
            categories=categories,
            date=date,
            max_results=limit,
        )

        # Apply keyword filter if provided
        if keywords:
            filter_obj = PaperFilter(keywords)
            filtered_results = filter_obj.filter(papers, min_matches=1)
            papers = [r.paper for r in filtered_results]

        return papers
    finally:
        await fetcher.close()
