"""
CS304 Final Project
finalproj.py

Written by: Ariel Moncrief, Linh Dinh, Sophie Thorpe
"""
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
    """
    Handles user login functionality.

    GET: Renders the login page.
    POST: Processes login credentials and initiates a user session.

    Returns:
        - Rendered login page on GET.
        - Redirect to profile page or re-renders login page with errors on POST.
    """
    conn = dbi.connect()

    if request.method == "GET":
        return render_template("login.html", page_title="Login")
    else:
        try:
            #get user and pass from the form (check both were inputted)
            username = request.form["username"]
            password = request.form["password"]
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
    """
    Gives uploaded files to the client.

    Args:
        filename (str): Name of the file to serve.

    Returns:
        The requested file from the uploads directory.
    """
    return send_from_directory(app.config['UPLOADS'], filename)

#route to user profile
@app.route('/profile/<username>', methods=['GET','POST'])
def profile(username):
    """
    Renders the user profile page and handles profile actions like uploading, 
    deleting, or updating data.

    Args:
        username (str): The username of the profile to display.

    Returns:
        Rendered profile page or redirect after handling an action.
    """
    uid = session.get('uid')
    conn = dbi.connect()

    #select statements to display information about user
    currentsResult,reviewsResult,profilePic = f.profile_render(conn,
                                                            session.get('uid'))
    if request.method == 'GET':
       #Validate session and user
        response = validate_user_session(conn,uid, username)
        if response:
            return response
        return render_profile_page(username, currentsResult, reviewsResult, 
                                   profilePic, uid)

    else:
        submit_action = request.form.get('submit')
        if submit_action == 'Upload':
            return handle_upload(conn, uid, currentsResult, reviewsResult, 
                                 profilePic, username)
            
        elif submit_action == "Delete":
            return handle_delete(conn, uid, username, currentsResult, 
                                 reviewsResult, profilePic)
        elif submit_action == 'Update':
            return handle_update_progress(conn, username)
        elif submit_action == "friend":
            #get friend id from list
            friend_id = request.form.get('friend_id')
            #get values to render friends profile
            currentsResult,reviewsResult,profilePic = f.profile_render(
                conn,friend_id)
            #pass the friend id as the "user id" so system knows you are 
            # looking at a friends page
            return render_profile_page(username, currentsResult, reviewsResult, 
                                       profilePic, friend_id)
#logout functionality
@app.route('/logout/')
def logout():
    """
    Logs the user out by clearing session data.

    Returns:
        Redirect to the home page with a logout confirmation message.
    """
    #remove data from session to log out
    session.pop('username')
    session.pop('uid')
    session.pop('logged_in')
    flash('You are logged out')
    return redirect(url_for('index'))

#create account functionality
@app.route("/CreateAccount/", methods=["GET", "POST"])
def newAcc():
    """
    Handles user account creation.

    GET: Renders the account creation page.
    POST: Processes new user data and creates an account.

    Returns:
        - Rendered account creation page on GET.
        - Redirect to profile page or re-renders account creation page with 
        errors on POST.
    """
    if request.method == "GET":
        return render_template("createAccount.html", 
                               page_title="Create Account")
    else:
        try:
            # get information from form
            email = request.form["email"]
            username = request.form["username"]
            password = request.form["password"]

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
    """
    Handles the insertion of media into the database. If the request method is 
    GET, it renders an empty form for the user to input media details.
    If the request method is POST, it validates the form inputs, and if valid, 
    inserts the media into the database.

    Returns:
        If GET: renders the insert media form.
        If POST: redirects to the index page or re-renders the form with errors.
    """
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
        

        #checks that user inputted a valid media type
        check_media_type = media_type != "Book" and media_type != "Movie" and media_type != "Song"

        # check all necessary inputs are filled out
        #else prompt user
        if title == "":
            flash("Please enter a title")
        if media_type == "" or (check_media_type):
            flash("Please enter a valid media type")
        if director == "" and artist == "" and author == "":
            flash("Please enter a director/artist/author")
        if (
            title == ""
            or media_type == ""
            or (director == "" and artist == "" and author == "") 
            or check_media_type
        ):
            media = {
                "media_id": "",
                "title": "",
                "media_type": "",
                "director": "",
                "artist": "",
                "author": ""
            }
            return render_template(
                "insert.html", media=media, page_title="Insert Media"
            )

        try:
            conn = dbi.connect()
            #add media into media table
            f.insert_media(conn, title, media_type, director, artist, author, uid)
            flash("Media successfully inserted")
            return redirect(url_for("index"))
        except Exception as err:
            flash(f"Error inserting media: {str(err)}")
            return redirect(url_for("index"))

