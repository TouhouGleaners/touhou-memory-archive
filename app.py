from flask import Flask


app = Flask(__name__)

@app.route('/')
def home():
    return "home"

@app.route('/manage')
def manage():
    return "manage"

@app.route('/videos')
def videos():
    return "videos"

@app.route('/fetch')
def fetch():
    return "fetch"


if __name__ == '__main__':
    app.run(debug=True)