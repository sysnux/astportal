<%inherit file="local:templates.master"/>


		<h1>${title}</h1>

% if debug :
		${debug}<br/>
% endif

      ${tmpl_context.form(values) | n}

      <a href='..'>Retour</a>

