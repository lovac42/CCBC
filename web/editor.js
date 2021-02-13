/* Copyright: Lovac42
 * Copyright: Ankitects Pty Ltd and contributors
 * License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html */

var currentField = null;
var changeTimer = null;
var dropTarget = null;

String.prototype.format = function() {
    var args = arguments;
    return this.replace(/\{\d+\}/g, function(m){
            return args[m.match(/\d+/)]; });
};

function onKey() {
    // esc clears focus, allowing dialog to close
    if (window.event.which == 27) {
        currentField.blur();
        return;
    }
    clearChangeTimer();
    if (currentField.innerHTML == "<div><br></div>") {
        // fix empty div bug. slight flicker, but must be done in a timer
        changeTimer = setTimeout(function () {
            currentField.innerHTML = "<br>";
            sendState();
            saveField("key"); }, 1);
    } else {
        changeTimer = setTimeout(function () {
            sendState();
            saveField("key"); }, 600);
    }
};

function sendState() {
    var r = {
        'bold': document.queryCommandState("bold"),
        'italic': document.queryCommandState("italic"),
        'under': document.queryCommandState("underline"),
        'super': document.queryCommandState("superscript"),
        'sub': document.queryCommandState("subscript"),
        'col': document.queryCommandValue("forecolor")
    };
    py.run("state:" + JSON.stringify(r));
};

function setFormat(cmd, arg, nosave) {
    document.execCommand(cmd, false, arg);
    if (!nosave) {
        saveField('key');
    }
};

function clearChangeTimer() {
    if (changeTimer) {
        clearTimeout(changeTimer);
        changeTimer = null;
    }
};

function onFocus(elem) {
    currentField = elem;
    py.run("focus:" + currentField.id.substring(1));
    // don't adjust cursor on mouse clicks
    if (mouseDown) { return; }
    // do this twice so that there's no flicker on newer versions
    caretToEnd();
    // need to do this in a timeout for older qt versions
    setTimeout(function () { caretToEnd() }, 1);
    // scroll if bottom of element off the screen
    function pos(obj) {
    	var cur = 0;
        do {
          cur += obj.offsetTop;
         } while (obj = obj.offsetParent);
    	return cur;
    }
    var y = pos(elem);
    if ((window.pageYOffset+window.innerHeight) < (y+elem.offsetHeight) ||
        window.pageYOffset > y) {
        window.scroll(0,y+elem.offsetHeight-window.innerHeight);
    }
}

function focusField(n) {
    $("#f"+n).focus();
}

function onDragOver(elem) {
    // if we focus the target element immediately, the drag&drop turns into a
    // copy, so note it down for later instead
    dropTarget = elem;
}

function caretToEnd() {
    var r = document.createRange()
    r.selectNodeContents(currentField);
    r.collapse(false);
    var s = document.getSelection();
    s.removeAllRanges();
    s.addRange(r);
};

function onBlur() {
    if (currentField) {
        saveField("blur");
    }
    clearChangeTimer();
    // if we lose focus, assume the last field is still targeted
    //currentField = null;
};

function saveField(type) {
    if (!currentField) {
        // no field has been focused yet
        return;
    }
    // type is either 'blur' or 'key'
    py.run(type + ":" + currentField.innerHTML);
    clearChangeTimer();
};

function wrappedExceptForWhitespace(text, front, back) {
    var match = text.match(/^(\s*)([^]*?)(\s*)$/);
    return match[1] + front + match[2] + back + match[3];
};

/* old method, kept around for the benefit of add-ons that were using it */
function wrap(front, back) {
    wrapInternal(front, back, false);
};

/* new method */
function wrap2(front, back) {
    wrapInternal(front, back, true);
};

function wrapInternal(front, back, plainText) {
    if (currentField.dir === "rtl") {
        front = "&#8235;" + front + "&#8236;";
        back = "&#8235;" + back + "&#8236;";
    }
    var s = window.getSelection();
    var r = s.getRangeAt(0);
    var content = r.cloneContents();
    var span = document.createElement("span");
    span.appendChild(content);
    if (plainText) {
        var new_ = wrappedExceptForWhitespace(span.innerText, front, back);
        setFormat("inserttext", new_);
    } else {
        var new_ = wrappedExceptForWhitespace(span.innerHTML, front, back);
        setFormat("inserthtml", new_);
    }
    if (!span.innerHTML) {
        // run with an empty selection; move cursor back past postfix
        r = s.getRangeAt(0);
        r.setStart(r.startContainer, r.startOffset - back.length);
        r.collapse(true);
        s.removeAllRanges();
        s.addRange(r);
    }
};

function onReplay(fname) {
    py.run("play:"+fname);
}

function onStop() {
    py.run("stop");
}

function onSticky(id, el) {
    el.class="fname";
    py.run("sticky:"+id);
};

function setFieldHtml(data, fieldNum) {
    $("#f"+fieldNum).html(data).focus();
};

