import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client
from openai import OpenAI
from mailjet_rest import Client

# Load environment variables
load_dotenv(override=True)

# Initialize clients
try:
    # Supabase setup
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    if not supabase_url or not supabase_key:
        raise ValueError("Supabase credentials not found")
    supabase = create_client(supabase_url, supabase_key)
    
    # OpenAI setup
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        raise ValueError("OpenAI key not found")
    client = OpenAI(api_key=openai_key)
    
    # Mailjet setup
    mailjet_api_key = os.getenv('MAILJET_API_KEY')
    mailjet_api_secret = os.getenv('MAILJET_API_SECRET')
    if not mailjet_api_key or not mailjet_api_secret:
        raise ValueError("Mailjet credentials not found")
    mailjet = Client(auth=(mailjet_api_key, mailjet_api_secret), version='v3.1')
        
    print("All API connections established successfully")
    
except Exception as e:
    print(f"Error initializing clients: {e}")
    exit(1)

def get_recent_data():
    """
    Fetch recent data from both tables with correct column names
    """
    try:
        # Get last 24 hours of data
        time_threshold = (datetime.utcnow() - timedelta(hours=24)).isoformat()
        
        # Fetch BTC prices with correct column names
        btc_prices = supabase.table('btc_price') \
            .select('id, price, timestamp') \
            .gte('timestamp', time_threshold) \
            .order('timestamp', desc=True) \
            .execute()
            
        # Fetch economic news with correct column names
        eco_news = supabase.table('eco_info') \
            .select('id, created_at, finance_info') \
            .gte('created_at', time_threshold) \
            .order('created_at', desc=True) \
            .execute()
            
        return btc_prices.data, eco_news.data
        
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None, None

def generate_analysis(btc_data, news_data):
    """
    Generate analysis using OpenAI with a personalized signature
    """
    try:
        # Prepare context with correct column names
        btc_context = "\n".join([
            f"Bitcoin Price at {item['timestamp']}: ${item['price']}"
            for item in btc_data[:5]
        ])
        
        news_context = "\n".join([
            f"News at {item['created_at']}: {item['finance_info']}"
            for item in news_data
        ])
        
        prompt = f"""
        As a professional financial analyst, write a concise email analyzing the following data:

        Recent Bitcoin Prices:
        {btc_context}

        Recent Financial News:
        {news_context}

        Focus on:
        1. Key price movements and their correlation with news
        2. Important market trends
        3. Potential short-term implications

        Keep the analysis professional, concise, and actionable.
        End the email with:
        
        Best regards,
        Ambika
        """
        
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional financial analyst writing a concise email update."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500
        )
        
        return completion.choices[0].message.content
        
    except Exception as e:
        print(f"Error generating analysis: {e}")
        return None

def send_email(analysis):
    """
    Send email using Mailjet
    """
    try:
        current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        
        data = {
            'Messages': [
                {
                    "From": {
                        "Email": "cvijay1116@gmail.com",  # Replace with your verified sender
                        "Name": "Finance Agent"
                    },
                    "To": [
                        {
                            "Email": "ambikaleads@gmail.com",
                            "Name": "Ambika"
                        }
                    ],
                    "Subject": f"Financial Market Analysis - {current_time}",
                    "TextPart": analysis,
                    "HTMLPart": analysis.replace('\n', '<br>')  # Basic HTML formatting
                }
            ]
        }
        
        result = mailjet.send.create(data=data)
        
        if result.status_code == 200:
            print("Email sent successfully!")
            return True
        else:
            print(f"Failed to send email. Status code: {result.status_code}")
            return False
        
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def main():
    try:
        # Fetch data
        btc_data, news_data = get_recent_data()
        if not btc_data or not news_data:
            print("No recent data found")
            return
            
        # Generate analysis
        analysis = generate_analysis(btc_data, news_data)
        if not analysis:
            print("Failed to generate analysis")
            return
            
        # Send email
        if send_email(analysis):
            print("Process completed successfully")
        else:
            print("Failed to send email")
            
    except Exception as e:
        print(f"Error in main process: {e}")

if __name__ == "__main__":
    main() 