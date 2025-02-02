"""
Research pipeline for analyzing connections between religious and spiritual traditions.
"""

import os
from dotenv import load_dotenv
from models.openai_model import OpenAIModel
from models.base import ResearchResult
from typing import List, Set
from test_openai_model import generate_research_queries, fetch_research_results, evaluate_source_quality

def run_research_pipeline():
    """Run the complete research pipeline."""
    load_dotenv()
    
    # Initialize the model
    model = OpenAIModel()
    
    print("\n=== Starting Research Pipeline ===\n")
    
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
    
    print(f"\n=== Pipeline Complete ({iteration} search iterations) ===")
    return report

if __name__ == "__main__":
    run_research_pipeline() 