from flask import (Flask, render_template, make_response, url_for, request,
                   redirect, flash, session, send_from_directory, jsonify)
from werkzeug.utils import secure_filename
app = Flask(__name__)

# one or the other of these. Defaults to MySQL (PyMySQL)
# change comment characters to switch to SQLite

import cs304dbi as dbi
#import cs304dbi_sqlite3 as dbi

import secrets
import bcrypt
import imghdr
import finalproj as f

app.secret_key = 'your secret here'
# replace that with a random key
app.secret_key = secrets.token_hex()

# This gets us better error messages for certain common request errors
app.config['TRAP_BAD_REQUEST_ERRORS'] = True

# for file upload
app.config['UPLOADS'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

@app.route('/')
def index():
    return render_template('main.html',
                           page_title='Home')


@app.route('/login/', methods=["GET", "POST"])
def login():
    conn = dbi.connect()
    
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
            
            result = f.check_login(conn,username,password)
            
            if result is None or result is False:
                flash('Incorrect login')
                return render_template('login.html',
                               page_title='Login')
            else:
                flash('successfully logged in as ' + username)
                #add log in info to session
                session['username'] = username
                session['uid'] = result['user_id']
                session['logged_in'] = True
                session['visits'] = 1
                return redirect(url_for('profile', username=username))

        except Exception as err:
            flash('form submission error'+str(err))
            return redirect(url_for('login') )

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOADS'], filename)

@app.route('/profile/<username>', methods=['GET','POST'])
def profile(username):

    uid = session.get('uid')

    if not uid:
        return redirect(url_for('index'))
    
    conn = dbi.connect()

    if request.method == 'GET':
        #select statements to display information about user
        currentsResult,friendsResult,reviewsResult,profilePic = f.profile_render(conn,
                                                                    session)

        return render_template('profile.html',
                               page_title='Profile',
                               username=username, currentsResult=currentsResult,
                               friendsResult=friendsResult, 
                               reviewsResult = reviewsResult,
                               profilePic = profilePic)
    else:
        submit_action = request.form.get('submit')

        if submit_action == 'Upload':
            print(submit_action)
            try:
                #if no file is selected, flash message
                if 'pfp' not in request.files or request.files['pfp'].filename == '':
                    flash('No selected file')
                    return redirect(url_for('profile', username=username))
                
                #change file name and create file path
                pfp = request.files['pfp']
                user_pic = pfp.filename

                ext = user_pic.split('.')[-1]
                if ext not in ['jpg', 'jpeg', 'png']:
                    flash('Incompatiable File Type. Please upload a .jpg, .jpeg, or .png file.')
                    return redirect(url_for('profile', username=username))

                filename = secure_filename('{}.{}'.format(uid,ext))
                pathname = os.path.join(app.config['UPLOADS'],filename)
                pfp.save(pathname)

                #add file
                f.insert_pic(conn, filename, uid)
                flash('Upload successful')

                return redirect(url_for('profile', username=username))
            
            except Exception as err:
                flash('Upload failed {why}'.format(why=err))
                return redirect(url_for('profile', username=username))
            
        elif submit_action == "Delete":
            try:
                f.delete_pic(conn, uid)
                flash(f'Profile Picture Deleted')
                return redirect(url_for('profile', username=username))

            except Exception as err:
                flash(f'Error deleting movie: {err}')
                return redirect(url_for('profile', username=username))


@app.route('/logout/')
def logout():
    #remove data from session to log out
    session.pop('username')
    session.pop('uid')
    session.pop('logged_in')
    flash('You are logged out')
    return redirect(url_for('index'))

@app.route('/CreateAccount/', methods=['GET','POST'])
def newAcc():
    if request.method == 'GET':
        return render_template('createAccount.html',
                               page_title='Create Account')
    else:
        try:
            #get information from form
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
            
            conn = dbi.connect()
            result = f.check_email(conn,email)
            if result:
                flash("Email already associated with an account")
                return redirect (url_for('login'))
            
            result = f.check_username(conn,username)
            if result:
                flash("Username already in use")
                return render_template('createAccount.html',
                               page_title='Create Account')
            
            result = f.add_new_user(conn,username,password,email)
            
            #log in with inputted data
            session['username'] = username
            session['uid'] = result['user_id']
            session['logged_in'] = True
            session['visits'] = 1
            flash('Account created successfully')
            
            return redirect(url_for('profile', username=username))

        except Exception as err:
            flash('form submission error'+str(err))
            return redirect(url_for('index') )

@app.route('/insert_media/', methods=["GET", "POST"])
def insert_media():
    uid = session.get('uid')

    if not uid:
        return redirect(url_for('index'))

    if request.method == 'GET':
        # Pass empty values or defaults to the template
        media = {
            'title': '',
            'media_type': '',
            'director': '',
            'artist': '',
            'author': ''
        }
        return render_template('insert.html', media=media, 
                               page_title='Insert Media')

    elif request.method == 'POST':
        title = request.form['title']
        media_type = request.form['media_type']
        director = request.form['director']
        artist = request.form['artist']
        author = request.form['author']
        #check all necessary inputs are filled out
        if title == "":
                flash("Please enter a title")
        if media_type == "":
            flash("Please enter a media type")
        if director == "" and artist == "" and author == "":
            flash("Please enter a director/artist/author")
        if title == "" or media_type == "" or (director == "" and artist == "" 
                                               and author == ""):
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
            conn = dbi.connect()
            f.insert_media(conn,title,media_type,director,artist,author)
            flash('Media successfully inserted')
            return redirect(url_for('index'))

        except Exception as err:
            flash(f"Error inserting media: {str(err)}")
            return redirect(url_for('index'))


@app.route('/update_media/<int:media_id>/', methods=["GET", "POST"])
def update_media(media_id):
    
    uid = session.get('uid')

    if not uid:
        return redirect(url_for('index'))
    conn = dbi.connect()
    if request.method == 'GET':
        # Current media data
        media = f.update_render(conn,media_id)
        if not media:
            flash('Media not found')
            return redirect(url_for('index'))
        return render_template('update.html', media=media, 
                               page_title='Update Media')

    elif request.method == 'POST':
        # Form data
        title = request.form['title']
        media_type = request.form['media_type']
        director = request.form['director']
        artist = request.form['artist']
        author = request.form['author']

        try:
            f.update_movie(conn,title,media_type,director,artist,author,media_id)

            flash('Media successfully updated')
            return redirect(url_for('index'))

        except Exception as err:
            flash(f"Error updating media: {str(err)}")
            return redirect(url_for('index'))

@app.route('/search/', methods=["GET"])
def search():
    uid = session.get('uid')

    if not uid:
        return redirect(url_for('index'))
    #Request the inputed search term from the form
    search_term = request.args.get('search_media')

    #if searchterm is not null, redirect the search_result
    #else, re-render the template
    if search_term and search_term != " ":
        return redirect(url_for('search_result', search_term=search_term))
    else:
        flash("Please enter something in the search bar")
        return render_template('display-search.html', results=None, 
                               search_term='', searched = False,
                               page_title='Search')

@app.route('/search/<search_term>', methods=["GET"])
def search_result(search_term):
    conn = dbi.connect()
    
    uid = session.get('uid')

    if not uid:
        return redirect(url_for('index'))
    
    #Query for finding the search_term in the media table
    results = f.search_render(conn,search_term)

    return render_template('display-search.html', results=results, 
                           search_term=search_term, searched = True,
                           page_title='Search Results')

@app.route('/review/', methods=['GET','POST'])
def review():
    uid = session.get('uid')

    if not uid:
        flash("Please login")
        return redirect(url_for('index'))

    conn = dbi.connect()
    if request.method == 'GET':
        tt = request.args.get('media_id')
        if tt:
            media = f.review_render(conn,tt)
        else:
            media = {
            'title': '',
            }
        return render_template('review.html', 
                            page_title='Review Media', 
                            media_title = media['title'], media_id = tt)

    elif request.method == 'POST':
        # Form data
        title = request.form['title']
        review_text = request.form['review']
        rating = request.form['Rating']
        media_id = request.form['media_id']

        #make sure all form data is filled out
        if title == "":
                flash("Please enter a title")
        if review_text == "":
            flash("Please enter a review")
        if rating == "":
            flash("Please enter a rating")
        if title == "" or review_text == "" or rating == "":
            return render_template('review.html', 
                               page_title='Review Media')

        f.insert_review(conn,media_id, session['uid'], review_text, rating)
        flash("Media reviewed")
        return redirect(url_for('profile', username=session['username']))

if __name__ == '__main__':
    import sys, os
    if len(sys.argv) > 1:
        # arg, if any, is the desired port number
        port = int(sys.argv[1])
        assert(port>1024)
    else:
        port = os.getuid()
    # set this local variable to 'wmdb' or your personal or team db
    db_to_use = 'recap_db' 
    print(f'will connect to {db_to_use}')
    dbi.conf(db_to_use)
    app.debug = True
    app.run('0.0.0.0',port)
