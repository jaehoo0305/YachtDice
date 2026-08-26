import random, jwt, hashlib, datetime
from flask import Flask, render_template, jsonify, request
from pymongo import MongoClient
from flask_cors import CORS

app = Flask(__name__)
client = MongoClient('mongodb+srv://grooochyjeff1234_db_user:iphxS3QU5dlnZi3z@cluster0.dkuz0fy.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = client['yacht_dice']
users_collection = db['users']
CORS(app)

@app.route('/')
def home():
    return render_template('Lobby.html')

@app.route('/game')
def Game():
    return render_template('Game.html')

@app.route('/api/roll', methods=['post'])
def roll_dice():
    holdval = request.get_json()
    getdice = holdval.get('dicelist', [])
    new_dicelist = []
    for i in range(5):
        if i < len(getdice) and getdice[i].get('hold') == True:
            new_dicelist.append({
                'val': getdice[i].get('val'),
                'hold': True
                })
        else:
            new_dicelist.append({
                'val': random.randint(1, 6),
                'hold': False
                }) 
    combolist =[]
    if(new_dicelist[i]==1):
        combolist.append({
            'yacht':True
        })
    else:
        combolist.append({
            'yacht':False
        })
    return jsonify({'combo':combolist, 'result': 'success', 'dicelist': new_dicelist})

if __name__ == '__main__':
    app.run(debug=True, port=5000)