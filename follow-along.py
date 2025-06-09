from langchain.chains import LLMChain
from langchain.llms.bedrock import Bedrock
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain_community.chat_models import BedrockChat
import boto3
import os
import streamlit as st

os.environ["AWS_PROFILE"] = "ryanj"

#bedrock client

bedrock_client = boto3.client(
    service_name = "bedrock-runtime",
    region_name = "us-west-2"
)

model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
model_id_2 = "anthropic.claude-3-haiku-20240307-v1:0"

llm = BedrockChat(
    model_id = model_id,
    client = bedrock_client,
    model_kwargs = {"max_tokens_to_sample": 2000, "temperature": 0.9}
)

def my_chatbot(language, freeform_text):
    prompt = PromptTemplate(
        input_variables = ["language", "freeform_text"],
        template = "You are a chatbot. You are in {language}, \n\n{freeform_text}"
    )
    bedrock_chain = LLMChain(llm = llm, prompt=prompt)
    response = bedrock_chain({'language': language, 'freeform_text': freeform_text})
    return response
print(my_chatbot("english", "Which country has the largest economy"))

