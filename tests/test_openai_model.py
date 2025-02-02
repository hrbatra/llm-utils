import os
import pytest
from dotenv import load_dotenv
from models.openai_model import OpenAIModel
from models.base import ResearchResult, SourceAnalysis
from datetime import datetime
from exa_py import Exa
from typing import List, Set, Tuple
from pydantic import BaseModel
import json

class ResearchQueries(BaseModel):
    queries: List[str]

class QualityScore(BaseModel):
    url: str
    score: float
    reason: str

class SourceQualityEvaluation(BaseModel):
    sufficient: bool
    explanation: str
    quality_scores: List[QualityScore]

def generate_research_queries(model: OpenAIModel, previous_results: List[ResearchResult] = None) -> List[str]:
    """Generate one or more research queries based on the research topic and any previous results."""
    
    if previous_results:
        # Create context from previous results
        results_context = "\n".join([
            f"Title: {r.title}\nURL: {r.url}\nDate: {r.published_date}"
            for r in previous_results
        ])
        
        messages = [{
            "role": "system",
            "content": """You are a religious studies scholar specializing in comparative mysticism.
            Based on the previous search results provided, generate 1-3 additional focused research queries 
            that would help fill gaps in our current findings about connections between Jesus's esoteric 
            teachings and Eastern spiritual traditions (yoga/tantra)."""
        }, {
            "role": "user",
            "content": f"""Previous search results:
            {results_context}
            
            Generate additional research queries to expand our investigation."""
        }]
    else:
        messages = [{
            "role": "system",
            "content": """You are a religious studies scholar specializing in comparative mysticism.
            Generate 2-3 focused research queries about potential connections between Jesus's esoteric 
            teachings and Eastern spiritual traditions (yoga/tantra).
            
            Each query should explore a different aspect:
            - Historical connections and influences
            - Philosophical and practical parallels
            - Specific practices or concepts that appear in both traditions"""
        }]
    
    response = model.client.beta.chat.completions.parse(
        model=model.eval_model,
        messages=messages,
        response_format=ResearchQueries,
        max_tokens=200
    )
    
    return response.choices[0].message.parsed.queries

def fetch_research_results(query: str, existing_urls: Set[str]) -> List[ResearchResult]:
    """Fetch research results for a query, excluding already seen URLs."""
    exa_api_key = os.getenv("EXA_API_KEY")
    if not exa_api_key:
        raise ValueError("EXA_API_KEY environment variable is not set")
        
    client = Exa(api_key=exa_api_key)
    search_response = client.search(query, num_results=5)
    
    research_results = []
    for result in search_response.results:
        if result.url in existing_urls:
            continue
            
        try:
            # Get the content directly from the search result
            research_results.append(ResearchResult(
                title=result.title,
                url=result.url,
                published_date=result.published_date or "Unknown",
                content=result.text if hasattr(result, 'text') else None
            ))
        except Exception as e:
            print(f"Error processing result {result.title}: {e}")
            continue
    
    return research_results

def evaluate_source_quality(model: OpenAIModel, results: List[ResearchResult]) -> Tuple[List[ResearchResult], bool]:
    """Evaluate if we have enough high-quality sources or need more."""
    
    sources_text = "\n\n".join([
        f"Title: {r.title}\nURL: {r.url}\nDate: {r.published_date}\nContent Preview: {r.content[:500] if r.content else 'No content'}"
        for r in results
    ])
    
    messages = [{
        "role": "system",
        "content": """You are a research quality evaluator.
        Assess the provided sources and determine:
        1. Their collective quality and relevance
        2. Whether they provide sufficient coverage of the topic
        3. If additional sources are needed, what aspects need more coverage
        
        Return your evaluation in JSON format like:
        {
            "sufficient": true/false,
            "explanation": "Explanation of the evaluation...",
            "scores": [
                {"url": "source_url", "score": 8.5},
                {"url": "source_url", "score": 7.2}
            ]
        }"""
    }, {
        "role": "user",
        "content": f"Evaluate these sources:\n{sources_text}"
    }]
    
    response = model.client.chat.completions.create(
        model=model.eval_model,
        messages=messages,
        response_format={"type": "json_object"},
        max_tokens=1000
    )
    
    try:
        evaluation = json.loads(response.choices[0].message.content)
        
        # Update source scores
        for result in results:
            for score_info in evaluation["scores"]:
                if score_info["url"] == result.url:
                    result.relevance_score = score_info["score"]
                    break
        
        # Sort by score
        ranked_results = sorted(results, key=lambda x: x.relevance_score, reverse=True)
        
        print(f"\nSource Evaluation: {evaluation['explanation']}")
        return ranked_results, evaluation["sufficient"]
    except (KeyError, json.JSONDecodeError) as e:
        print(f"Error parsing response: {e}")
        return results, False

