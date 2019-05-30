import urllib.parse, base64, rsa, json, pdb

sample_response = 'method=alipay.trade.app.pay&version=1.0&format=json&app_id=2014072300007148&sign_type=RSA2&sign=VA%2BCaei%2Bjz4lzTDWnKLbpNsMEUIVWjVbKIoYwTAQ%2FDhtQifTWD4WvuSuinxkwQSjdo71YMK9mYDGy6elf%2Fnq55I0dYSgCXI2G8de1knoCdPdavweI8kIK%2ByviYjbvpMdCXBlvUaR4Yg3F9zg3mRQmjpAPB%2Byx5AEzmTUalkeojdn1ysbf1zPK9Q3MwMB14%2BOH4vQGoXRM0c8mS2bDMEXp1zin5NuSx4YrGXbmVVTDSDjU3KgV1nbqkHwmmnQ7LqSEOa3on8RrkGCak%2BP9KiYMxPnU8kX2EBYHSeOzsPUIz3ZejcJjJDZWRhtFn8gnDTlMWtEiT5dH7XNaiIKHYzLLw%3D%3D&timestamp=2019-03-25+01%3A40%3A21&biz_content=%7B%22body%22%3A%22Iphone6+16G%22%2C%22out_trade_no%22%3A%22201800000001201%22%2C%22product_code%22%3A%22QUICK_MSECURITY_PAY%22%2C%22subject%22%3A%22iphone%22%2C%22timeout_express%22%3A%2290m%22%2C%22total_amount%22%3A%229.00%22%7D&charset=utf-8'

def add_start_end(key, startMarker, endMarker):
	if key.find(startMarker) < 0:
		key = startMarker + key
	if key.find(endMarker) < 0:
		key = key + endMarker
	return key

def fill_private_key_marker(private_key):
	return add_start_end(private_key, "-----BEGIN RSA PRIVATE KEY-----\n", "\n-----END RSA PRIVATE KEY-----")

def fill_public_key_marker(public_key):
	return add_start_end(public_key, "-----BEGIN PUBLIC KEY-----\n", "\n-----END PUBLIC KEY-----")

def verify_with_rsa(public_key, message, sign):
	public_key = fill_public_key_marker(public_key)
	sign = base64.b64decode(sign)
	return rsa.verify(message, sign, rsa.PublicKey.load_pkcs1_openssl_pem(public_key))

def sign_with_rsa2(private_key, sign_content, charset):
	sign_content = sign_content.encode(charset)
	private_key = fill_private_key_marker(private_key)
	signature = rsa.sign(sign_content, rsa.PrivateKey.load_pkcs1(private_key, format='PEM'), 'SHA-256')
	sign = base64.b64encode(signature)
	sign = str(sign, encoding=charset)
	return sign

class AlipayResponse(object):

	def __init__(self):
		self.code = None
		self.msg = None
		self.sub_code = None
		self.sub_msg = None
		self.body = None

	def is_success(self):
		return not self.sub_code

	def parse_response_content(self, response_content):
		response = json.loads(response_content)
		if 'code' in response:
			self.code = response['code']
		if 'msg' in response:
			self.msg = response['msg']
		if 'sub_code' in response:
			self.sub_code = response['sub_code']
		if 'sub_msg' in response:
			self.sub_msg = response['sub_msg']
		self.body = response_content
		return response

class AlipayTradeAppPayResponse(AlipayResponse):

	def __init__(self):
		super(AlipayTradeAppPayResponse, self).__init__()
		self._out_trade_no = None
		self._seller_id = None
		self._total_amount = None
		self._trade_no = None

	@property
	def out_trade_no(self):
		return self._out_trade_no

	@out_trade_no.setter
	def out_trade_no(self, value):
		self._out_trade_no = value
	@property
	def seller_id(self):
		return self._seller_id

	@seller_id.setter
	def seller_id(self, value):
		self._seller_id = value
	@property
	def total_amount(self):
		return self._total_amount

	@total_amount.setter
	def total_amount(self, value):
		self._total_amount = value
	@property
	def trade_no(self):
		return self._trade_no

	@trade_no.setter
	def trade_no(self, value):
		self._trade_no = value

	def parse_response_content(self, response_content):
		response = super(AlipayTradeAppPayResponse, self).parse_response_content(response_content)
		if 'out_trade_no' in response:
			self.out_trade_no = response['out_trade_no']
		if 'seller_id' in response:
			self.seller_id = response['seller_id']
		if 'total_amount' in response:
			self.total_amount = response['total_amount']
		if 'trade_no' in response:
			self.trade_no = response['trade_no']

