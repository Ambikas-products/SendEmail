import requests
from datetime import datetime
from supabase import create_client
import os
from dotenv import load_dotenv
from openai import OpenAI
import time
import sys  # Added for clean exit

# Load environment variables
load_dotenv(override=True)

# Initialize clients
try:
    # Supabase setup
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        raise ValueError("Supabase credentials not found in environment variables")
    
    supabase = create_client(supabase_url, supabase_key)
    
    # OpenAI setup
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        raise ValueError("OpenAI key not found in environment variables")
    
    client = OpenAI(api_key=openai_key)
    
    # Brave Search setup
    brave_api_key = os.getenv('BRAVE_API_KEY')
    if not brave_api_key:
        raise ValueError("Brave API key not found in environment variables")
        
    print("All API connections established successfully")
    
except Exception as e:
    print(f"Error initializing clients: {e}")
    exit(1)

def search_brave_news(query: str) -> list:
    """
    Search for news using Brave Search API with rate limiting
    """
    try:
        headers = {
            'X-Subscription-Token': brave_api_key,
            'Accept': 'application/json',
        }
        
        params = {
            'q': query,
            'format': 'news',
            'count': 5
        }
        
        response = requests.get(
            'https://api.search.brave.com/res/v1/news/search',
            headers=headers,
            params=params
        )
        
        response.raise_for_status()  # This will raise an exception for any bad status code
        time.sleep(1.1)
        return response.json()['results']
        
    except Exception as e:
        print(f"Fatal error in search_brave_news: {e}")
        sys.exit(1)  # Exit immediately on error

def store_news(news_info: str) -> bool:
    """
    Store news in Supabase database
    Args:
        news_info (str): The financial news information to store
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        data = {
            'created_at': datetime.utcnow().isoformat(),  # Changed from timestamp to created_at
            'finance_info': news_info
        }
        
        # Insert data into eco_info table
        result = supabase.table('eco_info').insert(data).execute()  # Changed from eco_news to eco_info
        print("News stored successfully:", result)
        return True
        
    except Exception as e:
        print(f"Fatal error in store_news: {e}")
        sys.exit(1)  # Exit immediately on error

def search_crypto_news() -> list:
    """
    Search specifically for crypto and Bitcoin related news
    """
    crypto_queries = [
        "bitcoin price market analysis",
        "cryptocurrency market trends",
        "crypto market updates",
    ]
    
    crypto_news = []
    print("\nFetching crypto news...")
    for i, query in enumerate(crypto_queries, 1):
        print(f"Fetching crypto query {i} of {len(crypto_queries)}: {query}")
        results = search_brave_news(query)
        crypto_news.extend(results)
    
    return crypto_news

def search_macro_news() -> list:
    """
    Search for general financial and macro market news
    """
    macro_queries = [
        "global financial markets analysis",
        "macroeconomic trends news",
        "stock market economic impact",
    ]
    
    macro_news = []
    print("\nFetching macro financial news...")
    for i, query in enumerate(macro_queries, 1):
        print(f"Fetching macro query {i} of {len(macro_queries)}: {query}")
        results = search_brave_news(query)
        macro_news.extend(results)
    
    return macro_news

def process_news_with_ai(news_list: list, news_type: str):
    """
    Process news with OpenAI to extract relevant information
    Args:
        news_list (list): List of news articles
        news_type (str): Type of news ('crypto' or 'macro')
    """
    try:
        tools = [{
            "type": "function",
            "function": {
                "name": "store_news",
                "description": "Store important financial news in the database",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "news_info": {
                            "type": "string",
                            "description": "The processed financial news information"
                        }
                    },
                    "required": ["news_info"]
                }
            }
        }]

        system_prompt = {
            'crypto': "You are a cryptocurrency market analyst. Summarize and analyze the key points of this news article, focusing on its impact on Bitcoin and crypto markets. Format your response to highlight price impacts and market sentiment.",
            'macro': "You are a macro financial analyst. Summarize and analyze the key points of this news article, focusing on its impact on global markets and potential effects on cryptocurrency markets. Format your response to highlight economic indicators and market correlations."
        }

        for news_item in news_list:
            try:
                completion = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": system_prompt[news_type]
                        },
                        {
                            "role": "user",
                            "content": f"Title: {news_item['title']}\nDescription: {news_item['description']}"
                        }
                    ],
                    tools=tools,
                    tool_choice="auto"
                )

                if completion.choices[0].message.tool_calls:
                    tool_call = completion.choices[0].message.tool_calls[0]
                    if tool_call.function.name == "store_news":
                        import json
                        args = json.loads(tool_call.function.arguments)
                        store_news(args["news_info"])

            except Exception as e:
                print(f"Fatal error processing news item: {e}")
                sys.exit(1)

    except Exception as e:
        print(f"Fatal error in process_news_with_ai: {e}")
        sys.exit(1)

def main():
    try:
        # Process crypto news
        crypto_news = search_crypto_news()
        if crypto_news:
            print(f"\nProcessing {len(crypto_news)} crypto news items...")
            process_news_with_ai(crypto_news, 'crypto')
        else:
            print("No crypto news found.")

        # Process macro news
        macro_news = search_macro_news()
        if macro_news:
            print(f"\nProcessing {len(macro_news)} macro news items...")
            process_news_with_ai(macro_news, 'macro')
        else:
            print("No macro news found.")

        print("\nAll news processed successfully!")
        
    except Exception as e:
        print(f"Fatal error in main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
