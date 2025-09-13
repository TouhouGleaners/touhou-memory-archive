from flask import Flask, render_template


app = Flask(__name__)

@app.route('/')
def home():
    return render_template("base.html")

@app.route('/manage')
def manage():
    return render_template("manage.html")

@app.route('/videos')
def videos():
    return "videos"

@app.route('/fetch')
def fetch():
    return "fetch"


if __name__ == '__main__':
    app.run(debug=True)