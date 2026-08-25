import random
from flask import Flask, render_template, jsonify
from pymongo import MongoClient

app = Flask(__name__)
client = MongoClient('mongodb+srv://grooochyjeff1234_db_user:iphxS3QU5dlnZi3z@cluster0.dkuz0fy.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = client['yacht_dice']
users_collection = db['users']

@app.route('/')
def home():
    return render_template('Lobby.html')

@app.route('/api/roll', methods=['post'])
def roll_dice():
    dicelist = [random.randint(1, 6)for i in range(5)]

    return jsonify({
        'result': 'success',
        'dicelist': [{'val':dicelist[0], 'hold':False},
                     {'val':dicelist[1], 'hold':False},
                     {'val':dicelist[2], 'hold':False},
                     {'val':dicelist[3], 'hold':False},
                     {'val':dicelist[4], 'hold':False}]
    })

# async function rollDice() {
#   const res = await fetch('/api/roll', { method: 'POST' });
#   const data = await res.json();
  
#   console.log(data.dicelist); 
# }
 
if __name__ == '__main__':
    app.run(debug=True, port=5000)