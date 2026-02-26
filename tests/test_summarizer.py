"""Tests for the AI summarizer module."""

import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

import pytest

from paper_tracker.summarizer.claude import Summarizer, PaperSummary
from paper_tracker.fetcher.arxiv import Paper


class TestPaperSummary:
    """Test cases for the PaperSummary dataclass."""

    def test_paper_summary_to_dict(self) -> None:
        """Test converting a PaperSummary to dictionary."""
        summary = PaperSummary(
            paper_id="2301.12345",
            key_points=["Point 1", "Point 2"],
            main_contributions=["Contribution 1"],
            relevance_score=0.85,
            summary_text="This is a summary",
            generated_at=datetime.datetime(2023, 1, 15, 10, 30),
        )

        result = summary.to_dict()

        assert isinstance(result, dict)
        assert result["paper_id"] == "2301.12345"
        assert result["key_points"] == ["Point 1", "Point 2"]
        assert result["main_contributions"] == ["Contribution 1"]
        assert result["relevance_score"] == 0.85
        assert result["summary_text"] == "This is a summary"
        assert result["generated_at"] == "2023-01-15T10:30:00"


class TestSummarizer:
    """Test cases for the Summarizer class."""

    def test_init(self) -> None:
        """Test Summarizer initialization."""
        summarizer = Summarizer(model="claude-sonnet-4-6")

        assert summarizer.model == "claude-sonnet-4-6"
        assert summarizer.gt_script_path == Path.home() / "gt-switcher" / "gt.sh"

    def test_init_with_custom_script_path(self, temp_dir: Path) -> None:
        """Test Summarizer initialization with custom script path."""
        custom_path = temp_dir / "custom_gt.sh"
        summarizer = Summarizer(gt_script_path=custom_path)

        assert summarizer.gt_script_path == custom_path

    def test_build_prompt_without_keywords(self, sample_fetcher_paper: Paper) -> None:
        """Test building a prompt without keywords."""
        summarizer = Summarizer()
        prompt = summarizer._build_prompt(sample_fetcher_paper, None)

        assert "You are an expert research assistant" in prompt
        assert sample_fetcher_paper.title in prompt
        assert ", ".join(sample_fetcher_paper.authors) in prompt
        assert sample_fetcher_paper.abstract in prompt
        assert sample_fetcher_paper.id in prompt
        assert "Keywords to consider" not in prompt

    def test_build_prompt_with_keywords(self, sample_fetcher_paper: Paper) -> None:
        """Test building a prompt with keywords."""
        summarizer = Summarizer()
        keywords = ["machine learning", "neural networks"]
        prompt = summarizer._build_prompt(sample_fetcher_paper, keywords)

        assert "Keywords to consider for relevance: machine learning, neural networks" in prompt

    def test_parse_response_valid_json(self) -> None:
        """Test parsing a valid JSON response."""
        summarizer = Summarizer()
        response = '''{
    "key_points": ["Point 1", "Point 2"],
    "main_contributions": ["Contribution 1"],
    "relevance_score": 0.85,
    "summary_text": "This is a summary"
}'''

        summary = summarizer._parse_response("2301.12345", response)

        assert summary.paper_id == "2301.12345"
        assert summary.key_points == ["Point 1", "Point 2"]
        assert summary.main_contributions == ["Contribution 1"]
        assert summary.relevance_score == 0.85
        assert summary.summary_text == "This is a summary"

    def test_parse_response_json_in_markdown(self) -> None:
        """Test parsing JSON response wrapped in markdown code blocks."""
        summarizer = Summarizer()
        response = '''Here's the summary:

```json
{
    "key_points": ["Point 1"],
    "main_contributions": ["Contribution 1"],
    "relevance_score": 0.9,
    "summary_text": "Summary text"
}
```

Hope this helps!'''

        summary = summarizer._parse_response("2301.12345", response)

        assert summary.paper_id == "2301.12345"
        assert summary.key_points == ["Point 1"]
        assert summary.relevance_score == 0.9

    def test_parse_response_invalid_json(self) -> None:
        """Test parsing invalid JSON returns fallback summary."""
        summarizer = Summarizer()
        response = "This is not JSON at all"

        summary = summarizer._parse_response("2301.12345", response)

        assert summary.paper_id == "2301.12345"
        assert summary.summary_text == "This is not JSON at all"
        assert summary.key_points == []
        assert summary.main_contributions == []
        assert summary.relevance_score == 0.0

    def test_parse_response_long_text_truncated(self) -> None:
        """Test that long non-JSON responses are truncated."""
        summarizer = Summarizer()
        long_text = "x" * 600  # Longer than 500 chars

        summary = summarizer._parse_response("2301.12345", long_text)

        assert len(summary.summary_text) <= 500

    @pytest.mark.asyncio
    async def test_summarize_paper(self, sample_fetcher_paper: Paper) -> None:
        """Test summarizing a single paper."""
        summarizer = Summarizer()

        mock_response = '''{
    "key_points": ["Novel ML approach"],
    "main_contributions": ["20% accuracy improvement"],
    "relevance_score": 0.85,
    "summary_text": "This paper introduces a new method."
}'''

        with patch.object(summarizer, '_call_claude', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response

            summary = await summarizer.summarize_paper(sample_fetcher_paper)

            assert summary.paper_id == sample_fetcher_paper.id
            assert summary.key_points == ["Novel ML approach"]
            assert summary.relevance_score == 0.85

    @pytest.mark.asyncio
    async def test_summarize_paper_with_keywords(self, sample_fetcher_paper: Paper) -> None:
        """Test summarizing with keywords guidance."""
        summarizer = Summarizer()
        keywords = ["machine learning"]

        with patch.object(summarizer, '_call_claude', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = '{"key_points": [], "main_contributions": [], "relevance_score": 0.5, "summary_text": "Summary"}'

            await summarizer.summarize_paper(sample_fetcher_paper, keywords)

            # Verify keywords were included in the prompt
            call_args = mock_call.call_args[0][0]
            assert "machine learning" in call_args

    @pytest.mark.asyncio
    async def test_summarize_papers(self) -> None:
        """Test summarizing multiple papers."""
        summarizer = Summarizer()

        papers = [
            Paper(
                id=f"2301.0000{i}",
                title=f"Paper {i}",
                authors=[f"Author {i}"],
                abstract=f"Abstract {i}",
                pdf_url=f"https://arxiv.org/pdf/2301.0000{i}.pdf",
                published_date=datetime.date(2023, 1, i + 1),
                categories=["cs.AI"],
            )
            for i in range(3)
        ]

        async def mock_summarize(paper, keywords=None):
            return PaperSummary(
                paper_id=paper.id,
                key_points=[f"Point for {paper.id}"],
                main_contributions=[],
                relevance_score=0.5,
                summary_text=f"Summary for {paper.id}",
                generated_at=datetime.datetime.now(),
            )

        with patch.object(summarizer, 'summarize_paper', side_effect=mock_summarize):
            summaries = await summarizer.summarize_papers(papers)

            assert len(summaries) == 3
            assert all(s.paper_id.startswith("2301.0000") for s in summaries)

    @pytest.mark.asyncio
    async def test_summarize_papers_with_error(self) -> None:
        """Test that errors in summarizing individual papers are handled gracefully."""
        summarizer = Summarizer()

        papers = [
            Paper(
                id="2301.00001",
                title="Valid Paper",
                authors=["Author"],
                abstract="Abstract",
                pdf_url="https://arxiv.org/pdf/2301.00001.pdf",
                published_date=datetime.date(2023, 1, 1),
                categories=["cs.AI"],
            ),
            Paper(
                id="2301.00002",
                title="Error Paper",
                authors=["Author"],
                abstract="Abstract",
                pdf_url="https://arxiv.org/pdf/2301.00002.pdf",
                published_date=datetime.date(2023, 1, 2),
                categories=["cs.AI"],
            ),
        ]

        async def mock_summarize_with_error(paper, keywords=None):
            if paper.id == "2301.00002":
                raise RuntimeError("Simulated error")
            return PaperSummary(
                paper_id=paper.id,
                key_points=["Point"],
                main_contributions=[],
                relevance_score=0.5,
                summary_text="Summary",
                generated_at=datetime.datetime.now(),
            )

        with patch.object(summarizer, 'summarize_paper', side_effect=mock_summarize_with_error):
            summaries = await summarizer.summarize_papers(papers)

            assert len(summaries) == 2
            assert summaries[0].paper_id == "2301.00001"
            assert summaries[0].key_points == ["Point"]
            assert summaries[1].paper_id == "2301.00002"
            assert "Error generating summary" in summaries[1].summary_text

    @pytest.mark.asyncio
    async def test_close(self) -> None:
        """Test the close method (should be a no-op for subprocess implementation)."""
        summarizer = Summarizer()
        await summarizer.close()  # Should not raise an error

    @pytest.mark.asyncio
    async def test_parse_response_with_partial_json(self) -> None:
        """Test parsing response with partial/malformed JSON."""
        summarizer = Summarizer()
        response = '''Some text before
{"key_points": ["Point 1"]}
Some text after'''

        summary = summarizer._parse_response("2301.12345", response)

        # Should extract the JSON part
        assert summary.paper_id == "2301.12345"
        assert summary.key_points == ["Point 1"]

    @pytest.mark.asyncio
    async def test_parse_response_empty_fields(self) -> None:
        """Test parsing JSON with empty fields."""
        summarizer = Summarizer()
        response = '''{
    "key_points": [],
    "main_contributions": [],
    "relevance_score": 0.0,
    "summary_text": ""
}'''

        summary = summarizer._parse_response("2301.12345", response)

        assert summary.paper_id == "2301.12345"
        assert summary.key_points == []
        assert summary.main_contributions == []
        assert summary.relevance_score == 0.0
        assert summary.summary_text == ""
