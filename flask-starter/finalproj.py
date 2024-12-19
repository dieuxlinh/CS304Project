"""
CS304 Final Project
finalproj.py

Written by: Ariel Moncrief, Linh Dinh, Sophie Thorpe
"""

# Module imports
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
import cs304dbi as dbi
import bcrypt
import os

# Database connections
dbi.conf("recap_db")


# Check if a user exists and their password is correct
def check_login(conn, username, password):
    """
    Check if a user exists in the database and verify their password.

    Args:
        conn: database connection object
        username (str): username to verify
        password (str): password to verify

    Returns:
        int: The user ID if the username exists and the password is correct.
        None: If the username does not exist.
        bool: False if the username exists but the password is incorrect.
    """
    curs = dbi.dict_cursor(conn)
    sql = "select user_id, password_hash from users where username = %s"
    curs.execute(sql, username)
    result = curs.fetchone()
    if result is None:
        return None
    else:
        # Check if the password matches the stored hash
        if check_pass(result["password_hash"], password):
            return result.get("user_id")
        else:
            return False

def check_pass(stored, password):
    """
    Verify if the input password matches the stored passwor

    Args:
        stored (str): The stored password hash.
        password (str): The input password to verify.

    Returns:
        bool: True if the password matches the stored hash, False otherwise.
    """
    hashed2 = bcrypt.hashpw(password.encode("utf-8"), stored.encode("utf-8"))
    hashed2_str = hashed2.decode("utf-8")
    if hashed2_str != stored:
        return False
    else:
        return True


# Render the user profile, including: current media list, their reviews, 
# and their profile picture if uploaded
def profile_render(conn, user_id):
    """
    Render the user profile, including current media list, their reviews,
    and their profile picture if uploaded.

    Args:
        conn: database connection object
        user_id (int): the users id

    Returns:
        tuple: A tuple containing:
            - currentsResult (list): List of the user's current media 
            - reviewsResult (list): List of the user's reviews
            - profilePic (dict): Dictionary containing the profile picture URL
    """
    curs = dbi.dict_cursor(conn)
    #get currents information
    sql = """select media.title, media_type, progress, media.media_id, 
        current_id from currents inner join media using 
        (media_id) where currents.user_id = %s
        """
    curs.execute(sql, user_id)
    currentsResult = curs.fetchall()

    #get reviews information
    sql = """select media.title, media.media_type, reviews.rating, 
        reviews.review_text from media inner join reviews using (media_id) 
        where reviews.user_id = %s
        """
    curs.execute(sql, user_id)
    reviewsResult = curs.fetchall()

    sql = """select profile_pic from users where users.user_id = %s """
    curs.execute(sql, user_id)
    profilePic = curs.fetchone()

    return currentsResult, reviewsResult, profilePic


# Insert or update the user's profile picture
def insert_pic(conn, profile_pic, user_id):
    """
    Insert or update the user's profile picture.

    Args:
        conn: database connection object
        profile_pic (str): The filename of the profile picture.
        user_id (int): The users id

    Returns:
        None
    """
    curs = dbi.cursor(conn)
    try:
        curs.execute(
            """insert into users(user_id, profile_pic) values (%s,%s)
                        on duplicate key update profile_pic = %s""",
            [user_id, profile_pic, profile_pic],
        )
        conn.commit()
        print("Picture updated")
    except Exception as err:
        print("Exception on insert of {}: {}".format(user_id, repr(err)))


# Delete the user's profile picture
def delete_pic(conn, user_id, app):
    """
    Delete the user's profile picture from the database and file system.

    Args:
        conn: database connection object
        user_id (int): users id
        app: The Flask app object in order to access the upload configuration.

    Returns:
        None
    """
    curs = dbi.cursor(conn)
    sql = "select profile_pic from users where user_id = %s"
    curs.execute(sql, [user_id])
    filename = curs.fetchone()[0]
    file_path = os.path.join(app.config['UPLOADS'],filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"File '{filename}' deleted successfully.")
    else:
        print(f"File '{filename}' does not exist.")
    curs.execute(
        """update users set profile_pic = NULL
                    where user_id = %s""",
        [user_id],
    )
    conn.commit()


