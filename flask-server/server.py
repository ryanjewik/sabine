from flask import Flask, redirect, url_for, request, jsonify
from flask_cors import CORS

#BACKEND FILE

app = Flask(__name__)
CORS(app)

# Array to store inputs
inputs = []


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
    if input_value:
        inputs.append(input_value)
        print(f"Input received: {input_value}")
        # For demonstration, print the inputs to the console
        print(inputs)
        # Save the input to a file (optional)
        return jsonify({"message": "Input saved successfully!", "inputs": inputs}), 200
    return jsonify({"error": "Invalid input"}), 400


if __name__ == "__main__":
    app.run(debug=True)