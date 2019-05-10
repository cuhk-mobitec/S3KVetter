#! /usr/bin/python
# -*- coding:utf-8 -*-

# ----- Import Section -----
from requests_oauthlib import OAuth2Session
from symbolic.args import *
# ----- End of Import Section -----


# ----- Constant Declaration -----
client_id = '1234'
client_secret = "clientsecret"
authorization_base_url = 'https://github.com/login/oauth/authorize'
token_url = 'https://github.com/login/oauth/access_token'
# ----- End of Constant Declaration -----


#Function Start
@symbolic(Req0Flag = 1, Req1Flag = 1, Req2Flag =1, request_url='http://www.example.com/callback', params={'code': 'codevalue', 'state': '1234'})
def client_app(Req0Flag, Req1Flag, Req2Flag, request_url, params):
	IdPObj = None

	authorization_url = ''
	state = ''
	token = '1234'
	user = None
	
	#Redirect user to IdP for authorization
	if Req0Flag == 0:
		IdPObj = OAuth2Session(client_id)
		authorization_url, state = IdPObj.authorization_url('')

	#Get the access token
	if Req1Flag != 0:
		if not IdPObj:
			IdPObj = OAuth2Session(client_id)

		token = IdPObj.my_fetch_token(token_url, client_secret=client_secret, 
			authorization_response=request_url, params=params)

	#Shuffle the request order
	if Req0Flag == 2:
		IdPObj = OAuth2Session(client_id)
		authorization_url, state = IdPObj.authorization_url('')

	#Retrieve User Info
	if Req2Flag != 0:
		if not IdPObj:
			IdPObj = OAuth2Session(client_id)

		user = IdPObj.get('https://api.github.com/user')
	
	if user == None:
		return {'token':token, 'user':None}
	else:
		return {'token':token, 'user':'USERID'}

