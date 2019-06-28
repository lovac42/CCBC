# CCBC On Raspbian (Jessie)

### No Stretch
CCBC cannot be installed on Stretch or later versions as QtWebkit was removed. A substantial amount of time is needed to compile and reinstall it, about a weeks on an Arms processor. Yes I have tried it, but then ran into bugs and missing headers and dependencies during compilation.

### Python 3.4 Patch
Python 3.6+ is required. However, I've found that it takes several tries and fixing broken links, as well as reinstalling dependencies. The process is not straight forward and so a patch was included for working with Python 3.4 which comes preinstalled with Raspbian-jessie.

To use it, just overwrite and replace the files. But keep in mind I may have missed a few areas that needed backporting, so compiling Python 3.6 from source is your best option.


## Installation:
These are the instructions for installing CCBC on Raspbian-jessie with the Python 3.4 patch:

1) Download Raspbian-jessie img: https://downloads.raspberrypi.org/raspbian/images/raspbian-2017-07-05/  
Follow instructions to save img to SD.


2) Update packages  
At the terminal, type:  
```$ sudo apt-get update```

3) Download, compile, and install sip: https://www.riverbankcomputing.com/software/sip/download
```
wget https://xyz.com/xxxx.tar.gz
tar xzvf xxxx.tar.gz
cd xxxx
sudo python3 configure.py  
sudo make  
sudo make install  
```


4) Download PyQt4  
```sudo apt-get install python3-pyqt4```
5) Download CCBC
6) Replace patch files
7) Install required packages

```sudo pip3 install --upgrade pip```

```sudo pip3 install -r requirements.txt```

OR (if error)
```
cat requirements.txt
sudo pip3 install *each line on list*
```

```sudo make install```

OR (if running from source)

```python3 runanki```


