from exa_py import Exa
import os
from pathlib import Path
from dotenv import load_dotenv
import argparse

# Load environment variables from the .env file
dotenv_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path)

EXA_API_KEY = os.getenv('EXA_API_KEY')
if not EXA_API_KEY:
    raise ValueError("EXA_API_KEY not set in environment variables")

# Initialize the Exa client
exa = Exa(api_key=EXA_API_KEY)

def basic_search(query: str):
    """
    Perform a basic search using Exa's API.
    """
    return exa.search(query)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Perform a basic search using Exa's API.")
    parser.add_argument("query", type=str, help="The query to search for")
    args = parser.parse_args()
    print(basic_search(args.query))
