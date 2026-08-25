import random
from flask import Flask, render_template, jsonify, request
from pymongo import MongoClient

app = Flask(__name__)
client = MongoClient('mongodb://localhost:27017/')
db = client['yacht_dice']
users_collection = db['users']

@app.route('/')
def home():
    return render_template('Lobby.html')

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
    return jsonify({'result': 'success', 'dicelist': new_dicelist})

# async function rollDice() {
#   const res = await fetch('/api/roll', { method: 'POST' });
#   const data = await res.json();
  
#   console.log(data.dicelist); 
# }
 
if __name__ == '__main__':
    app.run(debug=True, port=5000)