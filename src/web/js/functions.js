function test_function(name){
	var postdata = {"name": name} ;
	$.post('/test', postdata, function(data) {
		greeting = data["greeting"];
		name = data["name"];
		hash = data["hash"]
		$("#div_result").html(greeting + name + hash) ;
	});
	return false ;
};

$('#tab_config a').click(function (e) {
	e.preventDefault();
	$(this).tab('show');
})

$(function () {
	// On the config page, show the first tab.
	$('#tab_config a:first').tab('show');
})

$(document).ready(function() {
    var pathname = window.location.pathname.substring(1);
    $("#li_" + pathname).addClass("active");
});