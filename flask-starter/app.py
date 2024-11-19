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
                           page_title='Main Page')

# You will probably not need the routes below, but they are here
# just in case. Please delete them if you are not using them

@app.route('/login/', methods=["GET", "POST"])
def login():
    if request.method == 'GET':
        return render_template('login.html',
                               page_title='Login form')
    else:
        try:
            # throws error if there's trouble
            username = request.form['username']
            password = request.form['pass'] 
            pass1 = password
            hashed = bcrypt.hashpw(pass1.encode('utf-8'), bcrypt.gensalt())
            stored = hashed.decode('utf-8')
            
            flash('form submission successful')
            #redirect to profile upon login
            return render_template('profile.html')

        except Exception as err:
            flash('form submission error'+str(err))
            return redirect( url_for('index') )

# This route displays all the data from the submitted form onto the rendered page
# It's unlikely you will ever need anything like this in your own applications, so
# you should probably delete this handler

@app.route('/profile/', methods=['GET','POST'])
def profile():
    if request.method == 'GET':
        return render_template('form_data.html',
                               page_title='Display of Form Data',
                               method=request.method,
                               form_data=request.args)
    elif request.method == 'POST':
        return render_template('form_data.html',
                               page_title='Display of Form Data',
                               method=request.method,
                               form_data=request.form)
    else:
        raise Exception('this cannot happen')

# This route shows how to render a page with a form on it.

@app.route('/CreateAccount/')
def newAcc():
    conn = dbi.connect()
    curs = dbi.dict_cursor(conn)
    if request.method == 'GET':
        return render_template('createAccount.html',
                               page_title='Create Account')
    else:
        try:
            # throws error if there's trouble
            email = request.form['email']
            username = request.form['username']
            password = request.form['pass'] 
            sql = "select * from users where email = %s"

            pass1 = password
            hashed = bcrypt.hashpw(pass1.encode('utf-8'), bcrypt.gensalt())
            stored = hashed.decode('utf-8')
            flash('form submission successful')
            #redirect to profile upon login
            return render_template('profile.html')

        except Exception as err:
            flash('form submission error'+str(err))
            return redirect( url_for('index') )


if __name__ == '__main__':
    import sys, os
    if len(sys.argv) > 1:
        # arg, if any, is the desired port number
        port = int(sys.argv[1])
        assert(port>1024)
    else:
        port = os.getuid()
    # set this local variable to 'wmdb' or your personal or team db
    db_to_use = 'put_database_name_here_db' 
    print(f'will connect to {db_to_use}')
    dbi.conf(db_to_use)
    app.debug = True
    app.run('0.0.0.0',port)
