#! /usr/bin/python
# -*- coding:utf-8 -*-

# ----- Import Section -----
from facebook import get_user_from_cookie, GraphAPI,auth_url
from symbolic.args import *
from urllib import parse
# ----- End of Import Section -----


# ----- Constant Declaration -----
FB_APP_ID = '156258847901639'
FB_APP_NAME = 'LoginSample'
FB_APP_SECRET = '3ea39e503951c8db93ef73d68fd6f22a'
# ----- End of Constant Declaration -----


@symbolic(Req0Flag=1, Req1Flag=1, isHttps=1, cookies={"fbm_15625884790163":"base_domain=.yangronghai.github.io","fbsr_156258847901639":{"sig":"sig", "value": {"algorithm":"HMAC-SHA256","code":"AQC7RIzPz256ZXfsttR30OaqgsXwWdPyPI7txwIhhBk_QKeKhHoq112N9_dPcfWSXIhWrPYDtIvUArtS08CRD2nwet6PkmGbz6CAK04XjVEPcKMyvhbPGOaOTRMBvNFBXCMYF7x6kwAlVPWU92-HmdLOkcHesN3cVaRWpxW9Lyp7Ioc3Ft60mBVx6Ryo2pqooVD50WEcpHTg4GS3pG9l22mFyrYDUVJDeqDl8U8tt2cqohIeyx2D79fJKFfkQj13thu7moWNY8GVzyr5LR5bfZf_D7Z2RjK16xQEa_x-q45PwYQ6VULtwLyz0hrEE5EAc43sKbfi5XgdeVpmd_IM17uM","issued_at":1489387950,"user_id":1500071776953231}}})
def client_app(Req0Flag,Req1Flag,isHttps,cookies):

	graph = GraphAPI(version='2.2')
	hasState = 0
	
	#Redirect user to IdP for authorization
	perms = ['manage_pages']
	if isHttps == 1:
		canvas_url = 'https://domain.com/that-handles-auth-response/'
	else:
		canvas_url = 'http://domain.com/that-handles-auth-response/'
	if Req0Flag == 1:
		authUrl = auth_url(FB_APP_ID, canvas_url, perms)
		if 'state' in parse.parse_qs(parse.urlsplit(authUrl).query):
			hasState = 1

	#Get the access token
	tokenInfo = None
	if Req1Flag == 1:
		tokenInfo = get_user_from_cookie(cookies=cookies, app_id=FB_APP_ID,
                                  app_secret=FB_APP_SECRET)
		
	#Shuffle the request order
	if Req0Flag == 2:
		authUrl = auth_url(FB_APP_ID, canvas_url, perms)

	try:
		usedCode = cookies['fbsr_156258847901639']['value']['code']
	except:
		usedCode = None
	if not usedCode:
		usedCode = None
	
	if tokenInfo == None:
		return {'token':None, 'hasState':hasState, 'code':usedCode}
	else:
		return {'token':tokenInfo['access_token'], 'hasState':hasState, 'code':usedCode}



	