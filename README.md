# **Baby J.A.R.V.I.S.**

BABY J.A.R.V.I.S. is an assistant agent that uses Langchain and various tools to enhance productivity. It leverages NVIDIA foundation models with Langchain to access Notion, Google Calendar, Gmail, DuckDuckGo, and Google Scholar. It can perform tasks such as creating and summarizing notes, searching for information and scholarly papers, scheduling events, and managing emails. Two of the tools are custom tools I built utilizing the Notion API and Google Calendar API. The interface, built with Streamlit, allows easy access from any internet-connected device.

## Caution ⚠️

This is my first GitHub repository, so please forgive any novice mistakes :)

## Gather API Resources

First thing first, you need to get all of the resources you need in order for the agent to use the tools.

| Name | Type | Link |
| --- | --- | --- |
| Notion | API key & Page permissions & Page ID | https://developers.notion.com/docs/create-a-notion-integration |
| Gmail | Credentials json | https://developers.google.com/gmail/api/quickstart/python#authorize_credentials_for_a_desktop_application |
| Google Scholar | API key | https://serpapi.com/ |
| Nvidia Foundation Model | API key | https://build.nvidia.com/explore/discover |

## Video Tutorial

[![YouTube](http://i.ytimg.com/vi/DWPtfnuXFAA/hqdefault.jpg)](https://www.youtube.com/watch?v=DWPtfnuXFAA)

## Configuration

Once you get all of your resources begin going through `Tools.py` and `babyjarvis.py` replacing anything that ask you to with your resource for the API and also make sure to for Gmail API what ever file they gave you it must be renamed to `credentials.json` and placed in the save folder as `babyjarvis.py`.

## Installation

To install the necessary dependencies, run the following command:

```
pip install -r requirements.txt
```

## Running the App

To run the the agent, use the following command:

```
streamlit run babyjarvis.py
```

## Token

If you get an error saying your token expired you must go and delete `Token.json` and rerun it
