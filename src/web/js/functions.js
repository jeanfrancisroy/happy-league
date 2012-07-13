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
    $('#tab_config a:first').tab('show');
  })