#updating media functionality
@app.route("/update_media/<int:media_id>/", methods=["GET", "POST"])
def update_media(media_id):
    """
    Handles updating existing media in the database. If the request method is 
    GET, it retrieves the current media details and displays them.
    If the request method is POST, it updates the media with the new values.

    Args:
        media_id (int): The ID of the media to update.

    Returns:
        If GET: renders the update media form.
        If POST: redirects to the media page or re-renders with errors.
    """

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
            return redirect(url_for("media", media_id = media_id))

        except Exception as err:
            flash(f"Error updating media: {str(err)}")
            return redirect(url_for("index"))

#search media functionality
@app.route("/search/", methods=["GET"])
def search():
    """
    Handles searching for media by a search term. If the search term is 
    provided, it redirects to the search result page.
    If no term is provided, it prompts the user to enter one.

    Returns:
        If GET: renders the search page with or without search results.
    """
    uid = session.get("uid")

    if not uid:
        return redirect(url_for("index"))
    
    # Request the inputed search term from the form
    search_term = request.args.get("search_media")
    search_type = request.args.get("search_type")

    # if searchterm is not null, redirect the search_result
    # else, re-render the template
    if search_term and search_term != " ":
        return redirect(url_for("search_result", search_term=search_term, 
                                search_type = search_type))
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
    """
    Displays the results of the media search based on a search term. 
    Queries the database for the media matching the search term and 
    displays the results.

    Args:
        search_term (str): The search term to query media by.

    Returns:
        Renders the search result page with the matching media.
    """
    conn = dbi.connect()

    uid = session.get("uid")

    if not uid:
        return redirect(url_for("index"))
    
    #get the search type
    search_type = request.args.get("search_type")
    print(search_type)

    # Query for finding the search_term in the media table
    results = f.search_render(conn, search_term, search_type)

    print(results)

    return render_template(
        "display-search.html",
        results=results,
        search_term=search_term,
        search_type=search_type,
        searched=True,
        page_title="Search Results",
    )

#write a review functionality
@app.route("/review/", methods=["GET", "POST"])
def review():
    """
    Handles writing reviews for media. If the request method is GET, it renders 
    a form to enter a review.
    If the request method is POST, it validates the review form and adds the 
    review to the database.

    Returns:
        If GET: renders the review form.
        If POST: redirects to the user's profile or re-renders with errors.
    """
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
    """
    Displays a media page with details about a specific media item. Queries the 
    database for the media details using the media ID.

    Args:
        media_id (int): The ID of the media to display.

    Returns:
        Renders the media page with the details of the specified media.
    """
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
        user_id = session.get("uid"),
        addedby_id = result["media"].get("addedby_id")
    )

#friends list functionality
@app.route("/friends/<int:user_id>", methods=["GET", "POST"])
def friends(user_id):
    """
    Displays a user's friends list. If the request method is POST, it removes a 
    friend from the user's list.
    
    Args:
        user_id (int): The ID of the user whose friends list to display.

    Returns:
        Renders the friends page with the user's friends list.
    """
    conn = dbi.connect()
    if request.method == "POST":
        friend_id = request.form["friend_id"]
        f.remove_friend(conn,friend_id, user_id)
    friendsResult = f.friends_render(conn, user_id)
    return render_template(
        "friends.html", page_title="My Friends", friendsResult=friendsResult, user_id = user_id)

