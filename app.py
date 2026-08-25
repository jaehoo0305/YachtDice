import random
from flask import Flask, render_template, jsonify
from pymongo import MongoClient

app = Flask(__name__)
client = MongoClient('mongodb://localhost:27017/')
db = client['yacht_dice']
users_collection = db['users']

@app.route('/')
def home():
    return render_template('Lobby.html')

@app.route('/api/roll', methods=['get'])
def roll_dice():
    dice_results1 = [random.randint(1, 6) for i in range(5)]
    return jsonify({
        'result': 'success',
        'dice': dice_results1
    })
 
if __name__ == '__main__':
    app.run(debug=True, port=5000)

    # <script>
    #     async function rollDice() {
    #         const response = await fetch('/api/roll', {
    #             method: 'get'
    #         });
    #         const data = await response.json();
    #         if (data.result === 'success') {
    #             console.log('주사위 결과:', data.dice);
    #             // for(let i = 0; i < 5; i++) 
    #             document.getElementById('dice-result1').innerText = data.dice[0];
    #             document.getElementById('dice-result2').innerText = data.dice[1];
    #             document.getElementById('dice-result3').innerText = data.dice[2];
    #             document.getElementById('dice-result4').innerText = data.dice[3];
    #             document.getElementById('dice-result5').innerText = data.dice[4];
    #         }
    #     }
    # </script>
