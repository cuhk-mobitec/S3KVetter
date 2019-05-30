#!/usr/bin/env python
# -*- coding: utf-8 -*-

from wechatpy.pay import WeChatPay
import pdb
import wx_utils
from symbolic.args import *

app_id = 'wxd678efh567hg6787'
mch_id = '1230000109'
api_key = '192006250b4c09247ec02edce69f6a2d'
total_fee = 20
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

	#Step 2 and 3 in the protocol flow
	generate_order(total_fee1)

	#unifified order, Step 4 in the protocol flow
	pay = WeChatPay(app_id, api_key, mch_id)
	try:
		order = pay.order.create(trade_type='APP', body='iPad Mini in white with 16G memory', total_fee=total_fee, notify_url=notify_url, out_trade_no=out_trade_no)
	except:
		order = wxServer.app_unified_order(total_fee, out_trade_no)

	#Step 5 to 7 in the protocol flow
	try:
		if not pay.check_signature(order):
			print('Fail to verify the signature from WeChat server!')
			return 0
	except:
		print('Fail to verify the signature from WeChat server!')
		return 0

	paymentRequest = pay.order.get_appapi_params(order['prepay_id'])

	#Step 10 and 11 in the protocol flow
	xml = wxServer.asynchronous_notification(paymentRequest)

	#Step 14 to 16 in the protocol flow
	if sequential_notfied: # asynchronous notification arrives before the synchronous one
		try:
			data = pay.parse_payment_result(xml)
		except:
			return 0
		if verify_notification(data):
			return 1
		else:
			return 0
	elif active_query: # actively query the cashier server
		try:
			query_response = pay.order.query(out_trade_no=out_trade_no)
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