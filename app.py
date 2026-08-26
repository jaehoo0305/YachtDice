import random, jwt, hashlib, datetime, bcrypt
from flask import Flask, render_template, jsonify, request
from pymongo import MongoClient
from flask_cors import CORS

app = Flask(__name__)
SECRET_KEY = 'YACHT_DICE_SECRET_KEY_2008'
client = MongoClient('mongodb+srv://grooochyjeff1234_db_user:iphxS3QU5dlNzI3z@cluster0.dkuz0fy.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = client['yacht_dice']
users_collection = db['users']
CORS(app)

@app.route('/')
def home():
    return render_template('Lobby.html')

@app.route('/room')
def room():
    return render_template('Room.html')

@app.route('/game')
def Game():
    return render_template('Game.html')

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    user_id = data.get('userId')
    user_pw = data.get('userPw')
    existing_user = users_collection.find_one({'userId': user_id})

    if not user_id or not user_pw:
        return jsonify({'result': 'fail', 'message': '아이디와 비밀번호를 모두 입력해주세요.'})

    if existing_user:
        return jsonify({'result': 'fail', 'message': '이미 존재하는 유저 아이디입니다.'})
    
    hashed_pw = bcrypt.hashpw(user_pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    users_collection.insert_one({'userId': user_id, 'userPw': hashed_pw})

    return jsonify({'result': 'success', 'message': '회원가입이 완료되었습니다.'})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user_id = data.get('userId')
    user_pw = data.get('userPw')
    existing_user = users_collection.find_one({'userId': user_id})

    if not user_id or not user_pw:
        return jsonify({'result': 'fail', 'message': '아이디와 비밀번호를 모두 입력해주세요.'})

    if not existing_user:
        return jsonify({'result': 'fail', 'message': '존재하지 않는 유저 아이디입니다.'})

    db_hashed_pw = existing_user['userPw'].encode('utf-8')
    input_pw = user_pw.encode('utf-8')

    if not bcrypt.checkpw(input_pw, db_hashed_pw):
        return jsonify({'result': 'fail', 'message': '비밀번호가 일치하지 않습니다.'})

    payload = {
        'userId': user_id,
        'exp': datetime.datetime.now() + datetime.timedelta(hours=24)
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

    return jsonify(
    {
        'result': 'success',
        'token': token,
        'message': '로그인 성공!'
    })

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