def alipayNotify(notification_sample_response, sign_key = None, sign_key_path = None):
	data = json.loads(json.loads(notification_sample_response)['result'])
	signed_content = json.dumps(data['alipay_trade_app_pay_response'], sort_keys=True, separators=(',', ':'))
	
	if sign_key is not None:
		pubic_key = sign_key
	elif sign_key_path is not None:
		content = open(sign_key_path).read()
		pubic_key = ''.join(content.split('\n')[1:-2])
	else:
		print('No signing key is given!')
		return False	
		
	try:
		if not verify_with_rsa(pubic_key, signed_content.encode('utf-8'), data['sign']):
			return False
	except:
		return False

	response = AlipayTradeAppPayResponse()
	response.parse_response_content(signed_content)
	return response

def alipayNotify1(anotification_sample_request, sign_key = None, sign_key_path = None):
	queryString = urllib.parse.urlparse(anotification_sample_request).query
	queryString = dict((itm.split('=', 1)[0], itm.split('=', 1)[1]) for itm in queryString.split('&'))
	rawString = ''
	for key in sorted(list(queryString.keys())):
		if key == 'sign' or key == 'sign_type':
			continue
		else:
			rawString = rawString + key + '=' + queryString[key] + '&'
	rawString = rawString[0:-1]

	if sign_key is not None:
		pubic_key = sign_key
	elif sign_key_path is not None:
		content = open(sign_key_path).read()
		pubic_key = ''.join(content.split('\n')[1:-2])
	else:
		print('No signing key is given!')
		return False		
	try:
		if not verify_with_rsa(pubic_key, rawString.encode('utf-8'), queryString['sign']):
			return False
		else:
			return queryString
	except:
		return False

