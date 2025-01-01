from flask import Blueprint, render_template, request, session, flash, redirect

from app.config import Config

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and Config.USERNAME != "" and Config.PASSWORD != "":
        username = request.form['username']
        password = request.form['password']
        
        print(Config.USERNAME, Config.PASSWORD, username, password)
        if username == Config.USERNAME and password == Config.PASSWORD:
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect("/")
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out', 'success')
    return redirect("/")
