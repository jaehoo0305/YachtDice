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

def calculate_yacht_scores(dice_values):
    counts = {i: dice_values.count(i) for i in range(1, 7)}
    unique_vals = set(dice_values)
    total_sum = sum(dice_values)
    
    scores = {
        'aces': counts[1] * 1,
        'deuces': counts[2] * 2,
        'threes': counts[3] * 3,
        'fours': counts[4] * 4,
        'fives': counts[5] * 5,
        'sixes': counts[6] * 6,
        'choice': total_sum,
        '4_of_a_kind': total_sum if any(cnt >= 4 for cnt in counts.values()) else 0,
        'full_house': total_sum if (3 in counts.values() and 2 in counts.values()) or list(counts.values()).count(5) == 1 else 0,
        'small_straight': 15 if {1,2,3,4}.issubset(unique_vals) or {2,3,4,5}.issubset(unique_vals) or {3,4,5,6}.issubset(unique_vals) else 0,
        'large_straight': 30 if unique_vals in [{1,2,3,4,5}, {2,3,4,5,6}] else 0,
        'yacht': 50 if len(unique_vals) == 1 else 0
    }
    return scores

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

@app.route('/api/create-room', methods=['POST'])
@login_required
def create_room():
    data = request.get_json() or {}
    room_id = data.get('room_id')

    if not room_id:
        return jsonify({'result': 'fail', 'message': '방 번호를 입력해주세요.'})

    room_id = str(room_id).strip()

    existing_room = db.rooms.find_one({'room_id': room_id})
    if existing_room:
        return jsonify({'redirect_url': f'/game/{room_id}'})

    token = request.cookies.get('userToken')
    payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    host_id = payload['userId']

    db.rooms.insert_one({
        'room_id': room_id,
        'host': host_id,
        'players': [host_id],
        'status': 'waiting'
    })

    return jsonify({
        'result': 'success', 
        'message': '방이 생성되었습니다.',
        'redirect_url': f'/game/{room_id}'
    })
    

@app.route('/game/<room_id>')
@login_required
def Game(room_id):
    return render_template('Game.html', room_id=room_id)

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
        'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)
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

@app.route('/api/roll', methods=['POST'])
@login_required
def roll_dice():
    token = request.cookies.get('userToken')
    payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    current_user_id = payload['userId']

    data = request.get_json() or {}
    getdice = data.get('dicelist', [])
    new_dicelist = []

    for i in range(5):
        if i < len(getdice) and getdice[i].get('hold') is True:
            new_dicelist.append({
                'val': getdice[i].get('val'),
                'hold': True
            })
        else:
            new_dicelist.append({
                'val': random.randint(1, 6),
                'hold': False
            })

    dice_values = [d['val'] for d in new_dicelist]
    scores = calculate_yacht_scores(dice_values)

    return jsonify({
        'result': 'success',
        'userId': current_user_id,
        'dicelist': new_dicelist,
        'scores': scores
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)