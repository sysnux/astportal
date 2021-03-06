<%inherit file="local:templates.master"/>

   <script type="text/javascript">
//<![CDATA[

var last=0, error=0, server_time=0;
var begins= new Object();
var channels = new Object();

$(document).ready(function() {
   $(document).ajaxError(data_fetch_failed);
   update();
   display_tmo = setTimeout(display, 1500);
});

function update() {
   // update_channels has a 1 second sleep on server, so this can be called
   // in a loop without delay
   $.post(
      "${tg.url('/monitor/update_channels')}",
      {'last': last},
      list_channels, 'json');
}

function list_channels(data) {
   if (data) {
      // Data is null on AstPortal reload
      channels = data.channels;
      last = data.last_update;
      server_time = data.time;
      update();
   } else
      setTimeout(update, 1000);
}

function display() {
   var table = '', time = (new Date()).getTime(), tot_chan=0, tot_calls=0;
   for (p in channels) {
      var c = channels[p];
      if (c['State']=='Down')
         continue; // Don't display down channels
      tot_chan++;
      if (c['Link']!=undefined && c['Outgoing']) {
         // Don't display outgoing linked channel
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
         if (!c['Outgoing']) {
       		table += '<td>' + c['CallerIDName'] + ' ' + c['CallerIDNum'] + '</td>';
            table += '<td>&nbsp;</td>';
         } else {
            table += '<td>&nbsp;</td>';
       		table += '<td>' + c['CallerIDName'] + ' ' + c['CallerIDNum'] + '</td>';
         }
      } else { // Channel is linked to another
       	table += '<td>' + c['CallerIDName'] + ' ' + c['CallerIDNum'] + '</td>';
         if (channels[c['Link']]!=undefined) {
   		   table += '<td>' + channels[c['Link']]['CallerIDName'] + ' ' + channels[c['Link']]['CallerIDNum']  + '</td>';
         } else {
            table += '<td>&nbsp;</td>';
         }
      }
		table += '<td>' + duree + '</td>';
		table += '<td>' + c['State'] + '</td>';
      var x = '';
      if (c['Application']!=undefined)
         x = c['Application'] + ((c['AppData']!=undefined) ? '(' + c['AppData'] + ')' : '');
      table += '<td>' + x + '</td>';
      x = '';
      if (c['Context']!=undefined)
         x = c['Context'] + ((c['Priority']!=undefined) ? '(' + c['Priority'] + ')' : '');
      table += '<td>' + x + '</td>';
		table += '</tr>';
   }

   if (tot_chan) {
      table = '<table><tr><th>Appelant</th><th>Appelé</th><th>Durée</th><th>&Eacute;tat</th><th>Application</th><th>Contexte</th></tr>' + table;
      table += '<tr>';
      table += '<th>Total :</th>';
      table += '<th colspan="6">' + tot_calls + ' appel' + ((tot_calls>1) ? 's':'');
      table += ' (' + tot_chan + ' can' + ((tot_chan>1) ? 'aux':'al') + ')</th>';
      table += '</tr></table>';
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

