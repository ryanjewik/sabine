from flask import Flask, redirect, url_for, request, jsonify
from flask_cors import CORS
from datetime import datetime

#BACKEND FILE

app = Flask(__name__)
CORS(app)

# Array to store inputs
inputs = []


#database connection
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


if __name__ == "__main__":
    app.run(debug=True)


