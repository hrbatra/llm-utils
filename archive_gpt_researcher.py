from typing import List, Dict, Any
from openai import OpenAI
from tools.exa import basic_search, get_contents
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MODEL = "gpt-4o"

# Initialize OpenAI client
client = OpenAI()

# Define the research report schema
REPORT_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {
            "type": "string",
            "description": "A concise title for the research report"
        },
        "summary": {
            "type": "string",
            "description": "A brief executive summary of the findings"
        },
        "key_findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "finding": {
                        "type": "string",
                        "description": "A key research finding"
                    },
                    "supporting_sources": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "url": {"type": "string"},
                                "quote": {"type": "string"}
                            },
                            "required": ["title", "url", "quote"]
                        }
                    }
                },
                "required": ["finding", "supporting_sources"]
            }
        },
        "timeline": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "date": {"type": "string"},
                    "event": {"type": "string"},
                    "significance": {"type": "string"}
                },
                "required": ["date", "event", "significance"]
            },
            "description": "Timeline of significant events related to the research topic"
        },
        "metadata": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "sources_analyzed": {"type": "integer"},
                "date_range": {
                    "type": "object",
                    "properties": {
                        "earliest": {"type": "string"},
                        "latest": {"type": "string"}
                    },
                    "required": ["earliest", "latest"]
                }
            },
            "required": ["query", "sources_analyzed", "date_range"]
        }
    },
    "required": ["title", "summary", "key_findings", "timeline", "metadata"]
}

# Define the available tools/functions for GPT
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_articles",
            "description": "Search for articles on a given topic using Exa API",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 5)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_article_content",
            "description": "Get the full content of specific articles by their URLs",
            "parameters": {
                "type": "object",
                "properties": {
                    "urls": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of article URLs to fetch content for"
                    }
                },
                "required": ["urls"]
            }
        }
    }
]

class GPTResearcher:
    def __init__(self):
        self.client = client
        
    def _handle_function_call(self, tool_call) -> str:
        """Handle function calls from GPT."""
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        
        if function_name == "search_articles":
            try:
                results = basic_search(arguments["query"], arguments.get("max_results", 5))
                return json.dumps([{
                    "title": r.title,
                    "url": r.url,
                    "published_date": r.published_date
                } for r in results])
            except Exception as e:
                print(f"Warning: Search failed - {str(e)}")
                return json.dumps([])
            
        elif function_name == "get_article_content":
            try:
                contents = get_contents(arguments["urls"])
                return json.dumps(dict(zip(arguments["urls"], contents)))
            except Exception as e:
                print(f"Warning: Content retrieval failed - {str(e)}")
                return json.dumps({url: "" for url in arguments["urls"]})
            
        return "Function not found"

    def research(self, query: str) -> Dict[str, Any]:
        """
        Perform research on a topic using GPT and Exa.
        
        Args:
            query: The research question or topic
            
        Returns:
            A structured research report following the REPORT_SCHEMA format
        """
        messages = [{
            "role": "system",
            "content": """You are a research assistant that helps find and analyze articles on various topics.
            Follow these steps:
            1. Search for relevant articles using the search_articles function
            2. Analyze the results and decide which articles to read in detail
            3. Get the content of the most relevant articles using get_article_content
            4. Provide a comprehensive research report following this exact structure:
            {
                "title": "Concise title for the research",
                "summary": "Brief executive summary",
                "key_findings": [
                    {
                        "finding": "Key research finding",
                        "supporting_sources": [
                            {
                                "title": "Article title",
                                "url": "Article URL",
                                "quote": "Relevant quote from article"
                            }
                        ]
                    }
                ],
                "timeline": [
                    {
                        "date": "YYYY-MM-DD",
                        "event": "Significant event description",
                        "significance": "Why this event matters"
                    }
                ],
                "metadata": {
                    "query": "Original search query",
                    "sources_analyzed": "Number of sources analyzed",
                    "date_range": {
                        "earliest": "YYYY-MM-DD",
                        "latest": "YYYY-MM-DD"
                    }
                }
            }
            
            IMPORTANT:
            - Your response MUST be valid JSON following this exact schema
            - Include direct quotes from articles to support key findings
            - Order timeline events chronologically
            - Ensure all dates are in YYYY-MM-DD format
            - Be thorough but concise in your analysis"""
        }, {
            "role": "user",
            "content": f"Research this topic and provide a structured report: {query}"
        }]
        
        while True:
            response = self.client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                response_format={"type": "json_object"}  # Force JSON output
            )
            
            message = response.choices[0].message
            
            # If we have function calls, handle them and continue the conversation
            if message.tool_calls:
                messages.append(message)  # Add assistant's message with function calls
                
                # Process each function call and add the results
                for tool_call in message.tool_calls:
                    function_response = self._handle_function_call(tool_call)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "content": function_response
                    })
                continue
            
            # If no function calls, we have our final response
            # Parse the JSON response to ensure it matches our schema
            try:
                report = json.loads(message.content)
                # TODO: Add schema validation here
                return report
            except json.JSONDecodeError:
                # If response is not valid JSON, try again
                messages.append({
                    "role": "user",
                    "content": "Please provide your response in valid JSON format following the specified schema exactly."
                })
                continue

def main():
    researcher = GPTResearcher()
    query = "What scientific studies reveal about cat intelligence and their unique behaviors?"
    print("Researching:", query)
    print("\nAnalyzing and summarizing articles...")
    report = researcher.research(query)
    
    # Print the raw JSON report
    print("\nRaw Research Report:")
    print(json.dumps(report, indent=2))
    
    # Generate visualizations
    from tools.report_visualizer import ReportVisualizer
    visualizer = ReportVisualizer()
    
    # Generate basic HTML report
    basic_report_path = visualizer.visualize(report, template='basic_report.html')
    print(f"\nBasic HTML report generated: {basic_report_path}")
    
    # Generate interactive D3.js report
    d3_report_path = visualizer.visualize(report, template='d3_report.html')
    print(f"\nInteractive D3.js report generated: {d3_report_path}")

if __name__ == "__main__":
    main() 