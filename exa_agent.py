from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from tools.exa import basic_search, get_contents

@dataclass
class ResearchTask:
    """Represents a research task to be performed by the agent."""
    query: str
    max_results: int = 10
    min_date: Optional[str] = None  # ISO format date string
    require_recent: bool = True

class ExaAgent:
    """An agent that performs research tasks using the Exa API."""
    
    def __init__(self):
        """Initialize the ExaAgent."""
        self.search_history: List[Dict[str, Any]] = []
        
    def research(self, task: ResearchTask) -> List[Dict[str, str]]:
        """
        Perform a research task and return results.
        
        Args:
            task: ResearchTask object containing search parameters
            
        Returns:
            List of dictionaries containing search results with content
        """
        # Perform the search
        results = basic_search(task.query, max_results=task.max_results)
        
        # Store in search history
        self.search_history.append({
            "query": task.query,
            "num_results": len(results),
            "urls": [r.url for r in results]
        })
        
        # Get contents for all URLs
        urls = [result.url for result in results]
        contents = get_contents(urls)
        
        # Create results list
        results_list = [
            {
                "title": r.title,
                "url": r.url,
                "published_date": r.published_date,
                "content": content
            }
            for r, content in zip(results, contents)
        ]
        
        # Apply date filtering if specified
        if task.min_date:
            results_list = [
                r for r in results_list 
                if r["published_date"] >= task.min_date
            ]
            
        if task.require_recent:
            # Sort by date descending
            results_list.sort(key=lambda x: x["published_date"], reverse=True)
            
        return results_list
    
    def get_search_history(self) -> List[Dict[str, Any]]:
        """Return search history."""
        return self.search_history
    
    def summarize_results(self, results: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Provide a summary of the research results.
        
        Args:
            results: List of result dictionaries
            
        Returns:
            Dictionary with summary statistics
        """
        if not results:
            return {
                "total_results": 0,
                "date_range": {"earliest": None, "latest": None},
                "avg_content_length": 0
            }
            
        dates = [r["published_date"] for r in results]
        content_lengths = [len(r["content"]) for r in results]
        
        return {
            "total_results": len(results),
            "date_range": {
                "earliest": min(dates),
                "latest": max(dates)
            },
            "avg_content_length": sum(content_lengths) / len(content_lengths)
        } 