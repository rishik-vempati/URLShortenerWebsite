import pyshorteners
from flask import Flask, redirect, render_template, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

access_token = 'f056bc1c7a25d767a42a85697598eacd44c64ab8'

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://supplynote:flaskass@localhost:5432/urlflask'
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(20), nullable=False)

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def __repr__(self):
        return f'{self.username}'


class URLS(db.Model):
    long_url = db.Column(db.String(1000), primary_key=True)
    short_url = db.Column(db.String(150), unique=True, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow())

    def __init__(self, long_url, short_url, date_created):
        self.long_url = long_url
        self.short_url = short_url
        self.date_created = date_created

    def __repr__(self):
        return f'{self.long_url}'


@app.route('/', methods=['POST', 'GET'])
def home():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if (user.username == username) and (user.password == password):
            return redirect('/convert')
        else:
            return render_template('index.html')
    else:
        return render_template('index.html')


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password == confirm_password:
            user = User(username=username, password=password)
            db.session.add(user)
            db.session.commit()
            return redirect('/convert')
        else:
            return render_template('register.html')
    else:
        return render_template('register.html')


@app.route('/convert', methods=['POST', 'GET'])
def convert():
    if request.method == 'POST':
        long_url = request.form.get('url')

        url = URLS.query.filter_by(long_url=long_url).first()
        if url is None:
            type_bitly = pyshorteners.Shortener(api_key=access_token)
            short_url = type_bitly.bitly.short(long_url)

            url = URLS(long_url=long_url, short_url=short_url, date_created=datetime.utcnow())
            db.session.add(url)
            db.session.commit()

            return render_template('home.html', url=short_url, count=0)
        else:
            curr_date = datetime.utcnow()
            date_created = url.date_created
            diff = curr_date - date_created
            diff_min = divmod(diff.seconds, 60)

            # 48hrs - 2880min
            if diff_min[0] > 2880:
                return render_template('home.html', url='Invalid', count=0)

            type_bitly = pyshorteners.Shortener(api_key=access_token)
            short_url = url.short_url
            count_clicks = type_bitly.bitly.total_clicks(short_url)
            return render_template('home.html', url=short_url, count=count_clicks)

    return render_template('home.html')


if __name__ == '__main__':
    app.debug = True
    app.run()
