from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Following(db.Model):
    __tablename__ = 'following'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    follows_me = db.Column(db.Boolean, default=False)
    first_seen = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    current_status = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Following {self.username}>'

class FollowHistory(db.Model):
    __tablename__ = 'follow_history'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    event_type = db.Column(db.String(20), nullable=False)  # 'new_follow' 或 'unfollow'
    event_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<FollowHistory {self.username} {self.event_type}>'
