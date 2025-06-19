from flask import Flask, redirect, url_for, request, jsonify
from flask_cors import CORS
from datetime import datetime
import psycopg2
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


#messages database connection
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://ryanjewik:Happyrhino8@cluster0.0drkzoy.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
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
    timestamp = data.get("timestamp", datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    if input_value:
        inputs.append(input_value)
        print(f"Input received: {input_value}")
        # For demonstration, print the inputs to the console
        print(inputs)
        
        #let's add the first message to the database
        db = client["chat_database"]
        now = datetime.now()
        #currently saves the message, sender, and the timestamp
        #will need to separate them into separate chats per user
        db['chatzero'].insert_one({
            "message": input_value,
            "sender": sender,
            "timestamp": timestamp
        })
        
        chatzero = db.chatzero.find()
        for message in chatzero:
            print(f"Message: {message['message']}, Sender: {message['sender']}, Timestamp: {message['timestamp']}")
        
        # Save the input to a file (optional)
        return jsonify({"message": "Input saved successfully!", "inputs": inputs}), 200
    return jsonify({"error": "Invalid input"}), 400


@app.route("/get_messages", methods=["GET"])
def get_messages():
    db = client["chat_database"]
    # Sort by timestamp ascending (oldest first)
    chatzero = db.chatzero.find().sort("timestamp", 1)
    messages = []
    for message in chatzero:
        messages.append({
            "sender": message.get("sender", "user"),
            "text": message.get("message", ""),
            "time": message.get("timestamp", "")
        })
    return jsonify({"messages": messages}), 200



@app.route("/login", methods=["POST"])
def login():
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

    # Fetch the user from the database
    cur.execute("SELECT * FROM user_accounts WHERE username = %s", (username,))
    user = cur.fetchone()

    if user:
        if hashed_password == user['password_hash']:
            confirmation = True
            return jsonify({"message": "Login successful", "confirmation": confirmation}), 200
        else:
            return jsonify({"error": "Invalid password"}), 401
    else:
        confirmation = False
        return jsonify({"error": "User not found", "confirmation": confirmation}), 404



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
    cur.execute("SELECT * FROM user_accounts WHERE username = %s", (username,))
    existing_user = cur.fetchone()
    if existing_user:
        confirmation = False
        return jsonify({"error": "User already exists", "confirmation": confirmation}), 400
    # Create new user
    cur.execute("INSERT INTO user_accounts (username, password) VALUES (%s, %s)", (username, hashed_password))
    conn.commit()
    confirmation = True
    login()
    return jsonify({"message": "User created successfully", "confirmation": confirmation}), 201


if __name__ == "__main__":
    app.run(debug=True)


