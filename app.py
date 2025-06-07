from flask import Flask, request, jsonify
from flask_cors import CORS
#import xrpl_utilities

app = Flask(__name__)
CORS(app)


#login
@app.route("/api/login", methods=['POST'])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    
    if username == "test" and password == "test":
        return jsonify({'message': 'nice'}), 200
    else:
        return jsonify({'message': 'lol'}), 401
    
    """
    if database.validate_user_login(username, password):
            payload = {
            'username': username,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        return jsonify({'token': token})
    else:
        return jsonify({'error': 'Invalid credentials'}), 401
    """

# @app.route("/api/summarize_trustlines")
# def summarize():
#     address = request.args.get("address")
#     summary = xrpl_utilities.TrustLineAnalytics.summarize_trustlines(address)
#     return jsonify(summary)

if __name__ == "__main__":
    app.run(debug=True)