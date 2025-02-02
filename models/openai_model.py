from typing import List, Optional, Dict, Any
import tiktoken
from openai import OpenAI
import json
from pydantic import BaseModel, Field
from .base import BaseModel as AbstractBaseModel, ResearchResult, SourceAnalysis, ResearchReport
from datetime import datetime

class SourceEvaluation(BaseModel):
    """Schema for source evaluation response."""
    scores: List[Dict[str, float]] = Field(
        description="List of scores for each source, containing url and score"
    )

    class Config:
        json_schema_extra = {
            "required": ["scores"]
        }

class SourceSummary(BaseModel):
    """Schema for source summarization response."""
    summary: str = Field(description="Concise summary of the source content")
    key_points: List[str] = Field(description="Key points from the content")

class SourceAnalysisSchema(BaseModel):
    """Schema for source analysis response."""
    key_points: List[str] = Field(description="Main points from the source")
    methodology: Optional[str] = Field(description="Research methodology used")
    limitations: Optional[str] = Field(description="Study limitations and constraints")
    significance: str = Field(description="Research significance and implications")

class ResearchReportSchema(BaseModel):
    """Schema for final research report."""
    title: str = Field(description="Concise title for the research report")
    summary: str = Field(description="Brief executive summary")
    key_findings: List[str] = Field(description="Key research findings with supporting sources")
    detailed_analysis: str = Field(description="In-depth analysis of the research")
    critical_evaluation: str = Field(description="Critical evaluation of the findings")
    future_implications: str = Field(description="Implications for future research")
    methodology_analysis: str = Field(description="Analysis of research methodologies")
    limitations_and_gaps: str = Field(description="Research limitations and knowledge gaps")

    class Config:
        json_schema_extra = {
            "required": [
                "title", "summary", "key_findings", "detailed_analysis", 
                "critical_evaluation", "future_implications", "methodology_analysis",
                "limitations_and_gaps"
            ]
        }

class OpenAIModel(AbstractBaseModel):
    """OpenAI model implementation using different models for different tasks."""
    
    def __init__(self):
        self.client = OpenAI()

        """
        self.eval_model = "o3-mini"  
        self.summary_model = "o3-mini"
        self.analysis_model = "o3-mini" 
        self.synthesis_model = "o3-mini"
        """

        self.eval_model = "gpt-4o-mini"  
        self.summary_model = "gpt-4o-mini"
        self.analysis_model = "gpt-4o-mini" 
        self.synthesis_model = "gpt-4o-mini"

        
    def count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken."""
        enc = tiktoken.encoding_for_model("gpt-4")  # Base encoding for token estimation
        return len(enc.encode(text))
    
    def evaluate_sources(self, 
                        results: List[ResearchResult], 
                        query: str,
                        max_sources: int = 5) -> List[ResearchResult]:
        """Evaluate and rank sources using the evaluation model."""
        
        # Prepare the evaluation prompt
        sources_text = "\n\n".join([
            f"Title: {r.title}\nURL: {r.url}\nDate: {r.published_date}"
            for r in results
        ])
        
        messages = [{
            "role": "system",
            "content": """You are a research librarian expert at evaluating source quality and relevance.
            Analyze each source and assign a relevance score (0-10) based on:
            1. Relevance to the research query
            2. Source credibility and authority
            3. Recency and timeliness
            4. Methodology and rigor (if applicable)
            
            Return a list of scores in JSON format like:
            {
                "scores": [
                    {"url": "source_url", "score": 8.5},
                    {"url": "source_url", "score": 7.2}
                ]
            }"""
        }, {
            "role": "user",
            "content": f"""Research Query: {query}

Available Sources:
{sources_text}

