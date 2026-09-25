## Using LLMs to Assess and Categorize User-Inputted Text Based on Verifiability in Closed-Source Grounding

**Last Modified:** September 25th, 2026

---

### Overview

The goal of this capstone is to explore how general-purpose AI models (specifically LLMs) can be adapted for specific tasks and assess their performance in comparison to tools that are built specifically for an equivalent task. General-purpose AI models are largely accessible to the general public and can be adapted to specific tasks through techniques such as system instructions, output constraints, tool integration, and supplemental external data.

This program uses the **ARC VT LLM API** as a simple **content verification** and **document-grounded Q&A** tool. After loading one or more documents or web pages, the user can either:

- **Ask questions** about the content of those documents (Q&A mode), or
- **Submit statements** for the LLM to evaluate against the loaded documents (Content Verification mode). This does not assess the *objective truth* of a statement, only its **verifiability** relative to the approved sources. If an objectively true statement is submitted that is not addressed by any loaded document, it will be returned as **UNVERIFIABLE**.

---

### Features

**Document Loading**

This program supports content loaded from: 
- **Local Files** — TXT, DOCX, MD, HTML, and other plain-text formats.
- **Web URLs** — Web pages or remotely hosted PDFs.

To load content onto the program, the user simply needs to enter `add {url or path/to/text_file}` into the console while the program is running. The content is extracted and stored into a JSON located in the program folder. 

**Document Storage**

All loaded document and URL content is extracted and stored locally. This content is **not forgotten** after the program is stopped, allowing those same files to be used for future sessions without reupload. 

**Q&A**

The default mode. The user can ask any question and the LLM will respond using only the content of the currently active documents, citing the source document by name.

**Content Verification**

Activated with the `verifymode` command (or as a one-shot with `verify <statement>`). In this mode, each user input is treated as a statement to evaluate. The LLM returns a structured verdict:

```
VERDICT:     VERIFIED | CONTRADICTED | UNVERIFIABLE
CONFIDENCE:  HIGH | MEDIUM | LOW
SOURCE:      <document name(s) used>
EVIDENCE:    <exact quote or paraphrase from the document>
EXPLANATION: <one or two sentences explaining the verdict>
```

Each statement is evaluated independently — no conversation history is maintained between verifications, ensuring verdicts are not influenced by prior queries.

---

### Output Categories

| Verdict | Meaning |
|---|---|
| **VERIFIED** | The loaded document(s) explicitly support the statement. |
| **CONTRADICTED** | The loaded document(s) explicitly contradict the statement. |
| **UNVERIFIABLE** | The loaded document(s) do not contain enough information to evaluate the statement. |

Each verdict also includes a **CONFIDENCE** level (HIGH, MEDIUM, or LOW) reflecting how directly the document evidence maps to the statement.

---

### Example Outputs

#### Q&A

**Example 1 - From Uploaded PDF**
```
You: who is the head footbal coach at virginia tech?

  [Thinking...]
--------------------------------------------------------------
 Assistant (3.1s):

James Franklin is the head football coach at Virginia Tech. 【virginia_tech.pdf】
--------------------------------------------------------------
```
#### Content Verification

**Example 1 — VERIFIED**
```
 [VERIFY] You: Cats were first domesticated in the Near East.

  Verification Result (4.2s):

VERDICT:     VERIFIED
CONFIDENCE:  HIGH
SOURCE:      Cat (Wikipedia)
EVIDENCE:    "the earliest known indication for the taming of an African wildcat
             was excavated close by a human Neolithic grave in Shillourokambos,
             southern Cyprus, dating to about 7500-7200 BCE"
EXPLANATION: The document explicitly states that cat domestication originated in
             the Near East / West Asian mainland, supporting the statement.
```

**Example 2 — CONTRADICTED**
```
 [VERIFY] You: Cats are pack animals that hunt in groups.

  Verification Result (3.8s):

VERDICT:     CONTRADICTED
CONFIDENCE:  HIGH
SOURCE:      Cat (Wikipedia)
EVIDENCE:    "cats do not have a social survival strategy or herd behavior,
             they always hunt alone"
EXPLANATION: The document directly contradicts this statement, describing cats
             as solitary hunters without pack or herd behavior.
```

