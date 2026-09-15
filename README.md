## Leveraging General-Purpose AI Tools for Use in Specialized Tasks // Verifying User-Inputted Text 

**Last Modified:** September 15th, 2026

### Overview
---
The goal of this Capstone is to explore how general-purpose AI models (specifically LLMs such as ChatGPT, Copilot, Gemini, and Claude) can be made useful in specific tasks and assess their performance in comparison to specialized AI-based tools that are trained more linearly and specifically in certain tasks. These models are largely accessible to general public and can easily be adapted for special uses through effective system instructions and supplemental external data. In addition, the language-processing capabilities of these AI models can also give them some flexibility in task-handling which can help handle unexpected inputs, producing more comprehensive results, and improve overall usability. 

This specific case example is a program that uses Google Gemini as a simple "content verification" tool in which the user, after being prompted by the program, types or pastes text into the console for analysis. The program processes the user input, initiates a web search, and returns a verdict on the validity of the inputted text (whether or not it is true) with an in-depth explanation for its verdict with sources. 

### Program Design and API Methodology
---
The API was given the following instructions in its code:
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
### Example Outputs
---
User Input:
```
Cats are colorblind.
```
Program Output:
```
============================================================
VERIFICATION RESULT
============================================================
**VERDICT:** PARTIALLY TRUE / MISLEADING

### **Explanation**
The claim that "cats are colorblind" is misleading because it depends on how "colorblind" is defined.

Cats are not completely colorblind; they do not see the world strictly in black, white, and gray (a rare condition known as monochromacy). However, their ability to perceive colors is significantly more limited than that of a average human.

* **Dichromatic Vision:** Humans typically have trichromatic vision, meaning they possess three types of color-detecting cone cells in their eyes (sensitive to red, green, and blue). Cats are dichromats, possessing only two types of functional cones optimized primarily for blue-violet and yellow-green light wavelengths.
* **Red-Green Blindness Analogy:** A cat’s vision is roughly equivalent to a human with red-green color blindness. Cats struggle to perceive colors like red, orange, and pink, which often appear to them as muted shades of green, blue, or gray.
* **Saturation and Clarity:** Colors appear much less vibrant and saturated to cats. Their eyes evolved to prioritize low-light vision and motion detection (which relies on rod cells) rather than rich color perception (which relies on cone cells).

In summary, while cats cannot see the full spectrum of colors that humans do, they are still capable of seeing shades of blue, yellow, and green.

---

### **Sources**
1. **VCA Animal Hospitals:** *Do Cats See Color?*
   (https://vcahospitals.com/know-your-pet/do-cats-see-color)
2. **Smithsonian Magazine:** *See the World Through the Eyes of a Cat*
   (https://www.smithsonianmag.com/science-nature/see-the-world-through-the-eyes-of-a-cat-67820835/)
3. **Encyclopædia Britannica:** *Can Cats See Color?*
   (https://www.britannica.com/story/can-cats-see-color)
```
User Input:
```
Dogs are naturally purple.
```
Program Output:
```
============================================================
VERIFICATION RESULT
============================================================
**VERDICT:** FALSE / DEBUNKED

### **EXPLANATION**
Dogs are not naturally purple. The coat colors of domestic dogs are determined entirely by two base pigments: **eumelanin** (which produces black, brown, gray, or dark brown tones) and **pheomelanin** (which produces red, yellow, orange, gold, or cream tones). 

Genetic variations, dilutions, and combinations of these two pigments account for all naturally occurring coat patterns and colors in dogs. There is no biological mechanism or pigment present in canines that generates purple fur. Any dog with purple fur has been artificially dyed.

*Note: This statement appears to be an absurd claim or potential AI hallucination.*

### **SOURCES**
1. **UC Davis Veterinary Genetics Laboratory** – "Dog Coat Color Genetics"
   *https://vgl.ucdavis.edu/services/dog-coat-color-genetics*
2. **Wikipedia** – "Dog coat"
   *https://en.wikipedia.org/wiki/Dog_coat*
```
User Input:
```
Los pulpos tienen tres corazones y su sangre es de color azul.
```
Program Output: 
```
============================================================
VERIFICATION RESULT
============================================================
**VERDICTO:** VERIFICADO / VERDADERO

---

### **Explicación:**
La afirmación es totalmente correcta. Los pulpos poseen una anatomía y un sistema circulatorio con las siguientes características:        

1. **Tres corazones:**
   * Dos de los corazones (corazones branquiales) se encargan exclusivamente de bombear la sangre desoxigenada a través de las branquias para que recoja oxígeno.
   * El tercer corazón (corazón sistémico) circula la sangre oxigenada por el resto de los órganos y tejidos del cuerpo.

2. **Sangre de color azul:**
   * La sangre de los pulpos es azul debido a la presencia de la **hemocianina**, una proteína rica en cobre que se une al oxígeno para transportarlo a través del organismo. Esto contrasta con la sangre humana y de la mayoría de los vertebrados, que es roja porque utiliza **hemoglobina**, una proteína rica en hierro. La hemocianina es especialmente eficiente para transportar oxígeno en ambientes marinos fríos y con bajas concentraciones de oxígeno.

---

### **Fuentes:**
1. **Natural History Museum (Londres):** [*Why do octopuses have three hearts and blue blood?*](https://www.nhm.ac.uk) — Detalla la estructura anatómica del sistema circulatorio de los cefalópodos y la función de la hemocianina.
2. **Smithsonian Ocean:** [*Octopus and Squid - Ocean Portal*](https://ocean.si.edu) — Explica la fisiología del pulpo, incluyendo sus tres corazones y las propiedades químicas de su sangre azul.
3. **National Geographic:** [*Octopus Profile and Physiology*](https://www.nationalgeographic.com) — Documenta las adaptaciones biológicas de los cefalópodos.
```
### Conclusions
---
This program successfully utilizes Gemini in making a simple fact checker by giving it a list of rules and requirements it must follow. One important thing to note is that this program has case-handling in place where the program will still successfully run in the event that there are no tokens on the API key. Another thing to note is that this program is also able to handle non-English text and will automatically return its verdict in language it detects in the user input, which makes it a flexible option. 

### User Guide
---
1. Install GitHub files. 
2. Create and activate a Python environment for the program files.
3. Install the necessary packages from the requirements.txt file.
```bash
pip install -r requirements.txt --break-system-packages
```
5. Obtain a Google Gemini API key and insert it into the program.
