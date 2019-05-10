S3KVetter
======

This is the official code used in paper **Vetting Single Sign-On SDK Implementations via Symbolic Reasoning**. This code is based on another project, PyExZ3 (https://github.com/thomasjball/PyExZ3). We have added serveral features to support the verification with user-defined conditions.

If you are using this work, please cite the following paper:

>@inproceedings{yang2018vetting,
>  title={Vetting Single Sign-On $\{$SDK$\}$ Implementations via Symbolic Reasoning},
>  author={Yang, Ronghai and Lau, Wing Cheong and Chen, Jiongyi and Zhang, Kehuan},
>  booktitle={27th $\{$USENIX$\}$ Security Symposium ($\{$USENIX$\}$ Security 18)},
>  pages={1459--1474},
>  year={2018}
>}

### Prerequisites  

Please follow the instructions in https://github.com/thomasjball/PyExZ3 to setup the environment. Notice that we only support CVC4 as the theorem prover. 

If you are using Mac or Ubuntu, you can follow platform-specific instructions for [Ubuntu](https://github.com/cuhk-mobitec/S3KVetter/blob/master/setup%20notes/ubuntu.sh) and [Mac OS 10.14](https://github.com/cuhk-mobitec/S3KVetter/blob/master/setup%20notes/MacOS.sh).

### Usage

After configuring the environment, run the following code to check if the environment is cnofigured correctly.

	python3 pyexz3.py test/sample.py

For commandl line syntax, run the folllowing code to show the detailed syntax

	python3 pyexz3.py
	


Output is under directory `/verify`. 