from collections import defaultdict
import re
import os
import json
from typing import Dict, List, Any
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

def load_sample_files() -> Dict[str, str]:
    """Load sample test case and fixture files for context"""
    sample_context = {}
    
    # Load sample test case
    sample_test_path = "sample/test/OsdAwsCcsPublicClusterCreation.js"
    if os.path.exists(sample_test_path):
        try:
            with open(sample_test_path, 'r', encoding='utf-8') as f:
                sample_context['test_case'] = f.read()
        except Exception as e:
            print(f"Error loading sample test case: {e}")
    
    # Load sample fixture
    sample_fixture_path = "sample/fixtures/OsdAwsCcsCreatePublicCluster.json"
    if os.path.exists(sample_fixture_path):
        try:
            with open(sample_fixture_path, 'r', encoding='utf-8') as f:
                sample_context['fixture'] = f.read()
        except Exception as e:
            print(f"Error loading sample fixture: {e}")
    
    return sample_context

def extract_fixture_data_from_polarion_steps(polarion_steps: List[Dict]) -> Dict[str, Any]:
    """
    Extract fixture data from Polarion test steps.
    Look for the keyword "input" and extract the text that follows it.
    """
    fixture_data = {}
    
    if not polarion_steps:
        return fixture_data
    for step in polarion_steps:
        if isinstance(step, dict):
            step_text = step.get('step', '') or step.get('description', '') or str(step)
        else:
            step_text = str(step)
        if 'input' in step_text.lower():
            input_pos = step_text.lower().find('input')
            if input_pos != -1:
                after_input = step_text[input_pos + 5:].strip()
                quoted_matches = re.findall(r'"([^"]+)"', after_input)
                if quoted_matches:
                    for i, match in enumerate(quoted_matches):
                        fixture_data[f'input_{i+1}'] = match
                else:
                    parts = re.split(r'[,\s]+', after_input)
                    if parts:
                        first_part = parts[0].strip()
                        if first_part:
                            fixture_data['input_1'] = first_part
                        for i, part in enumerate(parts[1:], 2):
                            part = part.strip()
                            if part and len(part) > 1:
                                fixture_data[f'input_{i}'] = part
    
    return fixture_data

def generate_fixture_from_polarion_data(ai_client, polarion_steps: List[Dict], test_case_title: str = "") -> str:
    """
    Generate a fixture file based on Polarion test steps data.
    Extract input parameters from the test steps and use them to populate the fixture.
    """
    # Extract fixture data from Polarion steps
    extracted_data = extract_fixture_data_from_polarion_steps(polarion_steps)
    
    # Load sample fixture for structure reference
    sample_context = load_sample_files()
    sample_fixture = sample_context.get('fixture', '')
    
    # Convert Polarion steps to a readable format for AI
    steps_text = ""
    if polarion_steps:
        for i, step in enumerate(polarion_steps, 1):
            if isinstance(step, dict):
                step_text = step.get('step', '') or step.get('description', '') or str(step)
            else:
                step_text = str(step)
            steps_text += f"Step {i}: {step_text}\n"
    
    # Build the prompt for fixture generation
    prompt = f"""
You are a QA automation engineer responsible for creating test fixture files for Cypress tests based on Polarion test case data.

### Test Case Information:
**Title**: {test_case_title}

**Test Steps from Polarion:**
{steps_text}

**Extracted Input Parameters:**
{json.dumps(extracted_data, indent=2) if extracted_data else "No input parameters extracted"}

### Sample Fixture Structure:
```json
{sample_fixture}
```

### Requirements:
- Create a JSON fixture file that provides test data for the described test case
- Use the extracted input parameters from the Polarion test steps to populate the fixture
- Follow the structure and naming conventions from the sample fixture
- Map the extracted parameters to appropriate fixture fields
- Use realistic but test-appropriate values
- Ensure the fixture supports the test scenarios described in the Polarion steps
- Return only the JSON fixture content inside a markdown code block

### Mapping Guidelines:
- Map cluster-related parameters to appropriate fixture fields
- Map AWS/cloud provider parameters to the correct sections
- Map networking parameters (CIDR, etc.) to networking sections
- Map node/machine pool parameters to MachinePools sections
- Use the extracted values where available, otherwise use reasonable defaults

### Example Structure:
```json
{{
  "test-profile-name": {{
    "day1-profile": {{
      "Description": "Test description based on Polarion case",
      "Type": "OSD",
      "CloudProvider": "AWS",
      "ClusterName": "extracted-cluster-name",
      "Region": "extracted-region",
      // ... other configuration properties using extracted data
    }}
  }}
}}
```
"""

    response = ai_client.chat([{"role": "user", "content": prompt}])
    return response

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

