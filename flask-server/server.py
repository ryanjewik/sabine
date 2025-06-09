from flask import Flask, redirect, url_for

#BACKEND FILE

app = Flask(__name__)


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

if __name__ == "__main__":
    app.run(debug=True)