"""Database store for paper-tracker."""

from pathlib import Path
from typing import Optional

from paper_tracker.store.database import Database, Paper

__all__ = ["Database", "Paper", "init_db", "get_pending_papers", "save_papers", "update_paper_summary", "get_papers_by_date", "get_latest_paper_date"]


def init_db(db_path: Path | str) -> Database:
    """Initialize the database.

    Args:
        db_path: Path to the database file

    Returns:
        Initialized Database instance
    """
    db = Database(db_path)
    db.init_db()
    return db


def get_pending_papers(
    db_path: Path | str, limit: Optional[int] = None, include_summarized: bool = False
) -> list[Paper]:
    """Get pending papers from database.

    Args:
        db_path: Path to the database file
        limit: Maximum number of papers to return
        include_summarized: Whether to include summarized papers

    Returns:
        List of pending papers
    """
    db = Database(db_path)
    if include_summarized:
        return db.get_all_papers(limit=limit)
    return db.get_pending_papers(limit=limit)


def save_papers(db_path: Path | str, papers: list) -> int:
    """Save papers to database.

    Args:
        db_path: Path to the database file
        papers: List of paper objects or dictionaries

    Returns:
        Number of papers saved
    """
    db = Database(db_path)
    count = 0
    for paper_data in papers:
        # Convert dict to Paper if needed
        if isinstance(paper_data, dict):
            paper = Paper(
                id=paper_data.get("id", ""),
                title=paper_data.get("title", ""),
                authors=", ".join(paper_data.get("authors", [])),
                abstract=paper_data.get("abstract", ""),
                url=paper_data.get("url", f"https://arxiv.org/abs/{paper_data.get('id', '')}"),
                pdf_url=paper_data.get("pdf_url", ""),
                published_date=paper_data.get("published_date"),
                fetched_date=paper_data.get("fetched_date", paper_data.get("published_date")),
            )
        else:
            # Assume it's already a Paper object or compatible
            paper = Paper(
                id=paper_data.id,
                title=paper_data.title,
                authors=", ".join(paper_data.authors) if isinstance(paper_data.authors, list) else paper_data.authors,
                abstract=paper_data.abstract,
                url=getattr(paper_data, "url", f"https://arxiv.org/abs/{paper_data.id}"),
                pdf_url=paper_data.pdf_url,
                published_date=paper_data.published_date,
                fetched_date=getattr(paper_data, "fetched_date", paper_data.published_date),
            )
        if db.add_paper(paper):
            count += 1
    return count


def update_paper_summary(db_path: Path | str, paper_id: str, summary) -> bool:
    """Update a paper with summary.

    Args:
        db_path: Path to the database file
        paper_id: ID of the paper to update
        summary: Summary object or dict

    Returns:
        True if updated successfully
    """
    db = Database(db_path)
    if hasattr(summary, "summary_text"):
        return db.update_paper_summary(
            paper_id=paper_id,
            summary=summary.summary_text,
            key_points="\n".join(getattr(summary, "key_points", [])),
            relevance_score=getattr(summary, "relevance_score", 0.0) * 10,  # Convert 0-1 to 0-10
        )
    elif isinstance(summary, dict):
        return db.update_paper_summary(
            paper_id=paper_id,
            summary=summary.get("summary_text", ""),
            key_points="\n".join(summary.get("key_points", [])),
            relevance_score=summary.get("relevance_score", 0.0) * 10,
        )
    return False


def get_papers_by_date(db_path: Path | str, target_date, status: Optional[str] = None) -> list[Paper]:
    """Get papers by date.

    Args:
        db_path: Path to the database file
        target_date: Date to filter by
        status: Optional status filter

    Returns:
        List of papers
    """
    db = Database(db_path)
    return db.get_papers_by_date(target_date, status)


def get_latest_paper_date(db_path: Path | str):
    """Get the most recent published_date from the database.

    Args:
        db_path: Path to the database file

    Returns:
        Most recent date, or None if no papers exist
    """
    db = Database(db_path)
    return db.get_latest_paper_date()
