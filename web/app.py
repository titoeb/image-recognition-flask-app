from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt
import requests
import subprocess
import json

# Set-up App
app = Flask(__name__)
api = Api(app)

# Initiallize db connection
client = MongoClient("mongodb://db:27017")
db = client.ImageRecognition
users = db["users"]

# Helper functions
def user_exists(username: str) -> bool:
    return users.find({"Username":username}).count() > 0

def correct_password(username:str, password: str) -> bool:
    if not user_exists(username):
        return False

    hashed_pw = users.find({
        "Username": username
        })[0]["Password"]

    return bcrypt.hashpw(password.encode("utf8"), hashed_pw) == hashed_pw

def count_tokens(username:str) -> bool:
    return users.find({
        "Username": username
        })[0]["Tokens"]

class Register(Resource):
    def post(self):
        postedData = request.get_json()

        # Parse inputs
        username = postedData["username"]
        password = postedData["password"]
        
        if user_exists(username):
            return(jsonify({
                "status": 301,
                "msg": "Invalid Username"
                }))

        # Hash user password
        hashed_password = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())

        # Store the user data into the database.
        users.insert({
            "Username": username,
            "Password": hashed_password,
            "Tokens": 6,
        })

        return(jsonify({
                "status": 200,
                "msg": "User was sucessfully created"
        }))

class Classify(Resource):
    def post(self):
        postedData = request.get_json()
        
        # Parse inputs
        username = postedData["username"]
        password = postedData["password"]
        url = postedData["url"]

        if not user_exists(username):
            return(jsonify({
                    "status": 301,
                    "msg": "The user does not exist."
                }))

        if not correct_password(username, password):
            return(jsonify({
                    "status": 302,
                    "msg": "The password is wrong!"
                    }))

        number_tokens = count_tokens(username)
        if number_tokens <= 0:
            return(jsonify({
                    "status": 303,
                    "msg": "You don't have sufficient tokens!"
                }))

        # Download the image
        this_request = requests.get(url)
        with open("/usr/web/tmp.jpg", "wb") as file_handler:
            file_handler.write(this_request.content)
    
        # Classify the image
        proc = subprocess.Popen('/usr/local/bin/python /usr/web/classify_image.py --model_dir=/usr/web/ --image_file=/usr/web/tmp.jpg', shell=True)
        proc.communicate()[0]
        proc.wait()
        print(proc.stdout)
        print(proc.stderr)
        with open("prediction_results.json") as file_handler:
            results_classification = json.load(file_handler)

        # Reduce the number of tokens for the user
        users.update({
            "Username": username
            }, {"$set":{
                "Tokens": number_tokens-1
                }
            })

        # Return information to user
        return(jsonify({ **results_classification, **{
             "status": 200,
             "msg": "Similarity score calculated"
            }}))

class Refill(Resource):
    def post(self):
        postedData = request.get_json()
        
        username = postedData["username"]
        admin_password = postedData["admin_password"]
        refill_amount = postedData["refill_amount"]

        if not user_exists(username):
            return(jsonify({
                        "status": 301,
                        "msg": "Invalid Username"
                    }))

        # This pw should be hashed and stored in the database
        # But for the sake of time let's do it this way:
        if not admin_password == "admin":
            return(jsonify({
                    "status": 304,
                    "msg": "Invalid admin password"
                }))

        current_tokens = count_tokens(username)
        users.update({
                "Username": username,
                },{
                    "$set": {
                            "Tokens": refill_amount + current_tokens
                        }
            })
        message = f"Congratulations, you now have {count_tokens(username)} Tokens!"
        return(jsonify({
                "status": 200, 
                "msg": message
            }))

api.add_resource(Register, "/register")
api.add_resource(Classify, "/classify")
api.add_resource(Refill, "/refill")

if __name__ == "__main__":
    	app.run(debug=True)

