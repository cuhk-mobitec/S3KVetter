#Steps:

#1. Install Python 3
brew install python
#May need to create folder if has error
#sudo mkdir /usr/local/Frameworks
#sudo chown $(whoami):admin /usr/local/Frameworks

#2. Config brew (install brew first if not installed)
echo export PATH='/usr/local/bin:$PATH' >> ~/.bash_profile

#3. Install Z3
brew install z3
Then run the script to config env #(Need to change z3 version)
PyExZ3/setup.sh

#4. Install CVC
#Follow this instruction
#https://cs.nyu.edu/pipermail/cvc-users/2017/000900.html
#https://mytekmek.wordpress.com/2015/05/22/cvc4-python-api-on-mac/

brew install autoconf
#Use following to install automake1.5
curl -O -L http://ftpmirror.gnu.org/automake/automake-1.15.tar.gz
tar -xzf automake-1.15.tar.gz
cd automake-*
./configure
make
sudo make install

brew install libtool
brew install swig
brew install boost
brew install gmp
brew install gcc
tar zxf cvc4-1.5.tar.gz
cd cvc4-1.5/
echo 'python_cpp_SWIGFLAGS = -py3' >> src/bindings/Makefile.am
contrib/get-antlr-3.4
export LDFLAGS="-L/usr/local/lib"
export CPPFLAGS="-I/usr/local/include"
export CC="gcc-8"
export CXX="g++-8"
PYTHON_CONFIG=python3-config ./configure ANTLR=`pwd`/antlr-3.4/bin/antlr3 \
              --with-antlr-dir=`pwd`/antlr-3.4 \
              --enable-language-bindings=python \
              --prefix=/usr/local/cvc4
make
make install
( cd /usr/local/cvc4/share/pyshared/ && \
       ln -s ../../lib/pyshared/CVC4.so _CVC4.so )
#Add this to bash_profilec
export PYTHONPATH="/usr/local/cvc4/share/pyshared"
python examples/SimpleVC.py

#If needed, create enw folder
#sudo mkdir /usr/local/cvc4
#sudo chown $(whoami):admin /usr/local/cvc4
#May need to add /usr/local/cvc4/bin/ to env PATH variable

Then run test
python3 pyexz3.py test/abs_test.py --cvc


Also add symbolic and symbolic/symbolic_types to env PYTHONPATH