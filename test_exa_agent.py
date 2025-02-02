from exa_agent import ExaAgent, ResearchTask

def main():
    # Initialize the agent
    agent = ExaAgent()
    
    # Create a simple research task - just top 5 articles
    task = ResearchTask(
        query="AI safety concerns and regulation",
        max_results=5,
        min_date=None,  # No date filtering
        require_recent=False  # Don't sort by date
    )
    
    # Perform the research
    print("Performing research...")
    results = agent.research(task)
    
    # Print results with content previews
    print("\nFound articles:")
    for result in results:
        print(f"\nTitle: {result['title']}")
        print(f"Published: {result['published_date']}")
        print(f"URL: {result['url']}")
        print("Content preview:", result['content'][:200] + "..." if result['content'] else "No content")
    
    # Show search history
    print("\nSearch History:")
    history = agent.get_search_history()
    for entry in history:
        print(f"Query: {entry['query']}")
        print(f"Results found: {entry['num_results']}")

if __name__ == "__main__":
    main() 