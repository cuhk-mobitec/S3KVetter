If you want to test your own SDK of Oauth 2.0, you can use the two template files under this directory as a starting point. 

### client_app.py
This is the template for client side code. It calls APIs in your SDK. We have enumerate different orders of requests in this template file. 

### master_config.json

This if the template for the configuratoin file. The JSON file has two keys: 

- smt: if you have some variables not defined in your client side code, but used in your defined expected conditions, you can declare these variables here.

- complexfunc: When encounter some complex functions, like hash functions, PyExZ3 will use concrete value to execute it. By using this key, the concrete value that is used to executed will appear in your predicates. This help to understand each path in your predicate tree. 