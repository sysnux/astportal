<%inherit file="local:templates.master"/>

% if debug :
		${debug}<br/>
% endif

		<h1>${title}</h1>

      ${tmpl_context.form(values) | n}

      <a href='..'>Retour</a>

   <script type="text/javascript">
//<![CDATA[

$(document).ready( function() {
   $('#record').click(function () {
      console.log("${tg.url('../record_by_phone')}", $('#record').is(':checked'));
		if ($('#record').is(':checked'))
	      $.post("${tg.url('../record_by_phone')}");
   });
});

//]]>
   </script>

