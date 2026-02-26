"""Markdown report generation for daily paper summaries."""

from datetime import date
from pathlib import Path
from typing import Optional

from paper_tracker.dateutil import get_current_date
from paper_tracker.store.database import Paper


class ReportGenerator:
    """Generate Markdown reports for daily paper summaries."""

    def __init__(self, reports_dir: Path | str):
        """Initialize report generator.

        Args:
            reports_dir: Directory to save reports
        """
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def generate_daily_report(
        self, papers: list[Paper], target_date: Optional[date] = None
    ) -> str:
        """Generate a daily report for papers.

        Args:
            papers: List of papers to include in the report
            target_date: Date for the report. Defaults to today.

        Returns:
            Markdown report content
        """
        if target_date is None:
            target_date = get_current_date()

        # Sort papers by relevance score
        sorted_papers = sorted(
            papers,
            key=lambda p: p.relevance_score or 0,
            reverse=True,
        )

        lines = []
        lines.append(f"# Daily Paper Report - {target_date.isoformat()}\n")
        lines.append(f"**Total Papers**: {len(papers)}\n")
        lines.append("---\n")

        # Statistics section
        lines.append("## 📊 Statistics\n")
        lines.append(f"- **Total papers collected**: {len(papers)}\n")
        lines.append(f"- **Papers with summaries**: {sum(1 for p in papers if p.summary)}\n")
        lines.append(f"- **Average relevance score**: {self._avg_relevance(papers):.1f}/10\n")
        lines.append("\n---\n")

        # Top papers section
        lines.append("## 🏆 Top Papers\n\n")
        top_papers = sorted_papers[:5] if len(sorted_papers) >= 5 else sorted_papers

        for i, paper in enumerate(top_papers, 1):
            lines.append(f"### {i}. {paper.title}\n\n")
            lines.append(f"**Authors**: {paper.authors}\n\n")
            lines.append(f"**Published**: {paper.published_date.isoformat()}\n\n")
            lines.append(f"**Relevance Score**: {paper.relevance_score or 'N/A'}/10\n\n")

            if paper.summary:
                lines.append(f"**Summary**: {paper.summary}\n\n")

            if paper.key_points:
                lines.append("**Key Points**:\n")
                for point in paper.key_points.split("\n"):
                    point = point.strip()
                    if point:
                        lines.append(f"- {point}\n")
                lines.append("\n")

            lines.append(f"[📄 View Paper]({paper.url}) | [📥 Download PDF]({paper.pdf_url})\n\n")
            lines.append("---\n\n")

        # All papers section
        if len(sorted_papers) > 5:
            lines.append("## 📚 All Papers\n\n")
            for i, paper in enumerate(sorted_papers[5:], 6):
                relevance = f" ({paper.relevance_score}/10)" if paper.relevance_score else ""
                lines.append(f"{i}. [{paper.title}]({paper.url}){relevance}\n")
            lines.append("\n")

        # Footer
        lines.append("---\n")
        lines.append(f"*Report generated on {get_current_date().isoformat()}*\n")
        lines.append("*Powered by paper-tracker*")

        return "".join(lines)

    def save_daily_report(
        self,
        papers: list[Paper],
        target_date: Optional[date] = None,
    ) -> Path:
        """Generate and save a daily report.

        Args:
            papers: List of papers to include in the report
            target_date: Date for the report. Defaults to today.

        Returns:
            Path to the saved report file
        """
        if target_date is None:
            target_date = get_current_date()

        content = self.generate_daily_report(papers, target_date)
        filename = f"{target_date.isoformat()}.md"
        filepath = self.reports_dir / filename

        filepath.write_text(content, encoding="utf-8")
        return filepath

    def _avg_relevance(self, papers: list[Paper]) -> float:
        """Calculate average relevance score.

        Args:
            papers: List of papers

        Returns:
            Average relevance score
        """
        scores = [p.relevance_score for p in papers if p.relevance_score is not None]
        if not scores:
            return 0.0
        return sum(scores) / len(scores)

    def get_report_path(self, target_date: Optional[date] = None) -> Path:
        """Get the path for a report file.

        Args:
            target_date: Date for the report. Defaults to today.

        Returns:
            Path to the report file
        """
        if target_date is None:
            target_date = get_current_date()
        return self.reports_dir / f"{target_date.isoformat()}.md"

    def report_exists(self, target_date: Optional[date] = None) -> bool:
        """Check if a report exists for the given date.

        Args:
            target_date: Date to check. Defaults to today.

        Returns:
            True if report exists
        """
        return self.get_report_path(target_date).exists()

    def load_report(self, target_date: Optional[date] = None) -> Optional[str]:
        """Load an existing report.

        Args:
            target_date: Date of the report. Defaults to today.

        Returns:
            Report content or None if not found
        """
        filepath = self.get_report_path(target_date)
        if not filepath.exists():
            return None
        return filepath.read_text(encoding="utf-8")
