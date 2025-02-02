from exa_py import Exa
import os
from pathlib import Path
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import List, NewType
from datetime import datetime
from urllib.parse import urlparse

# Load environment variables from the .env file
dotenv_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path)

EXA_API_KEY = os.getenv('EXA_API_KEY')
if not EXA_API_KEY:
    raise ValueError("EXA_API_KEY not set in environment variables")

# Initialize the Exa client
exa = Exa(api_key=EXA_API_KEY)

# More specific URL type with validation
URL = NewType('URL', str)

def validate_url(url: str) -> URL:
    """Validate and return a URL."""
    parsed = urlparse(url)
    if not all([parsed.scheme in ('http', 'https'), parsed.netloc]):
        raise ValueError(f"Invalid URL format: {url}")
    return URL(url)

@dataclass
class SearchResult:
    """
    Represents the info we want out of each search result from Exa API.
    
    Attributes:
        title: The title of the search result
        url: The URL of the result (must be valid HTTP(S))
        published_date: ISO format date string of publication
    """
    title: str
    url: URL
    published_date: str

    def __post_init__(self):
        """Validate URL and date format after initialization."""
        self.url = validate_url(self.url)
        if self.published_date:  # Only validate if date exists
            try:
                datetime.fromisoformat(self.published_date.replace('Z', '+00:00'))
            except ValueError:
                raise ValueError(f"Invalid date format: {self.published_date}")

def basic_search(query: str, max_results: int = 10) -> List[SearchResult]:
    """
    Perform a basic search using Exa's API.
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return (default: 10)
        
    Returns:
        List of SearchResult objects
        
    Raises:
        ValueError: If the query is empty
        RuntimeError: If the API call fails
    """
    if not query.strip():
        raise ValueError("Search query cannot be empty")
    
    try:
        response = exa.search(query, num_results=max_results)
        return [
            SearchResult(
                result.title,
                result.url,
                result.published_date
            ) for result in response.results
        ]
    except Exception as e:
        raise RuntimeError(f"Search failed: {str(e)}") from e

def get_contents(urls: List[URL], chunk_size: int = 5) -> List[str]:
    """
    Get the contents of the URLs in batches.
    
    Args:
        urls: List of URLs to fetch
        chunk_size: Number of URLs to process in each batch (default: 5)
        
    Returns:
        List of text contents corresponding to the URLs
        
    Raises:
        ValueError: If any URL is invalid
        RuntimeError: If the API call fails
    """
    # Validate all URLs first
    validated_urls = [validate_url(url) for url in urls]
    
    try:
        # Process URLs in chunks to avoid overwhelming the API
        all_texts = []
        for i in range(0, len(validated_urls), chunk_size):
            chunk = validated_urls[i:i + chunk_size]
            response = exa.get_contents(chunk, text=True)
            all_texts.extend(result.text for result in response.results)
        return all_texts
    except Exception as e:
        raise RuntimeError(f"Content retrieval failed: {str(e)}") from e