function setFields(fields, focusTo) {
    var txt = "";
    for (var i=0; i<fields.length; i++) {
        //class, name, sticky, field_data
        var c = "";
        var n = fields[i][0]; //name
        var s = fields[i][1]; //sticky
        var f = fields[i][2]; //data
        var m = fields[i][3]; //media
        if (!f) {
            f = "<br>";
        }
        if(s){
          c="sticky";
        }
        txt += "<tr><td id=s{0} onClick='javascript:onSticky({1},this);' class='fname {2}'>{3}</td></tr><tr><td width=100%%>".format(i,i,c,n);

        txt += "<div id=f{0} onkeydown='onKey();' onmouseup='onKey();'".format(i);
        txt += " onfocus='onFocus(this);' onblur='onBlur();' class=field ";
        txt += "ondragover='onDragOver(this);' ";
        txt += "contentEditable=true class=field>{0}</div>".format(f);
        txt += "</td></tr>";

        // add media play button for each file
        t = getReplayButtons(m);
        txt += "<tr><td id=m{0}{1}</td></tr>".format(i,t);
    }
    $("#fields").html("<table cellpadding=0 width=100%%>"+txt+"</table>");
    if (!focusTo) {
        focusTo = 0;
    }
    if (focusTo >= 0) {
        $("#f"+focusTo).focus();
    }
};


function setReplayButtons(mediaArr, fieldNum) {
    if (!mediaArr) { //clear and exit
        $("#m"+fieldNum).removeClass("fmedia").html();
        return;
    }
    t = getReplayButtons(mediaArr);
    t = "<td id=m{0}{1}</td>".format(fieldNum,t);
    $("#m"+fieldNum).parent().html(t);
}

function getReplayButtons(mediaArr) {
    e = "";
    for (var i=0; i<mediaArr.length; i++) {
        m = mediaArr[i].replace(/'/g,"&#39;");
        e += "<a href='javascript:onReplay(\"{0}\");' title='{1}'>{2}</a> ".format(m,m,i);
    }
    if (e) {
        return " class='fmedia'><a href='javascript:onStop();' title='Stop'>ST</a> "+e;
    }
    return ">";
}


function appendReplayButton(col, fname) {
    m = unescape(fname).replace(/'/g,"&#39;");
    cnt = $("#m"+col+" a").length;
    if (cnt==0) {
        $("#m"+col).addClass("fmedia");
        $("#m"+col).append("<a href='javascript:onStop();' title='Stop'>ST</a> ");
    } else {
        cnt--; //offset ST link
    }
    $("#m"+col).append("<a href='javascript:onReplay(\"{0}\");' title={1}>{2}</a> ".format(m,m,cnt));
}


function setBackgrounds(cols) {
    for (var i=0; i<cols.length; i++) {
        $("#f"+i).css("background", cols[i]);
    }
}

function setFonts(fonts) {
    for (var i=0; i<fonts.length; i++) {
        $("#f"+i).css("font-family", fonts[i][0]);
        $("#f"+i).css("font-size", fonts[i][1]);
        $("#f"+i)[0].dir = fonts[i][2] ? "rtl" : "ltr";
    }
}

function showDupes() {
    $("#dupes").show();
}

function hideDupes() {
    $("#dupes").hide();
}

var mouseDown = 0;
var mouseDownImageSrc = "";
var mouseDownImageElement = null;

$(function () {
document.body.onmousedown = function () {
    mouseDown++;
}

document.body.onmouseup = function () {
    mouseDown--;
}

document.onclick = function (evt) {
    var src = window.event.srcElement;
    if (src.tagName == "IMG") {
        // image clicked; find contenteditable parent
        var p = src;
        while (p = p.parentNode) {
            if (p.className == "field") {
                $("#"+p.id).focus();
                break;
            }
        }
    }
}

document.oncontextmenu = function (evt) {
    if(window.getSelection().toString())
        return

    var src = window.event.srcElement;
    if (src.tagName == "IMG") {
        // image clicked; find contenteditable parent
        var p = src;
        while (p = p.parentNode) {
            if (p.className == "field") {
                $("#"+p.id).focus();
                mouseDownImageSrc = src.src;
                mouseDownImageElement = $(window.event.srcElement);
                break;
            }
        }
    }
}

});

function clearInlineStyle(){
    mouseDownImageElement.removeAttr("style")
        .removeAttr("width").removeAttr("height");
}

function isImgHiddenFrom(klass){
    if(mouseDownImageElement.hasClass(klass))
        return true;
    return false;
}

function toggleImgHiddenFrom(klass){
    mouseDownImageElement.toggleClass(klass);
    mouseDownImageElement = null;
}

function hasAttr(arr) {
    for (var i=0; i<arr.length; i++) {
        if(mouseDownImageElement.attr(arr[i])){
            return true;
        }
    }
    return false;
}

function currentFieldOrdinal() {
    return currentField.id.substring(1);
}

function startAutocomplete() {
    document.styleSheets[0].addRule('.autocomplete',
        'margin: 0.3em 0 1.0em 0; color: blue; text-decoration: underline; cursor: pointer;'
    );
    // every second send the current state over
    setInterval(function () {
        if (currentField) {
            var r = {text:currentField.innerHTML};
            py.run("autocomplete:" + JSON.stringify(r));
        }
    }, 1500);
}

function checkAutocomplete(txt) {
    $('.autocomplete').remove();
    if (currentField) {
        $('<div class="autocomplete">' + txt + '</div>').click({field: currentField}, updateField).insertAfter(currentField)
    }
    function updateField(event){
        currentField = event.data.field;
        currentField.innerHTML = txt;
        saveField("key");
        focusField(currentFieldOrdinal());
        caretToEnd();
    }
}

