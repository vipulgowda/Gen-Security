import os
import json
import argparse
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAI, HarmCategory, HarmBlockThreshold
from langchain.prompts.chat import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from mitreattack.stix20 import MitreAttackData

# Predefined incident response templates
incident_response_templates = {
    "Phishing Attack": ["Spearphishing Attachment (T1193)", "User Execution (T1204)", "Browser Extensions (T1176)", "Credentials from Password Stores (T1555)", "Input Capture (T1056)", "Exfiltration Over C2 Channel (T1041)"],
    "Ransomware Attack": ["Exploit Public-Facing Application (T1190)", "Windows Management Instrumentation (T1047)", "Create Account (T1136)", "Process Injection (T1055)", "Data Encrypted for Impact (T1486)"],
    "Malware Infection": ["Supply Chain Compromise (T1195)", "Command and Scripting Interpreter (T1059)", "Registry Run Keys / Startup Folder (T1060)", "Obfuscated Files or Information (T1027)", "Remote Services (T1021)", "Data Destruction (T1485)"],
    "Insider Threat": ["Valid Accounts (T1078)", "Account Manipulation (T1098)", "Exploitation for Privilege Escalation (T1068)", "Data Staged (T1074)", "Scheduled Transfer (T1029)", "Account Access Removal (T1531)"],
}

# Helper function to load threat groups from a JSON file
def load_threat_groups(json_file_path):
    try:
        with open(json_file_path, 'r') as file:
            data = json.load(file)
            if not isinstance(data, list):
                raise ValueError("Invalid format: Expected a list of dictionaries.")
            for item in data:
                if not isinstance(item, dict) or 'group' not in item:
                    raise ValueError("Invalid format: Each item should be a dictionary with a 'group' key.")
            return sorted(item['group'] for item in data)
    except FileNotFoundError:
        print(f"Error: The file '{json_file_path}' was not found.")
        return []
    except json.JSONDecodeError:
        print(f"Error: The file '{json_file_path}' is not valid JSON.")
        return []
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        return []

# # Helper function to load MITRE ATT&CK data
# def load_attack_data(attack_json_file):
#     try:
#         with open(attack_json_file, 'r') as file:
#             data = json.load(file)
#             return data
#     except FileNotFoundError:
#         print(f"Error: The file '{attack_json_file}' was not found.")
#         return None
#     except json.JSONDecodeError:
#         print(f"Error: The file '{attack_json_file}' is not valid JSON.")
#         return None
#     except Exception as e:
#         print(f"An unexpected error occurred: {str(e)}")
#         return None

# Function to load techniques from MITRE ATT&CK data
def load_techniques(attack_data):
    try:
        techniques = attack_data.get_techniques()
        techniques_list = []
        for technique in techniques:
            for reference in technique.external_references:
                if "external_id" in reference:
                    techniques_list.append({
                        'id': technique.id,
                        'Technique Name': technique.name,
                        'External ID': reference['external_id'],
                        'Display Name': f"{technique.name} ({reference['external_id']})"
                    })
        return techniques_list
    except Exception as e:
        print(f"Error in load_techniques: {e}")
        return []  # Return an empty list instead of an empty DataFrame



