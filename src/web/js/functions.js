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