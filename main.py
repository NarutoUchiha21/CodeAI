from app import app  # noqa: F401

if __name__ == "__main__":
    # Start the Flask app
    app.run(host="0.0.0.0", port=5000, debug=True)