#current media fuctionality
@app.route("/current/<int:media_id>", methods=["GET", "POST"])
def currents(media_id):
    """
    Handles adding media to the current media list for a user. If the request 
    method is GET, it checks if the media is already in the user's current list.
    If the request method is POST, it updates the user's progress on the media.

    Args:
        media_id (int): The ID of the media to add or update.

    Returns:
        If GET: renders the current media form.
        If POST: redirects to the user's profile or updates the media progress.
    """
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
    """
    Displays a review form for media that has been finished by the user.

    Args:
        media_id (int): The ID of the media to review.

    Returns:
        Renders the review page for the finished media.
    """
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
    """
    Validates if the user is logged in and authorized to access the profile. 
    If the user is not logged in or is unauthorized, it redirects to 
    the index page.

    Args:
        conn: The database connection.
        uid: The user ID.
        username: The username of the user.

    Returns:
        Redirects to the index page if validation fails, otherwise allows 
        access to the profile.
    """
    if not uid:
        flash("Please log in to access your profile.")
        return redirect(url_for('index'))
    #additional security to verify username to backend resources
    if not f.validate_user(conn, uid, username):
            flash("Unauthorized access to profile.")
            return redirect(url_for("index"))

#renders the profile page
def render_profile_page(username, currentsResult, reviewsResult, profilePic, 
                        friend_id):
    """
    Renders the user's profile page with details about their current media, 
    reviews, and profile picture.

    Args:
        username (str): The username of the user.
        currentsResult: The list of the user's current media.
        reviewsResult: The list of the user's reviews.
        profilePic: The URL or filename of the user's profile picture.
        friend_id (int): The ID of the user being viewed or the user 
        who is logged in.

    Returns:
        Renders the profile page with the user's details.
    """
    try:
        return render_template('profile.html',
                                page_title='Profile',
                                username=username, 
                                currentsResult=currentsResult, 
                                reviewsResult = reviewsResult,
                                user_id = session.get("uid"),
                                friend_id = friend_id,
                                profilePic = profilePic)
    except Exception as e:
        app.logger.error(f"Error displaying profile for {username}: {e}")
        flash("An error occurred while loading the profile.")
        return redirect(url_for("index"))

#functionality to handle profile pic upload
def handle_upload(conn, uid, currentsResult, reviewsResult, profilePic, 
                  username):
    """
    Handles the uploading of a new profile picture for the user. Validates 
    the file type and saves the uploaded file.

    Args:
        conn: The database connection.
        uid: The user ID.
        currentsResult: The list of the user's current media.
        reviewsResult: The list of the user's reviews.
        profilePic: The URL or filename of the user's profile picture.
        username: The username of the user.

    Returns:
        Renders the profile page after attempting the file upload.
    """
    try:
                #if no file is selected, flash message
                fname = request.files['pfp'].filename
                if 'pfp' not in request.files or fname == '':
                    flash('No selected file')
                    
                    return render_profile_page(username, currentsResult, 
                                               reviewsResult, profilePic, uid)
            
                #change file name and create file path
                pfp = request.files['pfp']
                user_pic = pfp.filename

                #check file type is compatible
                ext = user_pic.split('.')[-1]
                if ext not in ['jpg', 'jpeg', 'png']:
                    flash("""Incompatiable File Type. 
                          Please upload a .jpg, .jpeg, or .png file.""")
                    return render_profile_page(username, currentsResult, 
                                               reviewsResult, profilePic, uid)

                #create pathname for image
                filename = secure_filename('{}.{}'.format(uid,ext))
                pathname = os.path.join(app.config['UPLOADS'],filename)
                pfp.save(pathname)
                #add file
                f.insert_pic(conn, filename, uid)
                flash('Upload successful')

                currentsResult,reviewsResult,profilePic = f.profile_render(conn,
                                                            session.get('uid'))
                
                return render_profile_page(username, currentsResult, 
                                           reviewsResult, profilePic, uid)
            
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
def handle_delete(conn, uid, username, currentsResult, reviewsResult, 
                  profilePic):
    """
    Handles the deletion of the user's profile picture. Deletes the file and 
    updates the profile page.

    Args:
        conn: The database connection.
        uid: The user ID.
        username: The username of the user.
        currentsResult: The list of the user's current media.
        reviewsResult: The list of the user's reviews.
        profilePic: The URL or filename of the user's profile picture.

    Returns:
        Renders the profile page after deleting the profile picture.
    """
    try:
                #remove picture
                f.delete_pic(conn, uid, app)
                flash(f'Profile Picture Deleted')
                currentsResult,reviewsResult,profilePic = f.profile_render(
                    conn,session.get('uid'))
                return render_profile_page(username, currentsResult, 
                                           reviewsResult, profilePic, uid)

    except Exception as err:
                flash(f'Error deleting profle photo: {err}')
                return render_profile_page(username, currentsResult, 
                                           reviewsResult, profilePic, uid)

