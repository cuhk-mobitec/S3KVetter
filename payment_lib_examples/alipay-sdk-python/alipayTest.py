#!/usr/bin/env python
# -*- coding: utf-8 -*-
import traceback
import json
import urllib.parse
import pdb
import alipay_utils

from symbolic.args import *
from alipay.aop.api.AlipayClientConfig import AlipayClientConfig
from alipay.aop.api.DefaultAlipayClient import DefaultAlipayClient
from alipay.aop.api.domain.AlipayTradeAppPayModel import AlipayTradeAppPayModel
from alipay.aop.api.request.AlipayTradeAppPayRequest import AlipayTradeAppPayRequest
from alipay.aop.api.response.AlipayTradeAppPayResponse import AlipayTradeAppPayResponse
from alipay.aop.api.util.SignatureUtils import sign_with_rsa2, verify_with_rsa

alipay_client_config = AlipayClientConfig()
alipay_client_config.server_url = 'https://openapi.alipay.com/gateway.do'
alipay_client_config.app_id = '2014072300007148'
alipay_client_config.app_private_key = 'MIIEogIBAAKCAQEAoD2SrS5htJ+2IQ0WS+JbSxSnfSo/DWjWQSPHA2kJuzbuHp1D1gfUR4k+D92A5UrBb5U4AnF37e6CvUM3eyJXteR8D3MUqdpBNx0khSjkYU9AX6X/tOacgRf5VxpTQ2PWHuXaBqUA3GDZsjX8VHg3GfSO4dYVTb1xopLHfK9nAZB+VzB2MAI0V5VtBU7Tu89GNYB2gRNyAv4iZO2+iMhTGOR6rUJrd2tb61ZVdoMV5ktoXk4i3LAsOmpmW7lUjZv7rR3cwBcKRu25tjblkF29O8pRtHSrTz7kgISCN7ZpdGHoluqoI51iAuiwzzkgB8bUGNiwuymbotIW/x6E5aDxTwIDAQABAoIBACG+dankj4zC6U6ye9SFGWaJNfAkulxvjFbxWtJ8ByGWorRtt8BVq71YyGn84kzm3i9KRB43mOLRDFUg14klpUTXlcyHFn3iSUN67prgDp/zWYIK6ftFaQXCb66JC6mwV4HwM2aczr6Z4p4lwjpjim770i76r0fMsiZjNIEsSsvINZUcFbGMiDc1hy5c3BmIJrClc9eGbaV0yIa0dRaEFh0pHRDyt/6h17lIKSFAlwGhJbXH7ZxB4RayAyqxpZ/dn8SqAIzJeXAqavJswV/Lx92oyx+HSKle4UGPUmrgIX/fBRXWb8SKEPnlRPlOgn+gzjArllMDgKUNlWq42IM12bECgYEAyt7B4BoSwrVUn8icwoflA4oYZixIS1HGaSQfrxp+TXBFmJQGV6i/gGRDZATBk+4BojIL+JoslbqwzoUqjWBdYc4oSzkew2NF5X8Nm/OcKaGNBz6evw/cZxpdbeT3s5Rvsap0YASvs+7P8CRMED6ZqqW82Ivhz7LKdw/1fBxN10kCgYEAyjTAX8enGwzS9q2t2RCqpoZOGqnkooLykmbU2mrMcx0uRAUFFFt20Xi4CyVpbjEx4E9vTpg4vBZ+Eho/dHld2FJENsAeucDzzh2bEruoE9OB9vasDalUKHjIuBeP8MTfewCnEuvwc+1JbbkDu4zw4TzDZFBpsVPW+sPONlL5C9cCgYBo4pBD59cJOazdy19Yp9+8W7pPoNdjsYyuMVH8OutP6BrjTqyUx5byr2O0I01dyPCpRcywpC0m4FWnAGxGmarN9UMZ2RdRl1K821pS5bk4QODj/Pkf+PhPie8B8R4rhzPUHDd8qQ+aLH7vPiThRSw3cObY4kFGG77XnbWijBOmmQKBgEi3T7ciBWYk5njvXGWDKNtZ0RylnCMVFEax1Dn3zi5XgBvV8k2v1rrdvtHDUnbeGiGgb1bERyLcs9mutsMcIjN44i8OR/5k9UhaPTovYfI/Ta2SZ61CB5HGXehWEN107yk8wth7IK2P16gtsLnxpW5ae6nHgTrT+6uSXsYKcKVhAoGAf8Syw1s4gDuBPge3xKVY0QHSq5Fvk/1M1Lr9WkZcmnxEryAnA9yc63d+40CfZQI3X8sKmy6G0f7nPvXNPEOKkyVCZIU47wlF6JyzkDrVcbVYcK9SClstND8+fuQ6LHEp7eySquiZ+B1LRSaLIsrE3XNMnqx/nptmjnIYIEPmAFg='
alipay_client_config.alipay_public_key = 'MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA5vkMRcJKx+BNXYie+grIsIlMo+ZRC5Rx6LYvmA6bwUzdX+NscYTag5skRK2KDbuWqj/8O+ImmTXGAg0uOUObjWyZafItPOJUnNUMpnj0f7lPgNBevIxlyWIQinuPejFaQbjdfCvV61ys+aF3K4aKOWQ+2iqYjzIrylH0F8lls8wMt0Hp+/68D1sx8DYF1Ua1d4yP28z9g1PpCrMM/cnzw4cAvP1IHKLs9o5nyrCimpl/l0ydesHzUGWagm4VUf20ZglaMwTksvOwAHQo2Z7AOy58KMqEeM+Yxn9XL303n1d6gKxK8sfck8+wqog3ezjJBjdHisS5Z7sraxmeazAd/QIDAQAB'
client = DefaultAlipayClient(alipay_client_config=alipay_client_config)
model = AlipayTradeAppPayModel()
model.timeout_express = "90m"
model.total_amount = "9.00"
model.product_code = "QUICK_MSECURITY_PAY"
model.body = "Iphone6 16G"
model.subject = "iphone"
model.out_trade_no = "201800000001201"
seller_id = "2088301194649043"

