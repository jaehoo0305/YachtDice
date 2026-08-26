import random, jwt, hashlib, datetime, bcrypt
from functools import wraps
from flask import Flask, render_template, jsonify, request, redirect, make_response
from pymongo import MongoClient
from flask_cors import CORS

app = Flask(__name__)
SECRET_KEY = 'YACHT_DICE_SECRET_KEY_2008'
client = MongoClient('mongodb+srv://grooochyjeff1234_db_user:iphxS3QU5dlNzI3z@cluster0.dkuz0fy.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = client['yacht_dice']
users_collection = db['users']
CORS(app)

def calculate_win_rate(wins, losses):
    total = wins + losses
    return round((wins / total) * 100, 1) if total > 0 else 0

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get('userToken')

        if not token:
            return redirect('/')
        
        try:
            jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            resp = make_response(redirect('/'))
            resp.delete_cookie('userToken')
            return resp
        
        return f(*args, **kwargs)
    
    return decorated_function

@app.route('/')
def home():
    token = request.cookies.get('userToken')
    if token:
        try:
            jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            return redirect('/room')
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            pass
    return render_template('Lobby.html')

@app.route('/room')
@login_required
def room():
    token = request.cookies.get('userToken')
    payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    user_id = payload['userId']
    
    user = users_collection.find_one({'userId': user_id})
    wins = user.get('wins', 0)
    losses = user.get('losses', 0)
    
    total_games = wins + losses
    win_rate = round((wins / total_games) * 100, 1) if total_games > 0 else 0

    return render_template('Room.html', 
                           username=user_id, 
                           wins=wins, 
                           losses=losses, 
                           win_rate=win_rate)

@app.route('/game')
@login_required  # 추가
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
    users_collection.insert_one(
    {
        'userId': user_id,
        'userPw': hashed_pw,
        'wins': 0,
        'losses': 0
    })

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
        'exp': datetime.datetime.now() + datetime.timedelta(days=7)
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

    resp = make_response(jsonify({'result': 'success', 'message': '로그인 성공!'}))
    resp.set_cookie('userToken', token, max_age=60 * 60 * 24 * 7, httponly=True)
    return resp

@app.route('/api/verify', methods=['POST'])
def verify_token():
    data = request.get_json()
    token = data.get('token')

    if not token:
        return jsonify({'result': 'fail', 'message': '토큰이 없습니다.'})

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        
        return jsonify(
        {
            'result': 'success',
            'userId': payload['userId'],
            'message': '인증 성공'
        })

    except jwt.ExpiredSignatureError:
        return jsonify({'result': 'fail', 'message': '토큰이 만료되었습니다.'})

    except jwt.InvalidTokenError:
        return jsonify({'result': 'fail', 'message': '유효하지 않은 토큰입니다.'})

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