# python -m venv /home/gary/src/gemini/
# cd src/gemini
# bin/pip install google-genai
# bin/python news.py

from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch
from datetime import date

today = date.today()
formatted_date = today.strftime("%B %d, %Y")

client = genai.Client(api_key="YOUR_API_KEY")
model_id = "gemini-2.0-flash-exp"

google_search_tool = Tool(
    google_search = GoogleSearch()
)

response = client.models.generate_content(
    model=model_id,
    contents="Find the latest tech news headlines in the USA and Europe for today " + formatted_date + ", and generate a list of the top 10 most important stories along with a brief summary of each story.",
    config=GenerateContentConfig(
        tools=[google_search_tool],
        response_modalities=["TEXT"],
    )
)

for each in response.candidates[0].content.parts:
    print(each.text)