app_public_key = 'MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAoD2SrS5htJ+2IQ0WS+JbSxSnfSo/DWjWQSPHA2kJuzbuHp1D1gfUR4k+D92A5UrBb5U4AnF37e6CvUM3eyJXteR8D3MUqdpBNx0khSjkYU9AX6X/tOacgRf5VxpTQ2PWHuXaBqUA3GDZsjX8VHg3GfSO4dYVTb1xopLHfK9nAZB+VzB2MAI0V5VtBU7Tu89GNYB2gRNyAv4iZO2+iMhTGOR6rUJrd2tb61ZVdoMV5ktoXk4i3LAsOmpmW7lUjZv7rR3cwBcKRu25tjblkF29O8pRtHSrTz7kgISCN7ZpdGHoluqoI51iAuiwzzkgB8bUGNiwuymbotIW/x6E5aDxTwIDAQAB'
cashier_private_key = 'MIIEpAIBAAKCAQEA5vkMRcJKx+BNXYie+grIsIlMo+ZRC5Rx6LYvmA6bwUzdX+NscYTag5skRK2KDbuWqj/8O+ImmTXGAg0uOUObjWyZafItPOJUnNUMpnj0f7lPgNBevIxlyWIQinuPejFaQbjdfCvV61ys+aF3K4aKOWQ+2iqYjzIrylH0F8lls8wMt0Hp+/68D1sx8DYF1Ua1d4yP28z9g1PpCrMM/cnzw4cAvP1IHKLs9o5nyrCimpl/l0ydesHzUGWagm4VUf20ZglaMwTksvOwAHQo2Z7AOy58KMqEeM+Yxn9XL303n1d6gKxK8sfck8+wqog3ezjJBjdHisS5Z7sraxmeazAd/QIDAQABAoIBAQDB6xDZtLEyNOjfgafvyIQMa4nUBbe/oCcuuV8mLAWq+gzWx8sxV9haLDP8ETNaKkfpsoTkBhBgC5yt9kD7xP5hc28uWyyN9HwTnG/diKnGXmAYh1kytjFzLYkzq1+fuLXNfhc+fFNDIvD7OQwjl/aPDtISOzcQ6o+Hct0b53QiybMG27NseINxGWYrQMXK2acJ36tp2ET16WwdDBS3PYWiIgHUDoWE5/YrFc0Ryr6RFErT7GoyfQL7mxlow8ALhlN5nhoelahKHnVYxJ3c9qTnpkxv6xXVvNFS3mhgGad3XBv5QY38tx7uTz1pWquxYYrp6cxxvNVKnIkUA5gVGEZBAoGBAPMxSsefzfb3rr0k1mRFb6ISp8eYsvzRcX3DJ/2Hp0QVvRcjiNIFls+veBJw/zZakFCqJf7cL+Ds0WzxuBe1e/dvR4tApF5szTpBx/t2unYhzMl9w+DYaqy0+fcRetEyz44o/GmUtmITOfizpFnME1HJiGxWU3gCK0L71gfmvg9RAoGBAPMjAq9wqrloLacspU7n0ZhzjPyDWJ0Yh0BR4C96qoA5VMdhF3n1gSZxbkHsSbztUpZ6cJv9u+C+LII5gHfR5fbl+PKT7ijXcCoM9RcDjsCECEBUVORzuLl33ZB5VvtSL2yv/Hv42ujqcKOBETlTgMRbPh4RzEA44k/ELOy44PDtAoGBAI4jITHLlPXjjZ2/Cg9RBg4UGTvvY62gPFTk21qzDnAcxIfhnPYjjiGUzPj6Ui/Sfsamq85poxIzV7P1E0PILsxPneElxuvpa4nBKMEwg4rH9olNmE6yLqcCn5ZoAQCEUgskqWKMKIzp79gMJuLVA/WpdLLdQavCmMZtqoqzsiIBAoGABFr+M1JbXJLnLnV4SJ+Se56mSee4cKf91EMjNvaFk2JziFbO6tphA+VISloHQCEoN5Xd6o1zDiWZ+oM5L+xMqE2aVg4cWBLz6Wzt/wmLRxuWYkCgfK8uAfSJvYrO6hWgz9ufNEFS+pUoi2VGf7ZlOh9AT52WARiDxVYIT/1H2kkCgYBWYO2+7vXA0ZybrTgWZ7lapykX13XQjwnqDlABWmATR3Ecv2qocA1YkzmTlY7l2ilaHkh9C2OOPiq6XtftM3nuypqxPdRd8aHk1m3XNYwtH/j/phE+rwvLgMuKrkiBDecoHEq10+rPNqIQmhjm+BGCAzEuf4fxLZC8MP3MGLCUIA=='

