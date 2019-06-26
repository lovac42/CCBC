# Anki: CCBC Edition

This is Anki 2.1.13 with Qt4 & QtWebkit.

## About:
The reason for this is because QWebEngine is too sluggish for ebook reading. After importing any uncompressed 200kb file or "The Complete History of Supermemo" or "Supermemo 20 Rules", the webpage really starts to lag behind and in some cases freeze five seconds after every extraction. This project takes the codes from 2.1 and 2.0 and meshed them together.

Use cases of QtWebKit: https://github.com/annulen/webkit/wiki/Use-cases-of-QtWebKit

### Why QWebEngine is bad for IR?
"setHtml works by converting the html code you provide to percent-encoding, putting data: in front and using it as url which it navigates to, so the html code you provide becomes a url which exceeds the 2mb limit." <a href="https://bugreports.qt.io/browse/QTBUG-59369?focusedCommentId=352654&page=com.atlassian.jira.plugin.system.issuetabpanels%3Acomment-tabpanel#comment-352654">Source</a>

In other words, a 100kb webpage with the space character encoded as "%20", as well as user highlights and annotations added on top could potentially become more than 2MB, freezing Anki as a result.

<i>Correction:</i> I was not referring to the current version of IR. The current public version, IR v4 maintaied by luoliyan, does not use "setHtml" and should not be affected by this problem.


### Naming:
What does CCBC stand for?  
<i>Cannabis & Coffee; Breakfast of Champions.</i>


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
Large and Colorful Buttons (css only), by hkr: https://ankiweb.net/shared/info/1829090218  


### Arthur-Milchior Must Haves:
Using regexps to remove tags: https://ankiweb.net/shared/info/1502698883  
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


## Sync:
Sync has been disabled, but can be enabled for custom servers using modules.


## Zooming:
Fullscreen (F11) and zooming is builtin. Use Ctrl++/Ctrl+- to zoom-in/out or add Shift for finer control.  

Zoom adjustments are saved per card model based on front or back view. IR cards are saved per card.


## Screenshots:

<img src="https://github.com/lovac42/CCBC/blob/master/screenshots/Clipboard-1.png?raw=true">  

<img src="https://github.com/lovac42/CCBC/blob/master/screenshots/Clipboard-2.png?raw=true">  

<img src="https://github.com/lovac42/CCBC/blob/master/screenshots/Clipboard-3.png?raw=true">  

<img src="https://github.com/lovac42/CCBC/blob/master/screenshots/Clipboard-4.png?raw=true">  

<img src="https://github.com/lovac42/CCBC/blob/master/screenshots/nm_heatmap.png?raw=true">  

<img src="https://github.com/lovac42/CCBC/blob/master/screenshots/orange_pi.png?raw=true">  

<img src="https://github.com/lovac42/CCBC/blob/master/screenshots/orange_pi2.png?raw=true">  

