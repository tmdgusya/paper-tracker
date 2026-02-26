"""SQLite database implementation for paper storage."""

import sqlite3
from dataclasses import dataclass, asdict
from datetime import date, datetime
from pathlib import Path
from typing import Optional


@dataclass
class Paper:
    """Represents a research paper."""

    id: str
    title: str
    authors: str
    abstract: str
    url: str
    pdf_url: str
    published_date: date
    fetched_date: date
    summary: Optional[str] = None
    key_points: Optional[str] = None
    relevance_score: Optional[float] = None
    status: str = "pending"  # pending, summarized, reported


class Database:
    """SQLite database for storing papers."""

    def __init__(self, db_path: Path | str):
        """Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self) -> sqlite3.Connection:
        """Create and return a database connection.

        Returns:
            SQLite connection
        """
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
        return self.conn

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self) -> "Database":
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()

    def init_db(self) -> None:
        """Initialize database schema.

        Creates the papers table if it doesn't exist.
        """
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS papers (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                authors TEXT NOT NULL,
                abstract TEXT NOT NULL,
                url TEXT NOT NULL,
                pdf_url TEXT NOT NULL,
                published_date DATE NOT NULL,
                fetched_date DATE NOT NULL,
                summary TEXT,
                key_points TEXT,
                relevance_score REAL,
                status TEXT NOT NULL DEFAULT 'pending'
            )
        """
        )

        # Create indexes for common queries
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_published_date
            ON papers(published_date)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_status
            ON papers(status)
        """
        )

        conn.commit()

    def add_paper(self, paper: Paper) -> bool:
        """Add a paper to the database.

        Args:
            paper: Paper object to add

        Returns:
            True if paper was added, False if it already existed
        """
        conn = self.connect()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO papers (
                    id, title, authors, abstract, url, pdf_url,
                    published_date, fetched_date, summary, key_points,
                    relevance_score, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    paper.id,
                    paper.title,
                    paper.authors,
                    paper.abstract,
                    paper.url,
                    paper.pdf_url,
                    paper.published_date.isoformat(),
                    paper.fetched_date.isoformat(),
                    paper.summary,
                    paper.key_points,
                    paper.relevance_score,
                    paper.status,
                ),
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Paper with this ID already exists
            return False

    def get_paper(self, paper_id: str) -> Optional[Paper]:
        """Get a paper by ID.

        Args:
            paper_id: Paper identifier

        Returns:
            Paper object or None if not found
        """
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, title, authors, abstract, url, pdf_url,
                   published_date, fetched_date, summary, key_points,
                   relevance_score, status
            FROM papers WHERE id = ?
        """,
            (paper_id,),
        )

        row = cursor.fetchone()
        if row is None:
            return None

        return self._row_to_paper(row)

    def get_pending_papers(self, limit: Optional[int] = None) -> list[Paper]:
        """Get papers with status 'pending'.

        Args:
            limit: Maximum number of papers to return

        Returns:
            List of pending papers
        """
        conn = self.connect()
        cursor = conn.cursor()

        query = """
            SELECT id, title, authors, abstract, url, pdf_url,
                   published_date, fetched_date, summary, key_points,
                   relevance_score, status
            FROM papers WHERE status = 'pending'
            ORDER BY published_date DESC
        """
        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query)

        return [self._row_to_paper(row) for row in cursor.fetchall()]

    def get_papers_by_date(
        self, target_date: date, status: Optional[str] = None
    ) -> list[Paper]:
        """Get papers published on a specific date.

        Args:
            target_date: Date to filter by
            status: Optional status filter

        Returns:
            List of papers
        """
        conn = self.connect()
        cursor = conn.cursor()

        if status:
            cursor.execute(
                """
                SELECT id, title, authors, abstract, url, pdf_url,
                       published_date, fetched_date, summary, key_points,
                       relevance_score, status
                FROM papers
                WHERE published_date = ? AND status = ?
                ORDER BY relevance_score DESC
            """,
                (target_date.isoformat(), status),
            )
        else:
            cursor.execute(
                """
                SELECT id, title, authors, abstract, url, pdf_url,
                       published_date, fetched_date, summary, key_points,
                       relevance_score, status
                FROM papers
                WHERE published_date = ?
                ORDER BY relevance_score DESC
            """,
                (target_date.isoformat(),),
            )

        return [self._row_to_paper(row) for row in cursor.fetchall()]

    def update_paper_summary(
        self,
        paper_id: str,
        summary: str,
        key_points: str,
        relevance_score: float,
    ) -> bool:
        """Update a paper with AI-generated summary.

        Args:
            paper_id: Paper identifier
            summary: Generated summary text
            key_points: Key points extracted from paper
            relevance_score: Relevance score (1-10)

        Returns:
            True if updated, False if paper not found
        """
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE papers
            SET summary = ?, key_points = ?, relevance_score = ?, status = 'summarized'
            WHERE id = ?
        """,
            (summary, key_points, relevance_score, paper_id),
        )

        conn.commit()
        return cursor.rowcount > 0

    def mark_reported(self, paper_ids: list[str]) -> int:
        """Mark papers as reported.

        Args:
            paper_ids: List of paper identifiers

        Returns:
            Number of papers updated
        """
        conn = self.connect()
        cursor = conn.cursor()

        placeholders = ",".join("?" * len(paper_ids))
        cursor.execute(
            f"""
            UPDATE papers
            SET status = 'reported'
            WHERE id IN ({placeholders})
        """,
            paper_ids,
        )

        conn.commit()
        return cursor.rowcount

    def get_all_papers(self, limit: Optional[int] = None) -> list[Paper]:
        """Get all papers from database.

        Args:
            limit: Maximum number of papers to return

        Returns:
            List of all papers
        """
        conn = self.connect()
        cursor = conn.cursor()

        query = """
            SELECT id, title, authors, abstract, url, pdf_url,
                   published_date, fetched_date, summary, key_points,
                   relevance_score, status
            FROM papers
            ORDER BY published_date DESC
        """
        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query)

        return [self._row_to_paper(row) for row in cursor.fetchall()]

    @staticmethod
    def _row_to_paper(row: sqlite3.Row) -> Paper:
        """Convert database row to Paper object.

        Args:
            row: SQLite row object

        Returns:
            Paper instance
        """
        return Paper(
            id=row["id"],
            title=row["title"],
            authors=row["authors"],
            abstract=row["abstract"],
            url=row["url"],
            pdf_url=row["pdf_url"],
            published_date=date.fromisoformat(row["published_date"]),
            fetched_date=date.fromisoformat(row["fetched_date"]),
            summary=row["summary"],
            key_points=row["key_points"],
            relevance_score=row["relevance_score"],
            status=row["status"],
        )
