from flask import Flask
from routes import routes

app = Flask(__name__)

# Register routes
app.register_blueprint(routes)

@app.route("/", methods=["GET"])
def health_check():
    """Check if the API is running."""
    return {"message": "API is running"}

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
