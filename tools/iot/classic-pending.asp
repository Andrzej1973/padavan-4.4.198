<!DOCTYPE html>
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title><#Web_Title#> - IoT</title>
<link rel="stylesheet" href="/bootstrap/css/bootstrap.min.css">
<link rel="stylesheet" href="/bootstrap/css/main.css">
<script src="/jquery.js"></script>
<script src="/bootstrap/js/bootstrap.min.js"></script>
<script src="/state.js"></script>
<script src="/general.js"></script>
<script>
var $j = jQuery.noConflict();
function initial() { show_banner(1); show_menu(5,0,0); show_footer(); }
</script>
</head>
<body onload="initial();">
<div class="wrapper">
<div id="TopBanner"></div>
<div class="container-fluid"><div class="row-fluid">
<div class="span3"><div class="well sidebar-nav side_nav" style="padding:0">
<ul id="mainMenu" class="clearfix"></ul>
<ul class="clearfix"><li><div id="subMenu" class="accordion"></div></li></ul>
</div></div>
<div class="span9"><div class="box well grad_colour_dark_blue">
<h2 class="box_head round_top"><#menu5_1#> - IoT (2.4GHz)</h2>
<div class="round_bottom"><div id="tabMenu" class="submenuBlock"></div>
<div class="alert alert-info"><#WR_IOT_CLASSIC_Pending#></div>
<p><a class="btn" href="/index.asp"><#menu1#></a></p>
</div></div></div>
</div></div><div id="footer"></div>
</div>
</body>
</html>
