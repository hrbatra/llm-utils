from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class ResearchResult:
    """A single research result with metadata."""
    title: str
    url: str
    published_date: str
    relevance_score: float = 0.0
    content: Optional[str] = None
    content_summary: Optional[str] = None

@dataclass
class SourceAnalysis:
    """Analysis of a single source."""
    source: ResearchResult
    key_points: List[str]
    methodology: Optional[str] = None
    limitations: Optional[str] = None
    significance: str = ""
    
@dataclass
class ResearchReport:
    """Comprehensive research report."""
    title: str
    summary: str
    key_findings: List[str]  # Changed to List[str] to match schema
    detailed_analysis: str
    critical_evaluation: str
    future_implications: str
    methodology_analysis: str
    limitations_and_gaps: str
    timeline: List[Dict[str, str]]  # Timeline events
    metadata: Dict[str, str]  # Changed to Dict[str, str] to match schema
    source_analyses: List[SourceAnalysis]

class BaseModel(ABC):
    """Base class for all LLM models."""
    
    @abstractmethod
    def evaluate_sources(self, 
                        results: List[ResearchResult], 
                        query: str,
                        max_sources: int = 5) -> List[ResearchResult]:
        """
        Evaluate and rank research results for relevance.
        Returns selected sources with relevance scores.
        """
        pass
    
    @abstractmethod
    def summarize_source(self, 
                        source: ResearchResult,
                        max_length: Optional[int] = None) -> ResearchResult:
        """
        Summarize a single source's content if it's too long.
        Returns source with added content_summary if summarization was needed.
        """
        pass
    
    @abstractmethod
    def analyze_source(self, 
                      source: ResearchResult) -> SourceAnalysis:
        """
        Perform detailed analysis of a single source.
        Returns structured analysis including methodology, key points, etc.
        """
        pass
    
    @abstractmethod
    def synthesize_research(self,
                          sources: List[SourceAnalysis],
                          query: str) -> ResearchReport:
        """
        Synthesize multiple source analyses into a comprehensive report.
        Returns structured report with detailed analysis sections.
        """
        pass

    def count_tokens(self, text: str) -> int:
        """Count tokens in text. Implementation varies by model."""
        raise NotImplementedError("Token counting not implemented for this model.") 