#functionality to handle updating the progress of something in currents          
def handle_update_progress(conn,username):
    """
    Updates the progress of a media item in the user's "current" list. 
    If the progress reaches 100%, the user is redirected to review the media.

    Args:
        conn: The database connection.
        username: The username of the user.

    Returns:
        Renders the profile page after updating the progress or 
        reviewing the media.
    """
    
    try:
                new_progress = request.form.get("new_progress")
                current_id = request.form.get("current_id")
                media_id = request.form.get("media_id")
                #result contains None if currents progress = 100%
                result = f.update_current_progress(conn, new_progress, 
                                                   current_id)
                if result is None:
                    return redirect(url_for("review_finished", 
                                            media_id=media_id))
                currentsResult,reviewsResult,profilePic = f.profile_render(
                    conn,session.get('uid'))
                return render_profile_page(username, currentsResult, 
                                           reviewsResult, profilePic, 
                                           session.get('uid'))
    except Exception as err:
                flash(f'Error deleting movie: {err}')
                return render_profile_page(username, currentsResult, 
                                           reviewsResult, profilePic, 
                                           session.get('uid'))

# FRIENDS FUNCTIONS
# 1. Route for Explore Friends Page
@app.route('/explore_friends', methods=['GET', 'POST'])
def explore_friends():
    """
    Displays a page where users can explore other users to potentially add as 
    friends. Allows users to search for others.

    Returns:
        Renders the explore friends page with a list of users to explore.
    """
    db_conn = dbi.connect()

    if 'uid' not in session:
        flash("Please log in first!")
        return redirect(url_for('login'))
    
    user_id = session['uid']

    if request.method == 'GET':
        # Get the list of friends to explore
        #SHowing all other user ids
        explore_friends_list = f.explore_friends_render(db_conn, user_id)
    else:
        search_user = request.form.get("search_user","").strip()

        if search_user:
            explore_friends_list = f.search_users(db_conn, user_id, search_user)
        else:
            flash(f'Please enter a search term')
            explore_friends_list = f.explore_friends_render(db_conn, user_id)

    return render_template('explore_friends.html', 
                           explore_friends=explore_friends_list)


# 2. Route for Adding a Friend
@app.route('/add_friend/<int:friend_id>', methods=['POST'])
def add_friend_route(friend_id):
    """
    Adds a friend to the current user's friends list.

    Args:
        friend_id (int): The ID of the user to add as a friend.

    Returns:
        Redirects to the explore friends page after adding the friend.
    """
    db_conn = dbi.connect()

    if 'uid' not in session:
        flash("Please log in first!")
        return redirect(url_for('login'))
    
    user_id = session['uid']
    
    # Add the friend to the friends list
    f.add_friend(db_conn, user_id, friend_id)
    
    return redirect(url_for('explore_friends'))


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