from langchain.agents import AgentExecutor, create_react_agent
from langchain import hub
from langchain.tools import tool
from langchain_google_genai import GoogleGenerativeAI, HarmCategory, HarmBlockThreshold
import re
# Define the LLM
llm = GoogleGenerativeAI(
    model="gemini-1.5-pro-latest",
    temperature=0,
    safety_settings={
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }
)

def attack_questions(description):
    """
    Interactively asks a series of threat assessment questions to the user regarding application user wants to build. 
    The questions cover aspects such as application type, sensitivity level of the data, internet-facing status,
    and supported authentication methods. Each question might include multiple-choice options or be open-ended.
    """
    questions = [
        ("Select the application type?", [
         "Web Application", "Mobile Application", "Desktop Application", "Cloud Application", "IOT Application"]),
        ("What is the highest sensitivity level of the data processed by the application?", [
         "Top Secret", "Secret", "Confidential", "Restricted", "Unclassified", "None"]),
        ("Is the application internet-facing?", ["Yes", "No"]),
        ("What authentication methods are supported by the application?", [
         "Single Sign On", "Multi Factor Authentication", "OAuth2", "Basic", "None"])
    ]

    # Dictionary to store the answers
    answers = {}

    # Loop through the questions, asking each one
    for item in questions:
        if isinstance(item, tuple):
            question, options = item
            # Print the question and options with numbers
            print(question)
            for i, option in enumerate(options, 1):
                print(f"{i}. {option}")
            # Ask the question until a valid answer is given
            while True:
                try:
                    # Ask for the number corresponding to the choice
                    choice = int(input("Select your option (number): "))
                    # Validate the choice and store the answer if valid
                    if 1 <= choice <= len(options):
                        answers[question] = options[choice - 1]
                        break
                    else:
                        print("Please select a valid option number.")
                except ValueError:
                    print("Please enter a number.")
        else:
            # Ask the question
            answer = input(item + " ")
            # Store the answer in the dictionary
            answers[item] = answer

    # Print the answers
    print("\nHere are your answers:")
    response = []
    for question, answer in answers.items():
        if isinstance(question, tuple):
            print(f"{question[0]}: {answer}")
            response.append(answer)
        else:
            print(f"{question}: {answer}")
            response.append(answer)
    response.append(description)
    return response

def attack_tree_prompt(threat_model):
    """
    Generates a comprehensive prompt for conducting STRIDE threat modelling. This function is intended to be run
    after obtaining responses from the `threat_questions` function, using the responses as input to guide the threat 
    modelling process.
    """
    prompt = f"""
              Act as a cyber security expert with more than 20 years experience of using the STRIDE threat modelling methodology to produce comprehensive threat models for a wide range of applications. Your task is to use the application description provided to you to produce an attack tree in Mermaid syntax. The attack tree should reflect the potential threats for the application based on the details given.

              You MUST only respond with the Mermaid code block. See below for a simple example of the required format and syntax for your output.

              ```mermaid
              graph TD
                  A[Enter Chart Definition] --> B(Preview)
                  B --> C{{decide}}
                  C --> D["Keep"]
                  C --> E["Edit Definition (Edit)"]
                  E --> B
                  D --> F["Save Image and Code"]
                  F --> B
              ```

              IMPORTANT: Round brackets are special characters in Mermaid syntax. If you want to use round brackets inside a node label you MUST wrap the label in double quotes. For example, ["Example Node Label (ENL)"].
              content": {threat_model}
              """
    return prompt

# Integrate the tools with the LLM
tools = []

base_prompt = hub.pull("langchain-ai/react-agent-template")
prompt = base_prompt.partial(instructions="Answer the user's request utilizing at most 8 tool calls")

agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

print("Welcome to my application. I am configured with these tools:")
for tool in agent_executor.tools:
    print(f'  Tool: {tool.name} = {tool.description}')

while True:
    line = input("Describe the application to be modelled?>> ")
    try:
        if line:
            new_prompt = attack_tree_prompt(attack_questions(line))
            result = agent_executor.invoke({"input": new_prompt})
            resp = result['output']
            attack_tree_resp = re.sub(r'mermaid\s*graph TD\n|\n$', '', resp, flags=re.MULTILINE)
            print(attack_tree_resp)
        else:
            break
    except Exception as e:
        print(e)