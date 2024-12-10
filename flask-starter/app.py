from flask import (
    Flask,
    render_template,
    make_response,
    url_for,
    request,
    redirect,
    flash,
    session,
    send_from_directory,
    jsonify,
)
from werkzeug.utils import secure_filename

app = Flask(__name__)

# one or the other of these. Defaults to MySQL (PyMySQL)
# change comment characters to switch to SQLite

import cs304dbi as dbi

# import cs304dbi_sqlite3 as dbi

import secrets
import finalproj as f

app.secret_key = "your secret here"
# replace that with a random key
app.secret_key = secrets.token_hex()

# This gets us better error messages for certain common request errors
app.config["TRAP_BAD_REQUEST_ERRORS"] = True


# for file upload
app.config['UPLOADS'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

#Route to render the basic homepage
@app.route('/')
def index():
    return render_template("main.html", page_title="Home")

#login route
@app.route("/login/", methods=["GET", "POST"])
def login():
    conn = dbi.connect()

    if request.method == "GET":
        return render_template("login.html", page_title="Login")
    else:
        try:
            #get user and pass from the form (check both were inputted)
            username = request.form["username"]
            password = request.form["pass"]
            if username == "":
                flash("Please enter a username")
            if password == "":
                flash("Please enter a password")
            if username == "" or password == "":
                return render_template("login.html", page_title="Login")

            #result contains the user_id of the person logged in or None/False 
            # if the login info was incorrect
            result = f.check_login(conn, username, password)

            if result is None or result is False:
                flash("Incorrect login")
                return render_template("login.html", page_title="Login")
            else:
                flash("successfully logged in as " + username)
                # add log in info to session
                session["username"] = username
                session["uid"] = result
                session["logged_in"] = True
                session["visits"] = 1
                return redirect(
                    url_for("profile", username=username,
                             user_id=result)
                )

        except Exception as err:
            flash("form submission error" + str(err))
            return redirect(url_for("login"))

#this needs doesnt seem right but it doesnt work without it
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOADS'], filename)

#route to user profile
@app.route('/profile/<username>', methods=['GET','POST'])
def profile(username):
    uid = session.get('uid')
    conn = dbi.connect()

    #Validate session and user
    response = validate_user_session(conn,uid, username)
    if response:
        return response

    #select statements to display information about user
    currentsResult,reviewsResult,profilePic = f.profile_render(conn,
                                                                session)
    if request.method == 'GET':
       return render_profile_page(conn, username, currentsResult, reviewsResult, profilePic)

    else:
        submit_action = request.form.get('submit')

        if submit_action == 'Upload':
            return handle_upload(conn, uid, currentsResult, reviewsResult, profilePic, username)
            
        elif submit_action == "Delete":
            return handle_delete(conn, uid, username, currentsResult, reviewsResult, profilePic)
        elif submit_action == 'Update':
            return handle_update_progress(conn, username)
#logout functionality
@app.route('/logout/')
def logout():
    #remove data from session to log out
    session.pop('username')
    session.pop('uid')
    session.pop('logged_in')
    flash('You are logged out')
    return redirect(url_for('index'))

#create account functionality
@app.route("/CreateAccount/", methods=["GET", "POST"])
def newAcc():
    if request.method == "GET":
        return render_template("createAccount.html", 
                               page_title="Create Account")
    else:
        try:
            # get information from form
            email = request.form["email"]
            username = request.form["username"]
            password = request.form["pass"]

            #check all info is filled out
            if email == "":
                flash("Please enter an email")
            if username == "":
                flash("Please enter a username")
            if password == "":
                flash("Please enter a password")
            if email == "" or username == "" or password == "":
                return render_template(
                    "createAccount.html", page_title="Create Account"
                )

            conn = dbi.connect()
            #check email is not already used by an account
            result = f.check_email(conn, email)
            if result:
                flash("Email already associated with an account")
                return redirect(url_for("login"))
            
            #check username is not already used by an account
            result = f.check_username(conn, username)
            if result:
                flash("Username already in use")
                return render_template(
                    "createAccount.html", page_title="Create Account"
                )
            #result either contains none if there is an issue with adding 
            # the new user (includes thread safety) or the new users user_id
            result = f.add_new_user(conn, username, password, email)

            if result is None:
                return render_template(
                    "createAccount.html", page_title="Create Account"
                )
            # log in with inputted data
            session["username"] = username
            session["uid"] = result["user_id"]
            session["logged_in"] = True
            session["visits"] = 1
            flash("Account created successfully")

            return redirect(url_for("profile", username=username))

        except Exception as err:
            flash("form submission error" + str(err))
            return redirect(url_for("index"))

#insert media functionality
@app.route("/insert_media/", methods=["GET", "POST"])
def insert_media():
    uid = session.get("uid")

    if not uid:
        return redirect(url_for("index"))

    if request.method == "GET":
        # Pass empty values or defaults to the template
        media = {
            "title": "",
            "media_type": "",
            "director": "",
            "artist": "",
            "author": "",
        }
        return render_template("insert.html", media=media, 
                               page_title="Insert Media")

    elif request.method == "POST":
        #get media values from form
        title = request.form["title"]
        media_type = request.form["media_type"]
        director = request.form["director"]
        artist = request.form["artist"]
        author = request.form["author"]
        # check all necessary inputs are filled out
        #else prompt user
        if title == "":
            flash("Please enter a title")
        if media_type == "":
            flash("Please enter a media type")
        if director == "" and artist == "" and author == "":
            flash("Please enter a director/artist/author")
        if (
            title == ""
            or media_type == ""
            or (director == "" and artist == "" and author == "")
        ):
            media = {
                "media_id": "",
                "title": "",
                "media_type": "",
                "director": "",
                "artist": "",
                "author": "",
            }
            return render_template(
                "insert.html", media=media, page_title="Insert Media"
            )

        try:
            conn = dbi.connect()
            #add media into media table
            f.insert_media(conn, title, media_type, director, artist, author)
            flash("Media successfully inserted")
            return redirect(url_for("index"))

        except Exception as err:
            flash(f"Error inserting media: {str(err)}")
            return redirect(url_for("index"))

#updating media functionality
@app.route("/update_media/<int:media_id>/", methods=["GET", "POST"])
def update_media(media_id):

    uid = session.get("uid")

    if not uid:
        return redirect(url_for("index"))
    conn = dbi.connect()
    if request.method == "GET":
        # Current media data
        media = f.update_render(conn, media_id)
        if not media:
            flash("Media not found")
            return redirect(url_for("index"))
        return render_template("update.html", media=media, 
                               page_title="Update Media")

    elif request.method == "POST":
        # Form data
        title = request.form["title"]
        media_type = request.form["media_type"]
        director = request.form["director"]
        artist = request.form["artist"]
        author = request.form["author"]

        try:
            #updating the media in the media table
            f.update_movie(conn, title, media_type, director, artist, author, 
                           media_id)
            flash("Media successfully updated")
            return redirect(url_for("index"))

        except Exception as err:
            flash(f"Error updating media: {str(err)}")
            return redirect(url_for("index"))

#search media functionality
@app.route("/search/", methods=["GET"])
def search():
    uid = session.get("uid")

    if not uid:
        return redirect(url_for("index"))
    # Request the inputed search term from the form
    search_term = request.args.get("search_media")

    # if searchterm is not null, redirect the search_result
    # else, re-render the template
    if search_term and search_term != " ":
        return redirect(url_for("search_result", search_term=search_term))
    else:
        flash("Please enter something in the search bar")
        return render_template(
            "display-search.html",
            results=None,
            search_term="",
            searched=False,
            page_title="Search",
        )

#display search functionality
@app.route("/search/<search_term>", methods=["GET"])
def search_result(search_term):
    conn = dbi.connect()

    uid = session.get("uid")

    if not uid:
        return redirect(url_for("index"))

    # Query for finding the search_term in the media table
    results = f.search_render(conn, search_term)

    return render_template(
        "display-search.html",
        results=results,
        search_term=search_term,
        searched=True,
        page_title="Search Results",
    )

#write a review functionality
@app.route("/review/", methods=["GET", "POST"])
def review():
    uid = session.get("uid")

    if not uid:
        flash("Please login")
        return redirect(url_for("index"))

    conn = dbi.connect()

    if request.method == "GET":
        #get the media tt
        tt = request.args.get("media_id")

        #with media tt, get media title from media table
        #if none, set to empty
        if tt:
            media = f.review_render(conn, tt)
        else:
            media = {
                "title": "",
            }
        return render_template(
            "review.html",
            page_title="Review Media",
            media_title=media["title"],
            media_id=tt,
        )

    elif request.method == "POST":
        # Form data
        title = request.form["title"]
        review_text = request.form["review"]
        rating = request.form["Rating"]
        media_id = request.form["media_id"]

        # make sure all form data is filled out
        #else prompt user
        if title == "":
            flash("Please enter a title")
        if review_text == "":
            flash("Please enter a review")
        if rating == "":
            flash("Please enter a rating")
        if title == "" or review_text == "" or rating == "":
            return render_template("review.html", page_title="Review Media")

        #query to add a review to the reviews table
        f.insert_review(conn, media_id, session["uid"], review_text, rating)
        flash("Media reviewed")
        return redirect(url_for("profile", username=session["username"]))

#display media functionality
@app.route("/media/<int:media_id>")
def media(media_id):
    conn = dbi.connect()

    #query to get data for media page
    result = f.media_page_render(conn, media_id)
    person = (
        result["media"].get("director")
        or result["media"].get("artist")
        or result["media"].get("author")
        or "Unknown"
    )
    return render_template(
        "media.html",
        page_title=result["media"].get("title"),
        result=result,
        person=person,
        media_id=media_id,
    )

#friends list functionality
@app.route("/friends/<int:user_id>")
def friends(user_id):
    conn = dbi.connect()
    #query to get user friends data
    friendsResult = f.friends_render(conn, user_id)
    return render_template(
        "friends.html", page_title="My Friends", friendsResult=friendsResult
    )

#current media fuctionality
@app.route("/current/<int:media_id>", methods=["GET", "POST"])
def currents(media_id):
    conn = dbi.connect()
    uid = session.get("uid")
    if request.method == "GET":
        #check if media already in current
        #does not allow for duplicate media in current
        result = f.check_currents(conn,uid,media_id)
        if result is None:
            return redirect(url_for(('index')))
        
        #query to get the title of the media
        title = f.render_currents_form(conn, media_id)
        return render_template(
            "currents.html",
            page_title="Add to Currents",
            title=title,
            media_id=media_id,
        )
    else:
        #get progress from user and add progress to currents table
        progress = request.form["progress"]
        f.add_to_currents(conn, uid, media_id, progress)
        return redirect(url_for("profile", username=session.get("username")))

#when finished media, review media
@app.route("/review_finished/<int:media_id>")
def review_finished(media_id):
    conn = dbi.connect()

    #query to get media data for review
    media = f.review_render(conn, media_id)
    return render_template(
        "review.html",
        page_title="Review Media",
        media_title=media["title"],
        media_id=media_id,
    )

#extra security to validate login
def validate_user_session(conn, uid, username):
    if not uid:
        flash("Please log in to access your profile.")
        return redirect(url_for('index'))
    #additional security to verify username to backend resources
    if not f.validate_user(conn, uid, username):
            flash("Unauthorized access to profile.")
            return redirect(url_for("index"))

#redners the profile page
def render_profile_page(conn, username, currentsResult, reviewsResult, profilePic):
        try:
            return render_template('profile.html',
                                page_title='Profile',
                                username=username, 
                                currentsResult=currentsResult, 
                                reviewsResult = reviewsResult,
                                user_id = session.get("uid"),
                                profilePic = profilePic)
        except Exception as e:
            app.logger.error(f"Error displaying profile for {username}: {e}")
            flash("An error occurred while loading the profile.")
            return redirect(url_for("index"))

#functionality to handle profile pic upload
def handle_upload(conn, uid, currentsResult, reviewsResult, profilePic, username):
            try:
                #if no file is selected, flash message
                fname = request.files['pfp'].filename
                if 'pfp' not in request.files or fname == '':
                    flash('No selected file')
                    
                    return render_profile_page(conn, username, currentsResult, reviewsResult, profilePic)
            
                #change file name and create file path
                pfp = request.files['pfp']
                user_pic = pfp.filename

                #check file type is compatible
                ext = user_pic.split('.')[-1]
                if ext not in ['jpg', 'jpeg', 'png']:
                    flash("""Incompatiable File Type. 
                          Please upload a .jpg, .jpeg, or .png file.""")
                    return render_profile_page(conn, username, currentsResult, reviewsResult, profilePic)

                #create pathname for image
                filename = secure_filename('{}.{}'.format(uid,ext))
                pathname = os.path.join(app.config['UPLOADS'],filename)
                pfp.save(pathname)

                #add file
                f.insert_pic(conn, filename, uid)
                flash('Upload successful')

                currentsResult,reviewsResult,profilePic = f.profile_render(conn,
                                                                session)
                return render_profile_page(conn, username, currentsResult, reviewsResult, profilePic)
            
            except Exception as err:
                flash('Upload failed {why}'.format(why=err))
                return render_template('profile.html',
                                page_title='Profile',
                                username=username, 
                                currentsResult=currentsResult, 
                                reviewsResult = reviewsResult,
                                user_id = session.get("uid"),
                                profilePic = profilePic)

#functionality to handle the deleting of a profile pic
def handle_delete(conn, uid, username, currentsResult, reviewsResult, profilePic):
            try:
                #remove picture
                f.delete_pic(conn, uid)
                flash(f'Profile Picture Deleted')
                currentsResult,reviewsResult,profilePic = f.profile_render(conn,
                                                                session)
                return render_profile_page(conn, username, currentsResult, reviewsResult, profilePic)

            except Exception as err:
                flash(f'Error deleting movie: {err}')
                return render_profile_page(conn, username, currentsResult, reviewsResult, profilePic)

#functionality to handle updating the progress of something in currents          
def handle_update_progress(conn,username):
            try:
                new_progress = request.form.get("new_progress")
                current_id = request.form.get("current_id")
                media_id = request.form.get("media_id")
                #result contains None if currents progress = 100%
                result = f.update_current_progress(conn, new_progress, current_id)
                if result is None:
                    return redirect(url_for("review_finished", media_id=media_id))
                currentsResult,reviewsResult,profilePic = f.profile_render(conn,
                                                                session)
                return render_profile_page(conn, username, currentsResult, reviewsResult, profilePic)
            except Exception as err:
                flash(f'Error deleting movie: {err}')
                return render_profile_page(conn, username, currentsResult, reviewsResult, profilePic)

if __name__ == "__main__":
    import sys, os

    if len(sys.argv) > 1:
        # arg, if any, is the desired port number
        port = int(sys.argv[1])
        assert port > 1024
    else:
        port = os.getuid()
    # set this local variable to 'wmdb' or your personal or team db
    db_to_use = "recap_db"
    print(f"will connect to {db_to_use}")
    dbi.conf(db_to_use)
    app.debug = True
    app.run("0.0.0.0", port)