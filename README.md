### Leveraging General-Purpose AI Tools for Use in Specialized Tasks // Verifying User-Inputted Text 

#### Overview
The goal of this Capstone is to explore how general-purpose AI tools can be utilized in specific tasks, compared to specialized AI-tools that are trained specifically in those tasks. This specific program is powered by Google Gemini API and acts as a "content verification" tool in which the user, after being prompted by the program, types or pastes text into the console for analysis. The program processes the user input, initiates a web search, returns a verdict on the validity of the inputted text (whether or not is true), and gives an explanation to back up its verdict with online sources. 

This program was made in Python with the assistance of Google Gemini's chatbot and coding agent. also uses Google Gemini API to . I tasked Gemini with analyzing the text inputted by the user and performing a deep-web search to verify its correctness, and reporting those results to the user. 

#### Program Design and API Methodology
The API was given the following instructions in its code:
```python
system_instruction = """
YOUR ROLE:
You are an objective, professional fact-checking analyst.
YOUR TASKS:
1. Analyze the contents of the text provided by the user. This user-inputted text will be a fact or statement of some sort that needs verification from you. 
2. Using web searching, determine if the information is:
   - VERIFIED / TRUE
   - FALSE / DEBUNKED
   - PARTIALLY TRUE / MISLEADING
   - UNVERIFIABLE
3. Provide a concise explanation detailing why, highlighting key facts.
4. Reference the web sources where you recieved your conclusion and explanation from.
ADDITIONAL REQUIREMENTS:
1. Pay attention to the context of the websites you come accross during your web searching. Priortize using sources that known to be reliable such as peer-reviewed scholarly journals, government websites, educational websites, and reputable news outlets before using resorting to sources.
For quick facts, Wikipedia is acceptable. Do NOT use any social media websites as a source. 
2. Pay close to attention to any potential AI hallucinations that may be present in the statement. If you think a statement might be an AI hallucination, say so.
3. Do not make predictions relating to the infomration in the user-inputted statement, only make statements that are explicity stated in your sources. 
4. Limit the number of websources you pull information from when retunring your response to the user. Do not use more than three sources. 
"""
```
#### Example Outputs
User Input:
Program Output:

### Conclusions

### User Guide


