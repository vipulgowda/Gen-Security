from langchain.agents import AgentExecutor, create_react_agent
from langchain import hub
from langchain.tools import tool
from langchain_google_genai import GoogleGenerativeAI, HarmCategory, HarmBlockThreshold
import json

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

def threat_prompt(threat_model):
    """
    Generates a comprehensive prompt for conducting STRIDE threat modelling. This function is intended to be run
    after obtaining responses from the `threat_questions` function, using the responses as input to guide the threat 
    modelling process.

    The function constructs a detailed prompt for a cybersecurity expert with over 20 years of experience in using 
    the STRIDE methodology. It requests the production of a list of specific threats for each of the STRIDE categories:
    Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, and Elevation of Privilege.

    Parameters:
        threat_model (list): A list containing the responses from the `threat_questions` function. This list should 
                             include the application type, authentication methods, internet-facing status, data sensitivity,
                             and a brief application description.
                             
    Returns:
        str: A string prompt formatted to guide the creation of a threat model, including a template for a JSON response 
             with keys for "threat_model" and "improvement_suggestions", where the threat model should detail the threats
             identified and the suggestions should advise on how to improve the threat modelling process based on the 
             application description.

    The returned prompt also includes placeholders for inserting specific application details such as application type,
    authentication methods, whether the application is internet-facing, the sensitivity of the data, and a brief 
    description of the application, which are used to tailor the threat scenarios and suggestions.
    """
    prompt = f"""
              Act as a cyber security expert with more than 20 years experience of using the STRIDE threat modelling methodology to produce comprehensive threat models for a wide range of applications. Your task is to use the application description and additional provided to you to produce a list of specific threats for the application.

              For each of the STRIDE categories (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, and Elevation of Privilege), list multiple (3 or 4) credible threats if applicable. Each threat scenario should provide a credible scenario in which the threat could occur in the context of the application. It is very important that your responses are tailored to reflect the details you are given.

              When providing the threat model, use a JSON formatted response with the keys "threat_model" and "improvement_suggestions". Under "threat_model", include an array of objects with the keys "Threat Type", "Scenario", and "Potential Impact". 

              Under "improvement_suggestions", include an array of strings with suggestions on how the threat modeller can improve their application description in order to allow the tool to produce a more comprehensive threat model.

              APPLICATION TYPE: {threat_model[0]}
              AUTHENTICATION METHODS: {threat_model[1]}
              INTERNET FACING: {threat_model[2]}
              SENSITIVE DATA: {threat_model[3]}
              APPLICATION DESCRIPTION: {threat_model[4]}

              Example of expected JSON response format:
                
                  {{
                    "threat_model": [
                      {{
                        "Threat Type": "Spoofing",
                        "Scenario": "Example Scenario 1",
                        "Potential Impact": "Example Potential Impact 1"
                      }},
                      {{
                        "Threat Type": "Spoofing",
                        "Scenario": "Example Scenario 2",
                        "Potential Impact": "Example Potential Impact 2"
                      }},
                      // ... more threats
                    ],
                    "improvement_suggestions": [
                      "Example improvement suggestion 1.",
                      "Example improvement suggestion 2.",
                      // ... more suggestions
                    ]
                  }}
              """
    return prompt

def json_to_markdown(threat_model, improvement_suggestions):
    """
    Converts a JSON-formatted threat model and improvement suggestions into a Markdown formatted document. 
    This function is typically used to present the output from the `generate_threat_model` function in a human-readable format.

    The output includes a Markdown section for the threat model, formatted as a table with columns for "Threat Type", 
    "Scenario", and "Potential Impact". Each threat from the threat model is listed in this table. Another section lists 
    all improvement suggestions as bullet points under a separate heading.

    Parameters:
        threat_model (list of dicts): A list of dictionaries where each dictionary represents a threat with keys for 
                                      "Threat Type", "Scenario", and "Potential Impact". This list is generated by the 
                                      `generate_threat_model` function.
        improvement_suggestions (list of str): A list of strings, each being a suggestion on how to improve the application
                                               description to enable a more comprehensive threat model. Also generated by 
                                               the `generate_threat_model` function.

    Returns:
        str: A string containing the formatted Markdown document. The document includes a table of threats and a list 
             of improvement suggestions, each formatted for clarity and ease of reading.

    This function ensures that the output is well-organized, making it suitable for presentations, reports, or 
    documentation that requires a clear and professional appearance.
    """
    markdown_output = "## Threat Model\n\n"
    
    # Start the markdown table with headers
    markdown_output += "| Threat Type | Scenario | Potential Impact |\n"
    markdown_output += "|-------------|----------|------------------|\n"
    
    # Fill the table rows with the threat model data
    for threat in threat_model:
        markdown_output += f"| {threat['Threat Type']} | {threat['Scenario']} | {threat['Potential Impact']} |\n"
    
    markdown_output += "\n\n## Improvement Suggestions\n\n"
    for suggestion in improvement_suggestions:
        markdown_output += f"- {suggestion}\n"
    
    return markdown_output
    

# Integrate the tools with the LLM
tools = []

base_prompt = hub.pull("langchain-ai/react-agent-template")
prompt = base_prompt.partial(instructions="Answer the user's request utilizing at most 8 tool calls")

agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

print("Welcome to my threat model application")
for tool in agent_executor.tools:
    print(f'  Tool: {tool.name} = {tool.description}')

while True:
    line = input("Describe the application to be modelled? ")
    try:
        if line:
            new_prompt = threat_prompt(threat_questions(line))
            result = agent_executor.invoke({"input": new_prompt})
            cleaned_string = result["output"].strip('`')[5:].strip()
            json_data = json.loads(cleaned_string)
            threat_model = json_data["threat_model"]
            improvement_suggestions = json_data["improvement_suggestions"]
            final_res = json_to_markdown(threat_model, improvement_suggestions)
            print(final_res)
        else:
            break
    except Exception as e:
        print(e)