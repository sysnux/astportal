<%inherit file="local:templates.master"/>

   <script type="text/javascript">
//<![CDATA[
      
$(document).ready(function() {
   $(window).bind('resize', function() {
      $('#grid').setGridWidth($('#data').width()-10, true);
   });
});

function postdata(to,p) {
  var f = document.createElement('form');
  f.method = "post";
  f.action = to;
  for (var k in p) {
    var i = document.createElement('input') ;
    i.setAttribute('type', 'hidden') ;
    i.setAttribute('name', k) ;
    i.setAttribute('value', p[k]);
    f.appendChild(i) ;
  }
  document.body.appendChild(f) ;
  f.submit() ;
}

//]]>
   </script>
</head>

<body>
      <h1>${title}</h1>

      <div id="data">
         <!-- JQuery Grid -->
         ${tmpl_context.grid() | n}
      </div>
