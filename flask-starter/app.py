from flask import (Flask, render_template, make_response, url_for, request,
                   redirect, flash, session, send_from_directory, jsonify)
from werkzeug.utils import secure_filename
app = Flask(__name__)

# one or the other of these. Defaults to MySQL (PyMySQL)
# change comment characters to switch to SQLite

import cs304dbi as dbi
# import cs304dbi_sqlite3 as dbi

import secrets
import bcrypt

app.secret_key = 'your secret here'
# replace that with a random key
app.secret_key = secrets.token_hex()

# This gets us better error messages for certain common request errors
app.config['TRAP_BAD_REQUEST_ERRORS'] = True

@app.route('/')
def index():
    return render_template('main.html',
                           page_title='Home')

# You will probably not need the routes below, but they are here
# just in case. Please delete them if you are not using them

@app.route('/login/', methods=["GET", "POST"])
def login():
    conn = dbi.connect()
    curs = dbi.dict_cursor(conn)
    if request.method == 'GET':
        return render_template('login.html',
                               page_title='Login')
    else:
        try:
            username = request.form['username']
            password = request.form['pass'] 
            if username == "":
                flash("Please enter a username")
            if password == "":
                flash("Please enter a password")
            if username == "" or password == "":
                return render_template('login.html',
                               page_title='Login')
            
            sql = "select user_id, password_hash from users where username = %s"
            curs.execute(sql, username)
            result = curs.fetchone()

            if result is None:
                flash('Incorrect login')
                return render_template('login.html',
                               page_title='Login')
            
            stored = result['password_hash']

            hashed2 = bcrypt.hashpw(password.encode('utf-8'), stored.encode('utf-8'))
            hashed2_str = hashed2.decode('utf-8')

            if(hashed2_str != stored):
                flash('Incorrect password')
                return render_template('login.html',
                               page_title='Login')
            else:
                flash('successfully logged in as ' + username)
                session['username'] = username
                session['uid'] = result['user_id']
                session['logged_in'] = True
                session['visits'] = 1
                return redirect(url_for('profile', username=username))

        except Exception as err:
            flash('form submission error'+str(err))
            return redirect(url_for('login') )

@app.route('/profile/<username>', methods=['GET','POST'])
def profile(username):
    conn = dbi.connect()
    curs = dbi.dict_cursor(conn)
    if request.method == 'GET':
        sql = 'select media.title from currents inner join media using (media_id) where currents.user_id = %s'
        curs.execute(sql, session['uid'])
        currentsResult = curs.fetchall()
        
        sql = 'select users.username from users inner join friends on friends.friend_id = users.user_id where friends.user_id = %s'
        curs.execute(sql, session['uid'])
        friendsResult = curs.fetchall()

        sql = 'select media.title, reviews.rating, reviews.review_text from media inner join reviews using (media_id) where reviews.user_id = %s'
        curs.execute(sql, session['uid'])
        reviewsResult = curs.fetchall()

        return render_template('profile.html',
                               page_title='Profile',
                               username=username, currentsResult=currentsResult, friendsResult=friendsResult, reviewsResult = reviewsResult)
    else:
        raise Exception('this cannot happen')

@app.route('/logout/')
def logout():
    session.pop('username')
    session.pop('uid')
    session.pop('logged_in')
    flash('You are logged out')
    return redirect(url_for('index'))

