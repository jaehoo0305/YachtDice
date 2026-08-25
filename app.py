from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

# 나중에 aws할 때 수정 해야함
if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)