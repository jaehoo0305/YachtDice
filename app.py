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
matches_collection = db['matches']
CORS(app)

TOTAL_CATEGORIES_COUNT = 12

def calculate_player_total(player_scores):
    categories = [
        'aces', 'deuces', 'threes', 'fours', 'fives', 'sixes',
        'choice', '4_of_a_kind', 'full_house', 'small_straight', 'large_straight', 'yacht'
    ]
    upper_categories = ['aces', 'deuces', 'threes', 'fours', 'fives', 'sixes']
    
    upper_sum = sum(int(player_scores.get(cat, 0)) for cat in upper_categories if cat in player_scores)
    bonus = 35 if upper_sum >= 63 else 0
    
    total_score = sum(int(player_scores.get(cat, 0)) for cat in categories if cat in player_scores) + bonus
    return total_score, upper_sum, bonus

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
    wins = user.get('wins', 0) if user else 0
    losses = user.get('losses', 0) if user else 0
    
    total_games = wins + losses
    win_rate = round((wins / total_games) * 100, 1) if total_games > 0 else 0

    match_cursor = matches_collection.find({'players': user_id}).sort('created_at', -1).limit(20)
    records = []
    for m in match_cursor:
        players = m.get('players', [])
        scores = m.get('scores', {})
        winner = m.get('winner')
        created_at = m.get('created_at')
        
        date_str = created_at.strftime('%Y/%m/%d') if isinstance(created_at, datetime.datetime) else '최근'
        my_score = scores.get(user_id, 0)
        
        opponent_list = [p for p in players if p != user_id]
        opponent = opponent_list[0] if opponent_list else '상대'
        opp_score = scores.get(opponent, 0)

        if winner == 'draw':
            result_text = '무'
            result_class = 'draw'
        elif winner == user_id:
            result_text = '승'
            result_class = 'win'
        else:
            result_text = '패'
            result_class = 'loss'

        records.append({
            'date': date_str,
            'opponent': opponent,
            'score_text': f"{my_score} : {opp_score}",
            'result_text': result_text,
            'result_class': result_class
        })

    return render_template('Room.html', 
                           username=user_id, 
                           wins=wins, 
                           losses=losses, 
                           win_rate=win_rate,
                           records=records)

@app.route('/api/create-room', methods=['POST'])
@login_required
def create_room():
    data = request.get_json() or {}
    room_id = data.get('room_id')

    if not room_id:
        return jsonify({'result': 'fail', 'message': '방 번호를 입력해주세요.'})

    room_id = str(room_id).strip()

    token = request.cookies.get('userToken')
    payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    current_user_id = payload['userId'] 
    existing_room = db.rooms.find_one({'room_id': room_id})
    
    if existing_room:
        if current_user_id in existing_room['players']:
            return jsonify({'result': 'success', 'redirect_url': f'/game/{room_id}'})
        
        result = db.rooms.update_one(
            {
                'room_id': room_id,
                '$expr': {'$lt': [{'$size': '$players'}, 2]}
            },
            {
                '$push': {'players': current_user_id},
                '$set': {
                    'status': 'playing',
                    f'scores.{current_user_id}': {}
                }
            }
        )
        
        if result.modified_count == 0:
            return jsonify({'result': 'fail', 'message': '방이 꽉 찼습니다.'}), 400
            
        return jsonify({'result': 'success', 'redirect_url': f'/game/{room_id}'})

    db.rooms.insert_one({
        'room_id': room_id,
        'host': current_user_id,
        'players': [current_user_id],
        'status': 'waiting',
        'current_turn': current_user_id,
        'dice': [{'val': 0, 'hold': False} for _ in range(5)],
        'scores': {current_user_id: {}}
    })

    return jsonify({
        'result': 'success', 
        'message': '방이 생성되었습니다.',
        'redirect_url': f'/game/{room_id}'
    })

@app.route('/api/game-state/<room_id>', methods=['GET'])
@login_required
def get_game_state(room_id):
    token = request.cookies.get('userToken')
    payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    current_user_id = payload['userId']

    room = db.rooms.find_one({'room_id': room_id})
    if not room:
        return jsonify({'result': 'fail', 'message': '존재하지 않는 방입니다.'}), 404

    players = room.get('players', [])

    if current_user_id not in players and len(players) < 2:
        db.rooms.update_one(
            {'room_id': room_id},
            {
                '$push': {'players': current_user_id},
                '$set': {
                    'status': 'playing',
                    f'scores.{current_user_id}': {}
                }
            }
        )
        room = db.rooms.find_one({'room_id': room_id})

    return jsonify({
        'result': 'success',
        'players': room.get('players', []),
        'status': room.get('status', 'waiting'),
        'current_turn': room.get('current_turn'),
        'dice': room.get('dice', []),
        'scores': room.get('scores', {}),
        'winner': room.get('winner'),
        'final_scores': room.get('final_scores', {})
    })

