## Assessing the Usability of General-Purpose AI Tools for Specialized Task: Using Google Gemini to Assess and Categorize User-Inputted Text Based on Verifiability in Closed-Source Grounding

**Last Modified:** September 18th, 2026

### Overview
---
The goal of this capstone is to explore how general-purpose AI models (specifically LLMs such as ChatGPT, Copilot, Gemini, and Claude) can be adapted for specific tasks and assess their performance in comparison to tools that are built specifically for an equivalent task. General-purpose AI models are largely accessible to the general public and can be adapted to specific tasks through techniques such as system instructions, output constraints, tool integration, and supplemental external data. 

This program is a case example that uses Google Gemini in a simple "content verification" tool where the user, after being prompted by the console output, inputs text into the console for analysis. The program processes this user input and then checks it against the contents of manually approved sources listed in an external JSON file, then returns a verdict based on if the inputted text can be verified through those sources with an explanation citing the relevant sources if appliable. This program is not to assess the objective truth of a user-inputted statement, but the verifiability of the statement using only approved sources. If an objectively true statement is inputted into the console that is not relevant to any of the external sources, then that statement will be returned as being unverifiable. 

### Program Development
---
**System Instructions:**
This program was developed using Python and integrates Google Gemini API to assess and evaluate user-inputted text, which was adapted for this task through clear system instructions describing its role and requirements it must follow.

**Closed-Source Searching:**
To reduce the potential of AI hallucinations, Gemini was restricted to only using content from manually selected sources listed in an external JSON file. 

**Offline Mode:**
In the event the API is disconnected, the statement is checked by indexing through cached web content to search for key words from the user inputted text. 

### Output Categories 
---

### Example Outputs
---

### Limitations and Issues
---

### Conclusions
---
This project demonstrates how general-purpose AI tools can be adapted for specialized tasks through closed data access and clear system instructions, which create a controlled environment for the LLM to operate under while still being semantically flexible. 

The offline mode helps demonstrates the difference between traditional information retrieval and LLM-assisted retrieval.

Since this programs operates as a tool that determines the verifiability of statements based on a controlled pool of sources, it can be useful in research and academic writing. 

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
