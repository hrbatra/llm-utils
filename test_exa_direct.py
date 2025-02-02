from tools.exa import basic_search, get_contents

def main():
    # Test basic search
    print("Performing search...")
    try:
        results = basic_search("recent studies on cat-human bonding and attachment", max_results=3)
        
        print("\nSearch Results:")
        for result in results:
            print(f"\nTitle: {result.title}")
            print(f"URL: {result.url}")
            print(f"Published: {result.published_date}")
        
        # Test content retrieval for first result only
        if results:
            print("\nFetching content for first article...")
            url = results[0].url
            content = get_contents([url])
            
            print(f"\nContent from {url}:")
            print("Preview:", content[0][:500] + "..." if content[0] else "No content")
        else:
            print("\nNo search results found.")
            
    except Exception as e:
        print(f"\nError occurred: {str(e)}")

if __name__ == "__main__":
    main() 