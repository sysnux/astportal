<%inherit file="local:templates.master"/>

   <script type="text/javascript">
//<![CDATA[

var last=0, error=0, server_time=0;
var begins= new Object();
var channels = new Object();
var ws = null, ws_reconnect = null;

$(document).ready(function() {
	ws_connect();
   display_tmo = setTimeout(display, 1500);
});

function ws_connect() {
   // Create WebSocket
   ws = new WebSocket('${ws_url}');
   ws.onopen = function(evt) {
		if (ws_reconnect) clearInterval(ws_reconnect);
		ws_reconnect = null;
		ws_status('Connecté', 'green'); 
   	ws_send_message('subscribe_channels');
	};
   ws.onclose = function(evt) { ws_closed();	};
   ws.onmessage = function(evt) { list_channels(JSON.parse(evt.data)); };
   ws.onerror = function(evt) { ws_error(evt); };
}

function ws_error(evt) { 
	console.log('WS ERROR ' + evt.data);
	ws_status(evt.data, 'red'); 
}

function ws_status(msg, color) {
   if (color)
      msg = '<span style="color: ' + color + ';">' + msg + '</span>';
   $('#status').html(msg + '<br/>');
}

function ws_send_message(msg) {
   if (ws)
      ws.send(msg);
   else
      ws_status("ERREUR envoi: " + msg, 'red');
}

function ws_closed() {
   ws_status('Déconnecté', 'red');
   ws = null;
   ws_reconnect = setTimeout(ws_connect, 1000);
}

function list_channels(data) {
   if (data) {
      // Data is null on AstPortal reload
      channels = data['channels'];
      last = data['last_update'];
      server_time = data['time'];
   }
}

function display() {
   var table = '', time = (new Date()).getTime(), tot_chan=0, tot_calls=0;
   for (p in channels) {
      var c = channels[p];

      if (c['State']=='Down')
         continue; // Don't display down channels
      tot_chan++;
      if (c['Link']!=undefined && !c['Outgoing']) {
         /* Don't display called linked channels, they will be displayed with
			calling channel */
         tot_calls++;
         continue
      }

		if (!begins[p])
         /* We should use c['Begin'], but time offset between client 
            and server is a problem, so keep a local copy of begin.
            Javascript time is millisec, server time is sec  */
			begins[p] = time - 1000 * (server_time - c['Begin']);

		duree = min_sec(time-begins[p]);
		table += '<tr class="' + ((tot_chan%2) ? 'even':'odd') + '">';
      if (c['Link']==undefined) { // Channel not linked
         if (c['Outgoing']) {
       		table += '<td>' + c['CallerIDName'] + ' ' + c['CallerIDNum'] + '</td>' +
            	'<td>&nbsp;</td>';
         } else {
            table += '<td>&nbsp;</td>' +
       			'<td>' + c['CallerIDName'] + ' ' + c['CallerIDNum'] + '</td>';
         }
      } else { // Channel is linked to another: display both on same row
       	table += '<td>' + c['CallerIDName'] + ' ' + c['CallerIDNum'] + '</td>';
         if (channels[c['Link']]!=undefined) {
   		   table += '<td>' + channels[c['Link']]['CallerIDName'] + ' ' + 
					channels[c['Link']]['CallerIDNum']  + '</td>';
         } else {
            table += '<td>&nbsp;</td>';
         }
      }

		table += '<td>' + duree + '</td>' +
			'<td>' + c['State'] + '</td>';
      var x = '';
      if (c['Application']!=undefined)
         x = c['Application'] + ((c['AppData']!=undefined) ? '(' + c['AppData'] + ')' : '');
      table += '<td>' + x + '</td>';
      x = '';
      if (c['Context']!=undefined)
         x = c['Context'] + ((c['Priority']!=undefined) ? '(' + c['Priority'] + ')' : '');
      table += '<td>' + x + '</td>' +
			'</tr>';
   }

   if (tot_chan) {
      table = '<table><tr><th>Appelant</th><th>Appelé</th><th>Durée</th><th>&Eacute;tat</th><th>Application</th><th>Contexte</th></tr>' + table +
      	'<tr>' +
      	'<th>Total :</th>' +
   		'<th colspan="6">' + tot_calls + ' appel' + ((tot_calls>1) ? 's':'') +
      	' (' + tot_chan + ' can' + ((tot_chan>1) ? 'aux':'al') + ')</th>' +
      	'</tr></table>';
   } else
      table = '<i>Aucun appel en cours</i>';

   for (p in begins)
      if (channels[p]==undefined)
         delete begins[p]; // Clean up to free memory!

   $('#channels_list').html(table);
   setTimeout(display,500);
}

function data_fetch_failed (e, xhr, settings, exception) {
   error++;
   if (error>3) {
      alert('ERREUR !' + error);
   } else {
      // Wait a bit and try again
      setTimeout(update, 1000*error);
   }
}

function min_sec(millisec) {
   // Converts millisec to string min:sec (ex 1:23)
   var sec = Math.round(millisec/1000);
   var min = Math.floor(sec/60);
   sec %= 60;
   return min + ((sec<10) ? ':0':':') + sec;
}

//]]>
   </script>

   <h1>${title}</h1>
% if debug:
                ${debug}<br>
% endif

   <div id="channels_list"><i>Loading...</i></div>
   <div id="status"></div>

