<!DOCTYPE html>
<html>

<head>
    <meta charset="utf-8"/>
    <title>${title}</title>
    <link rel="stylesheet" href="${tg.url('/css/style.css')}" />
    <script type="text/javascript">
//<![CDATA[

$(document).ready(function () {
   $('#menu_toggle_link').css('height',$('#sidebar_div').css('height'));
   $('#menu_toggle_link').css('cursor','pointer');
   $('#menu_toggle_link').click(menu_toggle);
});

function set_prefs(menu) {
   $.post(
      "${tg.url('/users/set_prefs')}",
      {'menu': menu},
      set_prefs_cb, 'json'
      );
//alert('set_prefs ' + menu);
}

function set_prefs_cb(data) {
//alert('set_prefs_cb ' + data);
}

var menu_status=1;
function menu_toggle() {
   if (menu_status) {
      $('#sidebar_div').hide();
      $('#main_content').css('padding-left', '60px');
      $('#menu_toggle_link').text('>');
      menu_status=0;
//      set_prefs(false);
   } else {
      $('#sidebar_div').show();
      $('#main_content').css('padding-left', '180px');
      $('#menu_toggle_link').text('<');
      menu_status=1;
//      set_prefs(true);
   }
   if (typeof($('#grid').setGridWidth)=='function')
      $('#grid').setGridWidth($('#data').width()-10, true); // XXX $('#grid').parent()
}
//]]>
    </script>
</head>
<body>

   <!-- Entête -->
   <div id="header">
      <div id="toolbox">
% if tg.request.identity is not None:
           Connecté <b>${tg.request.identity['user']}</b><br/>
            <a href="${tg.url('/logout_handler')}">Déconnexion</a>
% else:
            <a href="${tg.url('/login')}">Connexion</a>
% endif
<br />
      </div>
   </div>

   <!-- Menu -->
   <div id="menu" class="menu">
      <table><tr><td>
         ${render_sidebar() | n}
      </td><td id="menu_toggle_link" style="background: #ccc">&lt;</td></tr></table>
   </div>

   <!-- Contenu -->
   <div id="main_content">
<% flash = tg.flash_obj.render('flash', use_js=False) %>
% if flash:
		<div>
			${flash | n}
		</div>
%endif
		${self.body()}
   </div>

   <!-- Pied -->
   <div id="footer">
      <p>Copyright &#169; 2007-2014 <a href="http://www.sysnux.pf">SysNux</a>, powered by:</p>
      <img src="${tg.url('/images/under_the_hood_blue.png')}" alt="TurboGears under the hood" />
   </div>

</body>

<%def name="my_title()">  </%def>
</html>