# Check if an email is already associated with an account to prevent duplicates
def check_email(conn, email):
    """
    Check if an email is already associated with an account.

    Args:
        conn: database connection object
        email (str): the email address to check

    Returns:
        dict or None: Dictionary containing the email if it exists, 
        otherwise None.
    """
    curs = dbi.dict_cursor(conn)
    sql = "select email from users where email = %s"
    curs.execute(sql, email)
    result = curs.fetchone()
    return result


# Check if a username is already associated with an account to 
# prevent duplicates
def check_username(conn, username):
    """
    Check if a username is already associated with an account.

    Args:
        conn: database connection object
        username (str): the username to check

    Returns:
        dict or None: Dictionary containing the username if it exists, 
        otherwise None.
    """
    curs = dbi.dict_cursor(conn)
    sql = "select username from users where username = %s"
    curs.execute(sql, username)
    result = curs.fetchone()
    return result


# Add a new user to the database
def add_new_user(conn, username, password, email):
    """
    Add a new user to the database 

    Args:
        conn: database connection object
        username (str): The username for the new user
        password (str): The plaintext password for the new user
        email (str): The email address of the new user

    Returns:
        int or None: The user ID of the newly created user, or None if 
        insertion fails
    """
    curs = dbi.dict_cursor(conn)
    # Hash the inputted password and insert user into db
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    stored = hashed.decode("utf-8")
    # Thread safety
    try:
        sql = """
            insert into users (username, email, password_hash) 
            values (%s,%s,%s)
            """
        curs.execute(sql, [username, email, stored])
        conn.commit()
    except Exception as err:
        flash("That username is taken: {}".format(repr(err)))
        return None

    sql = "select user_id from users where username = %s"
    curs.execute(sql, username)
    result = curs.fetchone()
    return result


