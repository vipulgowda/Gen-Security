from langchain_google_genai import GoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers import LanguageParser
from langchain.agents import AgentType
from langchain.agents import initialize_agent
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain.agents import tool
import requests
import tarfile
import os
import re
from bs4 import BeautifulSoup
import subprocess


#llm = GoogleGenerativeAI(model="gemini-1.5-pro-latest",temperature=0)
llm = GoogleGenerativeAI(model="gemini-pro",temperature=0)

@tool
def download_and_extract(url, relative_path):
  """
  This function takes two arguments from guarddog_analysis output, it has url and relative_path and url is used to download and extract from web and relative_path is sent to check_malware_analysis function.
  Run the program step by step.
  Args:
    url: The tuple that contains download url and the fle where the malicious link is present.
    folder: The folder where the extracted library will be stored (default: "packages").
  """

  # Get the filename from the URL
  filename = url.split("/")[-1]
  folder = "packages"
  # Create the packages folder if it doesn't exist
  os.makedirs(folder, exist_ok=True)

  # Download the library file
  try:
    response = requests.get(url, stream=True)
    response.raise_for_status()  # Raise an exception for unsuccessful downloads
  except requests.exceptions.RequestException as e:
    print(f"Error downloading library: {e}")
    return

  # Save the downloaded file
  filepath = os.path.join(folder, filename)
  print(filepath)
  with open(filepath, "wb") as f:
    for chunk in response.iter_content(1024):
      f.write(chunk)

  # Extract the downloaded file (assuming it's a tar.gz archive)
  try:
    with tarfile.open(filepath, 'r:gz') as tar_ref:
      tar_ref.extractall(folder)
    print(f"Library downloaded and extracted to: {folder}/{filename.replace('.tar.gz', '')}")
  except tarfile.ReadError as e:
    print(f"Error extracting library: {e}")
    os.remove(filepath)  # Remove the downloaded file if extraction fails

@tool
def guarddog_analysis(package: str):
  """
  This function take package name and run the command sequentially. After fetch the result, pass the return output as tuple to download_and_extract function.

  Args:
    package: The package name that is checked for any malicious content
  """
  try:
    # Use subprocess.run for capturing output and error messages (optional
    strCmd = "guarddog pypi scan " + package
    result = subprocess.run(strCmd.split(), check=True, capture_output=True, text=True)  # Exit script on non-zero exit code
    pattern = r"at (.*?):"
    match = re.search(pattern, result.stdout)
    if match:
      # Extract the captured group (text between 'at' and ':')
      extracted_path = match.group(1)
      extracted_text = extracted_path.split("/")
      url = f'https://pypi.org/project/{package}/#files'
      try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for non-2xx status codes
      except requests.exceptions.RequestException as error:
        return f"Error fetching webpage: {error}"
      # Parse the HTML content
      soup = BeautifulSoup(response.content, 'html.parser')

      # Find the desired link (replace with appropriate selector)
      desired_link = soup.find('a', string=lambda text: text and extracted_text[0] in text, href=True)
      if desired_link:
      # Extract the download URL from the href attribute
        download_url = desired_link['href']
        relative_path = extracted_path
        return {
            "url" : download_url, 
            "relative_path": relative_path
        }
      else:
        return "Couldn't find the desired download link "    
    else:
      return "This is not a malicious package"
  except subprocess.CalledProcessError as e:
    return f"Error running command: {e}"


