from langchain.agents import AgentExecutor, create_react_agent
from langchain import hub
from langchain.tools import tool
from langchain_google_genai import GoogleGenerativeAI, HarmCategory, HarmBlockThreshold

# Define the LLM
llm = GoogleGenerativeAI(
    model="gemini-1.5-pro-latest",
    temperature=0,
    safety_settings={
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }
)

def threat_questions(description):
    """
    Interactively asks a series of threat assessment questions to the user regarding application user wants to build. 
    The questions cover aspects such as application type, sensitivity level of the data, internet-facing status,
    and supported authentication methods. Each question might include multiple-choice options or be open-ended.

    The function executes a loop where it:
    - Displays each question along with the options (if any).
    - Accepts user input as answers, ensuring inputs are valid where necessary.
    - Stores each answer in a dictionary, keyed by the question.

    Returns:
        dict: A dictionary containing the questions as keys and the user-provided answers as values. 
              For multiple-choice questions, the selected option is stored as the answer.

    Raises:
        ValueError: If the user inputs a non-integer where an integer is expected for option selection.
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

# Function to create a prompt to generate mitigating controls
def create_mitigations_prompt(threats):
    prompt = f"""
Act as a cyber security expert with more than 20 years experience of using the STRIDE threat modelling methodology. Your task is to provide potential mitigations for the threats identified in the threat model. It is very important that your responses are tailored to reflect the details of the threats.

Example of expected JSON response format:
{{
  "Threat_type": "spoofing",
  "Scenario": "Scenario 1",
  "Suggested Mitigation": "Mitigation1"
}} // ... more threats

Below is the list of identified threats:
{threats}

YOUR RESPONSE (do not wrap in a code block):
"""
    return prompt


# Integrate the tools with the LLM
tools = []

base_prompt = hub.pull("langchain-ai/react-agent-template")
prompt = base_prompt.partial(instructions="You are a helpful assistant that provides threat mitigation strategies in Markdown format.")

agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

print("Welcome to Threat Mitigation application.")
for tool in agent_executor.tools:
    print(f'  Tool: {tool.name} = {tool.description}')

while True:
    line = input("Describe the application to show the mitigation: ")
    try:
        if line:
            new_prompt = create_mitigations_prompt(threat_questions(line))
            result = agent_executor.invoke({"input": new_prompt})
            print(result['output'])
        else:
            break
    except Exception as e:
        print(e)