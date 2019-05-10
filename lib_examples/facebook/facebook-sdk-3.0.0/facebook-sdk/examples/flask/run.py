#!/usr/bin/env python
from os import environ

from app import app
# from app import db

#db.create_all()
def run():
	app.run(host='0.0.0.0', port=8001)
