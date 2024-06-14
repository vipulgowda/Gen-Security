from langchain import hub
from langchain.agents import Tool, create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI,GoogleGenerativeAI, HarmCategory, HarmBlockThreshold
# from langchain_community.utilities import GoogleSerperAPIWrapper
import os
from typing import TypedDict, Annotated, Union
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.messages import BaseMessage
import operator
from typing import TypedDict, Annotated
from langchain_core.agents import AgentFinish
from langgraph.prebuilt.tool_executor import ToolExecutor
from langgraph.prebuilt import ToolInvocation
from langgraph.graph import END, StateGraph
from langchain_core.agents import AgentActionMessageLog
from ThreatIntelligence import get_user_selections, generate_scenario_google
from ThreatModel_new import generate_threat_model_google, threat_questions
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
import json
from langchain.agents import AgentExecutor

from langsmith import Client
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "LangSmith Introduction"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
client = Client()

llm = GoogleGenerativeAI(
    model="gemini-1.5-pro-latest",
    temperature=0,
    safety_settings={
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }
)

@tool
def run_intelligence():
    """
    Main function to run when asked for creating threat scenarios

    Returns:
        str: The final generated scenario, or None if an error prevents scenario generation.
    """
    selections = get_user_selections()
    response = generate_scenario_google(selections)
    return response

@tool
def threat_model():
    """
    Main function to run when asked for creating threat model
    """
  
    ques = " Develop highly secure web application for a finance company to manage customer portfolios, handle transactions, and provide real-time financial analytics. This application must offer a responsive user interface, ensure seamless performance, and incorporate advanced security measures to safeguard sensitive financial data. The application will utilize ReactJS on the frontend to deliver a dynamic and responsive experience. The backend will be powered by Node.js to handle server-side logic, API integrations, and interactions with our MongoDB database, which will store user profiles, transaction records, and financial data. All stored data will be encrypted using AES, and SSL/TLS will be used to secure data transmission. The system will feature different access levels for administrators, financial advisors, and customers to ensure data security. The system will support initiating, processing, and reviewing transactions with comprehensive logging and auditing."
    selections = threat_questions(ques)
    response = generate_threat_model_google(selections)
    return response



tools = [
  Tool(
        name="Model",
        func=threat_model,
        description="use to create threat models",
    ),
    Tool(
        name="Intelligence",
        func=run_intelligence,
        description="Use to create threat scenarios",
    )
]

base_prompt = hub.pull("langchain-ai/react-agent-template")
prompt = base_prompt.partial(instructions="Answer the user's request utilizing at most 4 tool calls")

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro-latest",
    temperature=0,
    safety_settings={
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }
)

tools = [run_intelligence(),threat_model()]
from langchain_core.output_parsers import StrOutputParser

agent_runnable = create_react_agent(llm, tools, prompt)


class AgentState(TypedDict):
    input: str
    chat_history: list[BaseMessage]
    agent_outcome: Union[AgentAction, AgentFinish, None]
    return_direct: bool
    intermediate_steps: Annotated[list[tuple[AgentAction, str]], operator.add]


tool_executor = ToolExecutor(tools)


def run_agent(state):
    """
    #if you want to better manages intermediate steps
    inputs = state.copy()
    if len(inputs['intermediate_steps']) > 5:
    inputs['intermediate_steps'] = inputs['intermediate_steps'][-5:]
    """
    agent_executor = AgentExecutor(agent=agent_runnable, tools=tools, verbose=True)
    agent_outcome = agent_executor.invoke({"input": state["input"]})
    return {"agent_outcome": agent_outcome}


def execute_tools(state):
    messages = [state['agent_outcome']]
    last_message = messages[-1]
    ######### human in the loop ###########
    # human input y/n
    # Get the most recent agent_outcome - this is the key added in the `agent` above
    state_action = state['agent_outcome']
    human_key = input(f"[y/n] continue with: {state_action}?")
    if human_key == "n":
        raise ValueError

    tool_name = last_message.tool

    arguments = last_message

    if tool_name == "Intelligence" or tool_name == "Model":

        if "return_direct" in arguments:
            del arguments["return_direct"]
    action = ToolInvocation(
        tool=tool_name,
        tool_input=last_message.tool_input,
    )
    response = tool_executor.invoke(action)
    return {"intermediate_steps": [(state['agent_outcome'], response)]}


def should_continue(state):
    print(state)
    messages = [state['agent_outcome']]

    last_message = messages[-1]

    if "Action" not in last_message:
        return "end"
    else:
        arguments = state["return_direct"]
        if arguments is True:
            return "final"
        else:
            return "continue"


# def first_agent(inputs):
#     action = AgentActionMessageLog(
#         tool="Search",
#         tool_input=inputs["input"],
#         log="",
#         message_log=[]
#     )
#     return {"agent_outcome": action}


workflow = StateGraph(AgentState)

workflow.add_node("agent", run_agent)
workflow.add_node("action", execute_tools)
workflow.add_node("final", execute_tools)
# uncomment if you want to always calls a certain tool first
# workflow.add_node("first_agent", first_agent)


workflow.set_entry_point("agent")
# uncomment if you want to always calls a certain tool first
# workflow.set_entry_point("first_agent")

workflow.add_conditional_edges(
    "agent", should_continue,
    {"continue": "action", "final": "final", "end": END})


workflow.add_edge('action', 'agent')
workflow.add_edge('final', END)
# uncomment if you want to always calls a certain tool first
# workflow.add_edge('first_agent', 'action')
chain = workflow.compile()


# The following functions interoperate between the top level graph state
# and the state of the research sub-graph
# this makes it so that the states of each graph don't get intermixed
# def enter_chain(message: str):

#   results = {
#         "messages": [HumanMessage(content=message)],
#     }
#   return results

# research_chain = enter_chain | chain

# for s in research_chain.stream(
#     {"input": "create a threat model using threat modelling tool"}, {"recursion_limit": 100}
# ):
#     if "__end__" not in s:
#         print(s)
#         print("---")

result = chain.invoke(
    {"input": "create a threat model using threat modelling tool", "chat_history": [], "return_direct": False})

print(result)
