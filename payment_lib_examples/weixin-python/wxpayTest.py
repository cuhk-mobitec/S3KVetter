# -*- coding: utf-8 -*-
import pdb, time, wx_utils
from symbolic.args import *
from weixin.pay import WeixinPay, WeixinPayError

app_id = 'wxd678efh567hg6787'
mch_id = '1230000109'
api_key = '192006250b4c09247ec02edce69f6a2d'
total_fee = 10
notify_url = 'http://www.weixin.qq.com/wxpay/pap.php'
out_trade_no = '1409811653'

def generate_order(total_fee1):
	global total_fee

	if total_fee != total_fee1:
		total_fee = total_fee1

def verify_notification(data):
	global app_id, mch_id, total_fee, out_trade_no

	if not ((data['appid'] == app_id) and (data['mch_id'] == mch_id) and (data['total_fee'] == total_fee) and (data['out_trade_no'] == out_trade_no)):
		return False
	else:
		return True

@symbolic(sequential_notfied = 1, active_query = 1, total_fee1 = 10, total_fee2 = 10, app_id2 = 'wxd678efh567hg6787', mch_id2 = '1230000109', out_trade_no2 = '1409811653', transaction_id2 = '1004400740201409030005092168')
def wxpayTest(sequential_notfied, active_query, total_fee1, total_fee2, app_id2, mch_id2, out_trade_no2, transaction_id2):
	global app_id, mch_id, api_key, total_fee, notify_url, out_trade_no

	wxServer = wx_utils.wx_server(app_id, mch_id, api_key)

	generate_order(total_fee1)
	wx_pay = WeixinPay(app_id, mch_id, api_key, notify_url)
	try:
		order = wx_pay.unified_order(trade_type='APP', body='iPad Mini in white with 16G memory', total_fee=total_fee, out_trade_no=out_trade_no)
	except:
		order = wxServer.app_unified_order(total_fee, out_trade_no)
	try:
		if not wx_pay.check(order):
			print('Fail to verify the signature from WeChat server!')
			return 0
	except:
		return 0

	paymentRequest = {'appid': app_id, 'partnerid': mch_id, 'prepayid': order['prepay_id'], 'package': 'Sign=WXPay', 'timestamp': str(int(time.time())), 'noncestr': wx_pay.nonce_str}
	sign = wx_pay.sign(paymentRequest)
	paymentRequest['sign'] = sign

	xml = wxServer.asynchronous_notification(paymentRequest)

	if sequential_notfied: # asynchronous notification arrives before the synchronous one
		data = wx_pay.to_dict(xml)
		if not wx_pay.check(data):
			return 0
		if verify_notification(data):
			return 1
		else:
			return 0
	elif active_query: # actively query the cashier server
		try:
			query_response = pay.order_query(out_trade_no=out_trade_no)
		except:
			query_response = wxServer.order_query(out_trade_no=out_trade_no)
			if not query_response:
				return 0
			else:
				if verify_notification(query_response):
					return 1
				else:
					return 0	
	else:
		return 0