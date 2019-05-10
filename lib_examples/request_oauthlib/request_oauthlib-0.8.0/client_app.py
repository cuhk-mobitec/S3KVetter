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
@symbolic(Req0Flag = 1, Req1Flag = 1, Req2Flag =1, isHttps=1, params={'code':'wrongcodeval', 'state': '123', 'refresh_token':'victimtoken'})
def client_app(Req0Flag, Req1Flag, Req2Flag, isHttps, params):
	IdPObj = None

	authorization_url = ''
	state = None
	token = '1234'
	user = None

	if isHttps:
		request_url='https://www.example.com/callback'
	else:
		request_url='http://www.example.com/callback'
	
	#Redirect user to IdP for authorization
	if Req0Flag == 1:
		IdPObj = OAuth2Session(client_id, redirect_uri=request_url)
		try:
			authorization_url, state = IdPObj.authorization_url(request_url, state=params['state'])
		except:
			return {'token':None, 'state':None, 'refresh_token':None}

	#Get the access token
	if Req1Flag == 1:
		if not IdPObj:
			IdPObj = OAuth2Session(client_id, redirect_uri=request_url)
		try:
			token = IdPObj.my_fetch_token(token_url, client_secret=client_secret, 
				authorization_response=request_url, params=params)
		except:
			return {'token':None, 'state':None, 'refresh_token':None}

	#Shuffle the request order
	if Req0Flag == 2:
		IdPObj = OAuth2Session(client_id, redirect_uri=request_url)
		try:
			authorization_url, state = IdPObj.authorization_url(request_url, state=params['state'])
		except:
			return {'token':None, 'state':None, 'refresh_token':None}

	#Retrieve User Info
	if Req2Flag == 1:
		if not IdPObj:
			IdPObj = OAuth2Session(client_id, redirect_uri=request_url)

		#user = IdPObj.get('https://api.github.com/user')

	if IdPObj != None:
		returnAT = None
		if 'access_token' in IdPObj.token:
			returnAT = IdPObj.token['access_token']
		elif IdPObj._client.access_token != None:
			returnAT = IdPObj._client.access_token
		if returnAT == '':
			returnAT = None
		returnRT = None
		if 'refresh_token' in IdPObj.token:
			returnRT = IdPObj.token['refresh_token']
		elif IdPObj._client.refresh_token != None:
			returnRT = IdPObj._client.refresh_token
		if returnRT == '':
			returnRT = None
		returnState = params['state']
		if IdPObj._state:
			returnState = IdPObj._state
		return {'token':returnAT, 'state':returnState, 'refresh_token':returnRT}
	else:
		return {'token':None, 'state':None, 'refresh_token':None}
	

