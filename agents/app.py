# app.py
import os
import re
from dotenv import load_dotenv
import streamlit as st
from agents.assistant_clients import AssistantClient
from tools import get_error_message
from tools import (
    extract_component_from_url,
    load_rules,
    analyze_failed_case,
    generate_test_script,
    extract_code_path_from_prompt,
    load_code_file
)
from tools import login_to_polarion, get_test_case_by_id
import truststore 

truststore.inject_into_ssl()
load_dotenv()
MODEL_API=os.getenv("MODEL_API")
MODEL_ID=os.getenv("MODEL_ID")
MODEL_KEY=os.getenv("MODEL_KEY")
POLARION_API=os.getenv("POLARION_API")
POLARION_USER=os.getenv("POLARION_USER")
POLARION_PASSWD=os.getenv("POLARION_PASSWORD")
POLARION_PROJECT=os.getenv("POLARION_PROJECT")
POLARION_TOKEN=os.getenv("POLARION_TOKEN")
client = AssistantClient(
    api_key=MODEL_KEY, base_url=MODEL_API, model=MODEL_ID)

# Streamlit 
def run_streamlit_app():

    # Init chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    st.set_page_config(
     page_title="🛠️ AI Assistant System",
     layout="wide",
     initial_sidebar_state="expanded"
)
    st.title("🛠️ AI Assistant System")
    st.markdown("""
Generate automation scripts and analyze failed test cases.

**💡 How to use:**
- **With Polarion**: `generate automation scripts OCP-40585 with components/App/App.tsx` (requires VPN)
- **Without Polarion**: `generate automation scripts for user login functionality`
- **Analyze failures**: Paste Jenkins URLs for AI-powered analysis
""")
    # Sidebar configuration
    #with st.sidebar:
   #  st.header("Configuration")
   #  rules_file = st.selectbox(
   #     "guidelines",
   #     ["rules/component-keywords.md"],
   #     format_func=lambda x: x.split('/')[-1]
   #  )
    
   #  st.divider()
     
    # manage chat states 
    if "messages" not in st.session_state:
      st.session_state.messages = []

    if "last_intent" not in st.session_state:
      st.session_state.last_intent = None

    if "last_suite_url" not in st.session_state:
     st.session_state.last_suite_url = None
 
    # Initial chat records
    if "messages" not in st.session_state:
     st.session_state.messages = [
        {"role": "system", "content": "You are a QA automation assistant."}
    ]
    # show chat history
    for msg in st.session_state.messages:
       with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

    #def regenerate_analysis():
    #    if "last_suite_url" in st.session_state and st.session_state.last_suite_url:
    #        prompt = f"{st.session_state.last_suite_url}"
    #        st.session_state.messages.append({"role": "user", "content": prompt})
    #        st.session_state.rerun_trigger = True 
            #st.experimental_rerun()
    #if "rerun_trigger" in st.session_state and st.session_state.rerun_trigger:
    # Reset the rerun trigger flag
    #  st.session_state.rerun_trigger = False
    # Trigger the rerun here
    #  st.rerun()
   
    if prompt := st.chat_input("Ask your question, for example, generate the automation scripts or analyse the failed case"):
      # save user input
      st.session_state.messages.append({"role": "user", "content": prompt})
      with st.chat_message("user"):
        st.markdown(prompt)
      # Judge the intention
      intent = None
      if "generate" in prompt.lower() or "RHACM4K-" in prompt.lower():
                   intent = "generate_test_script"
      elif "re-generate" in prompt.lower() or "generate again" in prompt.lower():
                   intent = st.session_state.last_intent
      elif "analyse" in prompt.lower() or "http" in prompt.lower():
                   intent = "analyze_failure_url"
      elif "analyse" in prompt.lower() or "re-analyse" in prompt.lower():
                   intent = st.session_state.last_intent
      else:
            intent = None
      # answer logic
      with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            reply = ""    
            if intent == "generate_test_script":
                    # the logic for generating automation scripts
                     feature_description = None  # Initialize to avoid UnboundLocalError
                     match = re.search(r"RHACM4K|OCP-\d+", prompt, re.IGNORECASE)
                     #match = re.search(prompt, re.IGNORECASE)
                     if match:
                      # Initialize reply for this branch
                      reply = ""
                      # Check if Polarion credentials are configured
                      if not POLARION_API:
                          reply = "❌ **Error**: POLARION_API environment variable is not set. Please configure Polarion credentials in your .env file."
                      elif not POLARION_PROJECT:
                          reply = "❌ **Error**: POLARION_PROJECT environment variable is not set. Please configure Polarion credentials in your .env file."
                      elif not POLARION_TOKEN and not (POLARION_USER and POLARION_PASSWD):
                          reply = "❌ **Error**: Polarion authentication not configured. Please set either POLARION_TOKEN or both POLARION_USER and POLARION_PASSWORD in your .env file."
                      
                      else:
                          try:
                              with st.spinner("Connecting to Polarion..."):
                                  polarion_client = login_to_polarion(polarion_endpoint=POLARION_API, polarion_user=POLARION_USER, polarion_password=POLARION_PASSWD, polarion_token=POLARION_TOKEN)  
                              
                              if not polarion_client:
                                  reply = """❌ **Polarion Connection Failed**
                                  
**Possible causes:**
- Invalid or expired authentication token
- Network connectivity issues  
- VPN not connected to Red Hat internal network

**Try these solutions:**
1. **For Red Hat employees**: Connect to Red Hat VPN and try again
2. **Alternative**: Use text-based script generation instead:
   - Type: `generate automation scripts for user login functionality`
   - Or describe your test scenario directly

**Note**: The standalone Polarion script works fine, so this appears to be a Streamlit-specific authentication issue."""
                              else:
                                  polarion_id = match.group(0)
                                  project_id = POLARION_PROJECT  
                                  with st.spinner(f"Retrieving test case {polarion_id}..."):
                                      _, steps, _ = get_test_case_by_id(polarion_client, project_id, polarion_id)
                                  
                                  if not steps:
                                      reply = f"""❌ **Test Case Not Found**: {polarion_id}
                                      
**Possible reasons:**
- Case ID doesn't exist in project {project_id}
- You don't have access permissions for this case
- Case ID format is incorrect

**Alternative**: Try describing the test scenario instead:
- `generate automation scripts for <your test description>`"""
                                  else:
                                      feature_description = steps
                                      st.success(f"✅ Retrieved test case {polarion_id} successfully!")
                          except Exception as e:
                              error_msg = str(e)
                              if "Failed to resolve" in error_msg or "nodename nor servname provided" in error_msg:
                                  reply = """❌ **Network Error**: Cannot reach Polarion server
                                  
**This means:**
- You're not connected to Red Hat's internal network
- Polarion requires VPN access for external connections

**Solutions:**
1. **Connect to Red Hat VPN** (if you're a Red Hat employee)
2. **Use text-based generation**: `generate automation scripts for <description>`
3. **Contact IT** for VPN access to internal tools"""
                              elif "Authentication failed" in error_msg or "No valid personal access token" in error_msg:
                                  reply = """❌ **Authentication Error**: Polarion token invalid
                                  
**This means:**
- Your Polarion token may be expired or invalid
- Token permissions may be insufficient

**Solutions:**
1. **Generate new token** in Polarion settings
2. **Update .env file** with the new token
3. **Use text-based generation**: `generate automation scripts for <description>`

**Note**: The standalone script works, suggesting a Streamlit-specific token handling issue."""
                              else:
                                  reply = f"""❌ **Polarion Error**: {error_msg}
                                  
**Alternative**: Try text-based script generation:
- `generate automation scripts for <your test description>`"""
                     else:
                       feature_description = re.sub(r"generate( automation)? scripts", "", prompt, flags=re.IGNORECASE).strip()  
                     
                     # Extract single code file path from prompt if any
                     code_file_path = extract_code_path_from_prompt(prompt)
                     code_file_content = None
                     if code_file_path:
                         with st.spinner(f"Loading code file: {code_file_path}..."):
                             try:
                                 code_file_content = load_code_file(code_file_path)
                                 st.success(f"✅ Loaded code file: {code_file_path}")
                             except Exception as e:
                                 st.error(f"❌ Error loading file {code_file_path}: {str(e)}")
                     
                     # Only generate test script if we have feature_description and no error reply
                     if not reply and feature_description:
                            test_script = generate_test_script(client, feature_description, code_file_content=code_file_content)
                            reply = f"**Automation scripts:**\n\n```\n{test_script}\n```"     
                     elif not reply:
                            reply = f"**No steps available.**"
                     st.markdown(reply)
            elif intent == "analyze_failure_url":
                 # if not st.session_state.get("generated"):
                    # URL 
                    url_match = re.match(r"^(.*?/\d+)/", prompt)
                    #match = re.match(r"^(.*?/\d+)/", url)
                
                    url_name = url_match.group(1) if url_match else st.session_state.last_suite_url
                    if not url_name:
                        reply = "Please provide the correct job URL. For example: https://jenkins-csb-rhacm-tests.dno.corp.redhat.com/view/Global%20Hub/job/globalhub-e2e/819"
                    else:
                        st.session_state.last_suite_url = url_name
                        component = extract_component_from_url(url_name)
                        if not component:
                           reply = f"Not find the component name"
                        else:   
                           failed_cases = get_error_message(url_name)
                           st.session_state['failed_cases'] = failed_cases
                        if not failed_cases:
                            reply = f"No found failed cases for url `{url_name}`."
                        else:
                            results = []
                            guideline = load_rules("runbooks/component-keywords.md")     
                            analysis = analyze_failed_case(client, component, failed_cases, guidelines_dict=guideline)
                            #results.append(f"{analysis}")
                            #reply = "\n\n---\n\n".join(results)
                            reply = analysis
                            st.session_state.last_intent = "analyze_failure_url" 
                           # st.session_state.generated = True
                    st.markdown(reply)
                    col1, col2 = st.columns([1,1])
                    with col1:
                              if st.session_state.last_suite_url:
                                  st.markdown(
                                        f"[🔗 Link to Jenkins Job]({st.session_state.last_suite_url})",
                                        unsafe_allow_html=True,
                                     )
                    #with col2:
                             # if st.button("🔄 Regenerate", key="regenerate_btn"):
                             #      st.session_state.pending_regeneration = True
                             #      st.session_state.messages.append({"role": "user", "content": "re-analyse"})
                             #      st.rerun()
                             #  st.button("🔄 Regenerate", key="regenerate_btn", on_click=regenerate_analysis)
                            #   pass
                            #if st.button("🔄 Regenerate", key="regenerate_btn"):
                            #     st.session_state.need_rerun = True
                             #     st.session_state.rerun_prompt = f"re-analyze {st.session_state.last_suite_url}"               
            else:
              # AI chat by default
              # parse AI response
              response = client.chat(st.session_state.messages)
              if isinstance(response, str):
                reply = response
              elif isinstance(response, dict) and "choices" in response:
                reply = response["choices"][0]["message"]["content"]
              else:
                 reply = "Unexpected AI response"
            # show reply
              st.markdown(reply)
            # save chat record
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.session_state.last_intent = intent
                
if __name__ == "__main__":
    run_streamlit_app()