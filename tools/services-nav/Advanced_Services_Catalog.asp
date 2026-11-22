<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title><#WRServicesNav#></title>
<link rel="stylesheet" href="/bootstrap/css/bootstrap.min.css">
<link rel="stylesheet" href="/bootstrap/css/main.css">
<script src="/jquery.js"></script>
<script src="/bootstrap/js/bootstrap.min.js"></script>
<script src="/state.js"></script>
</head>
<body onload="show_banner(1); show_menu(5,7,2); show_footer();">
<div class="wrapper">
    <div class="container-fluid">
        <div class="row-fluid">
            <div class="span3"><div id="logo"></div></div>
            <div class="span9"><div id="TopBanner"></div></div>
        </div>
        <div class="row-fluid">
            <div class="span3">
                <div class="well sidebar-nav side_nav">
                    <ul id="mainMenu" class="clearfix"></ul>
                    <ul class="clearfix"><li><div id="subMenu" class="accordion"></div></li></ul>
                </div>
            </div>
            <main class="span9">
                <div class="well">
                    <h2><#WRServicesNav#></h2>
                    <div id="wr_service_catalog"></div>
                </div>
            </main>
        </div>
    </div>
    <div id="Loading" class="popup_bg"></div>
    <div id="footer"></div>
</div>
</body>
</html>