# Insert a new media entry into the database
def insert_media(conn, title, media_type, director, artist, author):
    """
    Insert a new media entry into the database.

    Args:
        conn: database connection object
        title (str): The title of the media
        media_type (str): The type of media
        director (str): The director of the media (if applicable)
        artist (str): The artist of the media (if applicable)
        author (str): The author of the media (if applicable)

    Returns:
        None
    """
    curs = dbi.dict_cursor(conn)
    sql = """
            INSERT INTO media (title, media_type, director, artist, author,
                addedby)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
    curs.execute(sql, (title, media_type, director, artist, author, addedby))
    conn.commit()


# Retrieve details of any given media item so it can be updated
def update_render(conn, media_id):
    """
    Get details of a given media item for updating.

    Args:
        conn: database connection object
        media_id (int): The media's id

    Returns:
        dict: Dictionary containing the media details.
    """
    curs = dbi.dict_cursor(conn)
    sql = """SELECT media_id,title, media_type, director, artist, author 
        FROM media WHERE media_id = %s"""
    curs.execute(sql, (media_id,))
    media = curs.fetchone()
    return media


# Update the details/information of an existing media item
def update_movie(conn, title, media_type, director, artist, author, media_id):
    """
    Updates the details of an existing media item.

    Args:
        conn: database connection object
        title (str): The updated title of the media.
        media_type (str): The updated type of media.
        director (str): The updated director of the media.
        artist (str): The updated artist of the media.
        author (str): The updated author of the media.
        media_id (int): The media id

    Returns:
        None
    """
    curs = dbi.dict_cursor(conn)
    sql = """
        UPDATE media
        SET title = %s, media_type = %s, director = %s, artist = %s, 
        author = %s
        WHERE media_id = %s
        """
    curs.execute(sql, (title, media_type, director, artist, author, media_id))
    conn.commit()


# Search for a piece of media based on different features
def search_render(conn, search_term, search_type):
    """
    Search for a piece of media based on different features

    Args:
        conn: database connection object
        search_term (str): The term to search for
        search_type (str or None): The media type to filter by 

    Returns:
        list: List of media matching the search criteria.
    """
    curs = dbi.dict_cursor(conn)
    search_param = f"%{search_term}%"
    param = [search_param]
    
    #query handles if there is or is not a search fileter
    if search_type:
        sql = """select media_id, title, media_type from media 
            WHERE title like %s and media_type = %s
            """
        param.append(search_type)
    else:
        sql = """select media_id, title, media_type from media 
            WHERE title like %s
            """
    curs.execute(sql, param)
    results = curs.fetchall()
    return results


# Insert a new review for a media item
def insert_review(conn, media_id, user_id, review_text, rating):
    """
    Insert a new review for media

    Args:
        conn: database connection object
        media_id (int): id of media
        user_id (int): id of user
        review_text (str): The text of the review.
        rating (int): The rating for the media

    Returns:
        None
    """
    curs = dbi.dict_cursor(conn)
    sql = """
            INSERT INTO reviews (media_id, user_id, review_text, rating) 
            VALUES (%s, %s, %s, %s)
            """
    curs.execute(sql, [media_id, user_id, review_text, rating])
    conn.commit()


# Retrieve media title based on the unique media_id
def review_render(conn, media_id):
    """
    Retrieves the media title based on the media id.

    Args:
        conn: database connection object
        media_id (int): id of the media
    Returns:
        dict: Dictionary containing the media title.
    """
    curs = dbi.dict_cursor(conn)
    sql = "select title from media where media_id = %s"
    curs.execute(sql, [media_id])
    result = curs.fetchone()
    return result


# Render the media page, including reviews and media details
def media_page_render(conn, media_id):
    """
    Renders the media page, including reviews and media details.

    Args:
        conn: database connection object
        media_id (int): id of the media

    Returns:
        dict: Dictionary containing media details and reviews.
    """
    curs = dbi.dict_cursor(conn)
    #get reviews
    sql = """select users.username, reviews.review_text, reviews.rating from 
            reviews join users on reviews.user_id = users.user_id 
            where reviews.media_id = %s"""
    curs.execute(sql, [media_id])
    reviews = curs.fetchall()

    #get media info
    sql = """select title, media_type, director, artist, author, addedby from media 
            where media_id = %s"""
    curs.execute(sql, [media_id])
    media_info = curs.fetchone()

    sql = "select avg(rating) as avg_rating from reviews where media_id = %s"
    curs.execute(sql, [media_id])
    avg_rating = curs.fetchone()

    sql = "select username from users where user_id = %s"
    curs.execute(sql, media_info['addedby'])
    username = curs.fetchone()

    result = {
        "media": {
            "title": media_info["title"],
            "media_type": media_info["media_type"],
            "director": media_info.get("director"),
            "artist": media_info.get("artist"),
            "author": media_info.get("author"),
            "addedby": username.get('username'),
            "avg_rating": avg_rating,
        },
        "reviews": reviews,
    }
    return result


# Render the user's friends list
def friends_render(conn, user_id):
    """
    Render the user's friends list

    Args:
        conn: database connection object
        user_id (int): uer's id

    Returns:
        list: List of the user's friends.
    """
    curs = dbi.dict_cursor(conn)
    sql = """select users.username, users.user_id from users inner 
            join friends on 
            friends.friend_id = users.user_id where friends.user_id = %s
            """
    curs.execute(sql, [user_id])
    friendsResult = curs.fetchall()
    return friendsResult


# Add a piece of media to the user's current progress list
def add_to_currents(conn, user_id, media_id, progress):
    """
    Add a piece of media to the user's current progress list.

    Args:
        conn: database connection object
        user_id (int): users id
        media_id (int): medias id
        progress (int): The progress percentage of the media

    Returns:
        None
    """
    curs = dbi.dict_cursor(conn)
    sql = "insert into currents (user_id, media_id, progress) values (%s,%s,%s)"
    curs.execute(sql, [user_id, media_id, progress])
    conn.commit()


# Render the form for tracking current media progres
def render_currents_form(conn, media_id):
    """
    Renders the form for tracking current media progress.

    Args:
        conn: database connection object
        media_id (int): media's id

    Returns:
        dict: Dictionary containing the media title.
    """
    curs = dbi.dict_cursor(conn)
    sql = "select title from media where media_id = %s"
    curs.execute(sql, [media_id])
    result = curs.fetchone()
    return result


# Update the progress of media in the user's current list
def update_current_progress(conn, new_progress, current_id):
    """
    Updates the progress of media in the user's current list.

    Args:
        conn: database connection object
        new_progress (int): The updated progress percentage.
        current_id (int): The unique identifier of the current progress entry.

    Returns:
        bool or None: True if updated successfully, None if media is completed.
    """
    curs = dbi.dict_cursor(conn)
    if int(new_progress) == 100:
        flash("Yay you finished it!")
        sql = "delete from currents where current_id = %s"
        curs.execute(sql, int(current_id))
        conn.commit()
        return None
    sql = "update currents set progress = %s where current_id = %s"
    curs.execute(sql, [new_progress, int(current_id)])
    conn.commit()
    return True


# Validate that a user exists with the specified unique user_id
def validate_user(conn, uid, username):
    try:
        cursor = conn.cursor()
        query = """SELECT COUNT(*) FROM users WHERE user_id = %s 
                    AND username = %s"""
        cursor.execute(query, (uid, username))
        result = cursor.fetchone()
        return result[0] > 0
    except Exception as e:
        raise RuntimeError(f"Error validating user: {e}")


# Check if a media item is already in the user's currents list
def check_currents(conn, user_id, media_id):
    """
    Check if a media item is already in the user's currents list.

    Args:
        conn: database connection object
        user_id (int): user's id
        media_id (int): the media's id

    Returns:
        bool or None: True if the media item can be added, None if 
        already exists.
    """
    curs = dbi.dict_cursor(conn)
    sql = "select current_id from currents where user_id = %s and media_id = %s"
    curs.execute(sql, [user_id, media_id])
    result = curs.fetchone()
    if result:
        flash("Already in currents")
        return None
    else:
        return True

# FRIENDS FUNCTIONS

# 1. Render Explore Friends page (shows all users who are not friends 
# with the current user)
def explore_friends_render(conn, user_id):
    """
    Renders the Explore Friends page, showing all users who are not friends 
    with the current user.

    Args:
        conn: database connection object
        user_id (int): user's id

    Returns:
        list: List of users who are not friends with the current user.
    """
    curs = dbi.dict_cursor(conn)
    
    sql = """
        SELECT u.user_id, u.username 
        FROM users u
        WHERE u.user_id != %s
        AND u.user_id NOT IN (
            SELECT friend_id 
            FROM friends 
            WHERE user_id = %s
        )
    """
    curs.execute(sql, (user_id, user_id))
    explore_friends = curs.fetchall()
    
    return explore_friends

# 2. Add Friend Function
def add_friend(conn, user_id, friend_id):
    """
    Add a friend to the user's friend list.

    Args:
        conn: database connection object
        user_id (int): user's id
        friend_id (int): friend's id

    Returns:
        None
    """
    curs = dbi.cursor(conn)
    
    try:
        sql = "INSERT INTO friends (user_id, friend_id) VALUES (%s, %s)"
        curs.execute(sql, (user_id, friend_id))
        
        conn.commit()
        flash("Friend added successfully!")
    except Exception as err:
        flash(f"Error adding friend: {repr(err)}")
        conn.rollback()

# 3. Render Searched Explore Friends page (shows all users who are not friends
# with the current user and contain the user's search term)
def search_users(conn, user_id, search_query):
    """
    Search for users by name in the Explore Friends page.

    Args:
        conn: database connection object
        user_id (int): user's id
        search_query (str): The search query for user names.

    Returns:
        list: List of users matching the search query who are not friends 
        with the current user.
    """
    curs = dbi.dict_cursor(conn)

    sql = """
        SELECT u.user_id, u.username 
        FROM users u
        WHERE u.user_id != %s
        AND u.user_id NOT IN (
            SELECT friend_id 
            FROM friends 
            WHERE user_id = %s
        )
        AND u.username LIKE %s
    """
    search_term = f"%{search_query}%"
    curs.execute(sql, (user_id, user_id, search_term))
    result = curs.fetchall()
    
    return result


# 3. Render Friends page (shows all friends of the current user)
def friends_render(conn, user_id):
    """
    Render the user's friends list.

    This function retrieves a list of friends for a given user based on 
    their user ID.

    Args:
        conn: database connection object
        user_id (int): user's id

    Returns:
        list: A list of dictionaries containing user IDs and usernames of 
        friends.
    """
    
    curs = dbi.dict_cursor(conn)
    
    sql = """
        SELECT u.user_id, u.username
        FROM users u
        JOIN friends f ON u.user_id = f.friend_id
        WHERE f.user_id = %s
    """
    curs.execute(sql, [user_id])
    friends = curs.fetchall()
    
    return friends

def remove_friend(conn,friend_id, user_id):
    """
    Remove a friend from the user's friend list.

    Args:
        conn: database connection object
        friend_id (int): friend's id
        user_id (int): user's id

    Returns:
        None
    """
    curs = dbi.dict_cursor(conn)
    
    sql = """
        delete from friends where user_id = %s and friend_id = %s 
        """
    curs.execute(sql, [user_id, friend_id])
    conn.commit()