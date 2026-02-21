import json
from config import get_groq_client

def get_recommendation(user_query):
    # 1. Load your Indore Food Data
    with open('data/indore_vendors.json', 'r') as f:
        vendors = json.load(f)
    
    # 2. Prepare the Groq Client
    client = get_groq_client()
    
    # 3. Create the AI Prompt
    prompt = f"""
    You are an expert food guide for Indore city. 
    Based on the following vendor data: {vendors}
    
    User Question: {user_query}
    
    Provide a professional yet enthusiastic recommendation in 2-3 sentences. 
    Mention the specific location and dish.
    """
    
    # 4. Get Response from Llama 3 via Groq
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama3-8b-8192",
    )
    
    return response.choices[0].message.content

if __name__ == "__main__":
    query = "I am at Sarafa at 10 PM and want something sweet. Where should I go?"
    print(get_recommendation(query))