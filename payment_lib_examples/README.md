For python-alipay-sdk, the SDK itself does not provide the handling functions for some steps in the payment process so I reuse some private functions in it for the purpose, where python-alipay-sdk/__init__.py is the unmodified code.

Each directory here contains a payment SDK example, including the client_app code, e.g., wxpayTest.py, a configuration file, master_config.json, and an expectation file (.expected), as the user-defined conditions. Besides, wx_utils.py and alipay_utils.py are tow auxiliary libraries to simulate the operations of cashiers in the payment process. Our project will explore the SDK code to see if there is any path violating our expectation. 

To reproduce the result, first activate the virtual environment, and then run the following code:

	python3 pyexz3.py path_to_client_app.py --expected path_to_expectation --config path_to_configuration