**Example 3 — UNVERIFIABLE**
```
 [VERIFY] You: Cats were kept as pets in ancient Rome.

  Verification Result (4.1s):

VERDICT:     UNVERIFIABLE
CONFIDENCE:  LOW
SOURCE:      Cat (Wikipedia)
EVIDENCE:    N/A
EXPLANATION: While the document mentions cats were introduced to Corsica and
             Sardinia during the Roman Empire, it does not specifically address
             whether they were kept as pets in Rome.
```

---

### Program Development

**Overview** 

This program was developed in Python and integrates the ARC VT LLM API (an OpenAI-compatible endpoint) to assess and evaluate user-inputted text against locally extracted PDF and URL content.

**System Instructions**

The LLM is adapted for this task through explicit system instructions describing its role, the strict rules it must follow, and the exact output format it must produce.

```
You are a document-grounding assistant.
You MUST answer ONLY using information explicitly stated in the documents below.
STRICT RULES – you must follow ALL of these without exception:
  1. Do NOT use any knowledge from your training data or the internet.
  2. Do NOT infer, guess, or extrapolate beyond what the documents state.
  3. If the documents do not contain the answer, respond ONLY with:
     'The provided documents do not contain information about this topic.'
  4. Always cite which document (by name) your answer comes from.
  5. Partial answers are allowed only if explicitly supported by the documents.

=== PROVIDED DOCUMENTS ===
[DOCUMENTS]
=== END OF DOCUMENTS ===
Remember: your ONLY source of truth is the text above.
Do not supplement with outside knowledge under any circumstances.
```

```
You are a strict content verification assistant.
The user will provide a statement. Your ONLY job is to determine whether
that statement is supported, contradicted, or not addressed by the documents below.

RULES:
  1. Base your verdict SOLELY on text found in the provided documents.
  2. Do NOT use any external knowledge or training data.
  3. You MUST respond using EXACTLY this format – no exceptions:

     VERDICT: <VERIFIED | CONTRADICTED | UNVERIFIABLE>
     CONFIDENCE: <HIGH | MEDIUM | LOW>
     SOURCE: <document name(s) used>
     EVIDENCE: <exact quote or close paraphrase from the document that supports the verdict>
     EXPLANATION: <one or two sentences explaining the verdict>

  Verdict definitions:
    VERIFIED      – The document(s) explicitly support the statement.
    CONTRADICTED  – The document(s) explicitly contradict the statement.
    UNVERIFIABLE  – The document(s) do not contain enough information to judge.

=== PROVIDED DOCUMENTS ===
[DOCUMENTS]
=== END OF DOCUMENTS ===
Now await the user's statement and apply the format above precisely.
```

**Strict Closed-Source Grounding**

The LLM is restricted by system instruction to answer **only** using information explicitly stated in the loaded documents. It may not draw on its training data, general knowledge, or any external sources. If the documents do not contain information relevant to the user-input, the LLM is required to say so rather than speculate.

---

### Conclusions

This project demonstrates how general-purpose AI tools can be adapted for specialized tasks through closed data access and clear system instructions, which create a controlled environment for the LLM to operate in while remaining semantically flexible.

Since this program operates as a tool that determines the *verifiability* of statements based on a controlled pool of sources rather than objective truth, it can be useful in research, academic writing, and fact-checking workflows where the authoritative source is explicitly defined.

---

**Available commands:**

| Command | Description |
|---|---|
| `add <path or url>` | Load a local file or web URL into the cache and activate it |
| `list` | List all cached documents |
| `use <#>` | Toggle a cached document in/out of the active context |
| `info` | Show which documents are currently active |
| `verifymode` | Toggle Content Verification Mode on/off |
| `verify <statement>` | One-shot verification of a single statement |
| `clear` | Clear active documents and conversation history (cache kept) |
| `purge` | Delete all cached documents and session state from disk |
| `help` | Show the help menu |
| `quit` | Exit the program |

---

### Additional Resources

- [ARC VT Research Computing](https://arc.vt.edu)
