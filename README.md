## Assessing the Usability of General-Purpose AI Tools for Specialized Task: Using Google Gemini to Assess and Categorize User-Inputted Text Based on Verifiability in Closed-Source Grounding

**Last Modified:** September 18th, 2026

### Overview
---
The goal of this capstone is to explore how general-purpose AI models (specifically LLMs such as ChatGPT, Copilot, Gemini, and Claude) can be adapted for specific tasks and assess their performance in comparison to tools that are built specifically for an equivalent task. General-purpose AI models are largely accessible to the general public and can be adapted to specific tasks through techniques such as system instructions, output constraints, tool integration, and supplemental external data. 

This program is a case example that uses Google Gemini in a simple "content verification" tool where the user, after being prompted by the console output, types or pastes text into the console for analysis. The program processes this user input and then checks it against the contents of external source consisting of manually approved sources, then returns a verdict based on if the inputted text can be verified through those sources. The output will also include an explanation for the verdict reached, citing the sources used from the list. This program does not assess the objective truth of the user-inputted statement, but whether or not the given sources can verify it. 

### Program Development
---
**System Instructions**
This program was developed using Python and integrates Google Gemini API to assess and evaluate user-inputted text, which was adapted for this task through clear system instructions describing its role and requirements it must follow.

**Closed-Source Searching**
To reduce source and content hallucinations, the AI is restricted to only using manually selected sources in an external JSON file. 

**Offline Mode**
In the event the API is disconnected, the statement is checked by indexing through cached web content to search for key words from the user inputted text. 

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

### Limitations and Issues
---

### Conclusions
---
This project demonstrates how general-purpose AI tools can be adapted for specialized tasks through closed data access and clear system instructions that define the role, requirements, and constraints the AI is required to follow. 

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
