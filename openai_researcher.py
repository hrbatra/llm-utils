from typing import List, Dict, Any
from tools.exa import basic_search, get_contents
from models.base import ResearchResult, ResearchReport
from models.openai_model import OpenAIModel
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class OpenAIResearcher:
    """
    A research assistant that uses multiple LLM models to perform
    comprehensive research and analysis.
    """
    
    def __init__(self, initial_search_results: int = 20):
        self.model = OpenAIModel()
        self.initial_search_results = initial_search_results
        
    def _search(self, query: str) -> List[ResearchResult]:
        """Perform initial search and convert results to ResearchResult objects."""
        results = basic_search(query, max_results=self.initial_search_results)
        return [
            ResearchResult(
                title=r.title,
                url=r.url,
                published_date=r.published_date
            ) for r in results
        ]
    
    def _get_content(self, results: List[ResearchResult]) -> List[ResearchResult]:
        """Fetch content for selected results."""
        urls = [r.url for r in results]
        contents = get_contents(urls)
        
        for result, content in zip(results, contents):
            result.content = content
            
        return results
    
    def research(self, query: str) -> ResearchReport:
        """
        Perform comprehensive research on a topic.
        
        Steps:
        1. Initial broad search
        2. Evaluate and select most relevant sources
        3. Fetch full content
        4. Summarize long content if needed
        5. Analyze each source in detail
        6. Synthesize into final report
        """
        print(f"Researching: {query}")
        
        # Step 1: Initial search
        print("\nPerforming initial search...")
        initial_results = self._search(query)
        
        # Step 2: Evaluate and select sources
        print("\nEvaluating sources...")
        selected_results = self.model.evaluate_sources(initial_results, query)
        
        # Step 3: Fetch content
        print("\nFetching full content...")
        results_with_content = self._get_content(selected_results)
        
        # Step 4: Summarize if needed
        print("\nProcessing content...")
        processed_results = [
            self.model.summarize_source(r, max_length=4000)
            for r in results_with_content
        ]
        
        # Step 5: Analyze each source
        print("\nAnalyzing sources...")
        source_analyses = [
            self.model.analyze_source(r)
            for r in processed_results
        ]
        
        # Step 6: Synthesize final report
        print("\nSynthesizing research report...")
        report = self.model.synthesize_research(source_analyses, query)
        
        return report

def main():
    researcher = OpenAIResearcher()
    query = "What scientific studies reveal about cat intelligence and their unique behaviors?"
    
    report = researcher.research(query)
    
    # Print the raw JSON report
    print("\nRaw Research Report:")
    print(json.dumps(report.__dict__, indent=2))
    
    # Generate visualizations
    from tools.report_visualizer import ReportVisualizer
    visualizer = ReportVisualizer()
    
    # Generate basic HTML report
    basic_report_path = visualizer.visualize(report.__dict__, template='basic_report.html')
    print(f"\nBasic HTML report generated: {basic_report_path}")
    
    # Generate interactive D3.js report
    d3_report_path = visualizer.visualize(report.__dict__, template='d3_report.html')
    print(f"\nInteractive D3.js report generated: {d3_report_path}")

if __name__ == "__main__":
    main() 