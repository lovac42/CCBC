# CCBC Addons:
As a result of meshing 2.1 and 2.0, old addons require very little mod and new addons needs to be downgraded back to Qt4.

Some Anki API may have changed, but in most cases, porting is pretty straight forward.  
2.0 addons need to be upgraded to Python 3 code and placed in a folder by itself with a ```__init__.py``` file.  
2.1 addons need to change Qt5 back to Qt4.  
```
from PyQt5 import QtCore, QtGui, QtWidgets
```
Changes to:
```
from PyQt4 import QtCore, QtGui as QtWidgets, QtGui
```


### Included Addons:
Advanced Copy Fields, by Ambriel Angel: https://ankiweb.net/shared/info/1898445115  
Add-on window search bar, by ijgnd: https://ankiweb.net/shared/info/561945101  
Card Info Bar for Browser, by ijgnd: https://ankiweb.net/shared/info/2140680811  
Frozen Fields, by tmbb: https://github.com/tmbb/FrozenFields  
Large and Colorful Buttons (css only), by hkr: https://ankiweb.net/shared/info/1829090218  
Replay buttons on card, by ospalh: https://ankiweb.net/shared/info/498789867  
Don't remove mark on export, by Soren Bjornstad: https://ankiweb.net/shared/info/909480379  


### Arthur-Milchior Must Haves:
Keep empty note: https://ankiweb.net/shared/info/2018640062  
Tag missing media: https://ankiweb.net/shared/info/2027876532  
Clearer empty card info: https://ankiweb.net/shared/info/25425599  
Correct due (2.0 version): https://ankiweb.net/shared/info/127334978  


### My own addons:
Small potatoes: https://ankiweb.net/shared/info/75718778  
Cacher in the rye: https://ankiweb.net/shared/info/1302452246  
Hold'em Cardfield: https://ankiweb.net/shared/info/363320830  
Pennywise: https://ankiweb.net/shared/info/1032766035  
rated0search: https://ankiweb.net/shared/info/1056004913  
Blitzkrieg: https://ankiweb.net/shared/info/564851917  

