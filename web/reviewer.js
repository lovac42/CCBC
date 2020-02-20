/* Copyright: Ankitects Pty Ltd and contributors
 * License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html */

/* File has been modified by lovac42 for ccbc project */


var CCBC_FORK = true;
var ankiPlatform = "desktop";
var typeans;

function _updateQA (q, answerMode, klass) {
    $("#qa").html(q);
    typeans = document.getElementById("typeans");
    if (typeans) {
        typeans.focus();
    }
    if (answerMode) {
        var e = $("#answer");
        if (e[0]) { e[0].scrollIntoView(); }
        $(document.body).removeClass("frontSide").addClass("backSide");
    } else {
        window.scrollTo(0, 0);
    }
    if (klass) {
        document.body.className = klass;
    }
    // don't allow drags of images, which cause them to be deleted
    $("img").attr("draggable", false);
};


_flagColours = {
    1: "#ff6666",
    2: "#ff9900",
    3: "#77ff77",
    4: "#77aaff"
};

function _drawFlag(flag) {
    var elem = $("#_flag");
    if (flag === 0) {
        elem.hide();
        return;
    }
    elem.show();
    //elem.css("color", _flagColours[flag]);
    elem.css("fill", _flagColours[flag]);
}

function _toggleStar (mark) {
    var elem = $("#_mark");
    if (!mark) {
        elem.hide();
    } else {
        elem.show();
    }
}

function _getTypedText () {
    if (typeans) {
        py.link("typeans:"+typeans.value);
    }
};

function _typeAnsPress() {
    if (window.event.keyCode === 13) {
        py.link("ansHack");
    }
}


var menu_shown=false;
var mouse_shown=true;
$(document).mousemove(function(event){
    if(event.pageY>$(window).height()-20){
        menu_shown=true;
        py.link("showBottombar");
    }
    else if(event.pageY<20){
        menu_shown=true;
        py.link("showMenubar");
    }
    else if(menu_shown){
        menu_shown=false;
        window.setTimeout(function(){
            py.link("revFocused");
        }, 100);
    }

    if(!mouse_shown){
        mouse_shown=true;
        py.link("showCursor");
    }
});


$(document).mousedown(function(event){
    py.link("showCursor");
});

$(document).mouseleave(function(event){
    py.link("showCursor");
});

