import hashlib

from flask import (session, request, render_template, flash, redirect, url_for)
from functools import wraps
from pyDimension import app

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' in session:
            return f(*args, **kwargs)
        return redirect(url_for('login', next=request.url))
    return decorated_function
    
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        passwd = hashlib.sha512(request.form['password']).hexdigest()
        next = request.form['next']
        if (request.form['username'] == app.config['USERNAME'] and
            passwd == app.config['PASSWORD_HASH']):
            session['username'] = request.form['username']
            if next:
                return redirect(next)
            else:
                return redirect(url_for('control_panel'))
        else:
            flash('Login Failed: Username/Password incorrect.', category='error')
            
    return render_template('login.html', next=request.args.get('next'))


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('control_panel'))
