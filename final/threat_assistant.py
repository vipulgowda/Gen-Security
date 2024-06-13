import os
import json
import argparse
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts.chat import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain_google_genai import GoogleGenerativeAI, HarmCategory, HarmBlockThreshold

# Helper function to load a scenario from a JSON file
def load_scenario(json_file_path):
    try:
        with open(json_file_path, 'r') as file:
            data = json.load(file)
            if 'scenario' in data:
                return data['scenario']
            else:
                print("No scenario found in the file.")
                return None
    except FileNotFoundError:
        print(f"Error: The file '{json_file_path}' was not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: The file '{json_file_path}' is not valid JSON.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        return None

# Function to generate a response using Google Generative AI
def generate_response_google(input_scenario, user_input, chat_history):
    try:
        # Initialize the Google Generative AI model
        llm = GoogleGenerativeAI(
            model="gemini-1.5-pro-latest",
            temperature=0,
            safety_settings={
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )

        # Construct the prompt using the provided input scenario and chat history
        system_template = """
        You are an AI assistant that helps users update and ask questions about their incident response scenario.
        Only respond to questions or requests relating to the scenario, or incident response testing in general.
        """
        system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)

        human_template = f"""
        Here is the scenario that the user previously generated:\n\n{input_scenario}\n\nChat history:\n{chat_history}\n\nUser: {user_input}
        """
        human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

        # Construct the ChatPromptTemplate
        chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])

        # Format the prompt
        messages = chat_prompt.format_prompt(
            input_scenario=input_scenario,
            chat_history=chat_history,
            user_input=user_input
        ).to_messages()

        # Generate the response
        print("Generating response, please wait...")
        response = llm.invoke(messages)
        response_text = response

        # Display the generated response
        print("\nResponse generated successfully:")
        print(response_text)
        
        return response_text

    except Exception as e:
        print(f"An error occurred while generating the response: {str(e)}")
        return None

# Main script execution
if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Ask questions or update your incident response scenario using Google Generative AI")
    parser.add_argument('scenario_file', type=str, help="Path to the JSON file containing the previously generated scenario")
    parser.add_argument('user_input', type=str, help="User's question or update request for the scenario")

    args = parser.parse_args()

    # Load the previously generated scenario
    input_scenario = load_scenario(args.scenario_file)
    if input_scenario is None:
        print("Failed to load the scenario. Exiting...")
        exit(1)

    # Mocking a simple chat history
    chat_history = "This is a mock chat history for demonstration purposes."

    # Generate the response using Google Generative AI
    generate_response_google(input_scenario, args.user_input, chat_history)
