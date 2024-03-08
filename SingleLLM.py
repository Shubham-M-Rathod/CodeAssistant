import streamlit as st
import ast
import javalang

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, SummarizationPipeline

pipeline = SummarizationPipeline(
    model=AutoModelForSeq2SeqLM.from_pretrained("Salesforce/codet5-base-multi-sum"),
    tokenizer=AutoTokenizer.from_pretrained("Salesforce/codet5-base-multi-sum", skip_special_tokens=True, use_fast=False, padding='max_length')
)

def find_and_summarize_python(code):
  ans=''
  root = ast.parse(code)
  for node in ast.walk(root):
      if isinstance(node, ast.FunctionDef):
          function_code = ast.get_source_segment(code, node)
          print(f"Found function: {node.name}")
          summary = summarize_function(function_code)
          print(f"Summary: {summary}\n")
          ans += f"{node.name}: {summary[0].get('summary_text')}\n"
  return ans

import javalang as jl

def __get_start_end_for_node(node_to_find, tree):
    start = None
    end = None
    for path, node in tree:
        if start is not None and node_to_find not in path:
            end = node.position
            return start, end
        if start is None and node == node_to_find:
            start = node.position
    return start, end


def __get_string(start, end, code):
    if start is None:
        return ""

    end_pos = None

    if end is not None:
        end_pos = end.line - 1

    lines = code.splitlines(True)
    string = "".join(lines[start.line:end_pos])
    string = lines[start.line - 1] + string

    if end is None:
        left = string.count("{")
        right = string.count("}")
        if right - left == 1:
            p = string.rfind("}")
            string = string[:p]

    return string

def find_and_summarize_java(code):
  ans=''
  tree = jl.parse.parse(code)
  for _, node in tree.filter(jl.tree.MethodDeclaration):
      start, end = __get_start_end_for_node(node, tree)
      function_code = __get_string(start, end, code)   
      summary = summarize_function(function_code) 
      print(f"Summary: {summary}\n") 
      ans += f"{node.name}: {summary[0].get('summary_text')}\n"
  return ans

def summarize_function(function_code):
  summaries = pipeline(function_code, max_length=30)
  return summaries 

st.title('Enter Code')
language = st.selectbox('Select Language', ('Python', 'Java'))

with st.form(key='my_form'):
    code_input = st.text_area('Enter Code', value='', height=200)
    submit_button = st.form_submit_button(label='Submit')

if submit_button:
    if language == 'Python':
      summary = find_and_summarize_python(code_input)
    elif language == 'Java':
      summary = find_and_summarize_java(code_input)
    st.write(summary)
