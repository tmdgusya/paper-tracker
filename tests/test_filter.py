"""Tests for the paper filter module."""

import datetime

import pytest

from paper_tracker.fetcher.filter import PaperFilter, FilterResult
from paper_tracker.fetcher.arxiv import Paper


class TestFilterResult:
    """Test cases for the FilterResult dataclass."""

    def test_filter_result_to_dict(self, sample_fetcher_paper: Paper) -> None:
        """Test converting a FilterResult to dictionary."""
        result = FilterResult(
            paper=sample_fetcher_paper,
            matched_keywords=["machine learning", "AI"],
            relevance_score=0.85,
        )

        output = result.to_dict()

        assert isinstance(output, dict)
        assert "paper" in output
        assert output["matched_keywords"] == ["machine learning", "AI"]
        assert output["relevance_score"] == 0.85


class TestPaperFilter:
    """Test cases for the PaperFilter class."""

    def test_init_default_case_insensitive(self) -> None:
        """Test filter initialization with case insensitivity."""
        keywords = ["Machine Learning", "NEURAL NETWORKS"]
        filter_obj = PaperFilter(keywords)

        assert filter_obj.keywords == ["machine learning", "neural networks"]
        assert filter_obj.case_sensitive is False

    def test_init_case_sensitive(self) -> None:
        """Test filter initialization with case sensitivity."""
        keywords = ["Machine Learning", "AI"]
        filter_obj = PaperFilter(keywords, case_sensitive=True)

        assert filter_obj.keywords == ["Machine Learning", "AI"]
        assert filter_obj.case_sensitive is True

    def test_filter_basic_matching(self, sample_fetcher_paper: Paper) -> None:
        """Test basic keyword filtering."""
        filter_obj = PaperFilter(["machine learning"])
        results = filter_obj.filter([sample_fetcher_paper])

        assert len(results) == 1
        assert results[0].paper.id == sample_fetcher_paper.id
        assert "machine learning" in results[0].matched_keywords

    def test_filter_no_match(self) -> None:
        """Test filtering with no matches."""
        paper = Paper(
            id="2301.12345",
            title="Quantum Computing Advances",
            authors=["Alice Smith"],
            abstract="This paper discusses quantum computing.",
            pdf_url="https://arxiv.org/pdf/2301.12345.pdf",
            published_date=datetime.date(2023, 1, 15),
            categories=["cs.ET"],
        )

        filter_obj = PaperFilter(["machine learning", "AI"])
        results = filter_obj.filter([paper])

        assert len(results) == 0

    def test_filter_multiple_keywords(self, sample_fetcher_paper: Paper) -> None:
        """Test filtering with multiple keywords."""
        # Modify sample paper to match multiple keywords
        paper = Paper(
            id="2301.12345",
            title="Advances in Machine Learning and Neural Networks",
            authors=["Alice Smith"],
            abstract="This paper discusses neural networks and deep learning approaches.",
            pdf_url="https://arxiv.org/pdf/2301.12345.pdf",
            published_date=datetime.date(2023, 1, 15),
            categories=["cs.AI"],
        )

        filter_obj = PaperFilter(["machine learning", "neural networks", "deep learning"])
        results = filter_obj.filter([paper])

        assert len(results) == 1
        # Should match all three keywords (2 in title + abstract)
        assert len(results[0].matched_keywords) >= 2

    def test_filter_min_matches(self) -> None:
        """Test filtering with minimum matches requirement."""
        paper1 = Paper(
            id="2301.00001",
            title="Machine Learning Paper",
            authors=["Author 1"],
            abstract="About ML",
            pdf_url="https://arxiv.org/pdf/2301.00001.pdf",
            published_date=datetime.date(2023, 1, 1),
            categories=["cs.AI"],
        )

        paper2 = Paper(
            id="2301.00002",
            title="Quantum Computing",
            authors=["Author 2"],
            abstract="About quantum",
            pdf_url="https://arxiv.org/pdf/2301.00002.pdf",
            published_date=datetime.date(2023, 1, 2),
            categories=["cs.ET"],
        )

        filter_obj = PaperFilter(["machine learning", "neural networks"])
        results = filter_obj.filter([paper1, paper2], min_matches=1)

        # Only paper1 should match (has "machine learning")
        assert len(results) == 1
        assert results[0].paper.id == "2301.00001"

    def test_filter_sorting_by_relevance(self) -> None:
        """Test that results are sorted by relevance score."""
        paper1 = Paper(
            id="2301.00001",
            title="Machine Learning and Neural Networks",  # 2 keyword matches
            authors=["Author 1"],
            abstract="About ML and NN",
            pdf_url="https://arxiv.org/pdf/2301.00001.pdf",
            published_date=datetime.date(2023, 1, 1),
            categories=["cs.AI"],
        )

        paper2 = Paper(
            id="2301.00002",
            title="Machine Learning Paper",  # 1 keyword match
            authors=["Author 2"],
            abstract="About ML",
            pdf_url="https://arxiv.org/pdf/2301.00002.pdf",
            published_date=datetime.date(2023, 1, 2),
            categories=["cs.AI"],
        )

        filter_obj = PaperFilter(["machine learning", "neural networks"])
        results = filter_obj.filter([paper2, paper1])  # Intentionally reversed order

        # paper1 should come first (higher relevance)
        assert results[0].paper.id == "2301.00001"
        assert results[1].paper.id == "2301.00002"

    def test_match_keywords_case_insensitive(self) -> None:
        """Test keyword matching is case insensitive by default."""
        paper = Paper(
            id="2301.12345",
            title="MACHINE LEARNING Advances",
            authors=["Author"],
            abstract="About ML",
            pdf_url="https://arxiv.org/pdf/2301.12345.pdf",
            published_date=datetime.date(2023, 1, 15),
            categories=["cs.AI"],
        )

        filter_obj = PaperFilter(["machine learning"])
        matched = filter_obj._match_keywords(paper)

        assert "machine learning" in matched

    def test_match_keywords_case_sensitive(self) -> None:
        """Test keyword matching with case sensitivity."""
        paper = Paper(
            id="2301.12345",
            title="MACHINE LEARNING Advances",
            authors=["Author"],
            abstract="About ML",
            pdf_url="https://arxiv.org/pdf/2301.12345.pdf",
            published_date=datetime.date(2023, 1, 15),
            categories=["cs.AI"],
        )

        filter_obj = PaperFilter(["Machine Learning"], case_sensitive=True)
        matched = filter_obj._match_keywords(paper)

        assert len(matched) == 0  # Should not match due to case difference

    def test_calculate_score_title_boost(self) -> None:
        """Test that title matches get a relevance boost."""
        paper = Paper(
            id="2301.12345",
            title="Machine Learning Advances",
            authors=["Author"],
            abstract="About neural networks and AI",
            pdf_url="https://arxiv.org/pdf/2301.12345.pdf",
            published_date=datetime.date(2023, 1, 15),
            categories=["cs.AI"],
        )

        filter_obj = PaperFilter(["machine learning", "neural networks"])
        score = filter_obj._calculate_score(paper, ["machine learning", "neural networks"])

        # Should have a boost since one keyword is in the title
        assert score > 0
        assert score <= 1.0

    def test_calculate_score_no_matches(self) -> None:
        """Test score calculation with no matches."""
        paper = Paper(
            id="2301.12345",
            title="Some Paper",
            authors=["Author"],
            abstract="Some abstract",
            pdf_url="https://arxiv.org/pdf/2301.12345.pdf",
            published_date=datetime.date(2023, 1, 15),
            categories=["cs.AI"],
        )

        filter_obj = PaperFilter(["machine learning"])
        score = filter_obj._calculate_score(paper, [])

        assert score == 0.0

    def test_filter_by_category(self) -> None:
        """Test filtering by arXiv category."""
        papers = [
            Paper(
                id=f"2301.0000{i}",
                title=f"Paper {i}",
                authors=["Author"],
                abstract="Abstract",
                pdf_url=f"https://arxiv.org/pdf/2301.0000{i}.pdf",
                published_date=datetime.date(2023, 1, i + 1),
                categories=["cs.AI", "cs.LG"] if i % 2 == 0 else ["cs.ET"],
            )
            for i in range(5)
        ]

        filter_obj = PaperFilter([])
        filtered = filter_obj.filter_by_category(papers, ["cs.AI"])

        # Papers 0, 2, 4 have cs.AI
        assert len(filtered) == 3

    def test_filter_by_category_multiple(self) -> None:
        """Test filtering by multiple categories."""
        papers = [
            Paper(
                id="2301.00001",
                title="AI Paper",
                authors=["Author"],
                abstract="Abstract",
                pdf_url="https://arxiv.org/pdf/2301.00001.pdf",
                published_date=datetime.date(2023, 1, 1),
                categories=["cs.AI"],
            ),
            Paper(
                id="2301.00002",
                title="LG Paper",
                authors=["Author"],
                abstract="Abstract",
                pdf_url="https://arxiv.org/pdf/2301.00002.pdf",
                published_date=datetime.date(2023, 1, 2),
                categories=["cs.LG"],
            ),
            Paper(
                id="2301.00003",
                title="ET Paper",
                authors=["Author"],
                abstract="Abstract",
                pdf_url="https://arxiv.org/pdf/2301.00003.pdf",
                published_date=datetime.date(2023, 1, 3),
                categories=["cs.ET"],
            ),
        ]

        filter_obj = PaperFilter([])
        filtered = filter_obj.filter_by_category(papers, ["cs.AI", "cs.LG"])

        assert len(filtered) == 2
        assert any(p.id == "2301.00001" for p in filtered)
        assert any(p.id == "2301.00002" for p in filtered)

    def test_filter_by_author(self) -> None:
        """Test filtering by author name."""
        papers = [
            Paper(
                id="2301.00001",
                title="Paper 1",
                authors=["Alice Smith", "Bob Johnson"],
                abstract="Abstract",
                pdf_url="https://arxiv.org/pdf/2301.00001.pdf",
                published_date=datetime.date(2023, 1, 1),
                categories=["cs.AI"],
            ),
            Paper(
                id="2301.00002",
                title="Paper 2",
                authors=["Charlie Brown"],
                abstract="Abstract",
                pdf_url="https://arxiv.org/pdf/2301.00002.pdf",
                published_date=datetime.date(2023, 1, 2),
                categories=["cs.AI"],
            ),
        ]

        filter_obj = PaperFilter([])
        filtered = filter_obj.filter_by_author(papers, ["Alice Smith"])

        assert len(filtered) == 1
        assert filtered[0].id == "2301.00001"

    def test_filter_by_author_case_insensitive(self) -> None:
        """Test author filtering is case insensitive by default."""
        papers = [
            Paper(
                id="2301.00001",
                title="Paper",
                authors=["ALICE SMITH"],
                abstract="Abstract",
                pdf_url="https://arxiv.org/pdf/2301.00001.pdf",
                published_date=datetime.date(2023, 1, 1),
                categories=["cs.AI"],
            ),
        ]

        filter_obj = PaperFilter([], case_sensitive=False)
        filtered = filter_obj.filter_by_author(papers, ["alice smith"])

        assert len(filtered) == 1

    def test_filter_by_author_partial_match(self) -> None:
        """Test author filtering with partial name matching."""
        papers = [
            Paper(
                id="2301.00001",
                title="Paper",
                authors=["Alice Smith", "Bob Johnson"],
                abstract="Abstract",
                pdf_url="https://arxiv.org/pdf/2301.00001.pdf",
                published_date=datetime.date(2023, 1, 1),
                categories=["cs.AI"],
            ),
        ]

        filter_obj = PaperFilter([])
        filtered = filter_obj.filter_by_author(papers, ["Smith"])

        assert len(filtered) == 1

    def test_empty_keyword_list(self) -> None:
        """Test filter with empty keyword list."""
        paper = Paper(
            id="2301.12345",
            title="Test Paper",
            authors=["Author"],
            abstract="Abstract",
            pdf_url="https://arxiv.org/pdf/2301.12345.pdf",
            published_date=datetime.date(2023, 1, 15),
            categories=["cs.AI"],
        )

        filter_obj = PaperFilter([])
        results = filter_obj.filter([paper])

        # With no keywords, nothing should match (min_matches defaults to 1)
        assert len(results) == 0

    def test_abstract_matching(self) -> None:
        """Test that keywords are matched in abstract."""
        paper = Paper(
            id="2301.12345",
            title="Computing Advances",
            authors=["Author"],
            abstract="This paper introduces novel machine learning techniques.",
            pdf_url="https://arxiv.org/pdf/2301.12345.pdf",
            published_date=datetime.date(2023, 1, 15),
            categories=["cs.AI"],
        )

        filter_obj = PaperFilter(["machine learning"])
        results = filter_obj.filter([paper])

        assert len(results) == 1
        assert "machine learning" in results[0].matched_keywords