def main():
    """Run a test of the OpenAI research pipeline with iterative searching."""
    load_dotenv()
    
    # Initialize the model
    model = OpenAIModel()
    
    print("\n=== Starting Research Pipeline Test ===\n")
    
    all_results = []
    seen_urls = set()
    iteration = 1
    
    while True:
        print(f"\n--- Search Iteration {iteration} ---")
        
        # Generate queries
        print("\n1. Generating Research Queries...")
        queries = generate_research_queries(model, all_results if iteration > 1 else None)
        
        # Fetch results for each query
        new_results = []
        for i, query in enumerate(queries, 1):
            print(f"\nProcessing Query {i}: {query}")
            results = fetch_research_results(query, seen_urls)
            new_results.extend(results)
            seen_urls.update(r.url for r in results)
        
        all_results.extend(new_results)
        
        # Evaluate quality and sufficiency
        print("\n2. Evaluating Source Quality...")
        ranked_results, is_sufficient = evaluate_source_quality(model, all_results)
        
        if is_sufficient or iteration >= 3:  # Limit to 3 iterations
            all_results = ranked_results
            break
            
        iteration += 1
    
    # Process the final set of sources
    print("\n=== Processing Final Sources ===")
    
    # Take top 5 sources for detailed analysis
    top_results = all_results[:5]
    
    print("\n3. Summarizing Sources...")
    summarized_results = [
        model.summarize_source(result, max_length=2000)
        for result in top_results
    ]
    
    print("\n4. Analyzing Sources...")
    analyses = [
        model.analyze_source(result)
        for result in summarized_results
    ]
    
    for i, analysis in enumerate(analyses, 1):
        print(f"\nAnalysis {i}: {analysis.source.title}")
        print("Key Points:")
        for j, point in enumerate(analysis.key_points, 1):
            print(f"  {j}. {point}")
    
    print("\n5. Synthesizing Research...")
    report = model.synthesize_research(analyses, "Connections between Jesus's esoteric teachings and Eastern spiritual traditions")
    
    print("\n=== Final Research Report ===")
    print(f"\nTitle: {report.title}")
    print(f"\nSummary: {report.summary}")
    print("\nKey Findings:")
    for i, finding in enumerate(report.key_findings, 1):
        print(f"{i}. {finding}")
    
    print("\nMethodology Analysis:")
    print(report.methodology_analysis)
    
    print("\nLimitations and Gaps:")
    print(report.limitations_and_gaps)
    
    print("\nFuture Implications:")
    print(report.future_implications)
    
    print(f"\n=== Test Complete ({iteration} search iterations) ===")

# Test fixtures
@pytest.fixture
def model():
    """Initialize OpenAI model for testing."""
    load_dotenv()
    return OpenAIModel()

@pytest.fixture
def sample_results():
    """Create sample research results for testing."""
    return [
        ResearchResult(
            title="Test Article 1",
            url="https://example.com/1",
            published_date="2024-01-01",
            content="Sample content about Jesus and Eastern spirituality.",
            relevance_score=0.8
        ),
        ResearchResult(
            title="Test Article 2",
            url="https://example.com/2",
            published_date="2024-01-02",
            content="More sample content about yoga and Christianity.",
            relevance_score=0.6
        )
    ]

# Unit tests
def test_generate_research_queries(model):
    """Test query generation without previous results."""
    queries = generate_research_queries(model)
    assert isinstance(queries, list), "Response should be a list"
    assert 1 <= len(queries) <= 3, "Should generate 1-3 queries"
    assert all(isinstance(q, str) for q in queries), "All queries should be strings"
    assert all(len(q.strip()) > 0 for q in queries), "No empty queries allowed"
    assert all("?" in q for q in queries), "Queries should be questions"
    # Check that queries are about the topic
    relevant_terms = ["jesus", "christ", "eastern", "spiritual", "yoga", "tantra", "mysticism", "teaching"]
    assert all(any(term in q.lower() for term in relevant_terms) for q in queries), \
        "Queries should be relevant to the research topic"

def test_generate_research_queries_with_previous(model, sample_results):
    """Test query generation with previous results."""
    queries = generate_research_queries(model, sample_results)
    assert isinstance(queries, list), "Response should be a list"
    assert 1 <= len(queries) <= 3, "Should generate 1-3 queries"
    assert all(isinstance(q, str) for q in queries), "All queries should be strings"
    assert all(len(q.strip()) > 0 for q in queries), "No empty queries allowed"
    assert all("?" in q for q in queries), "Queries should be questions"
    # Check that queries are about the topic
    relevant_terms = ["jesus", "christ", "eastern", "spiritual", "yoga", "tantra", "mysticism", "teaching"]
    assert all(any(term in q.lower() for term in relevant_terms) for q in queries), \
        "Queries should be relevant to the research topic"

def test_fetch_research_results():
    """Test fetching research results."""
    exa_api_key = os.getenv("EXA_API_KEY")
    if not exa_api_key:
        pytest.skip("EXA_API_KEY not set")
    
    results = fetch_research_results(
        "Jesus Eastern spiritual practices comparison",
        existing_urls=set()
    )
    assert isinstance(results, list), "Response should be a list"
    assert len(results) <= 5, "Should return at most 5 results"
    
    for result in results:
        assert isinstance(result, ResearchResult), "Each result should be a ResearchResult"
        assert isinstance(result.title, str) and len(result.title.strip()) > 0, "Title should be non-empty string"
        assert isinstance(result.url, str) and result.url.startswith(("http://", "https://")), \
            "URL should be valid HTTP(S) URL"
        assert isinstance(result.published_date, str), "Published date should be string"
        assert result.relevance_score == 0.0, "Initial relevance score should be 0.0"
        if result.content is not None:
            assert isinstance(result.content, str) and len(result.content.strip()) > 0, \
                "Content if present should be non-empty string"