@tool
def check_malware_analysis(path):
    """
    Check for any vulnerability in the code being passed
    Args:
        path: path of the code to be reviewed to check for any vulnerability.
    """
    path = os.getcwd() + "/packages/" + path

    loader = GenericLoader.from_filesystem(
            path,
            glob="*",
            suffixes=[".py"],
            show_progress=True,
            parser=LanguageParser(),
    )
    docs = loader.load()

    prompt = PromptTemplate.from_template(
        """
        Task: As secureGPT, a python cybersecurity analyst, your task is to review code for potentially malicious behavior or sabotage. This code review is specifically for python libraries that are part of larger projects and published on public package managers such as Pypi. Review this code for supply chain security attacks, malicious behavior, and other security risks. Keep in mind the following: Analyse code for python security issues such as code injection, data leakage, insecure use of environment variables, unsafe SQL, and random number generation. Do NOT alert on minified code that is result of standard minification process.Third party library usage is not by itself suspicious behavior. Here are some guidelines that you follow. 
        
        Guidelines: Spot anomalies: hard-coded credentials, backdoors, unusual behaviors, or malicious code. Watch out for malicious privacy violations, credential theft, and information leaks. Note observations about the code. Evaluate the provided file only. Indicate low confidence if more info is needed. Avoid false positives and unnecessary warnings. Keep signals and reports succinct and clear. Consider user intent and the threat model when reasoning about signals. Focus on suspicious parts of the code. 
        
        What is Malware? In the context of an python package, malware refers to any code intentionally included in the package that is designed to harm, disrupt, or perform unauthorized actions on the system where the package is installed. Example: Sending System Data Over the Network Connecting to suspicious domains, Damaging system files, Mining cryptocurrency without consent, Reverse shells, Data theft (clipboard, env vars, etc), Hidden backdoors. 
        
        Security risks to consider in the code are Hardcoded credentials, Security mistakes, SQL injection, DO NOT speculate about vulnerabilities outside this module. There might also be Obfuscated code like Uncommon language features, Unnecessary dynamic execution, Misleading variables, DO NOT report minified code as obfuscated. 
        
        Malware score: - 0: No malicious intent, 0 - 0.25: Low possibility of malicious intent, 0.25 - 0.5: Possibly malicious behavior, 0.5 - 0.75: Likely malicious behavior, e.g., tracking scripts, 0.75 - 1: High probability of malicious behavior; do not use. 
        
        Security Risk Score: 0 - 0.25: No significant threat; we can safely ignore, 0.25 - 0.5: Security warning, no immediate danger, 0.5 - 0.75: Security alert should be reviewed, 0.75 - 1: Extremely dangerous, package should not be used.
        
        Confidence Score: Rate your confidence in your conclusion about whether the code is obfuscated, whether it contains malware and the overall security risk on a scale from 0 to 1.
        
        Code review: Please consider both the content of the code as well as the structure and format when determining the risks.Your analysis should include the following steps:
        Identify sources: These are places where the code reads input or data.
        Identify sinks: These are places where untrusted data can lead to potential security vulnerabilities. Identify flows: These are source-to-sink paths.
        Identify anomalies: These are places where there is unusual code, hardcoded secrets, etc.
        Conclusion: Finally, form the conclusion of the code, provide a succinct explanation of your reasoning.
        
        JSON Response: **Only respond in this format:** ["purpose": "Purpose of this source code", "sources": "Places where code reads input or data", "sinks": "Places where untrusted data can lead to potential data leak or effect", "flows": "Source- to-sink paths", "anomalies": "Places where code does anything unusual", "analysis": "Step-by-step analysis of the entire code fragment.", "conclusion": "Conclusions and short summary of your findings", "confidence": 0-1, "obfuscated": 0-1, "malware": 0-1, "securityRisk": 0-1]
        ONLY RESPOND IN JSON. No non-JSON text responses. Work through this step-by-step to ensure accuracy in the evaluation process.
        
        {text}
        """)
    llm = GoogleGenerativeAI(model="gemini-1.5-pro-latest",temperature=0)
    chain = (
      {"text": RunnablePassthrough()} 
      | prompt
      | llm
      | StrOutputParser()
    )
    output = "\n".join([d.page_content for d in docs])
    result = chain.invoke(output)
    return(result)


tools = [guarddog_analysis, download_and_extract, check_malware_analysis]
print("This is malware analyser. Please input your package name and let the LLM analyse for any issues ")


agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=True,
)

while True:
    try:
        line = input("llm>> ")
        if line:
            result = agent.invoke({"input": line})
            #asyncio.run(my_async_function(line))
        else:
            break
    except Exception as e:
        print(e)
        break