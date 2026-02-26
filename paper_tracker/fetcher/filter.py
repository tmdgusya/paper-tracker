"""Keyword-based paper filtering."""

from dataclasses import dataclass
from typing import Any

from paper_tracker.fetcher.arxiv import Paper


@dataclass
class FilterResult:
    """Result of filtering a paper."""

    paper: Paper
    matched_keywords: list[str]
    relevance_score: float

    def to_dict(self) -> dict[str, Any]:
        """Convert filter result to dictionary.

        Returns:
            Dictionary representation of the filter result
        """
        return {
            "paper": self.paper.to_dict(),
            "matched_keywords": self.matched_keywords,
            "relevance_score": self.relevance_score,
        }


class PaperFilter:
    """Filter papers based on keyword matching."""

    def __init__(self, keywords: list[str], case_sensitive: bool = False) -> None:
        """Initialize the filter.

        Args:
            keywords: List of keywords to filter by
            case_sensitive: Whether matching should be case sensitive
        """
        self.keywords = [kw if case_sensitive else kw.lower() for kw in keywords]
        self.case_sensitive = case_sensitive

    def filter(self, papers: list[Paper], min_matches: int = 1) -> list[FilterResult]:
        """Filter papers based on keyword matching.

        Args:
            papers: List of papers to filter
            min_matches: Minimum number of keyword matches required

        Returns:
            List of FilterResult objects for papers that match
        """
        results: list[FilterResult] = []

        for paper in papers:
            matched = self._match_keywords(paper)
            if len(matched) >= min_matches:
                score = self._calculate_score(paper, matched)
                results.append(
                    FilterResult(
                        paper=paper,
                        matched_keywords=matched,
                        relevance_score=score,
                    )
                )

        # Sort by relevance score (descending)
        results.sort(key=lambda r: r.relevance_score, reverse=True)
        return results

    def _match_keywords(self, paper: Paper) -> list[str]:
        """Find which keywords match in a paper.

        Args:
            paper: Paper to check for keyword matches

        Returns:
            List of matched keywords
        """
        matched: list[str] = []

        # Combine searchable text from title and abstract
        searchable = f"{paper.title} {paper.abstract}"
        if not self.case_sensitive:
            searchable = searchable.lower()

        for keyword in self.keywords:
            if keyword in searchable:
                matched.append(keyword)

        return matched

    def _calculate_score(self, paper: Paper, matched_keywords: list[str]) -> float:
        """Calculate a relevance score for a paper.

        Args:
            paper: Paper to score
            matched_keywords: Keywords that matched in this paper

        Returns:
            Relevance score between 0 and 1
        """
        if not matched_keywords:
            return 0.0

        # Base score from keyword matches
        keyword_score = len(matched_keywords) / len(self.keywords)

        # Boost for title matches (more important than abstract)
        title_text = paper.title if self.case_sensitive else paper.title.lower()
        title_matches = sum(1 for kw in matched_keywords if kw in title_text)
        title_boost = 0.2 * (title_matches / len(matched_keywords))

        # Normalize score to 0-1 range
        score = min(1.0, keyword_score + title_boost)

        return round(score, 3)

    def filter_by_category(self, papers: list[Paper], categories: list[str]) -> list[Paper]:
        """Filter papers by arXiv category.

        Args:
            papers: List of papers to filter
            categories: List of categories to include

        Returns:
            List of papers matching at least one category
        """
        return [
            p for p in papers
            if any(cat in p.categories for cat in categories)
        ]

    def filter_by_author(self, papers: list[Paper], authors: list[str]) -> list[Paper]:
        """Filter papers by author name.

        Args:
            papers: List of papers to filter
            authors: List of author names to include

        Returns:
            List of papers with at least one matching author
        """
        target_authors = [a if self.case_sensitive else a.lower() for a in authors]

        return [
            p for p in papers
            if any(
                any(target in (author if self.case_sensitive else author.lower()) for target in target_authors)
                for author in p.authors
            )
        ]
