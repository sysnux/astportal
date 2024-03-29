<%inherit file="local:templates.master"/>

   <link type="text/css" href="/toscawidgets/resources/tw.jquery.base/static/css/ui.all.css" rel="stylesheet" />
   <script type="text/javascript"
      src="/toscawidgets/resources/tw.jquery.base/static/javascript/ui/minified/jquery-ui.min.js"></script>

   <style>
tr.even td.free, tr.odd td.free { background-color: lightgreen;}
tr.even td.paused, tr.odd td.paused { background-color: violet;}
tr.even td.inuse, tr.odd td.inuse { background-color: red;}
tr.even td.ringing, tr.odd td.ringing { background-color: yellow;}
tr.even td.invalid, tr.odd td.invalid { background-color: lightgrey;}
   </style>

   <script type="text/javascript">
//<![CDATA[

var last=0, // last_update
    my_name = null, // Current user name
    my_phone = null, // Current user phone
    my_group = null, // Current user's groups
    my_location = null, // Current user SIP user
    admin = false, // Is administrator?
    my_status = null, // Current user status (1=> not in use)
    time_diff = 0, // Time difference beween client and server
    change = true, // Change in list of queues or members, need rebuild list
    first_time = true, error = 0, display_tmo = null,
    add_queue = null,  // List of users for adding members
    queues = new Object(), // List of queues
    members = new Object(), // List of members
    // Parameters of popup window (on connect / hangup)
    popup_params = 'location=no,scrollbars=yes,toolbar=no,menubar=no,width=600,height=600';


$(document).ready(function() {
   $('#add_form').dialog({ 
         autoOpen: false,  modal: true, width: '450px',
         buttons: { "Valider": function() {add_member()}, 
            "Annuler": function() {$('#add_form').dialog('close');}} });
   $(document).ajaxError(ajax_error);
   if (${auth}) {
      fetch_updates();
   }
});

function fetch_updates() { // Long running request for data updates
   $.post(
      "${tg.url('/cc_monitor/update_queues')}",
      {'last': last},
      updates_ready, 'json');
}

function updates_ready(data) {
   if (data) {
      // Data is null on AstPortal reload
      queues = data.queues;
      members = data.members;
      change = data.change;
      my_name = data.my_name;
      my_phone = data.my_phone;
      my_groups = data.my_groups;
      admin = data.admin;
      last = data.last;
      time_diff = last - ((new Date()).getTime()/1000); // Epoch time
      if (first_time) {
         change=true;
         first_time=false;
         list_queues();
      }
      data=null;
   }
   setTimeout(fetch_updates,500);
}