class alipay_server:
	def __init__(self, seller_id = None, public_key_path = None, private_key_path = None, app_public_key = 'MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAoD2SrS5htJ+2IQ0WS+JbSxSnfSo/DWjWQSPHA2kJuzbuHp1D1gfUR4k+D92A5UrBb5U4AnF37e6CvUM3eyJXteR8D3MUqdpBNx0khSjkYU9AX6X/tOacgRf5VxpTQ2PWHuXaBqUA3GDZsjX8VHg3GfSO4dYVTb1xopLHfK9nAZB+VzB2MAI0V5VtBU7Tu89GNYB2gRNyAv4iZO2+iMhTGOR6rUJrd2tb61ZVdoMV5ktoXk4i3LAsOmpmW7lUjZv7rR3cwBcKRu25tjblkF29O8pRtHSrTz7kgISCN7ZpdGHoluqoI51iAuiwzzkgB8bUGNiwuymbotIW/x6E5aDxTwIDAQAB', cashier_private_key = 'MIIEpAIBAAKCAQEA5vkMRcJKx+BNXYie+grIsIlMo+ZRC5Rx6LYvmA6bwUzdX+NscYTag5skRK2KDbuWqj/8O+ImmTXGAg0uOUObjWyZafItPOJUnNUMpnj0f7lPgNBevIxlyWIQinuPejFaQbjdfCvV61ys+aF3K4aKOWQ+2iqYjzIrylH0F8lls8wMt0Hp+/68D1sx8DYF1Ua1d4yP28z9g1PpCrMM/cnzw4cAvP1IHKLs9o5nyrCimpl/l0ydesHzUGWagm4VUf20ZglaMwTksvOwAHQo2Z7AOy58KMqEeM+Yxn9XL303n1d6gKxK8sfck8+wqog3ezjJBjdHisS5Z7sraxmeazAd/QIDAQABAoIBAQDB6xDZtLEyNOjfgafvyIQMa4nUBbe/oCcuuV8mLAWq+gzWx8sxV9haLDP8ETNaKkfpsoTkBhBgC5yt9kD7xP5hc28uWyyN9HwTnG/diKnGXmAYh1kytjFzLYkzq1+fuLXNfhc+fFNDIvD7OQwjl/aPDtISOzcQ6o+Hct0b53QiybMG27NseINxGWYrQMXK2acJ36tp2ET16WwdDBS3PYWiIgHUDoWE5/YrFc0Ryr6RFErT7GoyfQL7mxlow8ALhlN5nhoelahKHnVYxJ3c9qTnpkxv6xXVvNFS3mhgGad3XBv5QY38tx7uTz1pWquxYYrp6cxxvNVKnIkUA5gVGEZBAoGBAPMxSsefzfb3rr0k1mRFb6ISp8eYsvzRcX3DJ/2Hp0QVvRcjiNIFls+veBJw/zZakFCqJf7cL+Ds0WzxuBe1e/dvR4tApF5szTpBx/t2unYhzMl9w+DYaqy0+fcRetEyz44o/GmUtmITOfizpFnME1HJiGxWU3gCK0L71gfmvg9RAoGBAPMjAq9wqrloLacspU7n0ZhzjPyDWJ0Yh0BR4C96qoA5VMdhF3n1gSZxbkHsSbztUpZ6cJv9u+C+LII5gHfR5fbl+PKT7ijXcCoM9RcDjsCECEBUVORzuLl33ZB5VvtSL2yv/Hv42ujqcKOBETlTgMRbPh4RzEA44k/ELOy44PDtAoGBAI4jITHLlPXjjZ2/Cg9RBg4UGTvvY62gPFTk21qzDnAcxIfhnPYjjiGUzPj6Ui/Sfsamq85poxIzV7P1E0PILsxPneElxuvpa4nBKMEwg4rH9olNmE6yLqcCn5ZoAQCEUgskqWKMKIzp79gMJuLVA/WpdLLdQavCmMZtqoqzsiIBAoGABFr+M1JbXJLnLnV4SJ+Se56mSee4cKf91EMjNvaFk2JziFbO6tphA+VISloHQCEoN5Xd6o1zDiWZ+oM5L+xMqE2aVg4cWBLz6Wzt/wmLRxuWYkCgfK8uAfSJvYrO6hWgz9ufNEFS+pUoi2VGf7ZlOh9AT52WARiDxVYIT/1H2kkCgYBWYO2+7vXA0ZybrTgWZ7lapykX13XQjwnqDlABWmATR3Ecv2qocA1YkzmTlY7l2ilaHkh9C2OOPiq6XtftM3nuypqxPdRd8aHk1m3XNYwtH/j/phE+rwvLgMuKrkiBDecoHEq10+rPNqIQmhjm+BGCAzEuf4fxLZC8MP3MGLCUIA=='):
		self.app_public_key = app_public_key
		self.cashier_private_key = cashier_private_key
		self.seller_id = seller_id
		if public_key_path is not None:
			self.loadPublicKeyfromPEM(public_key_path)
		if private_key_path is not None:
			self.loadPrivateKeyfromPEM(private_key_path)

	def loadPublicKeyfromPEM(self, fileName="/home/mike/Desktop/new_test/python-alipay-sdk/public_key.pem"):
		content = open(fileName).read()
		self.app_public_key = ''.join(content.split('\n')[1:-2])

	def loadPrivateKeyfromPEM(self, fileName="/home/mike/Desktop/new_test/python-alipay-sdk/private_key.pem"):
		content = open(fileName).read()
		self.cashier_private_key = ''.join(content.split('\n')[1:-2])

	def synchronous_notification(self, response):
		notification_sample_response = {"memo":"sdk_testing", "result":{"alipay_trade_app_pay_response":{"code":"10000", "msg":"Success", "app_id":"", "out_trade_no":"", "trade_no":"2016081621001004400236957647", "total_amount":"", "seller_id":"2088301194649043", "charset":"utf-8", "timestamp":"2016-10-11 17:43:36"}, "sign":"", "sign_type": "RSA2"}, "resultStatus":"9000"}

		app_id = ""
		out_trade_no = ""
		total_amount = ""

		element = []
		signature = None
		for item in urllib.parse.unquote_plus(response).split('&'):
			if 'sign=' not in item:
				element.append(item)
			else:
				signature = item.split('=', 1)[1]

			if 'app_id=' in item:
				app_id = item.split('app_id=')[1]
			elif 'biz_content=' in item:
				biz_content = json.loads(item.split('=')[1])
				if 'out_trade_no' in list(biz_content.keys()):
					out_trade_no = biz_content['out_trade_no']
				if 'total_amount' in list(biz_content.keys()):
					total_amount = biz_content['total_amount']

		sign_content = '&'.join(sorted(element))
		try:
			verify_res = verify_with_rsa(self.app_public_key, sign_content.encode('utf-8') ,signature)
		except:
			print('fail to verify the signature in Alipay server!')
			return -1
		if not verify_res:
			print('fail to verify the signature in Alipay server!')
			return -1

		charset = notification_sample_response['result']['alipay_trade_app_pay_response']['charset']
		notification_sample_response['result']['alipay_trade_app_pay_response']['app_id'] = app_id
		notification_sample_response['result']['alipay_trade_app_pay_response']['out_trade_no'] = out_trade_no
		notification_sample_response['result']['alipay_trade_app_pay_response']['total_amount'] = total_amount
		if self.seller_id is not None:
			notification_sample_response['result']['alipay_trade_app_pay_response']['seller_id'] = self.seller_id
		sign_content = json.dumps(notification_sample_response['result']['alipay_trade_app_pay_response'], sort_keys=True, separators=(',', ':'))
		
		sign = sign_with_rsa2(self.cashier_private_key, sign_content, charset)
		notification_sample_response['result']['sign'] = sign
		notification_sample_response["result"] = json.dumps(notification_sample_response["result"], sort_keys=True, separators=(',', ':'))
		notification_sample_response = json.dumps(notification_sample_response)

		return notification_sample_response

	def asynchronous_notification(self, response):
		anotification_sample_request = 'https://api.xx.com/receive_notify.htm?total_amount=&buyer_id=2088102116773037&body=test&trade_no=2016081621001004400236957647&refund_fee=0.00&notify_time=2016-07-19 14:10:49&subject=test&sign_type=RSA2&charset=utf-8&notify_type=trade_status_sync&out_trade_no=&gmt_close=2016-07-19 14:10:46&gmt_payment=2016-07-19 14:10:47&trade_status=TRADE_SUCCESS&version=1.0&sign=&gmt_create=2016-07-19 14:10:44&app_id=&seller_id=2088301194649043&notify_id=4a91b7a78a503640467525113fb7d8bg8e'

		queryString = urllib.parse.urlparse(anotification_sample_request).query
		queryString = dict((itm.split('=')[0], itm.split('=')[1]) for itm in queryString.split('&'))

		app_id = ""
		out_trade_no = ""
		total_amount = ""

		element = []
		signature = None
		for item in urllib.parse.unquote_plus(response).split('&'):
			if 'sign=' not in item:
				element.append(item)
			else:
				signature = item.split('=', 1)[1]

			if 'app_id=' in item:
				app_id = item.split('app_id=')[1]
			elif 'biz_content=' in item:
				biz_content = json.loads(item.split('=')[1])
				if 'out_trade_no' in list(biz_content.keys()):
					out_trade_no = biz_content['out_trade_no']
				if 'total_amount' in list(biz_content.keys()):
					total_amount = biz_content['total_amount']

		sign_content = '&'.join(sorted(element))
		try:
			verify_res = verify_with_rsa(self.app_public_key, sign_content.encode('utf-8') ,signature)
		except:
			print('fail to verify the signature in Alipay server!')
			return -1
		if not verify_res:
			print('fail to verify the signature in Alipay server!')
			return -1

		queryString['app_id'] = app_id
		queryString['out_trade_no'] = out_trade_no
		queryString['total_amount'] = total_amount
		if self.seller_id is not None:
			queryString['seller_id'] = self.seller_id

		rawString = ''
		for key in sorted(list(queryString.keys())):
			if key == 'sign' or key == 'sign_type':
				continue
			else:
				rawString = rawString + key + '=' + str(queryString[key]) + '&'
		rawString = rawString[0:-1]
		sign = sign_with_rsa2(self.cashier_private_key, rawString, queryString['charset'])
		queryString['sign'] = sign

		anotification_sample_request = (anotification_sample_request.split('?')[0] + '?' + rawString + '&sign_type=' + queryString['sign_type'] + '&sign=' + sign)

		return anotification_sample_request
