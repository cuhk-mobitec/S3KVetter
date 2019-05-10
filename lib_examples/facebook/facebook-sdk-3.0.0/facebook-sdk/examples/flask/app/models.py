from datetime import datetime
'''
from app import db


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String, nullable=False, primary_key=True)
    created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated = db.Column(db.DateTime, default=datetime.utcnow, nullable=False,
                        onupdate=datetime.utcnow)
    name = db.Column(db.String, nullable=False)
    profile_url = db.Column(db.String, nullable=False)
    access_token = db.Column(db.String, nullable=False)
'''
class User:
    def __init__(self,id,name,profile_url,access_token):
	    self.id = id
	    self.name = name
	    self.profile_url = profile_url
	    self.access_token = access_token