@app.route('/CreateAccount/', methods=['GET','POST'])
def newAcc():
    conn = dbi.connect()
    curs = dbi.dict_cursor(conn)
    if request.method == 'GET':
        return render_template('createAccount.html',
                               page_title='Create Account')
    else:
        try:
            email = request.form['email']
            username = request.form['username']
            password = request.form['pass'] 
            
            if email == "":
                flash("Please enter an email")
            if username == "":
                flash("Please enter a username")
            if password == "":
                flash("Please enter a password")
            if email == "" or username == "" or password == "":
                return render_template('createAccount.html',
                               page_title='Create Account')
            
            sql = "select * from users where email = %s"
            curs.execute(sql, email)
            result = curs.fetchone()
            if result:
                flash("Email already associated with an account")
                return redirect (url_for('login'))
            
            sql = "select * from users where username = %s"
            curs.execute(sql, username)
            result = curs.fetchone()
            if result:
                flash("Username already in use")
                return render_template('createAccount.html',
                               page_title='Create Account')
            
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            stored = hashed.decode('utf-8')
            sql = 'insert into users (username, email, password_hash) values (%s,%s,%s)'
            curs.execute(sql, [username, email, stored])
            conn.commit()
            session['username'] = username

            sql = 'select user_id from users where username = %s'
            curs.execute(sql, username)
            result = curs.fetchone()
            
            session['uid'] = result['user_id']
            session['logged_in'] = True
            session['visits'] = 1
            flash('Account created successfully')
            
            return redirect(url_for('profile', username=username))

        except Exception as err:
            flash('form submission error'+str(err))
            return redirect( url_for('index') )

@app.route('/insert_media/', methods=["GET", "POST"])
def insert_media():
    conn = dbi.connect()
    curs = dbi.dict_cursor(conn)

    if request.method == 'GET':
        # Pass empty values or defaults to the template
        media = {
            'media_id': '',
            'title': '',
            'media_type': '',
            'director': '',
            'artist': '',
            'author': ''
        }
        return render_template('insert.html', media=media, page_title='Insert Media')

    elif request.method == 'POST':
        # Why are we asking for media id?
        title = request.form['title']
        media_type = request.form['media_type']
        director = request.form['director']
        artist = request.form['artist']
        author = request.form['author']
        if title == "":
                flash("Please enter a title")
        if media_type == "":
            flash("Please enter a media type")
        if director == "" and artist == "" and author == "":
            flash("Please enter a director/artist/author")
        if title == "" or media_type == "" or (director == "" and artist == "" and author == ""):
            media = {
            'media_id': '',
            'title': '',
            'media_type': '',
            'director': '',
            'artist': '',
            'author': ''
            }
            return render_template('insert.html', media=media,
                               page_title='Insert Media')

        try:
            sql = """
                INSERT INTO media (title, media_type, director, artist, author)
                VALUES (%s, %s, %s, %s, %s)
            """
            curs.execute(sql, (title, media_type, director, artist, author))
            conn.commit()

            flash('Media successfully inserted')
            return redirect(url_for('index'))

        except Exception as err:
            flash(f"Error inserting media: {str(err)}")
            return redirect(url_for('index'))


@app.route('/update_media/<int:media_id>/', methods=["GET", "POST"])
def update_media(media_id):
    conn = dbi.connect()
    curs = dbi.dict_cursor(conn)

    if request.method == 'GET':
        # Current media data
        sql = 'SELECT * FROM media WHERE media_id = %s'
        curs.execute(sql, (media_id,))
        media = curs.fetchone()

        if not media:
            flash('Media not found')
            return redirect(url_for('index'))
        return render_template('update.html', media=media, page_title='Update Media')

    elif request.method == 'POST':
        # Form data
        title = request.form['title']
        media_type = request.form['media_type']
        director = request.form['director']
        artist = request.form['artist']
        author = request.form['author']

        try:
            sql = """
                UPDATE media
                SET title = %s, media_type = %s, director = %s, artist = %s, author = %s
                WHERE media_id = %s
            """
            curs.execute(sql, (title, media_type, director, artist, author, media_id))
            conn.commit()

            flash('Media successfully updated')
            return redirect(url_for('index'))

        except Exception as err:
            flash(f"Error updating media: {str(err)}")
            return redirect(url_for('index'))

if __name__ == '__main__':
    import sys, os
    if len(sys.argv) > 1:
        # arg, if any, is the desired port number
        port = int(sys.argv[1])
        assert(port>1024)
    else:
        port = os.getuid()
    # set this local variable to 'wmdb' or your personal or team db
    db_to_use = 'st107_db' 
    print(f'will connect to {db_to_use}')
    dbi.conf(db_to_use)
    app.debug = True
    app.run('0.0.0.0',port)
