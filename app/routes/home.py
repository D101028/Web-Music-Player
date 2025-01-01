from flask import Blueprint, render_template, redirect, send_file

from app.support.user import check_auth

home_bp = Blueprint('home', __name__)

@home_bp.route('/')
def home():
    if check_auth():
        return render_template('index.html')
    return redirect('login')

@home_bp.route('/robots.txt')
def robot_txt():
    return send_file("static/robots.txt")

@home_bp.route('/favicon.ico')
def favicon():
    return send_file("static/favicon.ico")

