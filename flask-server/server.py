from flask import Flask, redirect, url_for, request, jsonify
from flask_cors import CORS
from datetime import datetime
import psycopg2
from pymongo import DESCENDING
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from pymongo.errors import OperationFailure
from pymongo.operations import SearchIndexModel
import langchain
from langchain_core.documents import Document
import glob
from langchain_mongodb.retrievers import MongoDBAtlasParentDocumentRetriever
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
import asyncio
from typing import Generator, List
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from typing import Annotated, Dict
from langchain.agents import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from typing_extensions import TypedDict
import getpass
import os
from langgraph.checkpoint.mongodb import MongoDBSaver
import openai



#BACKEND FILE

app = Flask(__name__)
CORS(app)

# Array to store inputs
inputs = []


#user database connection
try:
    conn = psycopg2.connect(
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USERNAME"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )
    cur = conn.cursor()
except Exception as e:
    print("Error connecting to the database:", e)
# Check if the connection was successful 
if conn:
    print("Connected to the user accounts database successfully!")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_accounts (
        id SERIAL PRIMARY KEY,
        username VARCHAR(100) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL
    )
    """)
    conn.commit()




#messages database connection
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi


#keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MONGODB_URI = os.getenv("MONGODB_URI")

client = MongoClient(MONGODB_URI, server_api=ServerApi('1'))
# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)
    
db = client["chat_database"]






embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=OPENAI_API_KEY,
)
DB_NAME = "sabine"
COLLECTION_NAME = "rag_docs"

def get_splitter(chunk_size: int) -> RecursiveCharacterTextSplitter:
    """
    Returns a token-based text splitter with overlap

    Args:
        chunk_size (_type_): Chunk size in number of tokens

    Returns:
        RecursiveCharacterTextSplitter: Recursive text splitter object
    """
    return RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="cl100k_base",
        chunk_size=chunk_size,
        chunk_overlap=0.15 * chunk_size,
    )
    
parent_doc_retriever = MongoDBAtlasParentDocumentRetriever.from_connection_string(
    connection_string=MONGODB_URI,
    embedding_model=embedding_model,
    child_splitter=get_splitter(200),
    database_name=DB_NAME,
    collection_name=COLLECTION_NAME,
    text_key="page_content",
    search_kwargs={"top_k": 10},
)
BATCH_SIZE = 256
MAX_CONCURRENCY  =4
collection = client[DB_NAME][COLLECTION_NAME]
VS_INDEX_NAME = "vector_index"

# Vector search index definition
model = SearchIndexModel(
    definition={
        "fields": [
            {
                "type": "vector",
                "path": "embedding",
                "numDimensions": 1536,
                "similarity": "cosine",
            }
        ]
    },
    name=VS_INDEX_NAME,
    type="vectorSearch",
)

# Check if the index already exists, if not create it
try:
    collection.create_search_index(model=model)
    print(
        f"Successfully created index {VS_INDEX_NAME} for collection {COLLECTION_NAME}"
    )
except OperationFailure:
    print(
        f"Duplicate index {VS_INDEX_NAME} found for collection {COLLECTION_NAME}. Skipping index creation."
    )
    
# Converting the retriever into an agent tool
@tool
def get_info_about_vct(user_query: str) -> str:
    """
    Retrieve information about Valorant Champion Tour, with token limit error handling by reducing top_k.
    """
    print("tool called")
    def summarize_for_query(query, document):
        print("summary called")
        messages = [
            {"role": "system", "content": "Extract only the parts of this document that are relevant to the question."},
            {"role": "user", "content": f"Question: {query}\nDocument: {document}"}
        ]
        response = openai.ChatCompletion.create(
            api_key=OPENAI_API_KEY,
            model="gpt-4o",
            messages=messages,
            temperature=0.3
        )
        print(response)
        return response.choices[0].message["content"]

    # Try with decreasing top_k values
    for top_k in [10, 5, 2, 1]:
        try:
            print(f"Trying with top_k={top_k}")
            docs = MongoDBAtlasParentDocumentRetriever.from_connection_string(
                connection_string=MONGODB_URI,
                embedding_model=embedding_model,
                child_splitter=get_splitter(200),
                database_name=DB_NAME,
                collection_name=COLLECTION_NAME,
                text_key="page_content",
                search_kwargs={"top_k": top_k},
            ).invoke(user_query)
            context = "\n\n".join([d.page_content for d in docs])
            return context
        except openai.RateLimitError as e:
            print(f"OpenAI RateLimitError at top_k={top_k}: {e}")
            # Try to extract a helpful message
            try:
                error_json = e.response.json() if hasattr(e, 'response') and e.response else None
                if error_json and 'error' in error_json and 'message' in error_json['error']:
                    msg = error_json['error']['message']
                else:
                    msg = str(e)
            except Exception:
                msg = str(e)
            if 'tokens per min' in msg or 'Request too large' in msg:
                continue  # Try with lower top_k
            return f"OpenAI Rate Limit Error: {msg}"
        except Exception as e:
            print(f"Error in get_info_about_vct at top_k={top_k}: {e}")
            continue
    return "Sorry, your request is too large for the current model's token limit, even with minimal context. Please shorten your input or ask for a smaller output."

tools = [get_info_about_vct]

# Define the LLM to use as the brain of the agent
llm = ChatOpenAI(temperature=0, model="gpt-4o-2024-11-20", api_key=OPENAI_API_KEY)

# Agent prompt (original, less strict)
prompt = ChatPromptTemplate.from_messages([
    (
        "You are a helpful AI assistant named Sabine."
        " You are provided with tools to answer questions about Valorant Champions Tour and build teams out of VCT players based on the user's requests."
        " Think step-by-step and use these tools to get the information required to answer the user query."
        " Do not re-run tools unless absolutely necessary."
        " If you are not able to get enough information using the tools, reply with I DON'T KNOW."
        " You have access to the following tools: {tool_names}."
    ),
    MessagesPlaceholder(variable_name="messages"),
])
prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
llm_with_tools = prompt | llm.bind_tools(tools)

# Define graph state
class GraphState(TypedDict):
    messages: Annotated[list, add_messages]
    
def agent(state: GraphState) -> Dict[str, List]:
    """
    Agent node

    Args:
        state (GraphState): Graph state

    Returns:
        Dict[str, List]: Updates to the graph state
    """
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)
    # We return a list, because this will get added to the existing list
    return {"messages": [response]}

# Convert tools into a graph node
tool_node = ToolNode(tools)



# Parameterize the graph with the state
graph = StateGraph(GraphState)
# Add graph nodes
graph.add_node("agent", agent)
graph.add_node("tools", tool_node)
# Add graph edges
graph.add_edge(START, "agent")
graph.add_edge("tools", "agent")
graph.add_conditional_edges(
    "agent",
    tools_condition,
    {"tools": "tools", END: END},
)












#app routing
@app.route("/")
def index():
    # Redirect to the homepage
    return redirect(url_for("homepage"))


@app.route("/homepage")
def homepage():
    return {"message": "Welcome to the Homepage!"}


@app.route("/members")
def members():
    return {"members": ["Member1", "Member2", "Member3"]}


@app.route("/save_input", methods=["POST", "GET"])
def save_input():
    data = request.get_json()
    input_value = data.get("input")


    sender = data.get("sender", "user")  # Default to 'user' if not provided
    userId = data.get("userId", -1)
    convoId = data.get("conversationId", -1)
    timestamp = data.get("timestamp", datetime.now().strftime("%m/%d/%Y %H:%M:%S"))
    if input_value:
        inputs.append(input_value)
        print(f"Input received: {input_value}")
        # For demonstration, print the inputs to the console
        print(inputs)
        
        #let's add the first message to the database
        db = client["chat_database"]
        #if we went through the homepage without a convoId, we will create a new convo
        if convoId == -1 and userId != -1:
            latest_convo = db.conversations.find_one(
                {"userId": userId},
                sort=[("timestamp", DESCENDING)],
                projection={"conversationId": 1}
            )
            if latest_convo:
                convoId = latest_convo.get("conversationId") + 1
            db["conversations"].insert_one({
                "name": input_value,
                "userId": userId,
                "conversationId": convoId,
                "timestamp": timestamp
            })
            
        if userId != -1: #keeps the conversationId at -1 if userId is -1
            db["messages"].insert_one({
                "message": input_value,
                "sender": sender,
                "userId": userId,
                "conversationId": convoId,
                "timestamp": timestamp
            })
        

        #we now handle the bot messaging
        chatResponse = run_sabine_chatbot(question = input_value, conversationId= convoId)
        db["messages"].insert_one({
            "message": chatResponse,
            "sender": "bot",
            "userId": userId,
            "conversationId": convoId,
            "timestamp": timestamp
        })
        
        
        # Save the input to a file (optional)
        return jsonify({"message": "Input saved successfully!", "inputs": inputs, "convoId": convoId, "chatbot_response": chatResponse}), 200
    return jsonify({"error": "Invalid input"}), 400


@app.route("/get_messages", methods=["POST"])
def get_messages():
    print("attempting to retrieve messages")
    data = request.get_json()
    userId = data.get("userId")
    convoId = data.get("conversationId", -1)
    db = client["chat_database"]
    
    if convoId == -1:
    # Sort by timestamp ascending (oldest first)
        latest_convo = db.conversations.find_one(
            {"userId": userId },
            sort=[("timestamp", DESCENDING)]
        )
        print("conversation found")
        if latest_convo:
            convoId = latest_convo.get("conversationId")
            chat = db.messages.find(
                {"conversationId": convoId, "userId": userId}
            ).sort("timestamp", 1)
            print("conversationId: ", convoId)
            messages = []
            for message in chat:
                messages.append({
                    "sender": message.get("sender", "user"),
                    "text": message.get("message", ""),
                    "time": message.get("timestamp", "")
                })
            return jsonify({"messages": messages, "convoId": convoId}), 200
        else:
            return jsonify({"error": "No conversations found for this user", "convoId": 1}), 404
    else:
        chat = db.messages.find(
            {"conversationId": convoId, "userId": userId}
        ).sort("timestamp", 1)
        messages = []
        for message in chat:
            messages.append({
                "sender": message.get("sender", "user"),
                "text": message.get("message", ""),
                "time": message.get("timestamp", "")
            })
        return jsonify({"messages": messages, "convoId": convoId}), 200

@app.route("/get_conversations", methods=["POST"])
def get_conversations():
    print("attempting to retrieve conversations")
    data = request.get_json()
    userId = data.get("userId")
    db = client["chat_database"]
    # Sort by timestamp ascending (oldest first)
    conversations = db.conversations.find(
        {"userId": userId}
    ).sort("timestamp", 1)
    
    convo_list = []
    for convo in conversations:
        convo_list.append({
            "name": convo.get("name"),
            "conversationId": convo.get("conversationId"),
            "timestamp": convo.get("timestamp")
        })
    
    if convo_list:
        return jsonify({"conversations": convo_list}), 200
    else:
        return jsonify({"error": "No conversations found for this user"}), 404
    
    
    
@app.route("/new_conversation", methods=["POST"])
def new_conversation():
    print("attempting to create a new conversation")
    data = request.get_json()
    userId = data.get("userId")
    timestamp = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
    
    if not userId:
        return jsonify({"error": "User ID is required"}), 400
    
    db = client["chat_database"]
    
    latest_convo = db.conversations.find_one(
        {"userId": userId},
        sort=[("timestamp", DESCENDING)],
        projection={"conversationId": 1}
    )
    if latest_convo:
        convoId = latest_convo.get("conversationId") + 1
    else:
        convoId = 1
    convoName = "new chat " + str(convoId)

        
    # Create a new conversation
    convoId = db.conversations.count_documents({"userId": userId}) + 1
    db.conversations.insert_one({
        "name": convoName,
        "userId": userId,
        "conversationId": convoId,
        "timestamp": timestamp
    })
    print("New conversation created with ID:", convoId)
    return jsonify({"message": "New conversation created successfully", "conversationId": convoId}), 201


@app.route("/rename_conversation", methods=["POST"])
def rename_conversation():
    print("attempting to rename conversation")
    data = request.get_json()
    userId = data.get("userId")
    conversationId = data.get("conversationId")
    newTitle = data.get("title")
    db = client["chat_database"]

    if not userId or not conversationId or not newTitle:
        return jsonify({"error": "User ID, conversation ID, and new title are required"}), 400

    result = db.conversations.update_one(
        {"userId": userId, "conversationId": conversationId},
        {"$set": {"name": newTitle}}
    )

    if result.modified_count > 0:
        print("Conversation renamed successfully")
        return jsonify({"message": "Conversation renamed successfully"}), 200
    else:
        print("Failed to rename conversation")
        return jsonify({"error": "Failed to rename conversation"}), 400
    

@app.route("/delete_conversation", methods=["POST"])
def delete_conversation():
    print("attempting to delete conversation")
    data = request.get_json()
    userId = data.get("userId")
    conversationId = data.get("conversationId")
    db = client["chat_database"]

    if not userId or not conversationId:
        return jsonify({"error": "User ID and conversation ID are required"}), 400

    # Delete from conversations
    result = db.conversations.delete_one({"userId": userId, "conversationId": conversationId})
    # Delete all messages for this conversation
    db.messages.delete_many({"userId": userId, "conversationId": conversationId})

    # Also delete from sabine.checkpoints where thread_id == conversationId
    sabine_db = client["sabine"]
    checkpoints_collection = sabine_db["checkpoints"]
    checkpoint_result = checkpoints_collection.delete_many({"thread_id": conversationId})

    if result.deleted_count > 0:
        print(f"Conversation deleted successfully. Also deleted {checkpoint_result.deleted_count} checkpoint(s) for thread_id {conversationId}.")
        return jsonify({"message": "Conversation and related checkpoints deleted successfully"}), 200
    else:
        print("Failed to delete conversation")
        return jsonify({"error": "Failed to delete conversation"}), 400
    
    

@app.route("/login", methods=["POST"])
def login():
    print("attempting to login")
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    print("data received!: ", data)
    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400
    #hash the password for security
    ph = PasswordHasher(
        time_cost=2,  # Time cost for hashing
        memory_cost=2**16,  # Memory cost in KB
        parallelism=1,  # Number of parallel threads
        hash_len=32,  # Length of the hash
        salt_len=16  # Length of the salt
    )

    # Fetch the user from the database
    cur.execute("SELECT * FROM user_accounts WHERE username = %s", (username,))
    user = cur.fetchone()
    print("user fetched: ", user)
    if user:
        if ph.verify(user[2], password):
            
            print("Login successful")
            return jsonify({"message": "Login successful", "userId": user[0]}), 200
        else:
            print("Invalid password")
            return jsonify({"error": "Invalid password"}), 401
    else:
        print("User not found")
        return jsonify({"error": "User not found"}), 404



@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    
    #hash the password for security
    ph = PasswordHasher(
        time_cost=2,  # Time cost for hashing
        memory_cost=2**16,  # Memory cost in KB
        parallelism=1,  # Number of parallel threads
        hash_len=32,  # Length of the hash
        salt_len=16  # Length of the salt
    )
    hashed_password = ph.hash(password)

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    # Check for existing user
    print("Checking for existing user")
    cur.execute("SELECT * FROM user_accounts WHERE username = %s", (username,))
    existing_user = cur.fetchone()
    if existing_user:
        print("User already exists")
        return jsonify({"error": "User already exists", "userId": existing_user[0]}), 400
    print("No existing user found, creating new user")
    # Create new user
    # must get a user ID
    cur.execute("SELECT userId FROM user_accounts ORDER BY userId DESC LIMIT 1;")
    userId = cur.fetchone()[0]
    userId += 1
    cur.execute("INSERT INTO user_accounts (userId, username, password_hash) VALUES (%s, %s, %s);", (userId, username, hashed_password))
    conn.commit()
    print(f"User created with ID: {userId}")
    login()
    return jsonify({"message": "User created successfully", "userId": userId}), 201



def run_sabine_chatbot(question, conversationId):
    """
    Main function to interact with the Sabine chatbot.
    """
    #chatbot response
    
    config = {"configurable": {"thread_id": conversationId}}
    # Execute the agent and view outputs
    inputs = {
        "messages": [
            ("user", question),
        ]
    }
    final_output = None
    

    try:
        with MongoDBSaver.from_conn_string(MONGODB_URI, db_name = "sabine", collection_name = "checkpoints") as checkpointer:
            # Compile the graph
            chatbot = graph.compile(checkpointer = checkpointer)
            for output in chatbot.stream(inputs,  config=config):
                final_output = output  # Only keep the last output

        if final_output:
            for key, value in final_output.items():
                print(f"Node {key}:")
                print(value)
            print("---FINAL ANSWER---")
            print(value["messages"][-1].content)
        # Format the response to preserve line breaks for frontend display
        response = None
        if isinstance(value, dict) and "messages" in value and isinstance(value["messages"], list) and value["messages"]:
            response = value["messages"][-1].content
        else:
            response = "Sorry, I couldn't generate a response."

        # Return markdown as-is for frontend markdown rendering
        return response
    except openai.RateLimitError as e:
        # Handle OpenAI rate limit or token limit errors
        print("OpenAI RateLimitError:", e)
        # Try to extract a helpful message
        try:
            error_json = e.response.json() if hasattr(e, 'response') and e.response else None
            if error_json and 'error' in error_json and 'message' in error_json['error']:
                msg = error_json['error']['message']
            else:
                msg = str(e)
        except Exception:
            msg = str(e)
        # Custom message for token limit
        if 'tokens per min' in msg or 'Request too large' in msg:
            return "Sorry, your request is too large for the current model's token limit. Please shorten your input or ask for a smaller output."
        return f"OpenAI Rate Limit Error: {msg}"
    except Exception as e:
        print("Error in run_sabine_chatbot:", e)
        return f"Sorry, an error occurred: {str(e)}"
    


if __name__ == "__main__":
    app.run(debug=True, host = '0.0.0.0', port = 5000)


cur.close()
conn.close()
client.close()