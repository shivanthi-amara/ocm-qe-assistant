from typing import Dict, List
import httpx
import requests
import urllib3

# Disable SSL warnings for Red Hat internal services
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class AssistantClient:
    def __init__(self, api_key, base_url, model):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
    def chat(self, messages, **kwargs):
        # Detect API type based on base_url and model
        if "anthropic.com" in self.base_url:
            return self._chat_claude(messages, **kwargs)
        elif "gemini" in self.model.lower():
            # If model contains "gemini", use OpenAI-compatible endpoint regardless of base_url
            return self._chat_openai_compatible(messages, **kwargs)
        elif "claude--apicast" in self.base_url or "stc.ai" in self.base_url:
            return self._chat_redhat_claude(messages, **kwargs)
        else:
            return self._chat_openai_compatible(messages, **kwargs)
    
    def _chat_claude(self, messages, **kwargs):
        """Handle Claude API calls"""
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        # Convert messages to Claude format
        system_message = ""
        claude_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                claude_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        payload = {
            "model": self.model,
            "messages": claude_messages,
            "max_tokens": kwargs.get("max_tokens", 4000),
            **{k: v for k, v in kwargs.items() if k != "max_tokens"}
        }
        
        if system_message:
            payload["system"] = system_message
            
        print("Debug - Claude Request Payload:", payload)
        
        try:
            response = requests.post(f"{self.base_url.rstrip('/')}/v1/messages", headers=headers, json=payload, verify=False)
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]
        except requests.exceptions.HTTPError as e:
            print("Status code:", response.status_code)
            print("Response body:", response.text)
            raise
    
    def _chat_redhat_claude(self, messages, **kwargs):
        """Handle Red Hat internal Claude API calls"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Convert messages to the format expected by Red Hat Claude
        system_message = ""
        user_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            elif msg["role"] == "user":
                user_messages.append(msg["content"])
        
        # Try different possible endpoints for Red Hat Claude
        possible_endpoints = [
            #"/sonnet/models/claude-sonnet-4@20250514:streamRawPredict", 
            "/haiku/models/claude-3-5-haiku@20241022:streamRawPredict", 
            "/v1/messages",  # Standard Claude format
            "/api/v1/messages",  # Alternative path
            "/v1beta/openai/chat/completions",  # OpenAI-compatible (current failing one)
            "/api/v1/chat",  # Alternative chat endpoint
            ""  # Direct to base URL
        ]
        
        for endpoint in possible_endpoints:
            try:
                if endpoint == "/v1beta/openai/chat/completions":
                    # OpenAI-compatible format
                    payload = {
                        "model": self.model,
                        "messages": messages,
                        "max_tokens": kwargs.get("max_tokens", 4000),
                        **{k: v for k, v in kwargs.items() if k != "max_tokens"}
                    }
                elif "streamRawPredict" in endpoint:
                    # Red Hat Vertex Claude format
                    claude_messages = []
                    for msg in messages:
                        if msg["role"] == "user":
                            claude_messages.append({
                                "role": "user",
                                "content": [{"type": "text", "text": msg["content"]}]
                            })
                        elif msg["role"] == "assistant":
                            claude_messages.append({
                                "role": "assistant", 
                                "content": [{"type": "text", "text": msg["content"]}]
                            })
                    
                    payload = {
                        "anthropic_version": "vertex-2023-10-16",
                        "messages": claude_messages,
                        "max_tokens": kwargs.get("max_tokens", 4000),
                        "temperature": kwargs.get("temperature", 0)
                    }
                    
                    if system_message:
                        payload["system"] = system_message
                else:
                    # Standard Claude format
                    payload = {
                        "model": self.model,
                        "messages": [{"role": "user", "content": "\n".join(user_messages)}],
                        "max_tokens": kwargs.get("max_tokens", 4000),
                        **{k: v for k, v in kwargs.items() if k != "max_tokens"}
                    }
                    
                    if system_message:
                        payload["system"] = system_message
                
                url = f"{self.base_url.rstrip('/')}{endpoint}"
                print(f"Debug - Trying Red Hat Claude endpoint: {url}")
                print(f"Debug - Payload: {payload}")
                
                response = requests.post(url, headers=headers, json=payload, verify=False)
                
                if response.status_code == 200:
                    data = response.json()
                    # Try different response formats
                    if "content" in data and isinstance(data["content"], list):
                        # Standard Claude format
                        if isinstance(data["content"][0], dict) and "text" in data["content"][0]:
                            return data["content"][0]["text"]
                        else:
                            return data["content"][0]
                    elif "choices" in data:
                        # OpenAI format
                        return data["choices"][0]["message"]["content"]
                    elif "message" in data:
                        # Simple message format
                        return data["message"]
                    elif isinstance(data, dict) and len(data) == 1:
                        # Single key response
                        return list(data.values())[0]
                    else:
                        # Fallback - convert to string
                        return str(data)
                elif response.status_code != 404:
                    # If it's not a 404, this might be the right endpoint with a different error
                    print(f"Red Hat Claude endpoint {endpoint} returned {response.status_code}: {response.text}")
                    
            except Exception as e:
                print(f"Error trying endpoint {endpoint}: {str(e)}")
                continue
        
        # If all endpoints fail, raise an error with helpful information
        raise ConnectionError(f"Could not connect to Red Hat Claude service. Tried endpoints: {possible_endpoints}. "
                            f"Last response: {response.status_code} - {response.text if 'response' in locals() else 'No response'}")
    
    def _chat_openai_compatible(self, messages, **kwargs):
        """Handle OpenAI-compatible API calls (for other models)"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": messages,
            **kwargs
        }
        print("Debug - OpenAI Request Payload:", payload) 

        try:
          response = requests.post(f"{self.base_url.rstrip('/')}/v1/chat/completions", headers=headers, json=payload, verify=False)
          response.raise_for_status()
          data = response.json()
          message = data["choices"][0]["message"]["content"]
          return message
        except requests.exceptions.HTTPError as e:
             print("Status code:", response.status_code)
             print("Response body:", response.text)
             print("HTTP Error Details:", e.response.text)
             raise   
    
    def __call__(self, prompt, *args, **kwargs):
        if isinstance(prompt, str):
            messages = [{"role": "user", "content": prompt}]
        elif isinstance(prompt, list):
            messages = prompt
        else:
            raise ValueError("prompt must be str or list of messages")       
        return self.chat(messages, **kwargs)
