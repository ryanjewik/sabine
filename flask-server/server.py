from flask import Flask, redirect, url_for, request, jsonify
from flask_cors import CORS
from datetime import datetime
import psycopg2
from pymongo import DESCENDING
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

#BACKEND FILE

app = Flask(__name__)
CORS(app)

# Array to store inputs
inputs = []


#user database connection
try:
    conn = psycopg2.connect(
        database="user accounts",
        user="postgres",
        password="Happyrhino8!",
        host="localhost",
        port=5432
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

uri = ""
client = MongoClient(uri, server_api=ServerApi('1'))
# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)
    
db = client["chat_database"]
chatzero = db.get_collection("chatzero")




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
            
        if userId != -1:
            db["messages"].insert_one({
                "message": input_value,
                "sender": sender,
                "userId": userId,
                "conversationId": convoId,
                "timestamp": timestamp
            })
        
        chatzero = db.chatzero.find()
        for message in chatzero:
            print(f"Message: {message['message']}, Sender: {message['sender']}, Timestamp: {message['timestamp']}")
        
        # Save the input to a file (optional)
        return jsonify({"message": "Input saved successfully!", "inputs": inputs, "convoId": convoId}), 200
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


if __name__ == "__main__":
    app.run(debug=True)


cur.close()
conn.close()
client.close()