@app.route('/api/select-score', methods=['POST'])
@login_required
def select_score():
    token = request.cookies.get('userToken')
    payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    current_user_id = payload['userId']

    data = request.get_json() or {}
    room_id = data.get('room_id')
    score_type = data.get('score_type')
    score_value = data.get('score_value')

    room = db.rooms.find_one({'room_id': room_id})
    if not room or room.get('current_turn') != current_user_id:
        return jsonify({'result': 'fail', 'message': '당신의 차례가 아닙니다.'}), 400

    players = room.get('players', [])
    if len(players) < 2:
        return jsonify({'result': 'fail', 'message': '상대방이 아직 입장하지 않았습니다.'}), 400

    if current_user_id not in players:
        return jsonify({'result': 'fail', 'message': '플레이어 목록에 없습니다.'}), 400

    current_index = players.index(current_user_id)
    next_index = (current_index + 1) % len(players) 
    next_turn = players[next_index]

    db.rooms.update_one(
        {'room_id': room_id},
        {
            '$set': {
                f'scores.{current_user_id}.{score_type}': score_value,
                'current_turn': next_turn,
                'roll_count': 0,
                'dice': [{'val': 0, 'hold': False} for _ in range(5)]
            }
        }
    )

    updated_room = db.rooms.find_one({'room_id': room_id})
    updated_scores = updated_room.get('scores', {})

    is_game_over = len(players) == 2 and all(
        len(updated_scores.get(p, {})) >= TOTAL_CATEGORIES_COUNT for p in players
    )

    if is_game_over:
        final_scores = {}
        for p in players:
            total, _, _ = calculate_player_total(updated_scores.get(p, {}))
            final_scores[p] = total

        p1, p2 = players[0], players[1]
        s1, s2 = final_scores[p1], final_scores[p2]

        if s1 > s2:
            winner, loser = p1, p2
        elif s2 > s1:
            winner, loser = p2, p1
        else:
            winner, loser = 'draw', None

        if winner != 'draw':
            users_collection.update_one({'userId': winner}, {'$inc': {'wins': 1}})
            users_collection.update_one({'userId': loser}, {'$inc': {'losses': 1}})

        # 🗄️ 대전 기록 컬렉션에 매치 결과 저장
        matches_collection.insert_one({
            'room_id': room_id,
            'players': players,
            'scores': final_scores,
            'winner': winner,
            'created_at': datetime.datetime.now()
        })

        db.rooms.update_one(
            {'room_id': room_id},
            {
                '$set': {
                    'status': 'finished',
                    'winner': winner,
                    'final_scores': final_scores
                }
            }
        )

        return jsonify({
            'result': 'success',
            'status': 'finished',
            'winner': winner,
            'final_scores': final_scores,
            'message': '게임이 종료되었습니다.'
        })

    return jsonify({
        'result': 'success', 
        'status': 'playing', 
        'next_turn': next_turn
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
    users_collection.insert_one({
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
        return jsonify({
            'result': 'success',
            'userId': payload['userId'],
            'message': '인증 성공'
        })
    except jwt.ExpiredSignatureError:
        return jsonify({'result': 'fail', 'message': '토큰이 만료되었습니다.'})
    except jwt.InvalidTokenError:
        return jsonify({'result': 'fail', 'message': '유효하지 않은 토큰입니다.'})

@app.route('/api/get-latest-data/<room_id>', methods=['GET'])
@login_required
def get_game_chak(room_id):
    room = db.rooms.find_one({'room_id': room_id})
    if not room:
        return jsonify({'result': 'fail', 'message': '존재하지 않는 방입니다.'}), 404

    return jsonify({
        'result': 'success',
        'players': room.get('players', []),
        'status': room.get('status', 'waiting'),
        'current_turn': room.get('current_turn'),
        'dice': room.get('dice', []),
        'scores': room.get('scores', {}),
        'winner': room.get('winner'),
        'final_scores': room.get('final_scores', {})
    })

@app.route('/api/roll', methods=['POST'])
@login_required
def roll_dice():
    token = request.cookies.get('userToken')
    payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    current_user_id = payload['userId']

    data = request.get_json() or {}
    room_id = data.get('room_id')

    room = db.rooms.find_one({'room_id': room_id})
    if not room or room.get('current_turn') != current_user_id:
        return jsonify({'result': 'fail', 'message': '당신의 차례가 아닙니다.'}), 400

    roll_count = room.get('roll_count', 0)
    if roll_count >= 3:
        return jsonify({'result': 'fail', 'message': '주사위는 턴당 최대 3회만 굴릴 수 있습니다.'}), 400

    getdice = data.get('dicelist', [])
    new_dicelist = []

    for i in range(5):
        if i < len(getdice) and getdice[i].get('hold') is True and roll_count > 0:
            new_dicelist.append({'val': getdice[i].get('val'), 'hold': True})
        else:
            new_dicelist.append({'val': random.randint(1, 6), 'hold': False})

    dice_values = [d['val'] for d in new_dicelist]
    scores = calculate_yacht_scores(dice_values)
    db.rooms.update_one(
        {'room_id': room_id},
        {'$set': {'dice': new_dicelist, 'roll_count': roll_count + 1}}
    )

    return jsonify({
        'result': 'success',
        'userId': current_user_id,
        'dicelist': new_dicelist,
        'scores': scores,
        'roll_count': roll_count + 1
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)