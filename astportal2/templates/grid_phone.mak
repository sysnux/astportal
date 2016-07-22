<%inherit file="local:templates.master"/>

   <script type="text/javascript">
//<![CDATA[

var subgrid_expanded = 0;      
$(document).ready(function() {
   $(window).bind('resize', function() {
      $('#grid').setGridWidth($('#data').width()-10, true);
   });
   window.setInterval(grid_reload, 5000);
	$('#grid').jqGrid('setGridParam', { 
		subGridBeforeExpand: function(e) {
			subgrid_expanded++;
			return true;
		},
		subGridRowColapsed: function(e) {
			subgrid_expanded--;
			grid_reload();
			return true;
		},
	});
});

function grid_reload() {
	if (!subgrid_expanded) {
      $('#grid').trigger("reloadGrid");
	}
}

function add(x) {
   location = 'new'
}

function del(xid,msg) {
   if (confirm(msg)) {
      with (document.form_delete) {
         _id.value = xid;
         submit();
      }
   }
}

function phone_open(ip, pwd, phone_type, mac) {
console.log('phone_type='+phone_type);
   with (document.phone_login) {
      if (phone_type=='1') {
         P2.value = pwd;
         action = 'http://' + ip + '/dologin.htm';
         submit();
      } else if (phone_type=='2') {
         P2.value = pwd;
         action = 'http://' + ip + '/cgi-bin/dologin';
         submit();
      } else if (phone_type=='3') {
         $.ajax({
            type: 'POST',
            url: 'gxplogin',
            data: {'ip': ip, 'mac': mac, 'pwd': pwd},
            success: function (data, stat, xhr) { 
console.log(data);
console.log(stat);
console.log(xhr);
               if (data) {
                  sid.value = data['sid'];
                  action = 'http://' + ip + ''; // '/#page:status_account';
                  submit();
               }
            },
            error: function (xhr, stat) { alert('ERREUR: ' + status); },
         });
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

      <!-- GS login form -->
      <form name="phone_login" action="" method="post" target="_blank">
         <!--input type="hidden" name="P2" value=""/>
         <input type="hidden" name="gnkey" value="0b82"/-->
         <input type="hidden" name="sid" value=""/>
      </form>

      <p>
         <input type="checkbox" id="unavailable_only" 
            onchange="$('#grid').trigger('reloadGrid');" />
         <label for="unavailable_only">
            Afficher seulement les postes non connectés
         </label>
      </p>

      <div id="data">
         <!-- JQuery Grid -->
         ${tmpl_context.grid() | n}
      </div>

      <!-- Delete form -->
      <form name="form_delete" action="delete" method="POST">
         <input type="hidden" name="_id" />
         <input type="hidden" name="_method" value="DELETE" />
      </form>

