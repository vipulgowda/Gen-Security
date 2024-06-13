import os
import json
import argparse
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts.chat import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain_google_genai import GoogleGenerativeAI, HarmCategory, HarmBlockThreshold


llm = GoogleGenerativeAI(model="gemini-1.5-pro-latest", temperature=0, safety_settings={ HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,})  

def load_threat_groups():
  with open("./groups.json", 'r') as file:
    data = json.load(file)
    threat_groups = sorted(item['group'] for item in data)
            
    # Ensure the threat groups are a list
    if not isinstance(threat_groups, list):
      raise ValueError("Invalid format: 'groups' should be a list.")
  
  print(threat_groups)
  
  return threat_groups

# Function to get user selections from the command line
def get_user_selections(threat_groups_file):
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
    threat_groups = load_threat_groups()

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

    # Store the selections in a dictionary
    selections = {
        "industry": selected_industry,
        "company_size": selected_size,
        "threat_group": selected_threat_group
    }

    # Display the selected industry, company size, and threat group
    print(f'Selected Industry: {selected_industry}')
    print(f'Selected Company Size: {selected_size}')
    print(f'Selected Threat Group: {selected_threat_group}')

    return selections

# Function to generate a scenario using Google Generative AI
def generate_scenario_google(selections):
    try:
        # Construct the prompt using selections
        industry = selections["industry"]
        company_size = selections["company_size"]
        threat_group = selections["threat_group"]
        
        # System Message Template
        system_template = "You are a cybersecurity expert. Your task is to produce a comprehensive incident response testing scenario based on the information provided."
        system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)

        # Human Message Template
        human_template = f"""
**Background information:**
The company operates in the '{industry}' industry and is of size '{company_size}'.

**Threat actor information:**
Threat actor group '{threat_group}' is planning to target the company using their known tactics.

**Your task:**
Create an incident response testing scenario based on the information provided. The goal of the scenario is to test the company's incident response capabilities against the identified threat actor group.

Your response should be well-structured and formatted using Markdown. Write in British English.
"""
        human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

        # Construct the ChatPromptTemplate
        chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])

        # Format the prompt
        messages = chat_prompt.format_prompt(selected_group_alias=threat_group, industry=industry, company_size=company_size).to_messages()

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
    # Specify the path to the JSON file containing the threat groups
    threat_groups_file = 'groups.json'

    # Parse command line arguments for API key and model name
    parser = argparse.ArgumentParser(description="Generate a threat group scenario using Google Generative AI.")

    args = parser.parse_args()

    # Get user selections
    user_selections = get_user_selections(threat_groups_file)

    # Generate the scenario
    generate_scenario_google(user_selections)
