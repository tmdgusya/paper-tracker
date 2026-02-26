"""CLI interface for paper-tracker."""

import sys
from datetime import datetime
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from paper_tracker.config import load_config

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="paper-tracker")
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Path to config file",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output",
)
@click.pass_context
def main(ctx: click.Context, config: str | None, verbose: bool) -> None:
    """Paper Tracker - AI-powered arXiv paper tracking and summarization.

    Track, summarize, and report on Computer Science research papers from arXiv.
    """
    ctx.ensure_object(dict)

    # Load configuration
    try:
        if config:
            settings = load_config().__class__.from_yaml(Path(config))
        else:
            settings = load_config()
        ctx.obj["settings"] = settings
    except Exception as e:
        console.print(f"[red]Error loading config: {e}[/red]")
        sys.exit(1)

    ctx.obj["verbose"] = verbose


@main.command()
@click.pass_context
def init(ctx: click.Context) -> None:
    """Initialize the database and create necessary directories."""
    settings = ctx.obj["settings"]

    console.print(Panel.fit("[bold blue]Initializing Paper Tracker[/bold blue]"))

    # Create directories
    console.print(f"[dim]Creating data directory: {settings.data_dir}[/dim]")
    settings.data_dir.mkdir(parents=True, exist_ok=True)

    console.print(f"[dim]Creating reports directory: {settings.reports_dir}[/dim]")
    settings.reports_dir.mkdir(parents=True, exist_ok=True)

    # Initialize database (will be implemented by store module)
    try:
        from paper_tracker.store import init_db

        console.print("[dim]Initializing database...[/dim]")
        init_db(settings.db_path)
        console.print("[green]Database initialized successfully[/green]")
    except ImportError:
        console.print(
            "[yellow]Database module not yet implemented. "
            "Run 'pip install -e .' first.[/yellow]"
        )
    except Exception as e:
        console.print(f"[red]Error initializing database: {e}[/red]")
        sys.exit(1)

    console.print("[green]Initialization complete![/green]")


@main.command()
@click.option(
    "--dry-run",
    is_flag=True,
    help="Fetch papers without saving to database",
)
@click.option(
    "--categories",
    "-c",
    multiple=True,
    help="ArXiv categories to fetch (e.g., cs.AI, cs.LG)",
)
@click.option(
    "--keywords",
    "-k",
    multiple=True,
    help="Filter papers by keywords",
)
@click.option(
    "--limit",
    "-l",
    type=int,
    default=100,
    help="Maximum number of papers to fetch",
)
@click.option(
    "--date",
    "-d",
    type=str,
    help="Date to fetch papers for (YYYY-MM-DD)",
)
@click.pass_context
def fetch(
    ctx: click.Context,
    dry_run: bool,
    categories: tuple[str, ...],
    keywords: tuple[str, ...],
    limit: int,
    date: str | None,
) -> None:
    """Fetch papers from arXiv."""
    settings = ctx.obj["settings"]

    # Use provided categories or default from config
    fetch_categories = list(categories) if categories else settings.categories
    fetch_keywords = list(keywords) if keywords else settings.keywords

    # Determine date first (before printing panel)
    import asyncio
    from datetime import date as dt_date
    from datetime import timedelta
    
    if date:
        fetch_date = dt_date.fromisoformat(date)
    else:
        # Default to yesterday (cronjob runs today to fetch yesterday's papers)
        fetch_date = dt_date.today() - timedelta(days=1)

    console.print(
        Panel.fit(
            f"[bold blue]Fetching Papers[/bold blue]\n"
            f"Categories: {', '.join(fetch_categories)}\n"
            f"Keywords: {', '.join(fetch_keywords) if fetch_keywords else 'None'}\n"
            f"Limit: {limit}\n"
            f"Date: {fetch_date.isoformat()}\n"
            f"Mode: {'Dry run' if dry_run else 'Save to DB'}"
        )
    )

    try:
        from paper_tracker.fetcher import fetch_papers

        console.print("[dim]Fetching papers from arXiv...[/dim]")
        papers = asyncio.run(fetch_papers(
            categories=fetch_categories,
            keywords=fetch_keywords,
            limit=limit,
            date=fetch_date,
        ))

        if dry_run:
            console.print(f"[yellow]Dry run: Found {len(papers)} papers[/yellow]")
            _display_papers_table(papers[:10])  # Show first 10
        else:
            from paper_tracker.store import save_papers

            console.print("[dim]Saving papers to database...[/dim]")
            saved_count = save_papers(settings.db_path, papers)
            console.print(f"[green]Saved {saved_count} papers to database[/green]")

    except ImportError as e:
        console.print(f"[red]Module not yet implemented: {e}[/red]")
        console.print("[yellow]Please ensure all modules are implemented.[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error fetching papers: {e}[/red]")
        if ctx.obj.get("verbose"):
            console.print_exception()
        sys.exit(1)


