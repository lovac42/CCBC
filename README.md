# Anki: CCBC Edition

This is Anki 2.1.13 with Qt4 & QtWebkit.

## About:
The reason for this is because QtWebEngine is too sluggish for ebook reading. After importing any uncompressed 200kb file or "The Complete History of Supermemo" or "Supermemo 20 Rules", the webpage really starts to lag behind and in some cases freeze five seconds after every extraction. This project takes the codes from 2.1 and 2.0 and meshed them together.

### Naming:
What does CCBC stand for?  
Cannabis & Coffee; Breakfast of Champions.


## Addons:
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
Hierarchical Tags, by Patrice Neff: https://ankiweb.net/shared/download/1089921461  
Advanced Copy Fields, by Ambriel Angel: https://ankiweb.net/shared/info/1898445115  
Add-on window search bar, by ijgnd: https://ankiweb.net/shared/info/561945101  
Card Info Bar for Browser, by ijgnd: https://ankiweb.net/shared/info/2140680811  
Frozen Fields, by tmbb: https://github.com/tmbb/FrozenFields  
Large and Colorful Buttons (css only) by hkr: https://ankiweb.net/shared/info/1829090218  
Small potatoes, https://ankiweb.net/shared/info/75718778  
Cacher in the rye, https://ankiweb.net/shared/info/1302452246  
Hold'em Cardfield, https://ankiweb.net/shared/info/363320830  
Pennywise, https://ankiweb.net/shared/info/1032766035  



## Sync:
Sync has been disabled, but can be enabled for custom servers using modules.
