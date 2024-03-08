import streamlit as st
import ast
import os
import autogen
import chromadb
from autogen import AssistantAgent
from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent
from autogen.agentchat.contrib.retrieve_assistant_agent import RetrieveAssistantAgent
os.environ['OAI_CONFIG_LIST'] = """
[{"model": "google/gemma-7b-it",
"api_key": "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",
"base_url": "https://openrouter.ai/api/v1",
"max_tokens":1000}]
"""

llm_config = {
    "timeout": 600,
    "cache_seed": 28,
    "config_list": autogen.config_list_from_json(
        "OAI_CONFIG_LIST",
        filter_dict={"model": ["google/gemma-7b-it"]},
    ),
    "temperature": 0.1,
}
coder = AssistantAgent(
    name='documenter',
    is_termination_msg=lambda x:x.get('content','').rstrip().endswith('TERMINATE'),
    system_message='You are a experienced programmer. Write code summary',
    llm_config=llm_config
  )
reviewer = AssistantAgent(
    name='Reviewer',
    is_termination_msg=lambda x:x.get('content','').rstrip().endswith('TERMINATE'),
    system_message='You are a senior programmer. Write code review. Reply `TERMINATE` if task done',
    llm_config=llm_config
  )
  
st.title('Enter Github Source Code Link (Raw)')

with st.form(key='my_form'):
    source = st.text_area('Enter Code', value='', height=50)
    submit_button = st.form_submit_button(label='Submit')

if submit_button:
  progress_bar = st.progress(0)
  manager_contexted = RetrieveUserProxyAgent(
      name='manager_contexted',
      is_termination_msg=lambda x:x.get('content','').rstrip().endswith('TERMINATE'),
      system_message='manager who has extra context retrieval power and asks questions. reply `TERMINATE` if task done',
      human_input_mode='NEVER',
      max_consecutive_auto_reply=5,
      retrieve_config={
          'docs_path':source,
          'chunk_token_size':1000,
          'model':'google/gemma-7b-it',
          'client':chromadb.PersistentClient(path='tmp/chromadb'),
          'collection_name':'groupchat',
          'get_or_create':True,
      },
      code_execution_config=False
    )
  progress_bar.progress(20) 
  groupchat = autogen.GroupChat(
    agents=[manager_contexted, coder, reviewer],
    messages=[],
    max_round=5,
    speaker_selection_method='auto',
    allow_repeat_speaker=False
  )
  progress_bar.progress(50) 
  groupManager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)
  problem = 'Write code documentation for the piece of code'
  manager_contexted.reset()
  progress_bar.progress(70) 
  manager_contexted.initiate_chat(groupManager, problem=problem)
  progress_bar.progress(100) 

  for i in groupchat.messages:
    if i['name']=='documenter':
      st.write(i['content'])
