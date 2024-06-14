from threat_test_operator import atomic_operator
from langchain_google_genai import GoogleGenerativeAI, HarmCategory, HarmBlockThreshold
from langchain.prompts.chat import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate

llm = GoogleGenerativeAI(model="gemini-1.5-pro-latest", temperature=0, safety_settings={ HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,})  

def generate_summarised_context():
    try:
        # System Message Template
        system_template = "You are a cybersecurity expert. Your task is the response you are battle testing the system with. You a get response."
        system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)
        response = atomic_operator()
        # Human Message Template
        human_template = f"""
        Response from atomics operator after running. Also list all the commands one by one that was used to run in the machine
        {response}
        """
        human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

        # Construct the ChatPromptTemplate
        chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])

        # Format the prompt
        messages = chat_prompt.format_prompt().to_messages()

        # Generate the scenario
        print("Summarizing....")
        scenario_text = llm.invoke(messages)

        # Display the generated scenario
        print("\nScenario content successfully:")
        
        return scenario_text

    except Exception as e:
        print(f"An error occurred while generating the scenario: {str(e)}")
        return None


generate_summarised_context()