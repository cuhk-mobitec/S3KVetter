from alipay import AliPay
import pdb, urllib.parse, json, alipay_utils
from symbolic.args import *

private_key_string = open("/home/mike/Desktop/new_test/python-alipay-sdk/private_key.pem").read()
public_key_string = open("/home/mike/Desktop/new_test/python-alipay-sdk/public_key.pem").read()

app_id = "2014072300007148"
seller_id = "2088301194649043"
out_trade_no = "201800000001201"
total_amount = "9.00"

alipay = AliPay(appid=app_id, app_notify_url=None, app_private_key_string=private_key_string, alipay_public_key_string=public_key_string, sign_type="RSA2", debug=False)

def generate_order(order_total_amount):
	global total_amount

	if total_amount != order_total_amount:
		total_amount = order_total_amount

def verifyNotificatoin(data):
	global app_id, seller_id, out_trade_no, total_amount

	if data['app_id'] != app_id or data['seller_id'] != seller_id or data['out_trade_no'] != out_trade_no or data['total_amount'] != total_amount:
		return False
	else:
		return True

@symbolic(total_amount1="9.00", app_id2="2014072300007148", out_trade_no2="201800000001201", trade_no2="2016081621001004400236957647", total_amount2="9.00", seller_id2="2088301194649043", app_id3="2014072300007148", out_trade_no3="201800000001201", trade_no3="2016081621001004400236957647", total_amount3="9.00", seller_id3="2088301194649043", sequential_notification=1, sequential_handling=1)
def alipayTest(total_amount1, app_id2, out_trade_no2, trade_no2, total_amount2, seller_id2, app_id3, out_trade_no3, trade_no3, total_amount3, seller_id3, sequential_notification, sequential_handling):
	global alipay

	alipayServer = alipay_utils.alipay_server(seller_id=seller_id, public_key_path="/home/mike/Desktop/new_test/python-alipay-sdk/public_key.pem", private_key_path="/home/mike/Desktop/new_test/python-alipay-sdk/private_key.pem")

	generate_order(total_amount1)
	order_string = alipay.api_alipay_trade_app_pay(out_trade_no=out_trade_no, total_amount=total_amount, subject="iphone")
	
	anotification_sample_request = alipayServer.asynchronous_notification(order_string)
	notification_sample_response = alipayServer.synchronous_notification(order_string)

	if sequential_notification:	
		try:
			synchronous_data = alipay.verify_and_return_sync_response1(json.loads(notification_sample_response)['result'], 'alipay_trade_app_pay_response')
		except:
			return 0
		if verifyNotificatoin(synchronous_data):
			if sequential_handling == 1:
				return 1
			elif sequential_handling == 2:
				queryString = urllib.parse.urlparse(anotification_sample_request).query
				queryString = dict((itm.split('=', 1)[0], itm.split('=', 1)[1]) for itm in queryString.split('&'))
				signature = queryString.pop('sign')
				try:
					alipay.verify(queryString, signature)
				except:
					return 0	
				if verifyNotificatoin(queryString):
					return 1			
				else:
					return 0	
			else:
				return 0				
		else:
			return 0
	else:			
		queryString = urllib.parse.urlparse(anotification_sample_request).query
		queryString = dict((itm.split('=', 1)[0], itm.split('=', 1)[1]) for itm in queryString.split('&'))
		signature = queryString.pop('sign')
		try:
			alipay.verify(queryString, signature)
		except:
			return 0	
		if verifyNotificatoin(queryString):
			return 1			
		else:
			return 0			
