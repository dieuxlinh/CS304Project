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


# Verify if the input password matches the stored hash
def check_pass(stored, password):
    hashed2 = bcrypt.hashpw(password.encode("utf-8"), stored.encode("utf-8"))
    hashed2_str = hashed2.decode("utf-8")
    if hashed2_str != stored:
        return False
    else:
        return True


# Render the user profile, including: current media list, their reviews, and their profile picture if uploaded
def profile_render(conn, user_id):
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
    curs = dbi.dict_cursor(conn)
    sql = "select email from users where email = %s"
    curs.execute(sql, email)
    result = curs.fetchone()
    return result


# Check if a username is already associated with an account to prevent duplicates
def check_username(conn, username):
    curs = dbi.dict_cursor(conn)
    sql = "select username from users where username = %s"
    curs.execute(sql, username)
    result = curs.fetchone()
    return result


# Add a new user to the database
def add_new_user(conn, username, password, email):
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
    curs = dbi.dict_cursor(conn)
    sql = """
            INSERT INTO media (title, media_type, director, artist, author)
            VALUES (%s, %s, %s, %s, %s)
        """
    curs.execute(sql, (title, media_type, director, artist, author))
    conn.commit()


# Retrieve details of any given media item so it can be updated
def update_render(conn, media_id):
    curs = dbi.dict_cursor(conn)
    sql = """SELECT media_id,title, media_type, director, artist, author 
        FROM media WHERE media_id = %s"""
    curs.execute(sql, (media_id,))
    media = curs.fetchone()
    return media


# Update the details/information of an existing media item
def update_movie(conn, title, media_type, director, artist, author, media_id):
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
    curs = dbi.dict_cursor(conn)
    sql = """
            INSERT INTO reviews (media_id, user_id, review_text, rating) 
            VALUES (%s, %s, %s, %s)
            """
    curs.execute(sql, [media_id, user_id, review_text, rating])
    conn.commit()


# Retrieve media title based on the unique media_id
def review_render(conn, media_id):
    curs = dbi.dict_cursor(conn)
    sql = "select title from media where media_id = %s"
    curs.execute(sql, [media_id])
    result = curs.fetchone()
    return result


# Render the media page, including reviews and media details
def media_page_render(conn, media_id):
    curs = dbi.dict_cursor(conn)
    #get reviews
    sql = """select users.username, reviews.review_text, reviews.rating from 
            reviews join users on reviews.user_id = users.user_id 
            where reviews.media_id = %s"""
    curs.execute(sql, [media_id])
    reviews = curs.fetchall()

    #get media info
    sql = """select title, media_type, director, artist, author from media 
            where media_id = %s"""
    curs.execute(sql, [media_id])
    media_info = curs.fetchone()

    sql = "select avg(rating) as avg_rating from reviews where media_id = %s"
    curs.execute(sql, [media_id])
    avg_rating = curs.fetchone()

    result = {
        "media": {
            "title": media_info["title"],
            "media_type": media_info["media_type"],
            "director": media_info.get("director"),
            "artist": media_info.get("artist"),
            "author": media_info.get("author"),
            "avg_rating": avg_rating,
        },
        "reviews": reviews,
    }
    return result


# Render the user's friends list
def friends_render(conn, user_id):
    curs = dbi.dict_cursor(conn)
    sql = """select users.username, users.user_id from users inner join friends on 
        friends.friend_id = users.user_id where friends.user_id = %s
        """
    curs.execute(sql, [user_id])
    friendsResult = curs.fetchall()
    return friendsResult


# Add a piece of media to the user's current progress list
def add_to_currents(conn, user_id, media_id, progress):
    curs = dbi.dict_cursor(conn)
    sql = "insert into currents (user_id, media_id, progress) values (%s,%s,%s)"
    curs.execute(sql, [user_id, media_id, progress])
    conn.commit()


# Render the form for tracking current media progres
def render_currents_form(conn, media_id):
    curs = dbi.dict_cursor(conn)
    sql = "select title from media where media_id = %s"
    curs.execute(sql, [media_id])
    result = curs.fetchone()
    return result


# Update the progress of media in the user's current list
def update_current_progress(conn, new_progress, current_id):
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

# 1. Render Explore Friends page (shows all users who are not friends with the current user)
def explore_friends_render(conn, user_id):
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
    curs = dbi.cursor(conn)
    
    try:
        sql = "INSERT INTO friends (user_id, friend_id) VALUES (%s, %s)"
        curs.execute(sql, (user_id, friend_id))
        
        conn.commit()
        flash("Friend added successfully!")
    except Exception as err:
        flash(f"Error adding friend: {repr(err)}")
        conn.rollback()


# 3. Render Friends page (shows all friends of the current user)
def friends_render(conn, user_id):
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
