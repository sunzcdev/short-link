import os
import string
import random
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, abort
from flask_sqlalchemy import SQLAlchemy
from user_agents import parse

app = Flask(__name__)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'data', 'shortlink.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'

db = SQLAlchemy(app)


class ShortLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_url = db.Column(db.String(2048), nullable=False)
    short_code = db.Column(db.String(16), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    visits = db.relationship('Visit', backref='short_link', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<ShortLink {self.short_code} -> {self.original_url}>'


class Visit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    short_link_id = db.Column(db.Integer, db.ForeignKey('short_link.id'), nullable=False)
    ip_address = db.Column(db.String(64))
    user_agent = db.Column(db.String(512))
    browser = db.Column(db.String(64))
    os = db.Column(db.String(64))
    device = db.Column(db.String(64))
    visited_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Visit {self.ip_address} at {self.visited_at}>'


def generate_short_code(length=6):
    chars = string.ascii_letters + string.digits
    while True:
        code = ''.join(random.choice(chars) for _ in range(length))
        if not ShortLink.query.filter_by(short_code=code).first():
            return code


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/stats')
def stats_page():
    return render_template('stats.html')


@app.route('/api/shorten', methods=['POST'])
def create_short_link():
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({'error': 'URL is required'}), 400

    original_url = data['url'].strip()
    if not original_url.startswith(('http://', 'https://')):
        original_url = 'https://' + original_url

    existing = ShortLink.query.filter_by(original_url=original_url).first()
    if existing:
        short_url = f"{request.host_url}{existing.short_code}"
        return jsonify({
            'short_code': existing.short_code,
            'short_url': short_url,
            'original_url': existing.original_url
        })

    short_code = generate_short_code()
    new_link = ShortLink(original_url=original_url, short_code=short_code)
    db.session.add(new_link)
    db.session.commit()

    short_url = f"{request.host_url}{short_code}"
    return jsonify({
        'short_code': short_code,
        'short_url': short_url,
        'original_url': original_url
    })


@app.route('/<short_code>')
def redirect_to_original(short_code):
    link = ShortLink.query.filter_by(short_code=short_code).first()
    if not link:
        abort(404)

    user_agent_string = request.headers.get('User-Agent', '')
    user_agent = parse(user_agent_string)

    visit = Visit(
        short_link_id=link.id,
        ip_address=request.remote_addr,
        user_agent=user_agent_string[:512],
        browser=user_agent.browser.family,
        os=user_agent.os.family,
        device=user_agent.device.family,
        visited_at=datetime.utcnow()
    )
    db.session.add(visit)
    db.session.commit()

    return redirect(link.original_url)


@app.route('/api/stats/<short_code>')
def get_stats(short_code):
    link = ShortLink.query.filter_by(short_code=short_code).first()
    if not link:
        return jsonify({'error': 'Short code not found'}), 404

    total_visits = link.visits.count()
    unique_ips = db.session.query(Visit.ip_address).filter_by(short_link_id=link.id).distinct().count()

    recent_visits = link.visits.order_by(Visit.visited_at.desc()).limit(10).all()
    visits_list = []
    for v in recent_visits:
        visits_list.append({
            'ip': v.ip_address,
            'browser': v.browser,
            'os': v.os,
            'device': v.device,
            'time': v.visited_at.strftime('%Y-%m-%d %H:%M:%S UTC')
        })

    return jsonify({
        'short_code': short_code,
        'original_url': link.original_url,
        'created_at': link.created_at.strftime('%Y-%m-%d %H:%M:%S UTC'),
        'total_visits': total_visits,
        'unique_visitors': unique_ips,
        'recent_visits': visits_list
    })


@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
