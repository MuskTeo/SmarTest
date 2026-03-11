from flask import Flask
from api_routes import api
from flask_cors import CORS

app = Flask(__name__)
CORS(app) 
app.register_blueprint(api)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
