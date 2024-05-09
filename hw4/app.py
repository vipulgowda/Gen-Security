from langchain_google_genai import GoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers import LanguageParser
from langchain_text_splitters import Language
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

llm = GoogleGenerativeAI(model="gemini-pro",temperature=0)

def summarize(path):
    loader = GenericLoader.from_filesystem(
            path,
            glob="*",
            suffixes=[".py"],
            show_progress=True,
            parser=LanguageParser(),
    )
    docs = loader.load()
    print(docs)
    prompt1 = PromptTemplate.from_template(
        """
        Task: As secureGPT, a python cybersecurity analyst, yout task is to review open source python packages and libraries for potentially malicious behavior or sabotage. This code review is specifically for python libraries that are part of larger projects and published on public package managers such as Pypi. Review this code for supply chain security attacks, malicious behavior, and other security risks. Keep in mind the following: Analyse code for python security issues such as code injection, data leakage, insecure use of environment variables, unsafe SQL, and random number generation. Do NOT alert on minified code that is result of standard minification process.Third party library usage is not by itself suspicious behavior. Here are some guidelines that you follow. 
        
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

    chain = (
      {"text": RunnablePassthrough()} 
      | prompt1
      | llm
      | StrOutputParser()
    )
    output = "\n".join([d.page_content for d in docs])
    result = chain.invoke(output)
    return(result)

print("Welcome to my code summarizer.  Give me a path to a Package program and I'll summarize it.")

while True:
    try:
        line = input("llm>> ")
        if line:
            result = summarize(line)
            print(result)
        else:
            break
    except Exception as e:
        print(e)
        break