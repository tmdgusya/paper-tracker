"""Shared fixtures and test configuration for paper-tracker tests."""

import datetime
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio

from paper_tracker.config import Settings
from paper_tracker.store.database import Database, Paper as StorePaper
from paper_tracker.fetcher.arxiv import Paper as FetcherPaper


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_db(temp_dir: Path) -> Generator[Database, None, None]:
    """Create a temporary database for testing."""
    db_path = temp_dir / "test.db"
    db = Database(db_path)
    db.init_db()
    yield db
    db.close()


@pytest.fixture
def sample_fetcher_paper() -> FetcherPaper:
    """Create a sample fetcher Paper object for testing."""
    return FetcherPaper(
        id="2301.12345",
        title="A Novel Approach to Machine Learning",
        authors=["Alice Smith", "Bob Johnson"],
        abstract="This paper presents a novel approach to machine learning that improves accuracy by 20%.",
        pdf_url="https://arxiv.org/pdf/2301.12345.pdf",
        published_date=datetime.date(2023, 1, 15),
        categories=["cs.AI", "cs.LG"],
    )


@pytest.fixture
def sample_store_paper() -> StorePaper:
    """Create a sample store Paper object for testing."""
    return StorePaper(
        id="2301.12345",
        title="A Novel Approach to Machine Learning",
        authors="Alice Smith, Bob Johnson",
        abstract="This paper presents a novel approach to machine learning that improves accuracy by 20%.",
        url="https://arxiv.org/abs/2301.12345",
        pdf_url="https://arxiv.org/pdf/2301.12345.pdf",
        published_date=datetime.date(2023, 1, 15),
        fetched_date=datetime.date(2023, 1, 16),
        summary="This paper introduces a new ML approach.",
        key_points="Point 1\nPoint 2\nPoint 3",
        relevance_score=8.5,
        status="summarized",
    )


@pytest.fixture
def sample_settings(temp_dir: Path) -> Settings:
    """Create a sample Settings object for testing."""
    return Settings(
        anthropic_api_key="test-api-key",
        categories=["cs.AI", "cs.LG"],
        keywords=["machine learning", "neural networks"],
        data_dir=temp_dir / "data",
        reports_dir=temp_dir / "reports",
        db_path=temp_dir / "data" / "papers.db",
        arxiv_base_url="http://export.arxiv.org/api/query",
        max_papers_per_batch=10,
        summary_model="claude-sonnet-4-6",
    )


@pytest.fixture
def sample_arxiv_xml_response() -> str:
    """Sample arXiv API XML response for testing."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2301.12345</id>
    <title>A Novel Approach to Machine Learning</title>
    <author>
      <name>Alice Smith</name>
    </author>
    <author>
      <name>Bob Johnson</name>
    </author>
    <summary>This paper presents a novel approach to machine learning that improves accuracy by 20%.</summary>
    <link href="https://arxiv.org/pdf/2301.12345.pdf" type="application/pdf"/>
    <published>2023-01-15T00:00:00Z</published>
    <category term="cs.AI"/>
    <category term="cs.LG"/>
  </entry>
</feed>"""


@pytest.fixture
def sample_arxiv_empty_response() -> str:
    """Empty arXiv API XML response for testing."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
</feed>"""


@pytest_asyncio.fixture
async def mock_http_client() -> AsyncGenerator:
    """Mock httpx.AsyncClient for testing."""
    # This will be used with httpx.MockTransport in actual tests
    yield None
