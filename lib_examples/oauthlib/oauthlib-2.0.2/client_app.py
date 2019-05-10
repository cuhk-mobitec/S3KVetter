#! /usr/bin/python
# -*- coding:utf-8 -*-

# ----- Import Section -----
from oauthlib.oauth2 import WebApplicationClient
from symbolic.args import *
import urllib.request
# ----- End of Import Section -----


# ----- Constant Declaration -----
client = WebApplicationClient('your_id')
coordination= 0
# ----- End of Constant Declaration -----

@symbolic(Req0Flag=1, Req1Flag=1, isHttps=1, useState=1, params={'code':'wrongcodeval','state':'sfetw45','access_token':"1234",'refresh_token':"4321", 'mac_key':"abcdef"})
def client_app(Req0Flag, Req1Flag, isHttps, useState, params):
	
	#Redirect user to IdP for authorization
	if useState:
		stateVal = 'sfetw45'
	else:
		stateVal = ''
	if isHttps:
		auth_url = 'https://example.com'
	else:
		auth_url = 'http://example.com'

	if Req0Flag == 1:
		try:
			auth_url = client.prepare_request_uri(auth_url, scope=['profile', 'pictures'], state=stateVal)
		except:
			return {'refresh_token':None, 'code':None, 'token':None, 'mac_key':None}

	#Get the access token
	if Req1Flag == 1:
		client.my_parse_request_uri_response(auth_url, params, state=stateVal)
		para = client.prepare_request_body()

		if 'code' in params and params['code'] =='correctcodeval':
			body = '{\
				"access_token":"2YotnFZFEjr1zCsicMWpAA",\
				"token_type":"example",\
				"expires_in":3600,\
				"refresh_token":"tGzv3JOkF0XG5Qx2TlKWIA",\
				"example_parameter":"example_value"\
			}'
		else:
			body = '{\
				"error":"error msg",\
				"access_token":"",\
				"token_type":"example",\
				"expires_in":3600,\
				"refresh_token":"",\
				"example_parameter":"example_value"\
			}'
		client.my_parse_token_response(body)

	#Shuffle the request order
	if Req0Flag == 2:
		try:
			auth_url = client.prepare_request_uri(auth_url, scope=['profile', 'pictures'], state='sfetw45')
		except:
			return {'refresh_token':None, 'code':None, 'token':None, 'mac_key':None}

	#Retrieve User Info
	#if Req2Flag != 0:
	return {'refresh_token':client.refresh_token, 'code':client.code, 'token':client.access_token, 'mac_key':client.mac_key}

	
		