@main.command()
@click.option(
    "--limit",
    "-l",
    type=int,
    default=10,
    help="Maximum number of papers to summarize",
)
@click.option(
    "--batch",
    "-b",
    type=int,
    default=5,
    help="Number of papers to process in each batch",
)
@click.option(
    "--force",
    is_flag=True,
    help="Re-summarize papers that already have summaries",
)
@click.pass_context
def summarize(
    ctx: click.Context,
    limit: int,
    batch: int,
    force: bool,
) -> None:
    """Run AI summarizer on pending papers."""
    settings = ctx.obj["settings"]

    console.print(
        Panel.fit(
            f"[bold blue]Summarizing Papers[/bold blue]\n"
            f"Limit: {limit}\n"
            f"Batch size: {batch}\n"
            f"Mode: {'Re-summarize all' if force else 'Only pending'}"
        )
    )

    try:
        import asyncio
        from paper_tracker.store import get_pending_papers, update_paper_summary
        from paper_tracker.summarizer import Summarizer

        # Get pending papers
        console.print("[dim]Fetching pending papers from database...[/dim]")
        papers = get_pending_papers(
            settings.db_path, limit=limit, include_summarized=force
        )

        if not papers:
            console.print("[yellow]No papers to summarize[/yellow]")
            return

        console.print(f"[dim]Found {len(papers)} papers to summarize[/dim]")

        # Summarize in batches
        summarized_count = 0
        for i in range(0, len(papers), batch):
            batch_papers = papers[i : i + batch]
            console.print(f"[dim]Processing batch {i // batch + 1}...[/dim]")

            for paper in batch_papers:
                try:
                    console.print(f"[dim]  Summarizing: {paper.title[:50]}...[/dim]")
                    summarizer = Summarizer(model=settings.summary_model)
                    summary = asyncio.run(summarizer.summarize_paper(paper))

                    update_paper_summary(
                        settings.db_path, paper.id, summary
                    )
                    summarized_count += 1
                    console.print(f"[green]  Summarized: {paper.title[:50]}[/green]")

                except Exception as e:
                    console.print(f"[red]  Error summarizing paper: {e}[/red]")
                    if ctx.obj.get("verbose"):
                        console.print_exception()

        console.print(f"[green]Summarized {summarized_count} papers[/green]")

    except ImportError as e:
        console.print(f"[red]Module not yet implemented: {e}[/red]")
        console.print("[yellow]Please ensure all modules are implemented.[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error summarizing papers: {e}[/red]")
        if ctx.obj.get("verbose"):
            console.print_exception()
        sys.exit(1)


