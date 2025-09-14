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
    return render_template("videos.html")

@app.route('/fetch')
def fetch():
    return render_template("fetch.html")


if __name__ == '__main__':
    app.run(debug=True)