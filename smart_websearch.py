import requests
import urllib.parse
import json
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from bs4 import BeautifulSoup

def make_request_with_headers(url, headers):
    """
    Make an HTTP GET request to a specified URL with given headers.
    """
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.text
    except requests.RequestException as e:
        return f"An error occurred: {e}"

def urlencode(string):
    return urllib.parse.quote(string, safe='/+')

def replace_spaces_with_plus(string):
    return string.replace(" ", "+")

def fetch_web_content(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    return soup.get_text()

def fetch_content_make_summary(url):
    content = fetch_web_content(url)
    prompt = "Summarize this text into a 300-word extractive summary, ignore all HTML, CSS, and Javascript. The summary text should be easy to read, and engaging:\n" + content
    summary = chat_model.predict(prompt)
    return summary

origterms = input("Please enter your search term: ")
terms = replace_spaces_with_plus(origterms)
terms = urlencode(terms)

print("Searching...")

url = "https://api.search.brave.com/res/v1/web/search?result_filter=web&q=" + terms
headers = {
    'Accept': 'application/json',
    "X-Subscription-Token": 'BSAszfdhPkpD0ud0aJNBFALfVxSgCIl'
}
response = make_request_with_headers(url, headers)

# Response in is JSON see https://api.search.brave.com/app/documentation/web-search/responses
data = json.loads(response)
web = data['web']
results = web['results']

# Extract first 3 URLs
url1 = results[0]['url']
url2 = results[1]['url']
url3 = results[2]['url']

print("Init ChatGPT...")

# Different models
# gpt-4
# gpt-4-1106-preview
# gpt-3.5-turbo (gpt-3.5-turbo-0613)
chat_model = ChatOpenAI(model_name="gpt-3.5-turbo", openai_api_key="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")

print("Fetch first web page and create summary...")
sum1 = fetch_content_make_summary(url1)

print("Fetch second web page and create summary...")
sum2 = fetch_content_make_summary(url2)

print("Fetch third web page and create summary...")
sum3 = fetch_content_make_summary(url3)

print("Ask ChatGPT about this subject...")
prompt = "Create a detailed summary about " + origterms
sum0 = chat_model.predict(prompt)

print("Ask ChatGPT to create a meta summary...")
prompt = "Rewrite the following text as a blog post, ignoring all duplicate information. The blog post text should be easy to read, and engaging:\n\n" + sum1 + "\n\n\n" + sum2 + "\n\n\n" + sum3 + "\n\n\n" + sum0
msummary = chat_model.predict(prompt)
print("\n\n", msummary)
print("\n\nSources:\n", url1, "\n", url2, "\n", url3, "\nAnd ChatGPT!")