def generate_fixture_file(ai_client, test_description, test_case_content=None):
    """Generate a fixture file based on test description and sample fixture"""
    sample_context = load_sample_files()
    
    # Build the prompt for fixture generation
    sample_fixture_context = ""
    if sample_context.get('fixture'):
        sample_fixture_context = f"""
### Sample Fixture Reference:
The following is a sample fixture file structure for reference:

```json
{sample_context['fixture']}
```

Use this structure as a template but adapt it for the specific test case being generated.
"""
    
    test_case_context = ""
    if test_case_content:
        test_case_context = f"""
### Test Case Context:
The following test case content should be used to understand what fixture data is needed:

```javascript
{test_case_content}
```
"""
    
    prompt = f"""
You are a QA automation engineer responsible for creating test fixture files for Cypress tests.

{sample_fixture_context}
{test_case_context}

### Test Description:
{test_description}

### Requirements:
- Create a JSON fixture file that provides test data for the described test case
- Follow the structure and naming conventions from the sample fixture
- Include all necessary configuration data that the test case would need
- Use realistic but test-appropriate values
- Ensure the fixture supports the test scenarios described
- Return only the JSON fixture content inside a markdown code block

### Example Structure:
```json
{{
  "test-profile-name": {{
    "day1-profile": {{
      "Description": "Test description",
      "Type": "Test type",
      "CloudProvider": "Provider name",
      "ClusterName": "test-cluster-name",
      // ... other configuration properties
    }}
  }}
}}
```
"""

    response = ai_client.chat([{"role": "user", "content": prompt}])
    return response

def generate_test_script(ai_client, feature_description, force_cypress=False, include_screenshots=False, code_file_content=None, generate_fixture=False):
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
    
    # Load sample files for context
    sample_context = load_sample_files()
    
    if use_cypress:
        framework = "cypress"
        language = "JavaScript"
        description = "You are a QA automation engineer experienced with Cypress, the JavaScript end-to-end testing framework."
        
        # Enhanced Cypress style guide with sample context
        style_guide = "Write realistic Cypress test code using JavaScript to automate browser interactions and validate UI behavior."
        
        # Add sample test case context
        sample_test_context = ""
        if sample_context.get('test_case'):
            sample_test_context = f"""

### Sample Test Case Reference:
The following is a sample Cypress test case for reference:

```javascript
{sample_context['test_case']}
```

Use this as a template for structure, naming conventions, and best practices when generating your test case.
"""
        
        if include_screenshots:
            style_guide += " Include cy.screenshot() commands after key interactions for debugging purposes."
            
        additional_requirements = """
- Use proper Cypress selectors (data-testid, data-cy attributes when possible)
- Include proper waits and assertions
- Handle loading states and dynamic content
- Use Cypress best practices for element selection and interaction
- Follow the structure and patterns from the sample test case"""
        
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
        sample_test_context = ""
    
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

{sample_test_context}
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
    return response

def generate_test_script_with_fixture(ai_client, feature_description, force_cypress=False, include_screenshots=False, code_file_content=None):
    """Generate both test script and fixture file"""
    # Generate the test script first
    test_script = generate_test_script(
        ai_client, 
        feature_description, 
        force_cypress=force_cypress, 
        include_screenshots=include_screenshots, 
        code_file_content=code_file_content
    )
    
    # Generate the fixture file
    fixture_content = generate_fixture_file(ai_client, feature_description, test_script)
    
    return {
        "test_script": test_script,
        "fixture_content": fixture_content
    }

def generate_test_script_with_polarion_fixture(ai_client, polarion_steps, test_case_title="", force_cypress=False, include_screenshots=False, code_file_content=None):
    """Generate test script and fixture file using Polarion data"""
    # Generate the test script first
    test_script = generate_test_script(
        ai_client, 
        polarion_steps, 
        force_cypress=force_cypress, 
        include_screenshots=include_screenshots, 
        code_file_content=code_file_content
    )
    
    # Generate the fixture file using Polarion data
    fixture_content = generate_fixture_from_polarion_data(ai_client, polarion_steps, test_case_title)
    
    return {
        "test_script": test_script,
        "fixture_content": fixture_content
    }

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