def test_evaluate_source_quality(model, sample_results):
    """Test source quality evaluation."""
    ranked_results = model.evaluate_sources(sample_results, "Test research topic")
    
    # Check return types
    assert isinstance(ranked_results, list), "First return value should be a list"
    assert len(ranked_results) == len(sample_results), "Should return same number of results"
    
    # Check ranking
    for result in ranked_results:
        assert isinstance(result, ResearchResult), "Each result should be a ResearchResult"
        assert hasattr(result, 'relevance_score'), "Each result should have relevance_score"
        assert isinstance(result.relevance_score, float), "Relevance score should be float"
    
    # Verify results are sorted
    scores = [r.relevance_score for r in ranked_results]
    assert scores == sorted(scores, reverse=True), "Results should be sorted by relevance_score in descending order"

def test_summarize_source(model, sample_results):
    """Test source summarization."""
    result = model.summarize_source(sample_results[0], max_length=2000)
    assert isinstance(result, ResearchResult), "Should return a ResearchResult"
    
    # If content is long enough to need summarization
    if len(result.content or "") > 2000:
        assert result.content_summary is not None, "Long content should be summarized"
        assert isinstance(result.content_summary, str), "Summary should be string"
        assert len(result.content_summary) < len(result.content), "Summary should be shorter than content"
        assert len(result.content_summary.strip()) > 0, "Summary should not be empty"
    
    # Original content should be preserved
    assert result.content == sample_results[0].content, "Original content should not be modified"
    assert result.title == sample_results[0].title, "Title should be preserved"
    assert result.url == sample_results[0].url, "URL should be preserved"
    assert result.published_date == sample_results[0].published_date, "Published date should be preserved"

def test_analyze_source(model, sample_results):
    """Test source analysis."""
    analysis = model.analyze_source(sample_results[0])
    
    # Check basic structure
    assert isinstance(analysis.key_points, list), "Key points should be a list"
    assert len(analysis.key_points) > 0, "Should have at least one key point"
    assert all(isinstance(p, str) and len(p.strip()) > 0 for p in analysis.key_points), \
        "Key points should be non-empty strings"
    
    # Check methodology (optional)
    if analysis.methodology is not None:
        assert isinstance(analysis.methodology, str), "Methodology should be string"
        assert len(analysis.methodology.strip()) > 0, "Methodology if present should be non-empty"
    
    # Check limitations (optional)
    if analysis.limitations is not None:
        assert isinstance(analysis.limitations, str), "Limitations should be string"
        assert len(analysis.limitations.strip()) > 0, "Limitations if present should be non-empty"
    
    # Check significance (required)
    assert isinstance(analysis.significance, str), "Significance should be string"
    assert len(analysis.significance.strip()) > 0, "Significance should be non-empty"
    
    # Check source preservation
    assert analysis.source == sample_results[0], "Original source should be preserved"

def test_synthesize_research(model, sample_results):
    """Test research synthesis."""
    # First create analyses
    analyses = [model.analyze_source(result) for result in sample_results]
    
    # Generate report
    report = model.synthesize_research(
        analyses,
        "Test research topic"
    )
    
    # Check required fields
    assert isinstance(report.title, str) and len(report.title.strip()) > 0, \
        "Title should be non-empty string"
    assert isinstance(report.summary, str) and len(report.summary.strip()) > 0, \
        "Summary should be non-empty string"
    
    # Check key findings
    assert isinstance(report.key_findings, list), "Key findings should be a list"
    assert len(report.key_findings) > 0, "Should have at least one key finding"
    assert all(isinstance(f, str) and len(f.strip()) > 0 for f in report.key_findings), \
        "Key findings should be non-empty strings"
    
    # Check analysis fields
    assert isinstance(report.detailed_analysis, str) and len(report.detailed_analysis.strip()) > 0, \
        "Detailed analysis should be non-empty string"
    assert isinstance(report.methodology_analysis, str) and len(report.methodology_analysis.strip()) > 0, \
        "Methodology analysis should be non-empty string"
    assert isinstance(report.limitations_and_gaps, str) and len(report.limitations_and_gaps.strip()) > 0, \
        "Limitations and gaps should be non-empty string"
    assert isinstance(report.critical_evaluation, str) and len(report.critical_evaluation.strip()) > 0, \
        "Critical evaluation should be non-empty string"
    assert isinstance(report.future_implications, str) and len(report.future_implications.strip()) > 0, \
        "Future implications should be non-empty string"
    
    # Check source preservation
    assert len(report.source_analyses) == len(analyses), "All source analyses should be preserved"
    assert all(isinstance(a, SourceAnalysis) for a in report.source_analyses), \
        "Source analyses should be SourceAnalysis objects"

if __name__ == "__main__":
    main() 