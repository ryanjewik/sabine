from flask import Flask, redirect, url_for, request, jsonify
from flask_cors import CORS
from datetime import datetime
import psycopg2
import time
import os
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
from langgraph.checkpoint.mongodb import MongoDBSaver
import openai
from dotenv import load_dotenv
import traceback




#BACKEND FILE

app = Flask(__name__)
CORS(app, origins=[
    "https://sabinechat.com",
    "https://www.sabinechat.com"
], supports_credentials=True)


# Array to store inputs
inputs = []


load_dotenv()  # This will look for .env in current directory or parent directories

#user database connection with retry mechanism
def connect_to_database(max_retries=30, delay=2):
    """
    Attempt to connect to the database with retry logic
    """
    for attempt in range(max_retries):
        try:
            print(f"Attempting to connect to database (attempt {attempt + 1}/{max_retries}):")
            print(f"  Host: {os.getenv('DB_HOST')}")
            print(f"  Database: {os.getenv('DB_NAME')}")
            print(f"  User: {os.getenv('DB_USERNAME')}")
            print(f"  Port: {os.getenv('DB_PORT')}")
            
            conn = psycopg2.connect(
                database=os.getenv("DB_NAME"),
                user=os.getenv("DB_USERNAME"),
                password=os.getenv("DB_PASSWORD"),
                host=os.getenv("DB_HOST"),
                port=os.getenv("DB_PORT")
            )
            print("✅ Database connection successful!")
            return conn
        except Exception as e:
            print(f"❌ Error connecting to the database (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                print(f"⏳ Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print(f"💀 Failed to connect to database after {max_retries} attempts")
                raise e

def get_db_connection():
    """
    Get a database connection, reconnecting if necessary
    """
    global conn, cur
    try:
        # Check if connection exists and is working
        if conn and not conn.closed:
            cur.execute("SELECT 1")  # Test query
            return conn, cur
    except (psycopg2.OperationalError, psycopg2.InterfaceError, AttributeError):
        print("🔄 Database connection lost, reconnecting...")
    
    # Reconnect
    try:
        conn = connect_to_database()
        cur = conn.cursor()
        return conn, cur
    except Exception as e:
        print(f"❌ Failed to reconnect to database: {e}")
        return None, None

try:
    conn = connect_to_database()
    cur = conn.cursor()
except Exception as e:
    print("❌ Failed to establish database connection:", e)
    conn = None
    cur = None
# Check if the connection was successful 
if conn and cur:
    print("Connected to the user accounts database successfully!")
    try:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS user_accounts (
            userid SERIAL PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        )
        """)
        conn.commit()
        print("✅ User accounts table is ready.")
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        conn.rollback()
else:
    print("⚠️ Database connection not available - some features will be disabled")


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












# Health check endpoint for testing connectivity
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "Server is running!"}), 200

@app.route("/api/debug/db", methods=["GET"])
def debug_database():
    """Debug endpoint to inspect database connection and user accounts"""
    try:
        # Get fresh database connection
        db_conn, db_cur = get_db_connection()
        if not db_conn or not db_cur:
            return jsonify({"error": "Database connection not available"}), 503
            
        # Test the connection
        db_cur.execute("SELECT 1")
        
        # Get database connection info
        db_cur.execute("SELECT current_database(), current_user, version();")
        db_info = db_cur.fetchone()
        
        # Get all user accounts
        db_cur.execute("SELECT userid, username, password_hash FROM user_accounts ORDER BY userid;")
        users = db_cur.fetchall()
        
        # Get table info
        db_cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
        tables = db_cur.fetchall()
        
        debug_info = {
            "connection_status": "connected",
            "database_info": {
                "database": db_info[0],
                "user": db_info[1],
                "version": db_info[2]
            },
            "environment_variables": {
                "DB_NAME": os.getenv("DB_NAME"),
                "DB_USERNAME": os.getenv("DB_USERNAME"),
                "DB_HOST": os.getenv("DB_HOST"),
                "DB_PORT": os.getenv("DB_PORT"),
                "DB_PASSWORD": "***" if os.getenv("DB_PASSWORD") else None
            },
            "tables": [table[0] for table in tables],
            "user_accounts": [
                {
                    "id": user[0],
                    "username": user[1],
                    "password_hash": user[2][:20] + "..." if user[2] else None
                } for user in users
            ],
            "total_users": len(users)
        }
        
        return jsonify(debug_info), 200
        
    except Exception as e:
        return jsonify({
            "error": "Database debug failed",
            "message": str(e),
            "connection_status": "error"
        }), 500
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


@app.route("/api/save_input", methods=["POST", "GET"])
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


@app.route("/api/get_messages", methods=["POST"])
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

@app.route("/api/get_conversations", methods=["POST"])
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
    


@app.route("/api/new_conversation", methods=["POST"])
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


@app.route("/api/rename_conversation", methods=["POST"])
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
    

@app.route("/api/delete_conversation", methods=["POST"])
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
    
    

@app.route("/api/login", methods=["POST"])
def login():
    print("=== LOGIN ENDPOINT HIT ===")
    print("attempting to login")
    
    data = request.get_json()
    print("Raw request data:", data)
    username = data.get("username") if data else None
    password = data.get("password") if data else None
    print("Extracted username:", username, "password length:", len(password) if password else 0)
    
    if not username or not password:
        print("Missing username or password")
        return jsonify({"error": "Username and password are required"}), 400
    
    # Get fresh database connection
    db_conn, db_cur = get_db_connection()
    if not db_conn or not db_cur:
        print("❌ Database connection not available")
        return jsonify({"error": "Database connection unavailable"}), 503
    
    try:
        # Ensure we're in a clean transaction state
        db_conn.rollback()
        
        #hash the password for security
        ph = PasswordHasher(
            time_cost=2,  # Time cost for hashing
            memory_cost=2**16,  # Memory cost in KB
            parallelism=1,  # Number of parallel threads
            hash_len=32,  # Length of the hash
            salt_len=16  # Length of the salt
        )

        # Fetch the user from the database
        db_cur.execute("SELECT userid, username, password_hash FROM user_accounts WHERE username = %s", (username,))
        user = db_cur.fetchone()
        print("user fetched: ", user)
        
        if user:
            user_id, db_username, password_hash = user
            if ph.verify(password_hash, password):
                print("Login successful")
                db_conn.commit()
                return jsonify({"message": "Login successful", "userId": user_id}), 200
            else:
                print("Invalid password")
                db_conn.rollback()
                return jsonify({"error": "Invalid password"}), 401
        else:
            print("User not found")
            db_conn.rollback()
            return jsonify({"error": "User not found"}), 401
            
    except Exception as e:
        print(f"Error in login: {e}")
        try:
            db_conn.rollback()
        except:
            pass  # Connection might be closed
        return jsonify({"error": "Database error occurred"}), 500



@app.route("/api/signup", methods=["POST"])
def signup():
    print("=== SIGNUP ENDPOINT HIT ===")
    print("attempting to signup")
    
    data = request.get_json()
    print("Raw request data:", data)
    username = data.get("username") if data else None
    password = data.get("password") if data else None
    print("Extracted username:", username, "password length:", len(password) if password else 0)
    
    if not username or not password:
        print("Missing username or password")
        return jsonify({"error": "Username and password are required"}), 400
    
    # Get fresh database connection
    db_conn, db_cur = get_db_connection()
    if not db_conn or not db_cur:
        print("❌ Database connection not available")
        return jsonify({"error": "Database connection unavailable"}), 503
    
    try:
        # Ensure we're in a clean transaction state
        db_conn.rollback()
        
        #hash the password for security
        ph = PasswordHasher(
            time_cost=2,  # Time cost for hashing
            memory_cost=2**16,  # Memory cost in KB
            parallelism=1,  # Number of parallel threads
            hash_len=32,  # Length of the hash
            salt_len=16  # Length of the salt
        )
        hashed_password = ph.hash(password)

        # Check for existing user
        print("Checking for existing user")
        db_cur.execute("SELECT userid FROM user_accounts WHERE username = %s", (username,))
        existing_user = db_cur.fetchone()
        if existing_user:
            print("User already exists")
            db_conn.rollback()
            return jsonify({"error": "User already exists", "userId": existing_user[0]}), 400
        
        print("No existing user found, creating new user")
        # Create new user - let PostgreSQL auto-generate the ID
        print(f"Inserting user: {username}")
        db_cur.execute("INSERT INTO user_accounts (username, password_hash) VALUES (%s, %s) RETURNING userid;", (username, hashed_password))
        userId = db_cur.fetchone()[0]
        db_conn.commit()
        print(f"✅ User created successfully with ID: {userId}")
        
        # Verify the user was created
        db_cur.execute("SELECT COUNT(*) FROM user_accounts WHERE username = %s", (username,))
        count = db_cur.fetchone()[0]
        print(f"✅ Verification: Found {count} user(s) with username '{username}'")
        
        return jsonify({"message": "User created successfully", "userId": userId}), 201
        
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        traceback.print_exc()  # Print full stack trace for debugging
        try:
            db_conn.rollback()
        except:
            pass  # Connection might be closed
        return jsonify({"error": "Failed to create user"}), 500



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
    


@app.route("/api/chat_unauthenticated", methods=["POST"])
def chat_unauthenticated():
    """Handle chat requests for unauthenticated users without saving to database"""
    data = request.get_json()
    input_value = data.get("input")
    
    if not input_value:
        return jsonify({"error": "Input is required"}), 400
    
    try:
        # Generate chatbot response using a temporary conversation ID
        # Use a negative conversation ID to indicate it's temporary/unauthenticated
        temp_conversation_id = -1
        chatbot_response = run_sabine_chatbot(question=input_value, conversationId=temp_conversation_id)
        
        return jsonify({
            "message": "Response generated successfully",
            "chatbot_response": chatbot_response
        }), 200
        
    except Exception as e:
        print(f"Error in chat_unauthenticated: {e}")
        return jsonify({"error": "Failed to generate response"}), 500

@app.route("/api/debug/repair-sequence", methods=["POST"])
def repair_sequence():
    """Repair the userid sequence to match the actual maximum ID in the table"""
    try:
        # Get fresh database connection
        db_conn, db_cur = get_db_connection()
        if not db_conn or not db_cur:
            return jsonify({"error": "Database connection not available"}), 503
        
        # Get the current maximum userid
        db_cur.execute("SELECT MAX(userid) FROM user_accounts;")
        max_id = db_cur.fetchone()[0]
        max_id = max_id if max_id is not None else 0
        
        # Reset the sequence to the next available ID
        next_id = max_id + 1
        db_cur.execute(f"SELECT setval('user_accounts_userid_seq', {next_id});")
        db_conn.commit()
        
        # Verify the sequence
        db_cur.execute("SELECT last_value FROM user_accounts_userid_seq;")
        current_seq = db_cur.fetchone()[0]
        
        return jsonify({
            "message": "Sequence repaired successfully",
            "max_userid": max_id,
            "sequence_value": current_seq
        }), 200
        
    except Exception as e:
        print(f"❌ Error repairing sequence: {e}")
        traceback.print_exc()
        try:
            db_conn.rollback()
        except:
            pass
        return jsonify({"error": "Failed to repair sequence", "details": str(e)}), 500

if __name__ == "__main__":
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    finally:
        # Close connections when the app shuts down
        if 'cur' in globals() and cur:
            cur.close()
        if 'conn' in globals() and conn:
            conn.close()
        if 'client' in globals() and client:
            client.close()