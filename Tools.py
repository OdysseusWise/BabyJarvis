import os
import requests
import pickle
from datetime import datetime, timezone
from langchain_core.tools import Tool
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.tools.google_scholar import GoogleScholarQueryRun
from langchain_community.utilities.google_scholar import GoogleScholarAPIWrapper
from langchain_community.agent_toolkits import GmailToolkit
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import StructuredTool
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

os.environ["SERP_API_KEY"] = "(PUT-API-KEY-HERE)"
NOTION_TOKEN = "(PUT-TOKEN-KEY-HERE)"
DATABASE_ID = "(PUT-DATABASE-ID-HERE)"

headers = {
    "Authorization": "Bearer " + NOTION_TOKEN,
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

wrapper = DuckDuckGoSearchAPIWrapper(max_results=15)

search = DuckDuckGoSearchRun(api_wrapper=wrapper)
scholar_search = GoogleScholarQueryRun(api_wrapper=GoogleScholarAPIWrapper())
gmail_toolkit = GmailToolkit()

class PageInput(BaseModel):
    title: str = Field(description="The title for the notes")
    notes: str = Field(description="write all notes and info for the user")

# Define the function to create a page in Notion
def create_page(title: str, notes: str) -> str:
    create_url = "https://api.notion.com/v1/pages"

    published_date = datetime.now().astimezone(timezone.utc).isoformat()
    data = {
        "Title": {"title": [{"text": {"content": title}}]},
        "Notes": {"rich_text": [{"text": {"content": notes}}]},
        "Published": {"date": {"start": published_date, "end": None}}
    }

    payload = {"parent": {"database_id": DATABASE_ID}, "properties": data}
    res = requests.post(create_url, headers=headers, json=payload)
    return res

notion = StructuredTool.from_function(
    func=create_page,
    name="make_notes",
    description="When you need to make a note for user with a title and notes section.",
    args_schema=PageInput,
)

def get_pages_and_parse(num_pages=None) -> str:
    """
    Fetches pages from Notion and parses URL, Title, and Published fields.
    
    If num_pages is None, get all pages, otherwise just the defined number.
    Returns a list of tuples containing (url, title, published).
    """
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"

    get_all = num_pages is None
    page_size = 100 if get_all else num_pages

    payload = {"page_size": page_size}
    response = requests.post(url, json=payload, headers=headers)

    data = response.json()
    results = data["results"]

    # Continue fetching if there are more pages and get_all is True
    while data.get("has_more") and get_all:
        payload = {"page_size": page_size, "start_cursor": data["next_cursor"]}
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        results.extend(data["results"])

    parsed_pages = []
    for page in results:
        page_id = page["id"]
        props = page["properties"]

        # Check if URL property exists and is not empty
        title = None
        if "Title" in props and props["Title"]["title"]:
            title = props["Title"]["title"][0]["text"]["content"]

        # Check if Title property exists and is not empty
        notes = None
        if "Notes" in props and props["Notes"]["rich_text"]:
            notes = props["Notes"]["rich_text"][0]["text"]["content"]

        # Check if Published property exists and is not empty
        published = None
        if "Published" in props and props["Published"]["date"]:
            published = props["Published"]["date"]["start"]
            published = datetime.fromisoformat(published)
        
        # Append only if all variables are not None
        if title and notes and published:
            parsed_pages.append((title, notes, published))
    
    return parsed_pages

class EventInput(BaseModel):
    text: str = Field(description="Description of the event including date, time, place, and year, examples: 'Venom 3 Movie Release on June 1 1:00pm-4:25pm','Appointment at Home on April 3rd 2025 10am-10:25am','Independence Day at Whitehouse on May 25 5am-6:45am' ")

SCOPES = ['https://www.googleapis.com/auth/calendar.events']

def create_event(text: str) -> str:
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)
    created_event = service.events().quickAdd(calendarId='primary', text=text).execute()
    
    return created_event['id']

event_calendar_tool = StructuredTool.from_function(
    func=create_event,
    name="EventCreator",
    description="Create a calendar event with a given description for user and do not include a place or year in the event unless specified otherwise by user",
    args_schema=EventInput,
)

get_notes = StructuredTool.from_function(
    func=get_pages_and_parse,
    name="get_notes",
    description="use to get notes Fetches all notes from Notion, returning Title, Notes, and Published fields.",
)

duck = Tool(
    name="duck_search",
    description="Search DuckDuckGo for recent results.",
    func=search.run,
)
scholar = Tool(
    name="scholar_search",
    description="Search Google Scholar for recent results of scholarly literature. NEVER USE unless directly asked to do a scholar search",
    func=scholar_search.run,
)
gmail = gmail_toolkit.get_tools()

tools = [duck,scholar,*gmail,notion,get_notes,event_calendar_tool]