# Function to get user selections from the command line
def get_user_selections(threat_groups_file, attack_data):
    # List of industry choices
    industries = sorted([
        'Aerospace / Defense', 'Agriculture / Food Services', 
        'Automotive', 'Construction', 'Education', 
        'Energy / Utilities', 'Finance / Banking', 
        'Government / Public Sector', 'Healthcare', 
        'Hospitality / Tourism', 'Insurance', 
        'Legal Services', 'Manufacturing', 
        'Media / Entertainment', 'Non-profit', 
        'Real Estate', 'Retail / E-commerce', 
        'Technology / IT', 'Telecommunication', 
        'Transportation / Logistics'
    ])

    # List of company size choices
    company_sizes = [
        '1-10 employees', '11-50 employees', '51-200 employees', 
        '201-500 employees', '501-1000 employees', '1001-5000 employees', 
        '5001-10,000 employees', '10,001+ employees'
    ]

    # Load threat groups from the JSON file
    threat_groups = load_threat_groups(threat_groups_file)

    def prompt_selection(options, prompt_message):
        print(prompt_message)
        for idx, option in enumerate(options, start=1):
            print(f"{idx}. {option}")

        while True:
            try:
                choice = int(input("Enter the number corresponding to your choice: "))
                if 1 <= choice <= len(options):
                    selected_option = options[choice - 1]
                    break
                else:
                    print(f"Invalid choice. Please enter a number between 1 and {len(options)}.")
            except ValueError:
                print("Invalid input. Please enter a number.")
        
        return selected_option

    # Get the user's industry selection
    industry_prompt = "Select your company's industry from the list below:"
    selected_industry = prompt_selection(industries, industry_prompt)

    # Get the user's company size selection
    size_prompt = "Select your company's size from the list below:"
    selected_size = prompt_selection(company_sizes, size_prompt)

    # Get the user's threat group selection
    threat_group_prompt = "Please select a threat group with associated Enterprise ATT&CK techniques from the list below:"
    selected_threat_group = prompt_selection(threat_groups, threat_group_prompt)

    # Load techniques from the attack data
    techniques_list = load_techniques(attack_data)

    techniques_options = [tech['Display Name'] for tech in techniques_list]

    # Get the user's choice of template or manual selection
    template_prompt = "Select an incident response template or choose 'Manual Selection' to select techniques yourself:"
    template_options = ["Manual Selection"] + list(incident_response_templates.keys())
    selected_template = prompt_selection(template_options, template_prompt)

    # If a template is selected, use the associated techniques
    if selected_template != "Manual Selection":
        selected_techniques = incident_response_templates[selected_template]
    else:
        # Get the user's ATT&CK techniques selection
        print("Select ATT&CK techniques for the scenario (you can choose multiple, separated by commas):")
        for idx, option in enumerate(techniques_options, start=1):
            print(f"{idx}. {option}")

        while True:
            try:
                choices = input("Enter the numbers corresponding to your choices, separated by commas: ")
                selected_indices = [int(x.strip()) for x in choices.split(',')]
                if all(1 <= idx <= len(techniques_options) for idx in selected_indices):
                    selected_techniques = [techniques_options[idx - 1] for idx in selected_indices]
                    break
                else:
                    print(f"Invalid choices. Please enter numbers between 1 and {len(techniques_options)}.")
            except ValueError:
                print("Invalid input. Please enter numbers separated by commas.")

    # Store the selections in a dictionary
    selections = {
        "industry": selected_industry,
        "company_size": selected_size,
        "threat_group": selected_threat_group,
        "techniques": selected_techniques,
        "template": selected_template if selected_template != "Manual Selection" else None
    }

    # Display the selected industry, company size, threat group, and techniques
    print(f'Selected Industry: {selected_industry}')
    print(f'Selected Company Size: {selected_size}')
    print(f'Selected Threat Group: {selected_threat_group}')
    if selections['template']:
        print(f'Selected Template: {selections["template"]}')
    print(f'Selected ATT&CK Techniques: {", ".join(selected_techniques)}')

    return selections

# Function to generate a scenario using Google Generative AI
def generate_scenario_google(selections):
    try:
        # Initialize the Google Generative AI model
        llm = GoogleGenerativeAI(
            model="gemini-1.5-pro-latest",
            temperature=0,
            safety_settings={
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )

        # Construct the prompt using selections
        industry = selections["industry"]
        company_size = selections["company_size"]
        threat_group = selections["threat_group"]
        techniques = selections["techniques"]
        template_info = f"This is a '{selections['template']}' scenario." if selections["template"] else ""

        selected_techniques_string = '\n'.join(techniques)
        
        # System Message Template
        system_template = "You are a cybersecurity expert. Your task is to produce a comprehensive incident response testing scenario based on the information provided."
        system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)

        # Human Message Template
        human_template = f"""
**Background information:**
The company operates in the '{industry}' industry and is of size '{company_size}'.

**Threat actor information:**
Threat actor group '{threat_group}' is planning to target the company using their known tactics.

{template_info}

**ATT&CK Techniques:**
{selected_techniques_string}

**Your task:**
Create an incident response testing scenario based on the information provided. The goal of the scenario is to test the company's incident response capabilities against the identified threat actor group.

Your response should be well-structured and formatted using Markdown. Write in British English.
"""
        human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

        # Construct the ChatPromptTemplate
        chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])

        # Format the prompt
        messages = chat_prompt.format_prompt(
            selected_group_alias=threat_group,
            industry=industry,
            company_size=company_size,
            selected_techniques_string=selected_techniques_string,
            template_info=template_info
        ).to_messages()

        # Generate the scenario
        print("Generating scenario, please wait...")
        response = llm.invoke(messages)
        scenario_text = response

        # Display the generated scenario
        print("\nScenario generated successfully:")
        print(scenario_text)
        
        return scenario_text

    except Exception as e:
        print(f"An error occurred while generating the scenario: {str(e)}")
        return None

# Main script execution
if __name__ == "__main__":
    # Specify the paths to the JSON files
    threat_groups_file = 'groups.json'
    attack_json_file = 'enterprise-attack.json'

    # Parse command line arguments for API key and model name
    parser = argparse.ArgumentParser(description="Generate a custom scenario using Google Generative AI")
    args = parser.parse_args()

    # Load the attack data
    attack_data = MitreAttackData("./enterprise-attack.json")
    if attack_data is None:
        print("Failed to load attack data. Exiting...")
        exit(1)
    # Get user selections
    selections = get_user_selections(threat_groups_file, attack_data)

    # Generate the scenario using Google Generative AI
    generate_scenario_google(selections)
