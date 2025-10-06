from collections import defaultdict
import re
import os
from typing import Dict, List
from urllib.parse import urlparse

from streamlit import html

def extract_component_from_url(url: str) -> str | None:
    try:
        path = urlparse(url).path  # e.g. /job/qe-acm/job/grc-e2e-test-execution/2532/
        parts = path.strip("/").split("/")
        # find all job/...，collect the job name from last job
        job_names = [parts[i+1] for i in range(len(parts)-1) if parts[i] == "job"]
        if job_names:
            # grc-e2e-test-execution
            last_job = job_names[-1]  
            # extract grc
            component = last_job.split("-")[0]  
            return component
        print (f"Component name is: {component}")
    except Exception as e:
        print("extract_component_from_url error:", e)
    return None
    

def load_rules(md_file: str) -> dict:
        component_guidelines = defaultdict(str)
        current_component = None
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                for line in f:
                 if line.startswith("## Component Name "):
                  current_component = line.replace("## Component Name", "").strip()
                 elif current_component:
                   component_guidelines[current_component] += line
        except Exception as e:
            raise ValueError(f"can not load the file: {str(e)}")

def load_code_file(file_path: str) -> str:
    normalized_path = file_path.strip('/\\').replace('\\', '/')
    full_path = os.path.join("code-context", normalized_path)
    
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"File not found: {normalized_path}")
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        raise Exception(f"Error reading file {full_path}: {e}")

def extract_code_path_from_prompt(prompt: str) -> str:
    patterns = [
        r'with\s+([A-Za-z0-9_\-\.\/]+\.(tsx?|jsx?))',
        r'using\s+([A-Za-z0-9_\-\.\/]+\.(tsx?|jsx?))',
        r'include\s+([A-Za-z0-9_\-\.\/]+\.(tsx?|jsx?))',
        r'file\s+([A-Za-z0-9_\-\.\/]+\.(tsx?|jsx?))',
    ] 
    for pattern in patterns:
        matches = re.findall(pattern, prompt, re.IGNORECASE)
        if matches:
            match = matches[0]
            if isinstance(match, tuple):
                return match[0]
            else:
                return match
    return None

#def generate_test_script(ai_client, feature_description):
 #       prompt = f"Please generate an automated test scripts for the following feature: {feature_description}"
 #       return ai_client.chat([{"role": "user", "content": prompt}])

def generate_test_script(ai_client, feature_description, force_cypress=False, include_screenshots=False, code_file_content=None):
    keywords = ["policy", "page", "browser", "UI", "button", "click", "input", "form", "dialog", "dropdown"]
    
    # Handle both string and list inputs
    if isinstance(feature_description, str):
        # If it's a string, check if any keywords are in the description
        use_cypress = any(kw in feature_description.lower() for kw in keywords)
    elif isinstance(feature_description, list):
        # If it's a list of dictionaries (from Polarion), check the steps
        use_cypress = any(
            kw in item.get("step", "").lower()
            for item in feature_description
            for kw in keywords
        )
    else:
        # Default to ginkgo if we can't determine
        use_cypress = False
    
    # Override with force_cypress if specified
    if force_cypress:
        use_cypress = True
    
    if use_cypress:
        framework = "cypress"
        language = "JavaScript"
        description = "You are a QA automation engineer experienced with Cypress, the JavaScript end-to-end testing framework."
        
        # Enhanced Cypress style guide with optional features
        style_guide = "Write realistic Cypress test code using JavaScript to automate browser interactions and validate UI behavior."
        
        if include_screenshots:
            style_guide += " Include cy.screenshot() commands after key interactions for debugging purposes."
            
        additional_requirements = """
- Use proper Cypress selectors (data-testid, data-cy attributes when possible)
- Include proper waits and assertions
- Handle loading states and dynamic content
- Use Cypress best practices for element selection and interaction"""
        
        if include_screenshots:
            additional_requirements += """
- Add cy.screenshot('step-name') after important actions
- Use descriptive screenshot names based on the test step"""
            
    else:
        framework = "ginkgo"
        language = "Go"
        description = "You are a QA automation engineer experienced with Ginkgo, the BDD testing framework for Go."
        style_guide = "Write clean and idiomatic Go code using Ginkgo for BDD-style testing. Use Gomega for assertions."
        additional_requirements = ""
    
    # Build the prompt with optional code context
    code_context_section = ""
    if code_file_content:
        code_context_section = f"""

### Code Context:
The following code file is provided for reference to understand the implementation:

```typescript
{code_file_content}
```

Please use the provided code context to understand the component structure, selectors, and implementation details when generating the test script.
"""
    
    prompt = f"""
{description}
Please generate an automated test script using **{framework}** for the following feature. Follow the standard practices and style conventions of the {framework} framework.

{code_context_section}
### Feature Description:
{feature_description}

### Requirements:
- Use {language} for writing the test script
- Use the {framework} framework
- {style_guide}
- Follow best practices for structuring tests
- Use mocks or stubs as needed
- Add comments to explain each step{additional_requirements}
- Return only the test code inside a markdown code block

### Example Structure for Cypress:
```javascript
describe('Feature Name', () => {{
  beforeEach(() => {{
    // Setup steps
  }});

  it('should perform the test scenario', () => {{
    // Test steps with proper selectors and assertions
    // Include cy.screenshot() if screenshots are enabled
  }});
}});
```
"""

    # Send prompt to AI and return response
    response = ai_client.chat([{"role": "user", "content": prompt}])
    #print("Raw AI response:", response)
    return response




def analyze_failed_case(ai_client, component, failed_cases, guidelines_dict):
       guidelines_dict = guidelines_dict or {}
       guideline = guidelines_dict.get(component, "")
       prompt = _build_prompt(failed_cases, guideline)
       return ai_client.chat([{"role": "user", "content": prompt}])

def _build_prompt(cases: List[Dict], rules_md: str) -> Dict:
        
    """prompt"""
    cases_str = "\n".join(
            f"### Total cases {idx+1}\n"
            f"- Case ID: {case['ID']}\n"
            f"- Case Title: {case['Title']}\n"
            f"- Assert Reason: {case['Error Message']}\n"
            for idx, case in enumerate(cases)
        )
    return f"""
    ## analysis contents
        
    ### analysis guidelines
        {rules_md}
        
    ### failed cases list
        {cases_str}
        
    ### output
        1. Following the template to generate:
           ```markdown table
           #### Test failure Analysis report
           
           **Analysis summary**
           - Total cases: {len(cases)}
           
           **Detailed Analysis**
            - Based on the component and the provided guidelines, analyze the error message and determine the failure type.  
            - The link might contain the information of which component for the error message.
            - Present the results in a clear and structured markdown table format as shown below:
           | Case ID | Case Title | Failure Type With High Possibility | Assert Reason |Suggestion/Note|
           |--------|--------------------------|----------|----------------------------------|-------------------------|
           
            - Then give suggestion or note:
            - If the faliure type is Automation bug, sugget to re-run it.
            - If the failure type is System issue, suggest to check the test envirnoment and then re-run it.
            - If the failure type is Product bug, suggest to be investigated further. 
            
           ```
        """