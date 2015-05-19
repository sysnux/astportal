<%inherit file="local:templates.master"/>

   <script type="text/javascript">
//<![CDATA[

$(document).ready(function() {
   $("#tabs").tabs();
   $('#grid').setGridWidth($('#data').width()-10, true);
   $(window).bind('resize', function() {
      $('#grid').setGridWidth($('#data').width()-10, true);
   });

});

function ecoute(f) {
   with(document.ecoute_form) {
      file.value = f
      submit()
   }
}
//]]>
   </script>

      <h1>${title}</h1>
% if debug:
		${debug}<br />
% endif

      <div id="tabs">
         <ul>
            <li><a href="#data">Données</a></li>
            <li><a href="#search_form">Recherche</a></li>
         </ul>

         <div id="data">
            <!-- JQuery Grid -->
            ${tmpl_context.grid() | n}
         </div>

         <div id="search_form">
				${tmpl_context.form(values) | n}
         </div>

      </div>

      <form name="ecoute_form" action="ecoute" method="post">
         <input type="hidden" name="file" />
      </form>

