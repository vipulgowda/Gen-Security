from langchain_google_genai import GoogleGenerativeAI
from langchain.agents import load_tools, AgentType
from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent
from langchain.agents.output_parsers import ReActSingleInputOutputParser
from langchain_community.tools import E2BDataAnalysisTool
import os


# Artifacts are charts created by matplotlib when `plt.show()` is called
def save_artifact(artifact):
    print("New matplotlib chart generated:", artifact.name)
    # Download the artifact as `bytes` and leave it up to the user to display them (on frontend, for example)
    file = artifact.download()
    basename = os.path.basename(artifact.name)

    # Save the chart to the `charts` directory
    with open(f"./charts/{basename}", "wb") as f:
        f.write(file)

os.environ["E2B_API_KEY"] = "e2b_0b1481ca38549fc90873bdcc85ebbfc7c740e546"

llm = GoogleGenerativeAI(model="gemini-pro", temperature=0)
base_prompt = hub.pull("langchain-ai/react-agent-template")
prompt = base_prompt.partial(instructions="Answer the user's request utilizing at most 8 tool calls")

e2b_data_analysis_tool = E2BDataAnalysisTool(
    # Pass environment variables to the sandbox
    env_vars={"MY_SECRET": "secret_value"},
    on_stdout=lambda stdout: print("stdout:", stdout),
    on_stderr=lambda stderr: print("stderr:", stderr),
    on_artifact=save_artifact,
)

with open("./hw2/netflix.csv") as f:
    remote_path = e2b_data_analysis_tool.upload_file(
        file=f,
        description="Data about Netflix tv shows including their title, category, director, release date, casting, age rating, etc.",
    )
    print(remote_path)    

tools = load_tools(["llm-math","terminal"], llm=llm, allow_dangerous_tools=True) + [e2b_data_analysis_tool.as_tool()]
agent = create_react_agent(llm,tools,prompt)
agent_executor = AgentExecutor(agent=agent,return_intermediate_steps=True, tools=tools, verbose=True, handle_parsing_errors=True)

print(f"Welcome to my application.  I am configured with these tools")
for tool in tools:
  print(f'  Tool: {tool.name} = {tool.description}')

while True:
    try:
        line = input("llm>> ")
        if line:
            result = agent_executor.invoke({"input": line})
            print(result)
        else:
            break
    except Exception as e:
        print(e)