Evaluate these sources and return relevance scores."""
        }]
        
        response = self.client.chat.completions.create(
            model=self.eval_model,
            messages=messages,
            response_format={"type": "json_object"}
        )
        
        # Parse the JSON response
        try:
            scores = json.loads(response.choices[0].message.content)["scores"]
            url_to_score = {s["url"]: s["score"] for s in scores}
            
            # Update scores and sort results
            for result in results:
                result.relevance_score = url_to_score.get(result.url, 0.0)
            
            return sorted(results, 
                         key=lambda x: x.relevance_score, 
                         reverse=True)[:max_sources]
        except (KeyError, json.JSONDecodeError) as e:
            print(f"Error parsing response: {e}")
            # Return original results if parsing fails
            return results[:max_sources]
    
    def summarize_source(self, 
                        source: ResearchResult,
                        max_length: Optional[int] = None) -> ResearchResult:
        """Summarize source content if needed."""
        if not source.content:
            return source
            
        # Check if summarization is needed
        token_count = self.count_tokens(source.content)
        if max_length and token_count > max_length:
            messages = [{
                "role": "system",
                "content": """Summarize the given text while preserving:
                1. Key findings and conclusions
                2. Important methodological details
                3. Significant data points and statistics
                4. Critical context and limitations
                
                Maintain academic tone and precision."""
            }, {
                "role": "user",
                "content": f"""Title: {source.title}
                
Text to summarize:
{source.content}"""
            }]
            
            response = self.client.beta.chat.completions.parse(
                model=self.summary_model,
                messages=messages,
                response_format=SourceSummary
            )
            
            source.content_summary = response.summary
            
        return source
    
    def analyze_source(self, source: ResearchResult) -> SourceAnalysis:
        """Perform detailed analysis of a single source."""
        content = source.content_summary if source.content_summary else source.content
        
        messages = [{
            "role": "system",
            "content": """Perform a detailed academic analysis of the research source.
            Focus on:
            1. Key findings and contributions
            2. Methodological approach and rigor
            3. Limitations and potential biases
            4. Significance and implications"""
        }, {
            "role": "user",
            "content": f"""Title: {source.title}
Published: {source.published_date}

Content:
{content}

Provide a detailed analysis."""
        }]
        
        response = self.client.beta.chat.completions.parse(
            model=self.analysis_model,
            messages=messages,
            response_format=SourceAnalysisSchema
        )
        
        parsed = response.choices[0].message.parsed
        
        return SourceAnalysis(
            source=source,
            key_points=parsed.key_points,
            methodology=parsed.methodology,
            limitations=parsed.limitations,
            significance=parsed.significance
        )
    
    def synthesize_research(self,
                          sources: List[SourceAnalysis],
                          query: str) -> ResearchReport:
        """Synthesize analyses into a comprehensive report."""
        
        # Prepare source information
        sources_text = "\n\n".join([
            f"""Source: {s.source.title}
URL: {s.source.url}
Published: {s.source.published_date}
Key Points: {json.dumps(s.key_points, indent=2)}
Methodology: {s.methodology}
Limitations: {s.limitations}
Significance: {s.significance}"""
            for s in sources
        ])
        
        messages = [{
            "role": "system",
            "content": """You are an expert research synthesist.
            Create a comprehensive research report that:
            1. Synthesizes findings across multiple sources
            2. Identifies patterns and contradictions
            3. Evaluates methodological strengths and weaknesses
            4. Discusses implications and future directions
            5. Maintains academic rigor while being accessible"""
        }, {
            "role": "user",
            "content": f"""Research Query: {query}

Source Analyses:
{sources_text}

Synthesize these sources into a comprehensive report."""
        }]
        
        response = self.client.beta.chat.completions.parse(
            model=self.synthesis_model,
            messages=messages,
            response_format=ResearchReportSchema
        )
        
        parsed = response.choices[0].message.parsed
        
        return ResearchReport(
            title=parsed.title,
            summary=parsed.summary,
            key_findings=parsed.key_findings,
            detailed_analysis=parsed.detailed_analysis,
            critical_evaluation=parsed.critical_evaluation,
            future_implications=parsed.future_implications,
            methodology_analysis=parsed.methodology_analysis,
            limitations_and_gaps=parsed.limitations_and_gaps,
            timeline=[{"event": "Research Completed", "date": datetime.now().strftime("%Y-%m-%d")}],
            metadata={"query": query, "num_sources": str(len(sources))},
            source_analyses=sources
        ) 