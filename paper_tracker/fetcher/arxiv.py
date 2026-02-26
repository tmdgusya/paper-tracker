"""arXiv API fetcher using httpx async client."""

import datetime
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class Paper:
    """Represents an arXiv paper."""

    id: str
    title: str
    authors: list[str]
    abstract: str
    pdf_url: str
    published_date: datetime.date
    categories: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert paper to dictionary.

        Returns:
            Dictionary representation of the paper
        """
        return {
            "id": self.id,
            "title": self.title,
            "authors": self.authors,
            "abstract": self.abstract,
            "pdf_url": self.pdf_url,
            "published_date": self.published_date.isoformat(),
            "categories": self.categories,
        }


class ArxivFetcher:
    """Fetch papers from the arXiv API."""

    # arXiv API namespace
    ARXIV_NAMESPACE = {"arxiv": "http://arxiv.org/schemas/atom"}
    BASE_URL = "https://export.arxiv.org/api/query"

    def __init__(self, timeout: int = 30) -> None:
        """Initialize the fetcher.

        Args:
            timeout: HTTP request timeout in seconds
        """
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client.

        Returns:
            Async HTTP client instance
        """
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def fetch_papers(
        self,
        categories: list[str],
        date: datetime.date | None = None,
        max_results: int = 100,
    ) -> list[Paper]:
        """Fetch papers from arXiv by category and date.

        Args:
            categories: List of arXiv categories (e.g., ["cs.AI", "cs.LG"])
            date: Date to fetch papers for. If None, uses today.
            max_results: Maximum number of results to return

        Returns:
            List of Paper objects
        """
        if date is None:
            date = datetime.date.today()

        # Build query for categories and date
        cat_query = " OR ".join(f"cat:{cat}" for cat in categories)
        date_str = date.strftime("%Y%m%d")
        query = f"({cat_query}) AND submittedDate:{date_str}*"

        # Build request parameters
        params = {
            "search_query": query,
            "start": 0,
            "max_results": max_results,
        }

        client = await self._get_client()
        response = await client.get(self.BASE_URL, params=params)
        response.raise_for_status()

        return self._parse_response(response.text)

    def _parse_response(self, xml_content: str) -> list[Paper]:
        """Parse arXiv API XML response.

        Args:
            xml_content: Raw XML response from arXiv API

        Returns:
            List of Paper objects
        """
        papers: list[Paper] = []

        # Parse XML
        root = ET.fromstring(xml_content)

        # Find all entry elements
        for entry in root.findall("atom:entry", namespaces={"atom": "http://www.w3.org/2005/Atom"}):
            try:
                paper = self._parse_entry(entry)
                if paper:
                    papers.append(paper)
            except Exception:
                # Skip malformed entries
                continue

        return papers

    def _parse_entry(self, entry: ET.Element) -> Paper | None:
        """Parse a single entry from the XML response.

        Args:
            entry: XML element representing a paper entry

        Returns:
            Paper object or None if parsing fails
        """
        # Extract ID
        id_elem = entry.find("atom:id", namespaces={"atom": "http://www.w3.org/2005/Atom"})
        if id_elem is None or id_elem.text is None:
            return None
        paper_id = id_elem.text.split("/")[-1]

        # Extract title
        title_elem = entry.find("atom:title", namespaces={"atom": "http://www.w3.org/2005/Atom"})
        if title_elem is None or title_elem.text is None:
            return None
        title = title_elem.text.strip().replace("\n", " ")

        # Extract authors
        authors: list[str] = []
        for author in entry.findall("atom:author", namespaces={"atom": "http://www.w3.org/2005/Atom"}):
            name_elem = author.find("atom:name", namespaces={"atom": "http://www.w3.org/2005/Atom"})
            if name_elem is not None and name_elem.text is not None:
                authors.append(name_elem.text)

        # Extract abstract
        summary_elem = entry.find("atom:summary", namespaces={"atom": "http://www.w3.org/2005/Atom"})
        if summary_elem is None or summary_elem.text is None:
            return None
        abstract = summary_elem.text.strip().replace("\n", " ")

        # Extract PDF URL
        pdf_elem = entry.find("atom:link[@type='application/pdf']", namespaces={"atom": "http://www.w3.org/2005/Atom"})
        if pdf_elem is None:
            return None
        pdf_url = pdf_elem.get("href", "")

        # Extract published date
        published_elem = entry.find("atom:published", namespaces={"atom": "http://www.w3.org/2005/Atom"})
        if published_elem is None or published_elem.text is None:
            return None
        published_date = datetime.datetime.fromisoformat(published_elem.text.replace("Z", "+00:00")).date()

        # Extract categories
        categories: list[str] = []
        for cat in entry.findall("atom:category", namespaces={"atom": "http://www.w3.org/2005/Atom"}):
            term = cat.get("term")
            if term:
                categories.append(term)

        return Paper(
            id=paper_id,
            title=title,
            authors=authors,
            abstract=abstract,
            pdf_url=pdf_url,
            published_date=published_date,
            categories=categories,
        )

    async def fetch_by_id(self, paper_id: str) -> Paper | None:
        """Fetch a specific paper by its arXiv ID.

        Args:
            paper_id: arXiv paper ID (e.g., "2301.12345")

        Returns:
            Paper object or None if not found
        """
        params = {
            "id_list": paper_id,
        }

        client = await self._get_client()
        response = await client.get(self.BASE_URL, params=params)
        response.raise_for_status()

        papers = self._parse_response(response.text)
        return papers[0] if papers else None