def generate_order(total_amount):
	global model
	global client

	#if total_amount != "":
	model.total_amount = total_amount
	request = AlipayTradeAppPayRequest(biz_model=model)
	response = client.sdk_execute(request)

	return response

def verify_notification(data):
	global alipay_client_config, model, seller_id

	check_list = ['out_trade_no', 'total_amount', 'seller_id', 'app_id']
	for item in check_list:
		if item in dir(data):
			target = getattr(data, item)
		elif isinstance(data, dict) and item in data.keys():
			target = data[item]
		else:
			continue
		if item == 'out_trade_no' and target != model.out_trade_no:
			return False
		elif item == 'total_amount' and target != model.total_amount:
			return False
		elif item == 'seller_id' and target != seller_id:
			return False
		elif item == 'app_id' and target != alipay_client_config.app_id:
			return False
	return True

@symbolic(total_amount1="9.00", app_id2="2014072300007148", out_trade_no2="201800000001201", trade_no2="2016081621001004400236957647", total_amount2="9.00", seller_id2="2088301194649043", app_id3="2014072300007148", out_trade_no3="201800000001201", trade_no3="2016081621001004400236957647", total_amount3="9.00", seller_id3="2088301194649043", sequential_notification=1, sequential_handling=1)
def alipayTest(total_amount1, app_id2, out_trade_no2, trade_no2, total_amount2, seller_id2, app_id3, out_trade_no3, trade_no3, total_amount3, seller_id3, sequential_notification, sequential_handling):
	global seller_id, app_public_key, cashier_private_key, alipay_client_config

	paid = False

	alipayServer = alipay_utils.alipay_server(seller_id = seller_id, app_public_key=app_public_key, cashier_private_key=cashier_private_key)

	ordering = generate_order(total_amount1)
	notification_sample_response = alipayServer.synchronous_notification(ordering) 
	anotification_sample_request = alipayServer.asynchronous_notification(ordering)

	if sequential_notification: # Synchronous notification arrives earlier than the asynchronous one
		response = alipay_utils.alipayNotify(notification_sample_response, sign_key = alipay_client_config.alipay_public_key)
		if not response:
			paid = False
			return 0
		if verify_notification(response):
			if sequential_handling == 1: #Trust the synchronous notification 
				paid = True
				return 1
			elif sequential_handling == 2: #Trust the following asynchronous notification
				queryString = alipay_utils.alipayNotify1(anotification_sample_request, sign_key = alipay_client_config.alipay_public_key)
				if not queryString:
					paid = False
					return 0
				if verify_notification(queryString):
					paid = True
					return 1
				else:
					paid = False
					return 0
			else: #No asynchronous notification received after the pre-configured time-out.
				paid = False
				return 0			
		else:
			paid = False
			return 0
	else: # Asynchronous notification arrives earlier than the synchronous one
		queryString = alipay_utils.alipayNotify1(anotification_sample_request, sign_key = alipay_client_config.alipay_public_key)
		if not queryString:
			paid = False
			return 0
		if verify_notification(queryString):
			paid = True
			return 1
		else:
			paid = False
			return 0