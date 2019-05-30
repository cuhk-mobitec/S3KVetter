import hashlib

def to_xml(raw):
	s = ""
	for k, v in raw.items():
		s += "<{0}>{1}</{0}>".format(k, v)
	s = "<xml>{0}</xml>".format(s)
	return s

def sign(raw, mch_key):
	raw = [(k, str(raw[k]) if isinstance(raw[k], int) else raw[k]) for k in sorted(raw.keys())]
	s = "&".join("=".join(kv) for kv in raw if kv[1])
	s += "&key={0}".format(mch_key)
	return hashlib.md5(s.encode("utf-8")).hexdigest().upper()

def check(data, mch_key):
	signature = data.pop("sign")
	return signature == sign(data, mch_key)

class wx_server:
	
	def __init__(self, appid = 'wxd678efh567hg6787', mch_id = '1230000109', api_key = '192006250b4c09247ec02edce69f6a2d'):
		self.api_key = api_key
		self.appid = appid
		self.mch_id = mch_id
		self.order_recorder = {}
		self.paid_order = {}

	def __del__(self):
		self.order_recorder = {}
		self.paid_order = {}

	def app_unified_order(self, total_fee, out_trade_no):
		order = {}
		order['return_code'] = 'SUCCESS'
		order['return_msg'] = 'OK'
		order['appid'] = self.appid
		order['mch_id'] = self.mch_id
		order['nonce_str'] = 'IITRi8Iabbblz1Jc'
		order['sign'] = None
		order['result_code'] = 'SUCCESS'
		order['prepay_id'] = 'wx201411101639507cbf6ffd8b0779950874'
		order['trade_type'] = 'APP'
		order['sign'] = sign(order, self.api_key)
		self.order_recorder[order['prepay_id']] = {'appid': order['appid'], 'mch_id': order['mch_id'], 'trade_type': order['trade_type'], 'total_fee': int(total_fee), 'out_trade_no': out_trade_no}

		return order

	def asynchronous_notification(self, payment_request):
		if not check(payment_request, self.api_key):
			return False
		else:
			#import pdb
			#pdb.set_trace()
			try:
				if self.order_recorder[payment_request['prepayid']]['appid'] not in self.paid_order:
					self.paid_order[self.order_recorder[payment_request['prepayid']]['appid']] = [self.order_recorder[payment_request['prepayid']]]
				else:
					self.paid_order[self.order_recorder[payment_request['prepayid']]['appid']].append(self.order_recorder[payment_request['prepayid']])
			except:
				return False
				
			anotification = {}
			anotification['appid'] = self.order_recorder[payment_request['prepayid']]['appid']
			anotification['bank_type'] = 'CFT'
			anotification['is_subscribe'] = 'Y'
			anotification['mch_id'] = self.order_recorder[payment_request['prepayid']]['mch_id']
			anotification['nonce_str'] = '5d2b6c2a8db53831f7eda20af46e531c'
			anotification['openid'] = 'oUpF8uMEb4qRXf22hE3X68TekukE'
			anotification['out_trade_no'] = self.order_recorder[payment_request['prepayid']]['out_trade_no']
			anotification['result_code'] = 'SUCCESS'
			anotification['return_code'] = 'SUCCESS'
			anotification['time_end'] = '20140903131540'
			anotification['total_fee'] = self.order_recorder[payment_request['prepayid']]['total_fee']
			anotification['trade_type'] = self.order_recorder[payment_request['prepayid']]['trade_type']
			anotification['transaction_id'] = '1004400740201409030005092168'
			anotification['sign'] = sign(anotification, self.api_key)
			
			return to_xml(anotification)

	def order_query(self, out_trade_no):
		try:
			return wx_server.paid_order[self.appid][out_trade_no]
		except:
			return False