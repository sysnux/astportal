<%inherit file="local:templates.master"/>

   <script type="text/javascript">
//<![CDATA[
      
$(document).ready(function() {
   $(window).bind('resize', function() {
      $('#grid').setGridWidth($('#data').width()-10, true);
   });
});

function add(x) {
   location = 'new/'
}

function del(xid,msg) {
   if (confirm(msg)) {
      with (document.form_delete) {
         _id.value = xid;
         submit();
      }
   }
}
//]]>
   </script>
</head>

<body>
   <h1>${title}</h1>
% if debug:
                ${debug}<br>
% endif

      <!-- Form -->
% if tmpl_context.form:
         ${tmpl_context.form(values) | n}
% endif

      <div id="data">
         <!-- JQuery Grid -->
         ${tmpl_context.grid() | n}
      </div>

      <!-- -->
      <form name="form_delete" action="delete" method="POST">
         <input type="hidden" name="_id" />
         <input type="hidden" name="_method" value="DELETE" />
      </form>

