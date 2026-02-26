"""Tests for the Markdown report generator module."""

import datetime
from pathlib import Path

import pytest

from paper_tracker.reporter.markdown import ReportGenerator
from paper_tracker.store.database import Paper


class TestReportGenerator:
    """Test cases for the ReportGenerator class."""

    def test_init(self, temp_dir: Path) -> None:
        """Test ReportGenerator initialization."""
        reports_dir = temp_dir / "reports"
        generator = ReportGenerator(reports_dir)

        assert generator.reports_dir == reports_dir
        assert reports_dir.exists()

    def test_init_creates_directory(self, temp_dir: Path) -> None:
        """Test that init creates the reports directory if it doesn't exist."""
        reports_dir = temp_dir / "new_reports"
        assert not reports_dir.exists()

        generator = ReportGenerator(reports_dir)

        assert reports_dir.exists()

    def test_avg_relevance_empty_list(self, temp_dir: Path) -> None:
        """Test average relevance calculation with empty list."""
        generator = ReportGenerator(temp_dir / "reports")
        avg = generator._avg_relevance([])

        # Should handle empty list gracefully
        assert isinstance(avg, float) or avg == 0.0

    def test_avg_relevance_with_papers(self, temp_dir: Path) -> None:
        """Test average relevance calculation."""
        generator = ReportGenerator(temp_dir / "reports")

        papers = [
            Paper(
                id=f"2301.0000{i}",
                title=f"Paper {i}",
                authors="Author",
                abstract="Abstract",
                url=f"https://arxiv.org/abs/2301.0000{i}",
                pdf_url=f"https://arxiv.org/pdf/2301.0000{i}.pdf",
                published_date=datetime.date(2023, 1, i),
                fetched_date=datetime.date(2023, 1, i),
                relevance_score=float(i),
            )
            for i in range(1, 6)  # Scores: 1.0, 2.0, 3.0, 4.0, 5.0
        ]

        avg = generator._avg_relevance(papers)
        assert avg == 3.0  # (1+2+3+4+5)/5 = 3.0

    def test_avg_relevance_with_none_scores(self, temp_dir: Path) -> None:
        """Test average relevance with None scores."""
        generator = ReportGenerator(temp_dir / "reports")

        papers = [
            Paper(
                id="2301.00001",
                title="Paper 1",
                authors="Author",
                abstract="Abstract",
                url="https://arxiv.org/abs/2301.00001",
                pdf_url="https://arxiv.org/pdf/2301.00001.pdf",
                published_date=datetime.date(2023, 1, 1),
                fetched_date=datetime.date(2023, 1, 1),
                relevance_score=None,
            ),
            Paper(
                id="2301.00002",
                title="Paper 2",
                authors="Author",
                abstract="Abstract",
                url="https://arxiv.org/abs/2301.00002",
                pdf_url="https://arxiv.org/pdf/2301.00002.pdf",
                published_date=datetime.date(2023, 1, 2),
                fetched_date=datetime.date(2023, 1, 2),
                relevance_score=8.0,
            ),
        ]

        avg = generator._avg_relevance(papers)
        assert avg == 8.0  # Only the non-None score

    def test_get_report_path(self, temp_dir: Path) -> None:
        """Test getting report path for a specific date."""
        generator = ReportGenerator(temp_dir / "reports")
        target_date = datetime.date(2023, 1, 15)

        path = generator.get_report_path(target_date)

        assert path == temp_dir / "reports" / "2023-01-15.md"

    def test_get_report_path_default_today(self, temp_dir: Path) -> None:
        """Test getting report path defaults to today."""
        generator = ReportGenerator(temp_dir / "reports")
        path = generator.get_report_path()

        today = datetime.date.today()
        assert path == temp_dir / "reports" / f"{today.isoformat()}.md"

    def test_report_exists(self, temp_dir: Path) -> None:
        """Test checking if report exists."""
        generator = ReportGenerator(temp_dir / "reports")
        target_date = datetime.date(2023, 1, 15)

        # Report doesn't exist yet
        assert not generator.report_exists(target_date)

        # Create the report
        generator.get_report_path(target_date).write_text("test")

        # Now it exists
        assert generator.report_exists(target_date)

    def test_load_report(self, temp_dir: Path) -> None:
        """Test loading an existing report."""
        generator = ReportGenerator(temp_dir / "reports")
        target_date = datetime.date(2023, 1, 15)
        content = "# Test Report\n\nThis is a test."

        # Create report file
        generator.get_report_path(target_date).write_text(content)

        # Load it
        loaded = generator.load_report(target_date)

        assert loaded == content

    def test_load_report_not_found(self, temp_dir: Path) -> None:
        """Test loading non-existent report returns None."""
        generator = ReportGenerator(temp_dir / "reports")

        loaded = generator.load_report(datetime.date(2023, 1, 15))

        assert loaded is None

    def test_generate_daily_report_basic(self, temp_dir: Path) -> None:
        """Test generating a basic daily report."""
        generator = ReportGenerator(temp_dir / "reports")
        target_date = datetime.date(2023, 1, 15)

        paper = Paper(
            id="2301.12345",
            title="Test Paper",
            authors="Author One, Author Two",
            abstract="This is a test abstract.",
            url="https://arxiv.org/abs/2301.12345",
            pdf_url="https://arxiv.org/pdf/2301.12345.pdf",
            published_date=target_date,
            fetched_date=target_date,
            summary="This is a summary.",
            key_points="Point 1\nPoint 2\nPoint 3",
            relevance_score=8.5,
            status="summarized",
        )

        report = generator.generate_daily_report([paper], target_date)

        assert "# Daily Paper Report - 2023-01-15" in report
        assert "**Total Papers**: 1" in report
        assert "Test Paper" in report
        assert "Author One, Author Two" in report
        assert "This is a summary." in report
        assert "Point 1" in report
        assert "Point 2" in report
        assert "Point 3" in report

    def test_generate_daily_report_with_multiple_papers(self, temp_dir: Path) -> None:
        """Test generating report with multiple papers."""
        generator = ReportGenerator(temp_dir / "reports")
        target_date = datetime.date(2023, 1, 15)

        papers = [
            Paper(
                id=f"2301.0000{i}",
                title=f"Paper {i}",
                authors=f"Author {i}",
                abstract=f"Abstract {i}",
                url=f"https://arxiv.org/abs/2301.0000{i}",
                pdf_url=f"https://arxiv.org/pdf/2301.0000{i}.pdf",
                published_date=target_date,
                fetched_date=target_date,
                relevance_score=float(i),
                status="summarized",
            )
            for i in range(1, 8)  # 7 papers
        ]

        report = generator.generate_daily_report(papers, target_date)

        assert "**Total Papers**: 7" in report
        assert "## 🏆 Top Papers" in report
        assert "## 📚 All Papers" in report

    def test_generate_daily_report_sorting(self, temp_dir: Path) -> None:
        """Test that papers are sorted by relevance score."""
        generator = ReportGenerator(temp_dir / "reports")
        target_date = datetime.date(2023, 1, 15)

        papers = [
            Paper(
                id="2301.00001",
                title="Low Score Paper",
                authors="Author",
                abstract="Abstract",
                url="https://arxiv.org/abs/2301.00001",
                pdf_url="https://arxiv.org/pdf/2301.00001.pdf",
                published_date=target_date,
                fetched_date=target_date,
                relevance_score=2.0,
                status="summarized",
            ),
            Paper(
                id="2301.00002",
                title="High Score Paper",
                authors="Author",
                abstract="Abstract",
                url="https://arxiv.org/abs/2301.00002",
                pdf_url="https://arxiv.org/pdf/2301.00002.pdf",
                published_date=target_date,
                fetched_date=target_date,
                relevance_score=9.0,
                status="summarized",
            ),
        ]

        report = generator.generate_daily_report(papers, target_date)

        # High score paper should appear first in Top Papers
        high_idx = report.index("High Score Paper")
        low_idx = report.index("Low Score Paper")
        assert high_idx < low_idx

    def test_generate_daily_report_statistics(self, temp_dir: Path) -> None:
        """Test statistics section in report."""
        generator = ReportGenerator(temp_dir / "reports")
        target_date = datetime.date(2023, 1, 15)

        papers = [
            Paper(
                id="2301.00001",
                title="Paper with summary",
                authors="Author",
                abstract="Abstract",
                url="https://arxiv.org/abs/2301.00001",
                pdf_url="https://arxiv.org/pdf/2301.00001.pdf",
                published_date=target_date,
                fetched_date=target_date,
                summary="Has summary",
                relevance_score=8.0,
                status="summarized",
            ),
            Paper(
                id="2301.00002",
                title="Paper without summary",
                authors="Author",
                abstract="Abstract",
                url="https://arxiv.org/abs/2301.00002",
                pdf_url="https://arxiv.org/pdf/2301.00002.pdf",
                published_date=target_date,
                fetched_date=target_date,
                relevance_score=6.0,
                status="pending",
            ),
        ]

        report = generator.generate_daily_report(papers, target_date)

        assert "## 📊 Statistics" in report
        assert "**Total papers collected**: 2" in report
        assert "**Papers with summaries**: 1" in report
        assert "**Average relevance score**: 7.0/10" in report

    def test_save_daily_report(self, temp_dir: Path) -> None:
        """Test saving a daily report to file."""
        generator = ReportGenerator(temp_dir / "reports")
        target_date = datetime.date(2023, 1, 15)

        paper = Paper(
            id="2301.12345",
            title="Test Paper",
            authors="Author",
            abstract="Abstract",
            url="https://arxiv.org/abs/2301.12345",
            pdf_url="https://arxiv.org/pdf/2301.12345.pdf",
            published_date=target_date,
            fetched_date=target_date,
            relevance_score=5.0,
            status="pending",
        )

        filepath = generator.save_daily_report([paper], target_date)

        assert filepath.exists()
        assert filepath == temp_dir / "reports" / "2023-01-15.md"

        content = filepath.read_text()
        assert "Test Paper" in content

    def test_save_daily_report_default_date(self, temp_dir: Path) -> None:
        """Test saving report defaults to today's date."""
        generator = ReportGenerator(temp_dir / "reports")

        paper = Paper(
            id="2301.12345",
            title="Test Paper",
            authors="Author",
            abstract="Abstract",
            url="https://arxiv.org/abs/2301.12345",
            pdf_url="https://arxiv.org/pdf/2301.12345.pdf",
            published_date=datetime.date.today(),
            fetched_date=datetime.date.today(),
            relevance_score=5.0,
            status="pending",
        )

        filepath = generator.save_daily_report([paper])

        today = datetime.date.today()
        assert filepath == temp_dir / "reports" / f"{today.isoformat()}.md"

    def test_paper_with_no_summary(self, temp_dir: Path) -> None:
        """Test report generation with papers that have no summary."""
        generator = ReportGenerator(temp_dir / "reports")
        target_date = datetime.date(2023, 1, 15)

        paper = Paper(
            id="2301.12345",
            title="Test Paper",
            authors="Author",
            abstract="Abstract",
            url="https://arxiv.org/abs/2301.12345",
            pdf_url="https://arxiv.org/pdf/2301.12345.pdf",
            published_date=target_date,
            fetched_date=target_date,
            relevance_score=None,
            status="pending",
        )

        report = generator.generate_daily_report([paper], target_date)

        # Should still include the paper
        assert "Test Paper" in report
        # Should show N/A for relevance
        assert "N/A" in report

    def test_report_footer(self, temp_dir: Path) -> None:
        """Test that report footer is generated correctly."""
        generator = ReportGenerator(temp_dir / "reports")
        target_date = datetime.date(2023, 1, 15)

        paper = Paper(
            id="2301.12345",
            title="Test Paper",
            authors="Author",
            abstract="Abstract",
            url="https://arxiv.org/abs/2301.12345",
            pdf_url="https://arxiv.org/pdf/2301.12345.pdf",
            published_date=target_date,
            fetched_date=target_date,
            relevance_score=5.0,
            status="pending",
        )

        report = generator.generate_daily_report([paper], target_date)

        assert "*Report generated on" in report
        assert "*Powered by paper-tracker*" in report

    def test_report_links(self, temp_dir: Path) -> None:
        """Test that paper links are correctly formatted."""
        generator = ReportGenerator(temp_dir / "reports")
        target_date = datetime.date(2023, 1, 15)

        paper = Paper(
            id="2301.12345",
            title="Test Paper",
            authors="Author",
            abstract="Abstract",
            url="https://arxiv.org/abs/2301.12345",
            pdf_url="https://arxiv.org/pdf/2301.12345.pdf",
            published_date=target_date,
            fetched_date=target_date,
            relevance_score=5.0,
            status="pending",
        )

        report = generator.generate_daily_report([paper], target_date)

        assert "[📄 View Paper](https://arxiv.org/abs/2301.12345)" in report
        assert "[📥 Download PDF](https://arxiv.org/pdf/2301.12345.pdf)" in report

    def test_key_points_formatting(self, temp_dir: Path) -> None:
        """Test key points are formatted as bullet list."""
        generator = ReportGenerator(temp_dir / "reports")
        target_date = datetime.date(2023, 1, 15)

        paper = Paper(
            id="2301.12345",
            title="Test Paper",
            authors="Author",
            abstract="Abstract",
            url="https://arxiv.org/abs/2301.12345",
            pdf_url="https://arxiv.org/pdf/2301.12345.pdf",
            published_date=target_date,
            fetched_date=target_date,
            key_points="Point 1\nPoint 2  \nPoint 3",  # Various whitespace
            relevance_score=5.0,
            status="summarized",
        )

        report = generator.generate_daily_report([paper], target_date)

        # Should be formatted as bullets
        assert "- Point 1" in report
        assert "- Point 2" in report
        assert "- Point 3" in report
