"""Tests for the SQLite database store module."""

import datetime
from pathlib import Path

import pytest

from paper_tracker.store.database import Database, Paper


class TestDatabase:
    """Test cases for the Database class."""

    def test_init_db_creates_tables(self, temp_db: Database) -> None:
        """Test that init_db creates the papers table and indexes."""
        conn = temp_db.connect()
        cursor = conn.cursor()

        # Check papers table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='papers'"
        )
        result = cursor.fetchone()
        assert result is not None, "Papers table should exist"

        # Check indexes exist
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_published_date'"
        )
        assert cursor.fetchone() is not None, "idx_published_date should exist"

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_status'"
        )
        assert cursor.fetchone() is not None, "idx_status should exist"

    def test_add_paper(self, temp_db: Database, sample_store_paper: Paper) -> None:
        """Test adding a paper to the database."""
        result = temp_db.add_paper(sample_store_paper)
        assert result is True, "Should return True when paper is added"

        # Verify paper was added
        paper = temp_db.get_paper(sample_store_paper.id)
        assert paper is not None
        assert paper.id == sample_store_paper.id
        assert paper.title == sample_store_paper.title
        assert paper.authors == sample_store_paper.authors

    def test_add_duplicate_paper(self, temp_db: Database, sample_store_paper: Paper) -> None:
        """Test that adding a duplicate paper returns False."""
        temp_db.add_paper(sample_store_paper)
        result = temp_db.add_paper(sample_store_paper)
        assert result is False, "Should return False for duplicate paper"

    def test_get_paper(self, temp_db: Database, sample_store_paper: Paper) -> None:
        """Test retrieving a paper by ID."""
        temp_db.add_paper(sample_store_paper)
        paper = temp_db.get_paper(sample_store_paper.id)

        assert paper is not None
        assert paper.id == sample_store_paper.id
        assert paper.title == sample_store_paper.title
        assert paper.abstract == sample_store_paper.abstract
        assert paper.status == sample_store_paper.status

    def test_get_paper_not_found(self, temp_db: Database) -> None:
        """Test retrieving a non-existent paper returns None."""
        paper = temp_db.get_paper("nonexistent.id")
        assert paper is None

    def test_get_pending_papers(self, temp_db: Database) -> None:
        """Test retrieving pending papers."""
        # Add papers with different statuses
        paper1 = Paper(
            id="2301.00001",
            title="Pending Paper",
            authors="Author One",
            abstract="Abstract 1",
            url="https://arxiv.org/abs/2301.00001",
            pdf_url="https://arxiv.org/pdf/2301.00001.pdf",
            published_date=datetime.date(2023, 1, 1),
            fetched_date=datetime.date(2023, 1, 1),
            status="pending",
        )
        paper2 = Paper(
            id="2301.00002",
            title="Summarized Paper",
            authors="Author Two",
            abstract="Abstract 2",
            url="https://arxiv.org/abs/2301.00002",
            pdf_url="https://arxiv.org/pdf/2301.00002.pdf",
            published_date=datetime.date(2023, 1, 2),
            fetched_date=datetime.date(2023, 1, 2),
            status="summarized",
        )

        temp_db.add_paper(paper1)
        temp_db.add_paper(paper2)

        pending = temp_db.get_pending_papers()
        assert len(pending) == 1
        assert pending[0].id == "2301.00001"

    def test_get_pending_papers_with_limit(self, temp_db: Database) -> None:
        """Test retrieving pending papers with a limit."""
        for i in range(5):
            paper = Paper(
                id=f"2301.0000{i}",
                title=f"Pending Paper {i}",
                authors=f"Author {i}",
                abstract=f"Abstract {i}",
                url=f"https://arxiv.org/abs/2301.0000{i}",
                pdf_url=f"https://arxiv.org/pdf/2301.0000{i}.pdf",
                published_date=datetime.date(2023, 1, i + 1),
                fetched_date=datetime.date(2023, 1, i + 1),
                status="pending",
            )
            temp_db.add_paper(paper)

        pending = temp_db.get_pending_papers(limit=3)
        assert len(pending) == 3

    def test_get_papers_by_date(self, temp_db: Database) -> None:
        """Test retrieving papers by publication date."""
        paper1 = Paper(
            id="2301.00001",
            title="Paper 1",
            authors="Author One",
            abstract="Abstract 1",
            url="https://arxiv.org/abs/2301.00001",
            pdf_url="https://arxiv.org/pdf/2301.00001.pdf",
            published_date=datetime.date(2023, 1, 1),
            fetched_date=datetime.date(2023, 1, 1),
            status="pending",
        )
        paper2 = Paper(
            id="2301.00002",
            title="Paper 2",
            authors="Author Two",
            abstract="Abstract 2",
            url="https://arxiv.org/abs/2301.00002",
            pdf_url="https://arxiv.org/pdf/2301.00002.pdf",
            published_date=datetime.date(2023, 1, 2),
            fetched_date=datetime.date(2023, 1, 2),
            status="pending",
        )

        temp_db.add_paper(paper1)
        temp_db.add_paper(paper2)

        papers = temp_db.get_papers_by_date(datetime.date(2023, 1, 1))
        assert len(papers) == 1
        assert papers[0].id == "2301.00001"

    def test_get_papers_by_date_with_status(self, temp_db: Database) -> None:
        """Test retrieving papers by date and status."""
        paper1 = Paper(
            id="2301.00001",
            title="Paper 1",
            authors="Author One",
            abstract="Abstract 1",
            url="https://arxiv.org/abs/2301.00001",
            pdf_url="https://arxiv.org/pdf/2301.00001.pdf",
            published_date=datetime.date(2023, 1, 1),
            fetched_date=datetime.date(2023, 1, 1),
            status="pending",
        )
        paper2 = Paper(
            id="2301.00002",
            title="Paper 2",
            authors="Author Two",
            abstract="Abstract 2",
            url="https://arxiv.org/abs/2301.00002",
            pdf_url="https://arxiv.org/pdf/2301.00002.pdf",
            published_date=datetime.date(2023, 1, 1),
            fetched_date=datetime.date(2023, 1, 1),
            status="summarized",
        )

        temp_db.add_paper(paper1)
        temp_db.add_paper(paper2)

        papers = temp_db.get_papers_by_date(
            datetime.date(2023, 1, 1), status="pending"
        )
        assert len(papers) == 1
        assert papers[0].id == "2301.00001"

    def test_update_paper_summary(self, temp_db: Database) -> None:
        """Test updating a paper with summary information."""
        paper = Paper(
            id="2301.00001",
            title="Test Paper",
            authors="Test Author",
            abstract="Test Abstract",
            url="https://arxiv.org/abs/2301.00001",
            pdf_url="https://arxiv.org/pdf/2301.00001.pdf",
            published_date=datetime.date(2023, 1, 1),
            fetched_date=datetime.date(2023, 1, 1),
            status="pending",
        )
        temp_db.add_paper(paper)

        result = temp_db.update_paper_summary(
            paper_id="2301.00001",
            summary="This is a summary",
            key_points="Point 1\nPoint 2",
            relevance_score=8.5,
        )

        assert result is True

        # Verify update
        updated_paper = temp_db.get_paper("2301.00001")
        assert updated_paper.summary == "This is a summary"
        assert updated_paper.key_points == "Point 1\nPoint 2"
        assert updated_paper.relevance_score == 8.5
        assert updated_paper.status == "summarized"

    def test_update_paper_summary_not_found(self, temp_db: Database) -> None:
        """Test updating a non-existent paper returns False."""
        result = temp_db.update_paper_summary(
            paper_id="nonexistent",
            summary="Summary",
            key_points="Points",
            relevance_score=5.0,
        )
        assert result is False

    def test_mark_reported(self, temp_db: Database) -> None:
        """Test marking papers as reported."""
        papers = [
            Paper(
                id=f"2301.0000{i}",
                title=f"Paper {i}",
                authors=f"Author {i}",
                abstract=f"Abstract {i}",
                url=f"https://arxiv.org/abs/2301.0000{i}",
                pdf_url=f"https://arxiv.org/pdf/2301.0000{i}.pdf",
                published_date=datetime.date(2023, 1, i + 1),
                fetched_date=datetime.date(2023, 1, i + 1),
                status="summarized",
            )
            for i in range(3)
        ]

        for paper in papers:
            temp_db.add_paper(paper)

        count = temp_db.mark_reported(["2301.00001", "2301.00002"])
        assert count == 2

        # Verify status updates
        paper0 = temp_db.get_paper("2301.00000")
        paper1 = temp_db.get_paper("2301.00001")
        paper2 = temp_db.get_paper("2301.00002")

        assert paper1.status == "reported"
        assert paper2.status == "reported"
        assert paper0.status == "summarized"

    def test_get_all_papers(self, temp_db: Database) -> None:
        """Test retrieving all papers."""
        for i in range(3):
            paper = Paper(
                id=f"2301.0000{i}",
                title=f"Paper {i}",
                authors=f"Author {i}",
                abstract=f"Abstract {i}",
                url=f"https://arxiv.org/abs/2301.0000{i}",
                pdf_url=f"https://arxiv.org/pdf/2301.0000{i}.pdf",
                published_date=datetime.date(2023, 1, i + 1),
                fetched_date=datetime.date(2023, 1, i + 1),
                status="pending",
            )
            temp_db.add_paper(paper)

        papers = temp_db.get_all_papers()
        assert len(papers) == 3

    def test_get_all_papers_with_limit(self, temp_db: Database) -> None:
        """Test retrieving all papers with a limit."""
        for i in range(5):
            paper = Paper(
                id=f"2301.0000{i}",
                title=f"Paper {i}",
                authors=f"Author {i}",
                abstract=f"Abstract {i}",
                url=f"https://arxiv.org/abs/2301.0000{i}",
                pdf_url=f"https://arxiv.org/pdf/2301.0000{i}.pdf",
                published_date=datetime.date(2023, 1, i + 1),
                fetched_date=datetime.date(2023, 1, i + 1),
                status="pending",
            )
            temp_db.add_paper(paper)

        papers = temp_db.get_all_papers(limit=3)
        assert len(papers) == 3

    def test_get_latest_paper_date_empty(self, temp_db: Database) -> None:
        """Test get_latest_paper_date on an empty database returns None."""
        result = temp_db.get_latest_paper_date()
        assert result is None

    def test_get_latest_paper_date(self, temp_db: Database) -> None:
        """Test get_latest_paper_date returns the most recent date."""
        for i, day in enumerate([5, 15, 10]):
            paper = Paper(
                id=f"2301.0000{i}",
                title=f"Paper {i}",
                authors=f"Author {i}",
                abstract=f"Abstract {i}",
                url=f"https://arxiv.org/abs/2301.0000{i}",
                pdf_url=f"https://arxiv.org/pdf/2301.0000{i}.pdf",
                published_date=datetime.date(2025, 7, day),
                fetched_date=datetime.date(2025, 7, day),
                status="pending",
            )
            temp_db.add_paper(paper)

        result = temp_db.get_latest_paper_date()
        assert result == datetime.date(2025, 7, 15)

    def test_context_manager(self, temp_dir: Path) -> None:
        """Test using Database as a context manager."""
        db_path = temp_dir / "test_context.db"

        with Database(db_path) as db:
            db.init_db()
            paper = Paper(
                id="2301.00001",
                title="Test Paper",
                authors="Test Author",
                abstract="Test Abstract",
                url="https://arxiv.org/abs/2301.00001",
                pdf_url="https://arxiv.org/pdf/2301.00001.pdf",
                published_date=datetime.date(2023, 1, 1),
                fetched_date=datetime.date(2023, 1, 1),
                status="pending",
            )
            db.add_paper(paper)

        # Connection should be closed after exiting context
        assert db.conn is None
