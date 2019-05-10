For some SDKs, we may need to change the source code of the SDK, in order to explore as many paths as possible. This directory provides you some examples of how we change and test a SDK. 

In each SDK, `orig source/` contains the original source code of the SDK. The other directory contains the modified version of the same SDK. In the modified folder, `client_app.py` is the client side code and `.expected` file contains user-defined conditions. Our project will explore the SDK code to see if there is any path violating user-defined conditions. 

To reproduce the result, first activate the virtual environment, and then run the following code:

	python3 pyexz3.py path_to_client_app.py --expected path_to_expected_file