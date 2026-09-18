## Assessing the Usability of General-Purpose AI Tools for Specialized Task: Using Google Gemini to Assess and Categorize User-Inputted Text Based on Verifiability

**Last Modified:** September 17th, 2026

### Overview
---
The goal of this capstone is to explore how general-purpose AI models (specifically LLMs such as ChatGPT, Copilot, Gemini, and Claude) can be adapted for specific tasks and assess their performance in comparison to tools that are trained specifically for an equivalent task. General-purpose AI models are largely accessible to the general public and can be adapted to specific tasks through techniques such as system instructions, output constraints, tool integration, and supplemental external data. 

This program is a case example that uses Google Gemini in a simple "content verification" tool in which the user, after being prompted by the console output, types or pastes text into the console for analysis. The program processes the user input, initiates a web search, and returns a verdict on if the inputted statement is categorized as being "TRUE", "FALSE", "PARTIALLY TRUE", or "UNVERIFIABLE" based on the available reliable evidence. The output will also include an explanation for the verdict reached with information from available online sources if applicable. 

### Program Development
---
This program was developed using Python and integrates Google Gemini API to assess and evaluate user-inputted text, which was adapted for this task through clear system instructions describing its role and requirements it must follow. 

```python
system_instruction =
"""
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

### Output Categories 
---
| Verdict | Definition |
|---|---|
| **VERIFIED / TRUE** | The inputted statement is true and can be debunked with reliable evidence. |
| **FALSE / DEBUNKED** | The inputted statement is false and can be debunked with reliable evidence. |
| **PARTIALLY TRUE / MISLEADING** | The inputted statement contains some factual element but omits important context, exaggerates the evidence, or has a combination of true and false elements. |
| **UNVERIFIABLE** | Invalid user inputs or there is insufficient reliable information to establish whether the inputted statement is true or false. |

### Example Outputs
---
**User Input**
```
Cats are colorblind.
```
**Program Output**

### Limitations and Issues
---

### Conclusions
---
This project demonstrates how general-purpose AI tools can be adapted for specialized tasks through clear system instructions that define the role, requirements, and constraints the AI is required to follow. 

As demonstrated in the program outputs, these tools are able to flexibly adapt to different user inputs which enhances its usability. But they are also prone to generating hallucinations. 

### User Guide
---
1. Install GitHub files. 
2. Create and activate a Python environment for the program files.
3. Install the necessary packages from the requirements.txt file.
```bash
pip install -r requirements.txt
```
5. Obtain a Google Gemini API key and insert it into the program.
### Additional Resources