@main.command()
@click.option(
    "--date",
    "-d",
    type=str,
    help="Date for report (YYYY-MM-DD). Defaults to today.",
)
@click.option(
    "--send",
    is_flag=True,
    help="Send report via Telegram",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file path (default: reports/YYYY-MM-DD.md)",
)
@click.pass_context
def report(
    ctx: click.Context,
    date: str | None,
    send: bool,
    output: str | None,
) -> None:
    """Generate daily report."""
    settings = ctx.obj["settings"]

    # Parse date, or use today.
    if date:
        try:
            report_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            console.print("[red]Invalid date format. Use YYYY-MM-DD[/red]")
            sys.exit(1)
    else:
        # Use today's date from system
        from datetime import date as dt_date
        report_date = dt_date.today()
        console.print(f"[dim]Using today's date: {report_date.isoformat()}[/dim]")

    console.print(
        Panel.fit(
            f"[bold blue]Generating Report[/bold blue]\n"
            f"Date: {report_date.isoformat()}\n"
            f"Send via Telegram: {'Yes' if send else 'No'}"
        )
    )

    try:
        from paper_tracker.store import get_papers_by_date
        from paper_tracker.reporter import ReportGenerator

        # Get papers for the date
        console.print("[dim]Fetching papers from database...[/dim]")
        papers = get_papers_by_date(settings.db_path, report_date)

        if not papers:
            console.print(f"[yellow]No papers found for {report_date.isoformat()}[/yellow]")
            return

        # Generate report
        console.print("[dim]Generating markdown report...[/dim]")
        generator = ReportGenerator(settings.reports_dir)
        report_content = generator.generate_daily_report(papers, report_date)

        # Determine output path
        if output:
            output_path = Path(output)
        else:
            output_path = settings.reports_dir / f"{report_date.isoformat()}.md"

        # Write report
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report_content)
        console.print(f"[green]Report saved to: {output_path}[/green]")

        # Send via Telegram if requested
        if send:
            console.print("[dim]Sending via Telegram...[/dim]")
            # Telegram sending will be implemented
            console.print("[yellow]Telegram sending not yet implemented[/yellow]")

    except ImportError as e:
        console.print(f"[red]Module not yet implemented: {e}[/red]")
        console.print("[yellow]Please ensure all modules are implemented.[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error generating report: {e}[/red]")
        if ctx.obj.get("verbose"):
            console.print_exception()
        sys.exit(1)


@main.command()
@click.option(
    "--fetch-only",
    is_flag=True,
    help="Only fetch papers, skip summarization and reporting",
)
@click.option(
    "--summarize-only",
    is_flag=True,
    help="Only summarize papers, skip fetching and reporting",
)
@click.option(
    "--report-only",
    is_flag=True,
    help="Only generate report, skip fetching and summarization",
)
@click.option(
    "--no-report",
    is_flag=True,
    help="Skip report generation",
)
@click.option(
    "--fetch-limit",
    type=int,
    default=100,
    help="Maximum papers to fetch",
)
@click.option(
    "--summarize-limit",
    type=int,
    default=10,
    help="Maximum papers to summarize",
)
@click.pass_context
def run(
    ctx: click.Context,
    fetch_only: bool,
    summarize_only: bool,
    report_only: bool,
    no_report: bool,
    fetch_limit: int,
    summarize_limit: int,
) -> None:
    """Run the full pipeline: fetch + summarize + report."""
    console.print(Panel.fit("[bold blue]Running Paper Tracker Pipeline[/bold blue]"))

    if report_only:
        # Only generate report
        ctx.invoke(report, date=None, send=False, output=None)
        return

    if summarize_only:
        # Only summarize
        ctx.invoke(summarize, limit=summarize_limit, batch=5, force=False)
        return

    # Fetch papers
    ctx.invoke(fetch, dry_run=False, categories=(), keywords=(), limit=fetch_limit)

    # Summarize papers
    ctx.invoke(summarize, limit=summarize_limit, batch=5, force=False)

    # Generate report (unless --no-report)
    if not no_report:
        ctx.invoke(report, date=None, send=False, output=None)

    console.print("[green]Pipeline complete![/green]")


def _display_papers_table(papers: list) -> None:
    """Display a table of papers.

    Args:
        papers: List of paper objects with title, authors, and url attributes
    """
    table = Table(title="Fetched Papers")
    table.add_column("Title", style="cyan", no_wrap=False)
    table.add_column("Authors", style="green")
    table.add_column("URL", style="blue")

    for paper in papers:
        # Handle both paper objects and dictionaries
        if hasattr(paper, "title"):
            title = paper.title[:60] + "..." if len(paper.title) > 60 else paper.title
            authors = (
                paper.authors[:30] + "..."
                if len(paper.authors) > 30
                else paper.authors
            )
            url = paper.url if hasattr(paper, "url") else "N/A"
        else:
            title = str(paper.get("title", ""))[:60]
            authors = str(paper.get("authors", ""))[:30]
            url = paper.get("url", "N/A")

        table.add_row(title, authors, url)

    console.print(table)


if __name__ == "__main__":
    main()
