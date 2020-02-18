# CCBC

### Download:
Please see <a href="https://github.com/lovac42/CCBC/releases">the release page.</a>

## About:
CCBC is based on Anki 2.1.15's backend and 2.0.52's frontend code. It uses QtWebkit which is licensed under AGPL. This is essentially upgrading 2.0 to python 3.

Use cases of QtWebKit: https://github.com/annulen/webkit/wiki/Use-cases-of-QtWebKit

### Why QWebEngine is bad for IR?
I find that QWebEngine is too sluggish for ebook reading. After importing any uncompressed 200kb file or "The Complete History of Supermemo" or "Supermemo 20 Rules", the webpage really starts to lag behind and in some cases freeze five seconds after every extraction.

"setHtml works by converting the html code you provide to percent-encoding, putting data: in front and using it as url which it navigates to, so the html code you provide becomes a url which exceeds the 2mb limit." <a href="https://bugreports.qt.io/browse/QTBUG-59369?focusedCommentId=352654&page=com.atlassian.jira.plugin.system.issuetabpanels%3Acomment-tabpanel#comment-352654">Source</a>

In other words, a 100kb webpage with the space character encoded as "%20", as well as user highlights and annotations added on top could potentially become more than 2MB, freezing Anki as a result.

<i>Correction:</i> I was not referring to the current version of IR. The current public version, IR v4 maintaied by luoliyan, does not use "setHtml" and should not be affected by this problem.


### Naming:
What does CCBC stand for?  
<i>Cannabis & Coffee; Breakfast of Champions.</i>  

What is an adze?  
An adze is a tool used in woodworking that is extremely cheap to make and could be purchased for a buck at Dollar Generals. However, to make it right, and not scratch up the surface of the project, is a craftmanship in itself. They are hard to come by even for those willing to pay. Similarly, plugins are cheap to make, but to do it right is difficult and time consuming. For that reason, CCBC addons end with a .adze extension.

## Sync:
Sync has been disabled, but can be enabled for custom servers using modules.

## Addons:
Some reasonable addons are integrated into CCBC.

See: https://github.com/lovac42/CCBC/blob/master/doc/addons.md

## Zooming:
Fullscreen (F11) and zooming is builtin. Use Ctrl++/Ctrl+- to zoom-in/out or add Shift for finer control.  

Zoom adjustments are saved per card model based on front or back view. IR cards are saved per card.

## Multi AddCard Dialog:
Allows opening of multiple addcard dialogs for entering cards to different decks or with different tags.

## Portable mode, windows only:
Portable mode is enabled if a file named `portable.dat` is in the ccbc.exe folder at the time it launches. All user data are stored in a folder called Data.

## Multiple instances:
CCBC allows multiple instances on different profiles to be run on the same system.

## Drag and drop:
Drag and drop for imports and addons.

## Shuffle or Show Next Card Button:
Added a small button to drop current card from the reviewer. The card will re-appear again in a few moments, this helps to alleviate tip-of-the-tongue phenomenons without failing the card in the event of a temporary mental lapse. The shuffling will be performed by the Hoochie addons if available.

Hotkey: CTRL+Enter (on question side only)


## Lightbox:
This will show one image in the reviewer and extra images in the lightbox.  

Field data:
```
<img src="image-1.jpg"/>
<img class="extra" src="image-2.jpg"/>
<img class="extra" src="image-3.jpg"/>
```

CSS in card layout:
```
img.extra {
  display: none;
}
img {
  max-width: 150px;
}
```

Use single quotes or non /> in templates to prevent lightboxing.  

<img src="https://github.com/lovac42/CCBC/blob/master/screenshots/lightbox.png?raw=true">  



## Screenshots:

<img src="https://github.com/lovac42/CCBC/blob/master/screenshots/Clipboard-1.png?raw=true">  

<img src="https://github.com/lovac42/CCBC/blob/master/screenshots/Clipboard-2.png?raw=true">  

<img src="https://github.com/lovac42/CCBC/blob/master/screenshots/Clipboard-3.png?raw=true">  

<img src="https://github.com/lovac42/CCBC/blob/master/screenshots/Clipboard-4.png?raw=true">  

<img src="https://github.com/lovac42/CCBC/blob/master/screenshots/nm_heatmap.png?raw=true">  

<img src="https://github.com/lovac42/CCBC/blob/master/screenshots/slackware.png?raw=true">  

<img src="https://github.com/lovac42/CCBC/blob/master/screenshots/debian.png?raw=true">  

<img src="https://github.com/lovac42/CCBC/blob/master/screenshots/orange_pi.png?raw=true">  

<img src="https://github.com/lovac42/CCBC/blob/master/screenshots/orange_pi2.png?raw=true">  


<img src="https://github.com/lovac42/CCBC/blob/master/screenshots/2021ccbc.png?raw=true">  

