# acm-qe-assistant

QE Assistant Tool helps to QE's routine works.

## Overview 

The QE Assistant Tool is aimed at facilitating QE tasks in OCM environments, currently, this tool includes two abilities, one is helping to analyse the failed cases to generate the analysis report, another is helping to generate automation scripts following Polarion test cases.

## How to use

### Using with Gemini CLI

This tool is now compatible with Google's Gemini CLI. See [GEMINI.md](GEMINI.md) for detailed instructions on available capabilities and usage patterns when using with Gemini models.

#### Prerequisites
1. Python 3.10 or higher
2. VPN required
3. Gemini CLI installed

#### Steps

1. Clone the repository:

 ```
 git clone https://github.com/stolostron/acm-qe-assistant.git
 cd acm-qe-assistant
 ```
 2. Install dependencies:
```
pip install -r requirements.txt
```
 3. Make the file named .env with few credentials

```
POLARION_API="https://polarion.engineering.redhat.com/polarion"
POLARION_PROJECT="OSE" --- This is RHACM project
POLARION_TOKEN="xxx" 

```

### Using with Claude Code

This tool is now compatible with Anthropic's Claude Code CLI, providing intelligent automation assistance for QE workflows. See [CLAUDE.md](CLAUDE.md) for detailed instructions on available capabilities and usage patterns.

#### Prerequisites
1. Python 3.10 or higher
2. VPN required
3. Claude Code CLI installed

#### Steps

1. Clone the repository:
   
```
cd ocm-qe-assistant
```

2. Install dependencies:
   
```
pip install -r requirements.txt
```

3. Set up environment variables:
   
```
export POLARION_API="https://polarion.engineering.redhat.com/polarion"
export POLARION_PROJECT="RHACM4K"
export POLARION_TOKEN="xxx"
```

### Using with AI Models

#### Prerequisites
1. Python 3.10 or higher
2. VPN required
3. You have AI model API token. for example, [Models.corp](https://gitlab.cee.redhat.com/models-corp/user-documentation/-/blob/main/getting-started.md)

#### Steps

1. Clone the repository:
 
 ```
 cd ocm-qe-assistant
 ```
2. Install dependencies:

```
pip install -r requirements.txt
```
3. Export AI model enviroment variable

```
export MODEL_API="https://claude--apicast-production.apps.int.stc.ai.prod.us-east-1.aws.paas.redhat.com:443" ---This is located in Models.corp
export MODEL_ID="claude-sonnet-4@20250514"
export MODEL_KEY=="xxxxx"
export POLARION_API="https://polarion.engineering.redhat.com/polarion"
export POLARION_PROJECT="OSE" --- This is RHACM project
export POLARION_TOKEN="xxx" 

Note: If you export POLARION_USER and POLARION_PASSWORD, you should have polarion certificate named "redhatcert.pem" in the directory so that connect the polarion.
```
4. Run App

```
python -m streamlit run agents/app.py
```

Then, you will get UI console, you can easily to chat it in this console.

### Demo

- For generating scripts, you can input prompt just like “generate scripts for OCP-40585(polation case ID)”

- ToDo - Analyze failed cases, you just input jenkins job link in the chat.