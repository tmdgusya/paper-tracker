"""Tests for the arXiv fetcher module."""

import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import httpx

from paper_tracker.fetcher.arxiv import ArxivFetcher, Paper


class TestPaper:
    """Test cases for the Paper dataclass."""

    def test_paper_to_dict(self, sample_fetcher_paper: Paper) -> None:
        """Test converting a Paper to dictionary."""
        result = sample_fetcher_paper.to_dict()

        assert isinstance(result, dict)
        assert result["id"] == sample_fetcher_paper.id
        assert result["title"] == sample_fetcher_paper.title
        assert result["authors"] == sample_fetcher_paper.authors
        assert result["abstract"] == sample_fetcher_paper.abstract
        assert result["pdf_url"] == sample_fetcher_paper.pdf_url
        assert result["published_date"] == sample_fetcher_paper.published_date.isoformat()
        assert result["categories"] == sample_fetcher_paper.categories


class TestArxivFetcher:
    """Test cases for the ArxivFetcher class."""

    @pytest.mark.asyncio
    async def test_init(self) -> None:
        """Test ArxivFetcher initialization."""
        fetcher = ArxivFetcher(timeout=30)
        assert fetcher.timeout == 30
        assert fetcher._client is None

    @pytest.mark.asyncio
    async def test_get_client(self) -> None:
        """Test getting or creating HTTP client."""
        fetcher = ArxivFetcher()
        client1 = await fetcher._get_client()
        client2 = await fetcher._get_client()

        assert client1 is client2, "Should return the same client instance"
        assert isinstance(client1, httpx.AsyncClient)

        await fetcher.close()

    @pytest.mark.asyncio
    async def test_close(self) -> None:
        """Test closing the HTTP client."""
        fetcher = ArxivFetcher()
        await fetcher._get_client()
        await fetcher.close()

        assert fetcher._client is None

    @pytest.mark.asyncio
    async def test_parse_response(
        self, sample_arxiv_xml_response: str, sample_fetcher_paper: Paper
    ) -> None:
        """Test parsing arXiv XML response."""
        fetcher = ArxivFetcher()
        papers = fetcher._parse_response(sample_arxiv_xml_response)

        assert len(papers) == 1
        paper = papers[0]

        assert paper.id == sample_fetcher_paper.id
        assert paper.title == sample_fetcher_paper.title
        assert "Alice Smith" in paper.authors
        assert "Bob Johnson" in paper.authors
        assert paper.abstract == sample_fetcher_paper.abstract
        assert paper.pdf_url == sample_fetcher_paper.pdf_url
        assert paper.published_date == datetime.date(2023, 1, 15)
        assert "cs.AI" in paper.categories
        assert "cs.LG" in paper.categories

    @pytest.mark.asyncio
    async def test_parse_empty_response(self, sample_arxiv_empty_response: str) -> None:
        """Test parsing empty arXiv response."""
        fetcher = ArxivFetcher()
        papers = fetcher._parse_response(sample_arxiv_empty_response)

        assert len(papers) == 0

    @pytest.mark.asyncio
    async def test_parse_entry_missing_id(self) -> None:
        """Test parsing entry with missing ID returns None."""
        fetcher = ArxivFetcher()
        xml_entry = """<entry xmlns="http://www.w3.org/2005/Atom">
            <title>Test Paper</title>
            <summary>Test summary</summary>
        </entry>"""

        import xml.etree.ElementTree as ET
        entry = ET.fromstring(xml_entry)
        result = fetcher._parse_entry(entry)

        assert result is None

    @pytest.mark.asyncio
    async def test_parse_entry_missing_title(self) -> None:
        """Test parsing entry with missing title returns None."""
        fetcher = ArxivFetcher()
        xml_entry = """<entry xmlns="http://www.w3.org/2005/Atom">
            <id>http://arxiv.org/abs/2301.12345</id>
            <summary>Test summary</summary>
        </entry>"""

        import xml.etree.ElementTree as ET
        entry = ET.fromstring(xml_entry)
        result = fetcher._parse_entry(entry)

        assert result is None

    @pytest.mark.asyncio
    async def test_fetch_papers(
        self, sample_arxiv_xml_response: str
    ) -> None:
        """Test fetching papers from arXiv API."""
        fetcher = ArxivFetcher()

        # Mock the HTTP client
        mock_response = MagicMock()
        mock_response.text = sample_arxiv_xml_response
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        fetcher._client = mock_client

        papers = await fetcher.fetch_papers(
            categories=["cs.AI", "cs.LG"],
            date=datetime.date(2023, 1, 15),
            max_results=100,
        )

        assert len(papers) == 1
        assert papers[0].id == "2301.12345"

        await fetcher.close()

    @pytest.mark.asyncio
    async def test_fetch_papers_default_date(
        self, sample_arxiv_xml_response: str
    ) -> None:
        """Test fetching papers with default date (today)."""
        fetcher = ArxivFetcher()

        mock_response = MagicMock()
        mock_response.text = sample_arxiv_xml_response
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        fetcher._client = mock_client

        papers = await fetcher.fetch_papers(categories=["cs.AI"])

        # Should not raise an error
        assert isinstance(papers, list)

        await fetcher.close()

    @pytest.mark.asyncio
    async def test_fetch_by_id(
        self, sample_arxiv_xml_response: str
    ) -> None:
        """Test fetching a specific paper by ID."""
        fetcher = ArxivFetcher()

        mock_response = MagicMock()
        mock_response.text = sample_arxiv_xml_response
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        fetcher._client = mock_client

        paper = await fetcher.fetch_by_id("2301.12345")

        assert paper is not None
        assert paper.id == "2301.12345"

        await fetcher.close()

    @pytest.mark.asyncio
    async def test_fetch_by_id_not_found(self) -> None:
        """Test fetching non-existent paper returns None."""
        fetcher = ArxivFetcher()

        empty_response = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
