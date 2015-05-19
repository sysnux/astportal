<%inherit file="local:templates.master"/>

<script type="text/javascript">
//<![CDATA[
$(document).ready(function() {
	email_voicemail_display();
	$('#voicemail').change(function () { email_voicemail_display(); });
});

function email_voicemail_display() {
   // Hide sub forms
	var vm = $('input:radio[name=voicemail]:checked').val();
	if (vm.toLowerCase()=='true')
		$('#email_voicemail\\.container').show();
	else
		$('#email_voicemail\\.container').hide();
}

//]]>
</script>

% if debug :
		${debug}<br/>
% endif

		<h1>${title}</h1>

      ${tmpl_context.form(values) | n}

      <a href='..'>Retour</a>
