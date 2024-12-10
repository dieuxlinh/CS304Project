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

dbi.conf("recap_db")


def check_login(conn, username, password):
    curs = dbi.dict_cursor(conn)
    sql = "select user_id, password_hash from users where username = %s"
    curs.execute(sql, username)
    result = curs.fetchone()
    if result is None:
        return None
    else:
        if check_pass(result["password_hash"], password):
            return result.get('user_id')
        else:
            return False


def check_pass(stored, password):
    hashed2 = bcrypt.hashpw(password.encode("utf-8"), stored.encode("utf-8"))
    hashed2_str = hashed2.decode("utf-8")
    if hashed2_str != stored:
        return False
    else:
        return True


def profile_render(conn, session):
    curs = dbi.dict_cursor(conn)
    sql = """select media.title, media_type, progress, media.media_id, 
        current_id from currents inner join media using 
        (media_id) where currents.user_id = %s
        """
    curs.execute(sql, session["uid"])
    currentsResult = curs.fetchall()

    sql = """select media.title, media.media_type, reviews.rating, 
        reviews.review_text from media inner join reviews using (media_id) 
        where reviews.user_id = %s
        """
    curs.execute(sql, session["uid"])
    reviewsResult = curs.fetchall()

    sql = '''select profile_pic from users where users.user_id = %s '''
    curs.execute(sql, session['uid'])
    profilePic = curs.fetchone()

    return currentsResult, reviewsResult, profilePic

def insert_pic(conn, profile_pic, user_id):
    curs = dbi.cursor(conn)
    try:
        curs.execute('''insert into users(user_id, profile_pic) values (%s,%s)
                        on duplicate key update profile_pic = %s''',
                     [user_id, profile_pic, profile_pic])
        conn.commit()
        print('Picture updated')
    except Exception as err:
        print('Exception on insert of {}: {}'.format(user_id, repr(err)))

def delete_pic(conn, user_id):
    curs = dbi.cursor(conn)
    path = '/'
    curs.execute('''update users set profile_pic = NULL
                    where user_id = %s''',
                 [user_id])
    conn.commit()

def check_email(conn, email):
    curs = dbi.dict_cursor(conn)
    # check if email or username are alreay associated with an account
    sql = "select email from users where email = %s"
    curs.execute(sql, email)
    result = curs.fetchone()
    return result


def check_username(conn, username):
    curs = dbi.dict_cursor(conn)
    sql = "select username from users where username = %s"
    curs.execute(sql, username)
    result = curs.fetchone()
    return result


def add_new_user(conn, username, password, email):
    curs = dbi.dict_cursor(conn)
    # hash the inputted password and insert user into db
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    stored = hashed.decode("utf-8")
    # thread safety
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


def insert_media(conn, title, media_type, director, artist, author):
    curs = dbi.dict_cursor(conn)
    sql = """
            INSERT INTO media (title, media_type, director, artist, author)
            VALUES (%s, %s, %s, %s, %s)
        """
    curs.execute(sql, (title, media_type, director, artist, author))
    conn.commit()


def update_render(conn, media_id):
    curs = dbi.dict_cursor(conn)
    sql = """SELECT media_id,title, media_type, director, artist, author 
        FROM media WHERE media_id = %s"""
    curs.execute(sql, (media_id,))
    media = curs.fetchone()
    return media


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


def search_render(conn, search_term):
    curs = dbi.dict_cursor(conn)
    search_param = f"%{search_term}%"
    sql = """select media_id, title, media_type from media 
            WHERE title like %s
        """
    curs.execute(sql, search_param)
    results = curs.fetchall()
    return results


def insert_review(conn, media_id, user_id, review_text, rating):
    curs = dbi.dict_cursor(conn)
    sql = """
            INSERT INTO reviews (media_id, user_id, review_text, rating) 
            VALUES (%s, %s, %s, %s)
            """
    curs.execute(sql, [media_id, user_id, review_text, rating])
    conn.commit()


def review_render(conn, media_id):
    curs = dbi.dict_cursor(conn)
    sql = "select title from media where media_id = %s"
    curs.execute(sql, [media_id])
    result = curs.fetchone()
    return result


def media_page_render(conn, media_id):
    curs = dbi.dict_cursor(conn)
    sql = """select users.username, reviews.review_text, reviews.rating from 
            reviews join users on reviews.user_id = users.user_id 
            where reviews.media_id = %s"""
    curs.execute(sql, [media_id])
    reviews = curs.fetchall()

    sql = """select title, media_type, director, artist, author from media 
            where media_id = %s"""
    curs.execute(sql, [media_id])
    media_info = curs.fetchone()

    # should we round this?
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


def friends_render(conn, user_id):
    curs = dbi.dict_cursor(conn)
    sql = """select users.username from users inner join friends on 
        friends.friend_id = users.user_id where friends.user_id = %s
        """
    curs.execute(sql, [user_id])
    friendsResult = curs.fetchall()
    return friendsResult

def add_to_currents(conn, user_id, media_id, progress):
    curs = dbi.dict_cursor(conn)
    sql = "insert into currents (user_id, media_id, progress) values (%s,%s,%s)"
    curs.execute(sql, [user_id, media_id, progress])
    conn.commit()


def render_currents_form(conn, media_id):
    curs = dbi.dict_cursor(conn)
    sql = "select title from media where media_id = %s"
    curs.execute(sql, [media_id])
    result = curs.fetchone()
    return result


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
    