</feed>"""

        mock_response = MagicMock()
        mock_response.text = empty_response
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        fetcher._client = mock_client

        paper = await fetcher.fetch_by_id("9999.99999")

        assert paper is None

        await fetcher.close()

    @pytest.mark.asyncio
    async def test_http_error_handling(self) -> None:
        """Test handling of HTTP errors."""
        fetcher = ArxivFetcher()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.HTTPStatusError(
            "Not Found", request=MagicMock(), response=MagicMock()
        ))

        fetcher._client = mock_client

        with pytest.raises(httpx.HTTPStatusError):
            await fetcher.fetch_papers(categories=["cs.AI"])

        await fetcher.close()

    @pytest.mark.asyncio
    async def test_parse_malformed_entry(self) -> None:
        """Test that malformed entries are skipped without crashing."""
        fetcher = ArxivFetcher()

        # Mix of valid and invalid entries
        xml_with_errors = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2301.11111</id>
    <title>Valid Paper</title>
    <author><name>Valid Author</name></author>
    <summary>Valid summary</summary>
    <link href="https://arxiv.org/pdf/2301.11111.pdf" type="application/pdf"/>
    <published>2023-01-15T00:00:00Z</published>
    <category term="cs.AI"/>
  </entry>
  <entry>
    <!-- Missing ID -->
    <title>Invalid Paper</title>
  </entry>
</feed>"""

        papers = fetcher._parse_response(xml_with_errors)

        assert len(papers) == 1
        assert papers[0].id == "2301.11111"

    @pytest.mark.asyncio
    async def test_paper_title_cleanup(self) -> None:
        """Test that paper titles are cleaned properly."""
        fetcher = ArxivFetcher()

        xml_with_newlines = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2301.12345</id>
    <title>  Title with
    multiple
    newlines  </title>
    <author><name>Test Author</name></author>
    <summary>Test summary</summary>
    <link href="https://arxiv.org/pdf/2301.12345.pdf" type="application/pdf"/>
    <published>2023-01-15T00:00:00Z</published>
    <category term="cs.AI"/>
  </entry>
</feed>"""

        papers = fetcher._parse_response(xml_with_newlines)

        assert len(papers) == 1
        # Title should have newlines replaced with spaces and be stripped
        assert "\n" not in papers[0].title
        assert papers[0].title == papers[0].title.strip()

    @pytest.mark.asyncio
    async def test_multiple_categories(self) -> None:
        """Test parsing paper with multiple categories."""
        fetcher = ArxivFetcher()

        xml_multi_cat = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2301.12345</id>
    <title>Multi-category Paper</title>
    <author><name>Test Author</name></author>
    <summary>Test summary</summary>
    <link href="https://arxiv.org/pdf/2301.12345.pdf" type="application/pdf"/>
    <published>2023-01-15T00:00:00Z</published>
    <category term="cs.AI"/>
    <category term="cs.LG"/>
    <category term="cs.CL"/>
  </entry>
</feed>"""

        papers = fetcher._parse_response(xml_multi_cat)

        assert len(papers) == 1
        assert len(papers[0].categories) == 3
        assert "cs.AI" in papers[0].categories
        assert "cs.LG" in papers[0].categories
        assert "cs.CL" in papers[0].categories
