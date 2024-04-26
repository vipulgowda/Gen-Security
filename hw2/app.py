from langchain_google_genai import GoogleGenerativeAI
from langchain.agents import load_tools, AgentType
from langchain import hub
from langchain.agents import tool
from langchain.agents import initialize_agent
from langchain_community.tools import E2BDataAnalysisTool
from dotenv import load_dotenv
from langchain_core.pydantic_v1 import BaseModel, Field
import os
import requests
import json
import csv


# Load environment variables from .env file
load_dotenv()

@tool
def get_word_length(word: str) -> int:
    """Returns the length of a word."""
    return len(word)


@tool
def fetch_json(bus_id: int) -> str:
    """takes the bus_id provided by the user and fetches the result and stores the response in a file"""
    bus_url = f'https://busdata.cs.pdx.edu/api/getBreadCrumbs?vehicle_id={bus_id}'
    response = requests.get(bus_url)
    response = response.json()
    with open(f'./hw2/{bus_id}.json', "w", encoding='utf-8') as file:
        return json.dump(response, file, indent=4)


@tool
def json_to_csv(bus_id):
    """takes the bus_id and converts the json file stored in files directory to csv directory"""
    with open(f'./hw2/{bus_id}.json', 'r') as f:
        data = json.load(f)
    
    # Get the field names from the first element of the JSON data
    field_names = list(data[0].keys())

    with open(f'./hw2/{bus_id}.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=field_names)
        writer.writeheader()
        for row in data:
            writer.writerow(row)
        fetch_bus_charts(bus_id)

def fetch_bus_charts(bus_id):
    """takes the bus_id and loads it to e2b data analysis tool"""
    with open(f"./hw2/{bus_id}.csv") as f:
        e2b_data_analysis_tool.upload_file(
        file=f,
        description="Data about Netflix tv shows including their title, category, director, release date, casting, age rating, etc.",
    )
    print("Loaded to e2b data analysis")

# Artifacts are charts created by matplotlib when `plt.show()` is called
def save_artifact(artifact):
    print("New matplotlib chart generated:", artifact.name)
    # Download the artifact as `bytes` and leave it up to the user to display them (on frontend, for example)
    file = artifact.download()
    basename = os.path.basename(artifact.name)

    # Save the chart to the `charts` directory
    with open(f"./hw2/{basename}", "wb") as file:
        f.write(file)

os.environ["E2B_API_KEY"] = os.getenv('E2B_API_KEY')

llm = GoogleGenerativeAI(model="gemini-pro",temperature=0)
base_prompt = hub.pull("langchain-ai/react-agent-template")
prompt = base_prompt.partial(instructions="Answer the user's request utilizing at most 8 tool calls")


class E2BDataAnalysisToolArguments(BaseModel):
    """Arguments for the E2BDataAnalysisTool. It should be in code format. Do not use Tool Call or python in string format"""

    python_code: str = Field(
        ...,
        example='''
        def print_hello():
            print("Hello World")
        ''',
        description=(
            "You should just output the formatted code and do not stringify"
        ),
    )

e2b_data_analysis_tool = E2BDataAnalysisTool(
    # Pass environment variables to the sandbox
    env_vars={"MY_SECRET": "secret_value"},
    on_stdout=lambda stdout: print("stdout:", stdout),
    on_stderr=lambda stderr: print("stderr:", stderr),
    on_artifact=save_artifact,
    args_schema=E2BDataAnalysisToolArguments
)

with open("./hw2/netflix.csv") as f:
    remote_path = e2b_data_analysis_tool.upload_file(
        file=f,
        description="Data about Netflix tv shows including their title, category, director, release date, casting, age rating, etc.",
    )
    print(remote_path)    

tools = load_tools(["llm-math","terminal"], llm=llm, allow_dangerous_tools=True) + [e2b_data_analysis_tool.as_tool()] + [get_word_length, fetch_json, json_to_csv]

agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=True,
)

print(f"Welcome to my application.  I am configured with these tools")
for tool in tools:
  print(f'  Tool: {tool.name} = {tool.description}')

while True:
    try:
        line = input("llm>> ")
        if line:
            result = agent.invoke({ "input":line})
            #agent_executor.invoke({"input": line})
            print(result)
            e2b_data_analysis_tool.close()
        else:
            e2b_data_analysis_tool.close()
            break
    except Exception as e:
        print(e)
        e2b_data_analysis_tool.close()
