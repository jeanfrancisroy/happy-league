function test_function(){
	var postdata = {name: "Allo"} ;
	$.post('/test', postdata, function(data) {
		$("#div_test").html(data["text"] + ", " + data["chiffre"]) ;
	});
	return false ;
};