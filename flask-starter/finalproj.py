import cs304dbi as dbi
import bcrypt
dbi.conf('recap_db')

def check_login(conn,username,password):
    curs = dbi.dict_cursor(conn)
    sql = "select user_id, password_hash from users where username = %s"
    curs.execute(sql, username)
    result = curs.fetchone()
    if result is None:
        return None
    else:
        if(check_pass(result['password_hash'], password)):
            return result
        else:
            return False

def check_pass(stored, password):
    hashed2 = bcrypt.hashpw(password.encode('utf-8'), 
                                    stored.encode('utf-8'))
    hashed2_str = hashed2.decode('utf-8')
    if(hashed2_str != stored):
        return False
    else:
        return True

def profile_render(conn, session):
    curs = dbi.dict_cursor(conn)
    sql = '''select media.title from currents inner join media using 
        (media_id) where currents.user_id = %s
        '''
    curs.execute(sql, session['uid'])
    currentsResult = curs.fetchall()
        
    sql = '''select users.username from users inner join friends on 
        friends.friend_id = users.user_id where friends.user_id = %s
        '''
    curs.execute(sql, session['uid'])
    friendsResult = curs.fetchall()

    sql = '''select media.title, reviews.rating, reviews.review_text from 
        media inner join reviews using (media_id) where reviews.user_id = %s
        '''
    curs.execute(sql, session['uid'])
    reviewsResult = curs.fetchall()

    sql = '''select profile_pic from users where users.user_id = %s '''
    curs.execute(sql, session['uid'])
    profilePic = curs.fetchone()

    return currentsResult, friendsResult, reviewsResult, profilePic

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
    curs.execute('''update users set profile_pic = NULL
                    where user_id = %s''',
                 [user_id])
    conn.commit()

def check_email(conn,email):
    curs = dbi.dict_cursor(conn)
    #check if email or username are alreay associated with an account
    sql = "select email from users where email = %s"
    curs.execute(sql, email)
    result = curs.fetchone()
    return result

def check_username(conn,username):
    curs = dbi.dict_cursor(conn)
    sql = "select username from users where username = %s"
    curs.execute(sql, username)
    result = curs.fetchone()
    return result

def add_new_user(conn, username,password,email):
    curs = dbi.dict_cursor(conn)
   # hash the inputted password and insert user into db
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    stored = hashed.decode('utf-8')
    sql = '''
        insert into users (username, email, password_hash) values (%s,%s,%s)
        '''
    curs.execute(sql, [username, email, stored])
    conn.commit()
            

    sql = 'select user_id from users where username = %s'
    curs.execute(sql, username)
    result = curs.fetchone()
    return result

def insert_media(conn,title,media_type,director,artist,author):
    curs = dbi.dict_cursor(conn)
    sql = """
            INSERT INTO media (title, media_type, director, artist, author)
            VALUES (%s, %s, %s, %s, %s)
        """
    curs.execute(sql, (title, media_type, director, artist, author))
    conn.commit()

def update_render(conn,media_id):
    curs = dbi.dict_cursor(conn)
    sql = """SELECT media_id,title, media_type, director, artist, author 
        FROM media WHERE media_id = %s"""
    curs.execute(sql, (media_id,))
    media = curs.fetchone()
    return media

def update_movie(conn,title,media_type,director,artist,author,media_id):
    curs = dbi.dict_cursor(conn)
    sql = """
        UPDATE media
        SET title = %s, media_type = %s, director = %s, artist = %s, 
        author = %s
        WHERE media_id = %s
        """
    curs.execute(sql, (title, media_type, director, artist, author, 
                               media_id))
    conn.commit()

def search_render(conn,search_term):
    curs = dbi.dict_cursor(conn)
    search_param = f"%{search_term}%"
    sql = '''select media_id, title, media_type from media WHERE title like %s'''
    curs.execute(sql, search_param)
    results = curs.fetchall()
    return results

def insert_review(conn,media_id,user_id,review_text,rating):
    curs = dbi.dict_cursor(conn)
    sql = """
            INSERT INTO reviews (media_id, user_id, review_text, rating) 
            VALUES (%s, %s, %s, %s)
            """
    curs.execute(sql, [media_id, user_id, 
    review_text, rating])
    conn.commit()

def review_render(conn,media_id):
    sql = "select title from media where media_id = %s"
    curs = dbi.dict_cursor(conn)
    curs.execute(sql, [media_id])
    result = curs.fetchone()
    return result