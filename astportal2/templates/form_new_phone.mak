<%inherit file="local:templates.master"/>

   <script type="text/javascript">
//<![CDATA[

var wait_msg_html;

$(document).ready(function() {
   $("#wait_msg").hide();
   $("#wait").hide();
   $("#tabs").tabs();
//   $("#tabs").tabs( "disable", 1 );
   wait_msg_html = $("#wait_msg").html();
});

function wait() {
   // Called before phone discovery starts: display wait screen
   $("#wait").css({'width':$(document).width(),
         'height':$(document).height()});
   $("#wait_msg").html(wait_msg_html);
   $("#wait_msg").css({'left': ($(document).width()-$("#wait_msg").width())/2,
         'top': $(document).height()/3});
   $("#wait").show();
   $("#wait_msg").show();
}


function phone_ok(x) {
   // Called when phone discovery is finished: displays result for 2 seconds,
   // then chains to phone_ok2
   var data = $.parseJSON(x);
   $("#wait_msg").html(data.msg);
   setTimeout(phone_ok2, 2000, data);
}

function phone_ok2(data) {
   // Unlocks second tab
   $("#wait_msg").hide();
   $("#wait").hide();
   document.form_info.ip.value = data.ip;
   document.form_info.mac.value = data.mac;
   document.form_info.password.value = data.password;
   $("#phone_type").html(data.msg);
   if (!data.status) {
      $("#tabs").tabs( "enable", 1 )
   }
}

function wait2() {
   $("#wait").css({'width':$(document).width(),
         'height':$(document).height()});
   $("#wait_msg").html('<i>Configuration en cours, veuillez patienter... </i><img src="/images/ajax-loader.gif"/>');
   $("#wait_msg").css({'left': ($(document).width()-$("#wait_msg").width())/2,
         'top': $(document).height()/3});
   $("#wait").show();
   $("#wait_msg").show();
}

function created(x) {
   $("#wait_msg").hide();
   $("#wait").hide();
   data = $.parseJSON(x);
   if (data.status=='bad_exten') {
      alert('Poste déjà utilisé !');
   } else if (data.status=='bad_dnis') {
      alert('Numéro direct déjà utilisé !');
   } else {
      $(location).attr('href','/phones/');
   }
}
//]]>
   </script>

		<h1>${title}</h1>

% if debug :
		${debug}<br/>
% endif

      <div id="tabs">
         <ul>
            <li><a href="#ip">Identification</a></li>
            <li><a href="#info">Informations</a></li>
         </ul>
         <div id="ip">
            <!-- Phone discovery form -->
      		${tmpl_context.ip_form() | n}
            <div id="phone_type"></div>
         </div>
         <div id="info">
            <!-- Phone info form -->
      		${tmpl_context.form(values) | n}
         </div>
      </div>
      <div id="wait" style="position: absolute; left: 0; top: 0; 
         background: #000; opacity: 0.3;">
      </div>
      <div id="wait_msg" style="position: absolute; z-index: 1000; 
         background: #FFF; margin: 5px; padding: 15px; border: 5px solid #CCC">
         <i>Recherche du téléphone, veuillez patienter... </i>
         <img src="/images/ajax-loader.gif"/>
      </div>

