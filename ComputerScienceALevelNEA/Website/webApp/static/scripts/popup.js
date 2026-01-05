$ = function(id) {
    return document.getElementById(id);
}

var hide = function(id) {
	$(id).style.display ='none';
}

window.onload = function() {
    setTimeout(hide, 5000, "popup");
}

