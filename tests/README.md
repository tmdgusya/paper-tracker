# Tests for paper-tracker

This directory contains comprehensive tests for all components of the paper-tracker package.

## Test Structure

- `conftest.py` - Shared fixtures for all tests
- `test_store.py` - Tests for SQLite database operations
- `test_fetcher.py` - Tests for arXiv API client
- `test_filter.py` - Tests for paper keyword filtering
- `test_summarizer.py` - Tests for AI summarization
- `test_reporter.py` - Tests for Markdown report generation

## Running Tests

### Install Dependencies

First, install the package in development mode with test dependencies:

```bash
pip install -e ".[dev]"
```

Or manually install the test dependencies:

```bash
pip install pytest pytest-asyncio httpx
```

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test File

```bash
pytest tests/test_store.py -v
```

### Run Specific Test

```bash
pytest tests/test_store.py::TestDatabase::test_add_paper -v
```

### Run with Coverage

```bash
pytest tests/ --cov=paper_tracker --cov-report=html
```

## Test Coverage

The tests aim for >80% coverage of all modules:

- **Store (database.py)**: Tests CRUD operations, status updates, filtering
- **Fetcher (arxiv.py)**: Tests API parsing, error handling, paper data extraction
- **Filter (filter.py)**: Tests keyword matching, relevance scoring, category filtering
- **Summarizer (claude.py)**: Tests prompt building, response parsing, error handling
- **Reporter (markdown.py)**: Tests report generation, file I/O, formatting

## Fixtures

Shared fixtures defined in `conftest.py`:

- `temp_dir` - Temporary directory for test files
- `temp_db` - Temporary SQLite database
- `sample_fetcher_paper` - Sample arXiv Paper object
- `sample_store_paper` - Sample database Paper object
- `sample_settings` - Sample Settings configuration
- `sample_arxiv_xml_response` - Mock arXiv API response
