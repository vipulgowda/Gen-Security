from langchain_google_genai import GoogleGenerativeAI, HarmCategory, HarmBlockThreshold
from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import BaseTool, StructuredTool, tool
from langchain.pydantic_v1 import BaseModel, Field
import readline
import subprocess
import pexpect
import sys
import select
import threading
import re

command_line_injections="code refactoring for website"

llm = GoogleGenerativeAI(
    model="gemini-1.5-pro-latest",
    temperature=0,
    safety_settings = { HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE, }
    )

class Nmap(BaseModel):
    command: str = Field(description="""This tool has the same options and arguments as nmap command line tool.""")


@tool("nmap_validator",args_schema=Nmap)
def nmap_validator(command):
    """
    Validate the given nmap command for correct syntax and usage.
    """
    # Define a regular expression pattern for basic nmap command validation
    nmap_pattern = re.compile(r'^nmap\s+(?:(?:-[\w\/]+(?:\s+\S+)?\s*)+)?(?:[\w\.-]+|\d{1,3}(?:\.\d{1,3}){3}|\[\:\w+:\w+:\w+:\w+:\w+:\w+:\w+:\w+\])?(?:\/\d{1,2})?(?:\s+(?:(?:-[\w\/]+(?:\s+\S+)?\s*)+)?(?:[\w\.-]+|\d{1,3}(?:\.\d{1,3}){3}|\[\:\w+:\w+:\w+:\w+:\w+:\w+:\w+:\w+\])?(?:\/\d{1,2})?)*$')
    
    # Check if the command matches the basic pattern
    if not nmap_pattern.match(command):
        print("Command does not match basic nmap pattern.")
        return False
    
    # Split the command into a list for subprocess call
    command_list = command.split()
    
    try:
        command_list.insert(0, "sudo")
        # Run the command with subprocess to check its validity
        result = subprocess.run(command_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Check if there were any errors
        if result.returncode != 0:
            print("Error in nmap command execution:", result.stderr)
            return False
        
        # If no errors, command is valid
        return True
        
    except Exception as e:
        print("Exception occurred while validating command:", str(e))
        return False


@tool("nmap_tool")
def nmap_tool(command: str):
    """This tool prints out the command"""
    print(f"this is the command: {command}")
    return command


# tools = load_tools(["terminal"], llm=llm, allow_dangerous_tools=True)
tools = [nmap_tool, nmap_validator]
base_prompt = hub.pull("langchain-ai/react-agent-template")

prompt = base_prompt.partial(instructions="You are a cybersecurity expert with knowledge of nmap comamnds. Riterate as many times and validate the nmap commands")
agent = create_react_agent(llm,tools,prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

print(f"Welcome to my application.  I am configured with these tools")
for tool in tools:
  print(f'  Tool: {tool.name} = {tool.description}')

while True:
    try:
        line = input("llm>> ")
        if line:
            result = agent_executor.invoke({"input":line})
            print(result)
        else:
            break
    except Exception as e:
        print(e)
