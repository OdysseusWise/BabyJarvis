import os
import streamlit as st
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage
from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain_community.callbacks.manager import get_openai_callback
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from Tools import tools
import signal

os.environ["NVIDIA_API_KEY"] = "(PUT-API-KEY-HERE)"

llm = ChatNVIDIA(temperature=0.25, model="meta/llama3-70b-instruct")

system = '''Respond to the human as helpfully and accurately as possible. You have access to the following tools:

{tools}

Use a json blob to specify a tool by providing an action key (tool name) and an action_input key (tool input).

Valid "action" values: "Final Answer" or {tool_names}

Whenever user ask to search or ask for latest info use the 'duck_search' tool. When every user ask you to make/create notes you MUST use the 'make_notes' only and 'get_notes' when the user all to get their notes. Make sure not to use scholar tool unless directly asked to do scholar search. When the user says to send an email you MUST use 'send_gmail_message' tool and not an email draft tool and if user ask to make an email draft use the email draft tool and do not send an email.

ONLY EVER USE ONE ACTION

The $JSON_BLOB should only contain a SINGLE action and MUST be formatted as markdown, do NOT return a list of multiple actions. Here is an example of a valid $JSON_BLOB:

```
{{
  "action": $TOOL_NAME,
  "action_input": $INPUT
}}
```
Make sure to have the $INPUT in the right format for the tool you are using.

ONLY EVER USE ONE ACTION

Follow this format with ONLY ONE Action/$JSON_BLOB (remember to only focus and think about the most recent message from human nothing before that only their most recent message if the question asked by the user does not need a tool or they don't ask you to do something just respond and SKIP the action no action should be used unless you are certain they want you to use a tool claify to them if you are unsure):

Question: the input question you must answer
Thought: (Think about if your response needs a action only focus on the newest closet messsage from human if the user does not ask you or make it clear they want you to probably use a tool SKIP the one action.) you should always think about one action to take. Only one action at a time in this format:
Action:
```
$JSON_BLOB
```
Observation: the result of the action that you MUST include in your 'Final answer'
... (this Thought/Action/Observation can repeat N times, you should take several steps when needed. The $JSON_BLOB must be formatted as markdown and only use a SINGLE action at a time.)
Thought: I know what to respond
Action:
```
{{
  "action": "Final Answer",
  "action_input": "Final response to human"
}}

ONLY EVER USE ONE ACTION

Begin! Reminder to ALWAYS respond with a valid json blob of a single action. Use tools if necessary. Respond directly if appropriate. Format is Action:```$JSON_BLOB```then Observation'''

chat_history = []

human = '''

Chat History (Remember This is NOT my Response or Current Request):{chat_history}

My current Response:{input}

{agent_scratchpad}

(reminder to respond in a JSON blob no matter what)'''

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", human),
    ]
)

agent = create_structured_chat_agent(llm, tools, prompt)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    handle_parsing_errors=True,
    verbose=True,
    max_iterations=100,
    stream_runnable=True,
)

with st.sidebar:
    st.title('Baby J.A.R.V.I.S.')
    if st.button("Clear Conversation"):
        st.session_state.messages = [{"role": "assistant", "content": "How can I assist you today?"}]
        st.session_state["History"] = [AIMessage(content="How can I assist you today?")]
        chat_history = []
        st.rerun()
    if st.button("Quit"):
        os.kill(os.getpid(), signal.SIGTERM)

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I assist you today?"}]
    st.session_state["History"] = [AIMessage(content="How can I assist you today?")]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input("Type your message here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state["History"].append(HumanMessage(content=prompt))
    st.chat_message("user").write(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        with get_openai_callback() as cb:
            try:
                out = agent_executor.invoke({"input": prompt, "chat_history": st.session_state["History"],})
            except AssertionError as e:
                st.error(f"An error occurred: {str(e)}")
                st.stop()
        
        for chunk in out["output"]:
            full_response += chunk
            message_placeholder.markdown(full_response + "|")
        
        message_placeholder.markdown(full_response)
        
        st.session_state["History"].append(AIMessage(content=full_response))
        st.session_state.messages.append({"role": "assistant", "content": full_response})