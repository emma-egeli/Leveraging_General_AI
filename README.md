### Leveraging General-Purpose AI Tools for Use in Specialized Tasks // Verifying User-Inputted Text 

#### Overview
The goal of this Capstone is to explore how general-purpose AI tools can be utilized in specific tasks, compared to specialized AI-tools that are trained specifically in those tasks. This specific program is powered by Google Gemini API and acts as a "content verification" tool in which the user, after being prompted by the program, types or pastes text into the console for analysis. The program processes the user input, initiates a web search, returns a verdict on the validity of the inputted text (whether or not is true), and gives an explanation to back up its verdict with online sources. 

This program was made in Python with the assistance of Google Gemini's chatbot and coding agent in Antigravity IDE.

#### Program Design and API Methodology
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
#### Example Outputs
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
### Conclusions

### User Guide