function list_queues() { // Builds main part of the screen

   var now = ((new Date()).getTime()/1000) + time_diff; // Epoch time
   if (change) { 
      // Something has changed (queue or member), need to rebuild the whole screen
      change = false;
      var html = '';
      var j=1;

      // qt is queues table: single table with # of agents, # of calls in queue, 
      // and times in queue
      var qt = '<table><tr><th>Agents connectés</th><th>Groupes</th><th>Appels en attente</th><th>Temps en attente</th></tr>';

      for (var q in queues) { // For each queue, display name and table
         var qname = queues[q]['name'];
         var qparams = queues[q]['params'];
         var qm = qparams['Members'], lm;
         if (qm==undefined) lm=0;
         else lm=qm.length;
         qt += '<tr class="' + ((j++%2) ? 'even':'odd') + '"><td>' + lm + '</td>';
         qt += '<td>' + qname + '</td>';
         var w=0, qw_keys = Object.keys(qparams['Wait']).sort();
         qt += '<td>' + qw_keys.length + '</td>';
         var waiting = new Array();
         for (var i=0;  i<qw_keys.length; i++) {
            w++;
            var qwid = qw_keys[i];
            waiting.push((1+i) + ' : ' + min_sec(now - qparams['Wait'][qwid][0]));
         }
         var qid = qname.replace(/\W/g,'_');
         qt += '<td id="wait_' + qid + '">' + waiting.join(', ') + '</td></tr>';

         // Queue details: status + information on members
         html += '<h2>Groupe ' + qname + '</h2>';
         var in_group = false;
         var table = '';
         if (admin) {
            table += '<table><tr><th rowspan="2">&nbsp;</th><th rowspan="2">Agents<br/>(pénalité)</th><th rowspan="2">&Eacute;tat</th>';
            table += '<th rowspan="2">Durée</th><th colspan="2">Appels reçus</th><th colspan="2">Appel émis</th><th rowspan="2">&Eacute;couter</th>';
            table += '<th rowspan="2">Enreg.</th rowspan="2"><th rowspan="2">Retirer</th></tr>';
            table += '<tr><th>Nb</th><th>Total</th><th>Nb</th><th>Total</th></tr>';
         } else {
            table += '<table><tr><th rowspan="2">&nbsp;</th><th rowspan="2">Agents<br/>(pénalité)</th><th rowspan="2">&Eacute;tat</th>';
            table += '<th rowspan="2">Durée</th><th colspan="2">Appels reçus</th><th colspan="2">Appel émis</th>';
            table += '</tr><tr><th>Nb</th><th>Total</th><th>Nb</th><th>Total</th></tr>';
         }

         var i=1;
         for (m in qm) { // For each member in this queue
            if (members[qm[m]]==undefined) continue; // XXX
            var id = qid + '_' + qm[m].replace(/\W/g,'_');
            table += '<tr class="' + ((i%2) ? 'even':'odd') + '"><td>' + i + '</td>';
            table += '<td>' + qm[m] + ' (' + members[qm[m]]['Queues'][qname]['Penalty'] + ')' + '</td>';
            //[sclass, sta, dur, nci, tci, nco, tco, lis, rec] = NOT working in chrome !
            var a = member_status(qm[m], now, qname);
            table += '<td id="sta_' + id + '"class="' + a[0] + '">' + a[1] + '</td>';
            table += '<td id="dur_' + id + '">' + a[2] + '</td>';
            table += '<td id="nci_' + id + '">' + a[3] + '</td>';
            table += '<td id="tci_' + id + '">' + a[4] + '</td>';
            table += '<td id="nco_' + id + '">' + a[5] + '</td>';
            table += '<td id="tco_' + id + '">' + a[6] + '</td>';
            if (admin) {
               table += '<td id="lis_' + id + '">' + a[7] + '</td>';
               table += '<td id="rec_' + id + '">' + a[8] + '</td>';
               table += '<td><input type="checkbox" onclick="remove_member(\'' + 
                  qname + '\',\'' + members[qm[m]]['Location']  + 
                  '\',\'' + qm[m].replace(/'/, ' ') + '\')"/></td>';
            }
            table += '</tr>';
            if (qm[m]==my_name) {
               in_group = true;
               my_location = members[qm[m]]['Location'];
            }
            i++;
         }
         if (i==1) { // No members !
            html += '<i>Aucun agent</i><br/>';
         } else {
            html += table +'</table>';
         }
         if (!admin && my_groups.indexOf('AG ' + qname)>=0) {
            if (in_group) {
               html += '<a href="#" onclick="leave_queue(\'' + qname + '\', \'' + my_location + '\', \'' + my_name + '\')">Sortir</a> du groupe';
            } else {
               html += '<a href="#" onclick="join_queue(\'' + qname + '\', ' + my_phone + ')">Entrer</a> dans le groupe';
            }
         }
         if (admin) {
            html += '<a href="#" onclick="fetch_exten(\'' + qname + '\')">Ajouter un agent</a>';
         }
      }
      html += "<h2>&Eacute;tat des files d'attente</h2>" + qt + '</table>';
//      if (admin) {
//         html += '<a href="#" onclick="fetch_exten(\'__ALL__\')">Ajouter un agent à toutes les files</a>';
//      }
      $('#queues_list').html(html);
   }

   else {
      // No change, just update variable fields
      for (q in queues) { // For each queue, display name and table
         var qname =  queues[q]['name'];
         var qparams =  queues[q]['params'];
         var qm = qparams['Members'];
         var qid = qname.replace(/\W/g,'_');

         var qw_keys = Object.keys(qparams['Wait']).sort();
         var waiting = new Array();
         for (var i=0;  i<qw_keys.length; i++)
            waiting.push((1+i) + ' : ' + min_sec(now - qparams['Wait'][qw_keys[i]][0]));
         $('#wait_' + qid).html(waiting.join(', '));

         for (m in qm) { // For each member in this queue
            if (members[qm[m]]==undefined) continue; // XXX
            var id = qid + '_' + qm[m].replace(/\W/g,'_');
            var a = member_status(qm[m], now, qname);
            $('#sta_' + id).attr('class', a[0]);
            $('#sta_' + id).html(a[1]);
            $('#dur_' + id).html(a[2]);
            $('#nci_' + id).html(a[3]);
            $('#tci_' + id).html(a[4]);
            $('#nco_' + id).html(a[5]);
            $('#tco_' + id).html(a[6]);
            $('#lis_' + id).html(a[7]);
            $('#rec_' + id).html(a[8]);
         }
      }
   }
   display_tmo = setTimeout(list_queues, 500);
}

function join_queue(q, u) {
   $.post(
      "${tg.url('/cc_monitor/add_member')}",
      {'queue': q, 'member': u, 'penality': 0},
      function (data) { // 
      },
      'json');
}

function leave_queue(q, i, u) {
   $.post(
      "${tg.url('/cc_monitor/remove_member')}",
      {'queue': q, 'iface': i, 'member': u},
      function (data) { // 
      },
      'json');
}

function member_status(name, now, queue) {
   member = members[name];
   var lis = '', rec = '';
   var sclass, stat, dur, nci, tci, nco, tco;
   switch (member['Status']) {
      case '1': // AST_DEVICE_NOT_INUSE
         if (name==my_name && my_status) {
	    		my_status = null;
            if (member['HangupURL']!='') {
               // Open hangup window
               var params = '?uid=' + member['Uniqueid'] +
                         '&member=' + name +
                         '&interface=' + member['StateInterface'] +
                         '&queue=' + queue +
                         '&custom1=' + member['Custom1'] +
               			 '&custom2=' + member['Custom2'];
	        window.open(member['HangupURL'] + params, 
                    'Hangup' + member['Uniqueid'], popup_params);
            }
         }
         if (member['Paused']!='0') {
            sclass = 'paused';
            stat = member['Paused'];
            dur = min_sec(now - member['PauseBegin']);
         } else {
            sclass = 'free';
            stat = 'Libre';
            dur = '';
         }
         break;
      case '2': // AST_DEVICE_INUSE
      case '3': // AST_DEVICE_BUSY
         if (name==my_name && 
             member['PeerChannel']!='' && 
             (my_status==null || my_status!=member['Uniqueid'])) {
            my_status = member['Uniqueid'];
            if (member['ConnectURL']) {
               // Open connect window
               var params = '?uid=' + member['Uniqueid'] +
                            '&member=' + name +
                            '&interface=' + member['StateInterface'] +
                            '&callerid=' + member['PeerCallerid'] +
                            '&channel=' + member['PeerChannel'] +
                            '&queue=' + queue +
                            '&holdtime=' + member['HoldTime'] +
                            '&custom1=' + member['Custom1'] +
                            '&custom2=' + member['Custom2'];
               window.open(member['ConnectURL'] + params,
                  'CRM' + member['Uniqueid'], popup_params);
            }
         }
      case '8': // AST_DEVICE_ONHOLD
         sclass='inuse'; 
         if (member['Outgoing']) {
            stat='Appel émis';
            dur = min_sec(now - member['OutBegin']);
         } else {
            stat='Appel reçu';
            dur = min_sec(now - member['InBegin']);
         }
         lis = '<input type="checkbox" onclick="spy(\'' + 
            name + '\',\'' + member['StateInterface'] + '\')"';
         if (member['Spied']) lis += ' checked="checked"';
         lis += '/>';
         rec = '<input type="checkbox" onclick="record(\'' + 
            name + '\',\'' + member['StateInterface'] + '\', \'' + queue + '\');"';
         if (member['Recorded']) rec += ' checked="checked"';
         rec += '/>';
         break;
      case '6': // AST_DEVICE_RINGING
      case '7': // AST_DEVICE_RINGINUSE
         sclass='ringing'; stat='Sonnerie'; dur=0; break; 
      case '4': // AST_DEVICE_INVALID
      case '5': // AST_DEVICE_UNAVAILABLE
      default: 
         sclass = 'invalid';
         stat = 'Invalide';
         dur = 0;
         break;
   }
   nci = member['Queues'][queue]['CallsTaken'];
   tci = min_sec(member['InTotal']);
   nco = member['CallsOut'];
   tco = min_sec(member['OutTotal']);
   return [sclass, stat, dur, nci, tci, nco, tco, lis, rec];
}

function spy(name, channel) {
   $.post(
      "${tg.url('/cc_monitor/spy')}",
      {'name': name, 'channel': channel},
      function (data) { // 
      },
      'json');
   members[name]['Spied'] = true;
}

function record(name,channel,queue) {
   $.post(
      "${tg.url('/cc_monitor/record')}",
      {'name': name, 'channel': channel, 'queue': queue,
         'custom1': members[name]['Custom1'], 
         'custom2': members[name]['Custom2']},
      function (data) { // 
      },
      'json');
   members[name]['Recorded'] = true;
}

function ajax_error(e, xhr, settings, exception) {
   error++;
   if (error>3) {
      alert('ERREUR ! ' + error);
      error=0;
   } else {
      // Wait a bit and try again
      setTimeout(fetch_updates,1000*error);
   }
}

function fetch_exten(queue) { // Request exten list
   add_queue = queue;
   $.post(
      "${tg.url('/cc_monitor/list_exten')}",
      {'queue': queue},
      function (data) { // Populate select and display add member form
         $('option', '#agent_select').remove();
         for (p in data.phones) {
            $('#agent_select').append(new Option(data.phones[p][1],data.phones[p][0]));
         }
         $('#add_form').dialog('open');
      },
      'json');
}

function add_member() { // Called from click on "Add member" link
   $.post(
      "${tg.url('/cc_monitor/add_member')}",
      {'queue': add_queue, 'member': $('#agent_select').val(),
      'penality': $('#penality').val()},
      null, 'json');
   add_queue = null;
   $('#add_form').dialog('close');
}

function remove_member(queue, iface, member) {
   if (confirm('Retirer "' + member + '" du groupe "' + queue + '"')) {
      $.post(
         "${tg.url('/cc_monitor/remove_member')}",
         {'queue': queue, 'iface': iface, 'member': member},
         null, 'json');
   } else {
      change = true; // Force redisplay to cleanup checkbox
   }
}

function min_sec(sec) {
   // Converts sec to string min:sec (ex 83 -> 1:23)
   sec = Math.ceil(sec);
   var min = parseInt(sec/60);
   sec %= 60;
   if (sec<10) sec = '0'+sec;
   return min + ':' + sec;
}

//]]>
   </script>

		<h1>${title}</h1>

% if debug :
		${debug}<br/>
% endif


      <div id="add_form">
         <table>
            <tr><td>Agent :</td>
               <td><select id="agent_select"></select></td></tr>
            <tr><td>Pénalité :</td>
               <td><input type="text" id="penality" size="4"/></td></tr>
         </table>
      </div>

      <div id="queues_list"><i>Loading. . .</i></div>

