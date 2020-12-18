<%inherit file="local:templates.master"/>

   <link type="text/css" href="/toscawidgets/resources/tw.jquery.base/static/css/ui.all.css" rel="stylesheet" />
   <!--[if IE]><script type="text/javascript" src="../excanvas.compiled.js"></script><![endif]-->
   <script type="text/javascript"
      src="/toscawidgets/resources/tw.jquery.base/static/javascript/ui/minified/jquery-ui.min.js"></script>
   <script type="text/javascript" src="/js/jquery.timeentry.pack.js"></script>

   <style type="text/css">
      canvas {
         position:absolute;
         width: 2000px;
         height: 4000px;
         margin-left: -30px;
      }
      .bloc_title {
         background: #fff;
         border: 1px solid #fa0;
         margin: 5px;
         position: absolute;
      }
      .bloc_th {
         background: #fa0;
         color: #fff;
         cursor: move;
      }
   </style>

   <script type="text/javascript">
//<![CDATA[

var scenario = new Array();
var actions = new Object();
var applications = new Object();
var actions_by_id = new Object();
var sounds = new Object();
var sounds_by_id = new Object();
var texts = new Object();
var texts_by_id = new Object();
var queues = new Object();
var queues_by_id = new Object();
var qevents = new Object();
var qe_by_id = new Object();
var labels = new Object();
var contexts_pos = new Object();
var current=-1, unload_warning=1;
var add_edit = 'add';

window.onbeforeunload = function () {
   if (unload_warning)
      return 'Modifications non enregistrées';
}

$(document).ready(
   function() {
      // Action dialog
      $('#action_form').dialog({ 
         autoOpen: false,  modal: true, width: '450px',
         buttons: { "Valider": function() {valid_action()}, 
         "Annuler": function() {cancel_action()}} });

      // Fill objects (scenario, actions, sounds, ...)
      $.post(
      'fetch_scenario',
      {id: ${tmpl_context.app_id} },
      function(data,stat){
         scenario = data.scenario;
         scenario.sort(sort_scenario);
         actions = data.actions;
         sounds = data.sounds;
         texts = data.texts;
         queues = data.queues;
         qevents = data.qevents;
         contexts_pos = data.positions;
         applications = data.applications;

         var o = '<option value="-1"> - - - </option>\n';
         for (a in actions) {
            actions_by_id[actions[a].action_id] = actions[a].action_name;
            if (actions[a].action_id==0) continue;
//            if (actions[a].action_id==5) continue;
            o += '<option value="' + actions[a].action_id + '">'; 
            o += actions[a].action_name + ': ' + actions[a].action_comment;
            o += '</option>\n';
         }
         $('select#type_action').html(o);
         o = '<option value="-1"> - - - </option>\n';
         o += '<optgroup label="Sons pré enregistrés">\n';
         for (s in sounds) {
            o += '<option value="s;' + sounds[s].sound_id + '">'; 
            o += sounds[s].sound_name;
            if (sounds[s].sound_comment) o += ' (' + sounds[s].sound_comment + ')';
            o += '</option>\n';
            sounds_by_id[sounds[s].sound_id] = sounds[s].sound_name;
         }
         o += '</optgroup>\n';
         o += '<optgroup label="Synthèse vocale">\n';
         for (t in texts) {
            o += '<option value="t;' + texts[t].text_id + '">'; 
            o += texts[t].text_name;
            if (texts[t].text_comment) o += ' (' + texts[t].text_comment + ')';
            o += '</option>\n';
            texts_by_id[texts[t].text_id] = texts[t].text_name;
         }
         o += '</optgroup>\n';
         $('#1_file').html(o);
         $('#3_announce').html(o);
         $('#3_error').html(o);
         $('#3_abandon').html('<option value="-2">Continuer</option>\n' + o);
         $('#4_announce').html(o);
         $('#4_error').html(o);
         $('#4_abandon').html(o);
         $('#6_announce').html(o);
         $('#15_announce').html(o);
         $('#15_error').html(o);
         $('#15_abandon').html(o);

         o = '<option value="-1"> - - - </option>\n';
         for (q in queues) {
            queues_by_id[queues[q].queue_id] = queues[q].queue_name;
            o += '<option value="' + queues[q].queue_id + '">'; 
            o += queues[q].queue_name + ': ' + queues[q].queue_comment;
            o += '</option>\n';
         }
         $('#20_queuename').html(o);

         o = '<option value="-1"> - - - </option>\n';
         o += '<optgroup label="Groupes ACD">\n';
         for (q in queues) {
            queues_by_id[queues[q].queue_id] = queues[q].queue_name;
            o += '<option value="' + queues[q].queue_id + '">'; 
            o += queues[q].queue_name + ': ' + queues[q].queue_comment;
            o += '</option>\n';
         }
         o += '</optgroup>\n';
         o += '<optgroup label="Spéciaux">\n';
         o += '<option value="-2">Trace 1</option>\n';
         o += '<option value="-3">Trace 2</option>\n';
         o += '<option value="-4">Trace 3</option>\n';
         o += '</optgroup>\n';
         queues_by_id[-2] = 'Trace 1';
         queues_by_id[-3] = 'Trace 2';
         queues_by_id[-4] = 'Trace 3';
         $('#21_queuename').html(o);

         o = '<option value="-1"> - - - </option>\n';
         for (qe in qevents) {
            qe_by_id[qevents[qe].qe_id] = qevents[qe].event;
            o += '<option value="' + qevents[qe].qe_id + '">'; 
            o += qevents[qe].event + '</option>\n';
         }
         $('#21_event').html(o);

         $('#11_begin').timeEntry({show24Hours: true,
            spinnerImage: '/images/spinnerDefault.png',
            spinnerTexts: ['Maintenant', 'Champ précédent', 'Champ suivant', 'Augmenter', 'Diminuer'],
            timeSteps: [1, 5, 1],
            });
         $('#11_end').timeEntry({show24Hours: true,
            spinnerImage: '/images/spinnerDefault.png',
            spinnerTexts: ['Maintenant', 'Champ précédent', 'Champ suivant', 'Augmenter', 'Diminuer'],
            timeSteps: [1, 5, 1],
            });
         display();
      },
      'json'
      );
      unload_warning=0;
   }
);

function play_or_tts_to_text(x) {
   switch (x[0]) {
      case 's':
         return sounds_by_id[x.substr(2)];
         break;
      case 't':
         return texts_by_id[x.substr(2)];
         break;
      default:
         return 'NONE';
   }
}

function valid_action() {
   var param = '';
   var type = parseInt($("#type_action").val());
   switch (type) {
      case 0: // New context XXX
         break;

      case 1:
         param = $("#1_file").val();
         if (param==-1) {
            alert('Veuillez choisir un fichier à jouer !');
            return;
         }
         break;

      case 15: // Select
         var p1 = $("#15_announce").val();
         var p2 = $("#15_error").val();
         var p3 = $("#15_abandon").val();
         var p4 = $("#15_choice").val().replace(/[^\d*#]/g, '');
         var p5 = $("#15_var").val().replace(/\W/g, '_');
         if (p1==-1 || p2==-1 || p3==-1 || p4.length==0 || p5.length==0) {
            alert('Veuillez vérifier les données !');
            return;
         }
         param = p1 + '::' + p2 + '::' + p3 + '::' + p4 + '::' + p5;
         break;

      case 2: // Menu
         var p1 = $("#3_announce").val();
         var p2 = $("#3_error").val();
         var p3 = $("#3_abandon").val();
         var p4 = $("#3_choice").val().replace(/[^\d*#]/g, '');
         if (p1==0 || p2==0 || p3==0 || p4.length==0) {
            alert('Veuillez vérifier les données !');
            return;
         }
         param = p1 + '::' + p2 + '::' + p3 + '::' + p4;
         var choices = p4.split('');
         var ctxt = scenario[current-1].context + '_Menu_';
         for (i=0; i<choices.length; i++) {
            var create_context = true;
            for (s in scenario)
               if (scenario[s].context==ctxt + choices[i]) {
                  create_context = false;
                  break
               }
            if (!create_context) continue;
            var s = new Object();
            s.context = ctxt + choices[i];
            s.extension = 's';
            s.priority = 0;
            s.application = 0;
            scenario.splice(current+i+1,0,s);
         }
         break;

      case 3: // Input
         var p1 = $("#4_announce").val();
         var p2 = $("#4_error").val();
         var p3 = $("#4_abandon").val();
         var p4 = $("#4_var").val().replace(/\s/g, '');
         var radio = $("input[@name='4_input_type']:checked").val();
         if (p1==0 || p2==0 || p3==0 || p4.length==0 || radio.length==0) {
            alert('Veuillez vérifier les données !');
            return;
         }
         param = p1 + '::' + p2 + '::' + p3 + '::' + p4 + '::' + radio;
         if (radio=='fixed') {
            var len = parseInt($("#4_len").val());
            if (len<=0 || len>=20) { // XXX
               alert('Longueur invalide !');
               return;
            }
            param += '::' + len;
         }
         break;

      case 4: // Hangup
         break;

      case 5: // TTS
         param = $("#2_tts").val().replace(/::+/g, ':');
         if (param.length==0) {
            alert('Veuillez entrer un texte à synthétiser !');
            return;
         }
         break;

      case 6: // Record
         var p1 = $("#6_announce").val();
         if (p1==-1) {
            $('#6_announce').select();
            alert('Veuillez choisir une annonce !');
            return;
         }
         var p2 = parseInt($('#6_duration').val());
         if ($('#6_duration').val()!=p2) {
            $('#6_duration').select();
            alert('Veuillez entrez un nombre !');
            return;
         }
         if (p2<=5) p2=5; // Min duration
         if (p2>=300) p2=300; // Max duration
         var bip = $("input[@name='6_bip']:checked").val();
         param = [p1, p2, bip].join('::');
         break;

      case 7: // Transfer
         var number = $("#7_number").val();
         var timeout = $("#7_timeout").val();
         var noanswer = $("#7_noanswer").val();
         var busy = $("#7_busy").val();
         var error = $("#7_error").val();
         param = [number, timeout, noanswer, busy, error].join('::');
         // XXX vérifications...
         break;

      case 8: // Service Web
         var request = $("#8_request").val();
         var variable = $("#8_var").val();
         var param = request + '::' + variable;
         break;

      case 9: // Boucle
         var param = $("#9_action").val();
         if (param==-1) {
            alert('Veuillez choisir une action à répéter !');
            return;
         }
         var loop = $('#9_loop').val();
         if (parseInt(loop)!=loop) {
            $('#9_loop').select();
            alert('Veuillez entrez un nombre !');
            return;
         }
         param += '::' + loop;
         break;

      case 10: // Test
         var variable = $("#10_var").val();
         var value = $("#10_value").val();
         var ope = $("#10_ope").val();
         var if_true = $("#10_if_true").val();
         var if_false = $("#10_if_false").val();
         param = [variable, ope, value, if_true, if_false].join('::');
         // XXX vérification if_true...
         break;

      case 11: // Test selon date / heure
         var begin = $('#11_begin').val();
         var end = $('#11_end').val();
         var dow = $('#11_dow').val();
         var day = $('#11_day').val();
         var month = $('#11_month').val();
         var if_true = $('#11_if_true').val();
         var if_false = $('#11_if_false').val();
         param = [begin, end, dow, day, month, if_true, if_false].join('::');
         break;

      case 12: // Create context
         param = $("#12_name").val().replace(/\W/g, '_');
         if (param.length==0) {
            alert('Veuillez définir le nom du bloc à créer !');
            return;
         }
         for (s in scenario) {
            if (scenario[s].context==param) {
               alert('Nom de bloc déjà utilisé !');
               return;
            }
         }
         var s = new Object();
         s.context = param;
         s.extension = 's';
         s.priority = 0;
         s.application = 0;
         s.parameters = '';
         s.comments = $("#comments").val().replace(/::+/g, ':');
         scenario.push(s) // Add new context
         scenario.splice(current,1); // Remove empty line
         break;

      case 13: // Variable
         var name = $("#13_name").val(); // Variable can be eg. DB(lock/X{CHANNEL:-17:8}) .replace(/[^()\w]/g, '_');
         var value = $("#13_predefined").val();
         if (value==-1) {
            // XXX nettoyage valeur
            value = $("#13_value").val();
         }
         param = name + '::' + value;
         break;

      case 14: // Goto
         param = $("#14_goto").val();
         break;

      case 16: // Label
         param = $("#16_name").val();
         break;

      case 17: // Save to database
         param = $("#17_variable").val();
         break;

      case 18: // Holidays
         var if_true = $('#18_if_true').val();
         var if_false = $('#18_if_false').val();
         param = if_true + '::' + if_false;
         break;

      case 19: // Voicemail
         param = $('#19_mailbox').val() + '::' + $('#19_msg').val();
         break;

      case 20: // Queue
         param = $('#20_queuename').val();
         break;

      case 21: // QueueLog
         param = $("#21_queuename").val();
         param += '::' + $("#21_event").val();
         param += '::' + $("#21_info").val();
         param += '::' + $("#21_agent").val();
         break;

      case 22: // Open playback
         param = $("#22_file").val();
         break;

      case 23: // Conference
         param = $("#23_name").val();
         break;

      case 24: // AGI
         param = $("#24_script").val();
         break;

      case 25: // SayDigits
         param = $("#25_saydigits").val();
         break;

      case -1:
         alert('Veuillez choisir une action ! ');
         return;
         break;

      default:
         alert('Action inconnue : ' + type);
         return;
         break;
   }

   if (type!=12) { // Create context
      scenario[current].parameters = param;
      scenario[current].comments = $("#comments").val().replace(/::+/g, ':');
      scenario[current].application = type;
      scenario[current].context = scenario[current-1].context;
      scenario[current].extension = scenario[current-1].extension;
      scenario[current].priority = 1+scenario[current-1].priority;
   }
   display();
   $('#action_form').dialog('close');
   scenario.sort(sort_scenario);
}

function cancel_action() { 
   $('#action_form').dialog('close');
   if (add_or_edit=='add')
      // Remove empty scenario
      scenario.splice(current,1);
   display();
}

function display(redraw) {
   var context_re = RegExp('^xxx$');
   var context_opts = '<option value="-1"> - - - </option>';
   context_opts += '<optgroup label="Blocs">\n';
   var label_opts = '<optgroup label="étiquettes">\n';
   var blocs = {};

   for (let r=0; r<scenario.length; r++) {
      let step=scenario[r], context=step.context, parameters=step.parameters;
      if (!context_re.test(context)) {
         // Different bloc
         context_opts += '<option value="c:' + context + '">' + context + '</option>';
         context_re = RegExp(context + '_*$');

         if (! (context in blocs)) {
            blocs[context] = {};
            blocs[context]['prio'] = 0;
            blocs[context]['html'] = '<div id="context_' + context + '" title="' + context + '" class="bloc_title"><table><tbody><tr><th id="' + context + '" colspan="4" class="bloc_th">' + context + '</th>\n';
         }
      }

      blocs[context]['step'] = step;
      step.priority = blocs[context]['prio']++;
      row_style = (step.priority%2) ? 'class="odd"':'class="even"';
      blocs[context]['html'] += '<tr id="row_' + r + '" '+ row_style + '><td>';

      if (step.priority==0 && context=='Entrant') { // Incoming context -> delete forbidden !
         blocs[context]['html'] += ' <a href="#" onclick="add_action(0)"><img src="/images/add.png" border="0" title="Ajouter une action"></a>';
      } else {
         blocs[context]['html'] += ' <a href="#" onclick="add_action(' + r + ')"><img src="/images/add.png" border="0" title="Ajouter une action"></a>';
         blocs[context]['html'] += ' <a href="#" onclick="del_action(' + r + ')"><img src="/images/delete.png" border="0" title="Supprimer cette action"></a>';
         blocs[context]['html'] += ' <a href="#" onclick="edit_action(' + r + ')"><img src="/images/edit.png" border="0" title="Modifier cette action"></a>';
      }

      if (r>1 && scenario[r-1].context==context && scenario[r-1].application!='0')
         // Move action up
         blocs[context]['html'] += ' <a href="#" onclick="up_action(' + r + ')"><img src="/images/view-sort-ascending.png" border="0" title="Monter cette action"></a>';

      if (r>0 && r<scenario.length-1 && step.application!='0' && context==scenario[r+1].context)
         // Move action down
         blocs[context]['html'] += ' <a href="#" onclick="down_action(' + r + ')"><img src="/images/view-sort-descending.png" border="0" title="Descendre cette action"></a>';

      blocs[context]['html'] += '</td>';
      var app = parseInt(step.application);
      var act = actions_by_id[app];
      switch (app) {
         case 0: // NoOp
            par = '&nbsp;';
            break;

         case 1: // Playback
            par = play_or_tts_to_text(parameters);
            break;

         case 2: // Menu
            p = parameters.split('::');
            par  = play_or_tts_to_text(p[0]) + ', ';
            par += play_or_tts_to_text(p[1]) + ', ';
            par += play_or_tts_to_text(p[2]) + ', "' + p[3] + '"';
            break;

         case 15: // Select
            p = parameters.split('::');
            par  = play_or_tts_to_text(p[0]) + ', ';
            par += play_or_tts_to_text(p[1]) + ', ';
            par += play_or_tts_to_text(p[2]) + ', "' + p[3] + '"';
            par += ' -> ' + p[4];
            break;

         case 3: // Input
            p = parameters.split('::');
            par  = play_or_tts_to_text(p[0]) + ', ';
            par += play_or_tts_to_text(p[1]) + ', ';
            par += play_or_tts_to_text(p[2]) + ', ';
            par += p[3];
            switch (p[4]) {
               case 'fixed':
                  par += ', ' + p[5] + ' digits';
                  break;
               case 'pound':
                  par += ', terminé par #';
                  break;
               case 'star':
                  par += ', terminé par *';
                  break;
            }
            break;

         case 4: // Hangup
            par = '&nbsp;';
            break;

         case 5: // TTS
            par = '"' + parameters + '"';
            break;

         case 6: // Record
            p = parameters.split('::');
            par = '"' + play_or_tts_to_text(p[0]) + '", ' + p[1] + ' sec';
            if (p[2]=='true') par += ', bip';
            break;

         case 7: // Transfert
            var a = parameters.split('::');
            var number=a[0], timeout=a[1], noanswer=a[2], busy=a[3], error=a[4];
            if (noanswer==-2) noanswer = 'continuer';
            if (error==-2) error = 'continuer';
            if (busy==-2) busy = 'continuer';
            par = number + ' (' + timeout + ' sec): ' + noanswer + '; ' + busy + '; ' + error;
            break;

         case 8: // Web Service
            par = parameters.split('::');
            par = par[0] + ' -> ' + par[1];
            break;

         case 9: // Loop
            par = parameters.split('::');
            par =  par[1] + ' x ' + par[0].substr(2);
            break;

         case 10: // Test
            var a = parameters.split('::');
            var variable=a[0], ope=a[1], value=a[2], if_true=a[3], if_false=a[4];
            var ops = new Object();
            ops['eq'] = ' = ';
            ops['ne'] = ' # ';
            ops['lt'] = ' < ';
            ops['le'] = ' <= ';
            ops['gt'] = ' > ';
            ops['ge'] = ' >= ';
            if (if_true==-2) if_true = 'continuer';
            if (if_false==-2) if_false = 'continuer';
            par = variable + ops[ope] + value + ' ? ' + if_true + ', sinon ' + if_false;
            break;

         case 13: // Variable
            p = parameters.split('::');
            par = p[0] + ' = ';
            switch (p[1]) {
               case '__1__':
                  par += 'numéro appelant'; 
                  break;
               case '__2__':
                  par += "identifiant d'appel"; 
                  break;
               default:
                  par += p[1];
                  break;
            }
            break;

         case 14: // Goto
            act = actions_by_id[app];
            if (parameters.substr(0,1)=='a')
               if (parameters.substr(2) in applications) 
                  par = 'Appli: ' + applications[parameters.substr(2)].name;
               else
                  par = '';
            else
               par = parameters.substr(2);
            break;

         case 16: // Label
            act = actions_by_id[app];
            par = parameters;
            labels[context + ',' + par] = r;
            label_opts += '<option value="l:' + context + ',' + par + '">' + par + '</option>';
            break;

         case 17: // Save to database
            act = actions_by_id[app];
            par = parameters;
            break;

         case 18: // Holidays
            act = actions_by_id[app];
            var a = parameters.split('::');
            var if_true = a[0], if_false = a[1];
            if (if_true==-1 || if_false==1) {
               alert('Vérifiez les actions');
               return;
            }
            if (if_true==-2) if_true = 'Continuer';
            if (if_false==-2) if_false = 'Continuer';
            par = '? ' + if_true + ', sinon ' + if_false;
            break;

         case 19: // Voicemail
            act = actions_by_id[app];
            var a = parameters.split('::');
            par = a[0] + ' (' + ['aucun message', 'message indisponible', 'message occupé'][a[1]] + ')';
            break;

         case 20: // Queue
            act = actions_by_id[app];
            par = queues_by_id[parameters];
            break;

         case 21: // QueueLog
            act = actions_by_id[app];
            var a = parameters.split('::');
            par = queues_by_id[a[0]] + ': ' + qe_by_id[a[1]];
            if (a[2]) par += ': ' + a[2];
            break;

         case 22: // Open playback
            act = actions_by_id[app];
            par = parameters;
            break;

         case 23: // Conference
            act = actions_by_id[app];
            par = parameters;
            break;

         case 24: // AGI
            act = actions_by_id[app];
            par = parameters;
            break;

         case 25: // Say digits
            act = actions_by_id[app];
            par = parameters;
            break;

         case 11: // Time based test
            var a = parameters.split('::');
            var begin=a[0], end=a[1], dow=a[2], day=a[3], 
               month=a[4], if_true=a[5], if_false=a[6];
            par = '';
            if (begin) par += 'de ' + begin + ' à ' + end + ', ';
            if (dow) par += 'jour(s): ' + dow + ', ';
            if (day) par += 'date(s): ' + day + ', ';
            if (month) par += 'mois: ' + month;
            if (if_true==-2) if_true = 'Continuer';
            if (if_false==-2) if_false = 'Continuer';
            par += ' ? ' + if_true + ', sinon : ' + if_false;
            break;

         case 12: // New context
            par = '"' + parameters + '"';
            break;

         default:
            act = ' . . . ';
            par = '&nbsp;';
            break;
      }
      var par2=par;
      if (par2 && par2.length>20) par2 = par2.substr(0,17) + '...';
      blocs[context]['html'] += '<td style="padding: 5px">' + act + '</td>';
      blocs[context]['html'] += '<td style="padding: 5px" title="'+ par + '">' + par2 + '</td>';
      if (step.comments) {
         var comments = step.comments;
         if (comments.length>20) comments = comments.substr(0,17) + '...';
         blocs[context]['html'] += '<td style="padding: 5px" title="' + step.comments + '">' + comments + '</td>';
      } else
         blocs[context]['html'] += '<td style="padding: 5px">&nbsp;</td>';
      blocs[context]['html'] += '</tr>\n';
   }

   context_opts += '</optgroup>';
   $('#9_action').html(context_opts);
   context_opts += label_opts + '</optgroup>';
   let divs = '';
   for (let b in blocs)
      divs += blocs[b]['html'] + '</tbody></table></div>\n';
   $("#scenario").html(divs);
   let goto_opts = context_opts + '<optgroup label="Application">';
   for (let a in applications)
      goto_opts += '<option value="a:' + a + '">' +
                                         applications[a].name + ' (' +
                                         applications[a].comment + 
                   ')</option>';
   goto_opts += '</optgroup>';
   $('#14_goto').html(goto_opts);
   context_opts += '<optgroup label="Autre">\n';
   context_opts += '<option value="-2">Continuer</option></optgroup>';
   $('#11_if_false').html(context_opts);
   $('#11_if_true').html(context_opts);
   $('#7_noanswer').html(context_opts);
   $('#7_busy').html(context_opts);
   $('#7_error').html(context_opts);
   $('#10_if_false').html(context_opts);
   $('#10_if_true').html(context_opts);
   $('#18_if_false').html(context_opts);
   $('#18_if_true').html(context_opts);

   // HTML divs are updated, now compute positions
   var context = '';
   var pos, top=0, left=0; 
   for (r=0; r<scenario.length; r++) {
      // Look for first bloc (incoming): defines origin of drawing
      context = scenario[r].context.replace(/([*#])$/g,'\\$1');
      if (context=='Entrant') { // Origin
         pos = $('#context_' + context).position();
         left = pos.left;
         top = pos.top + $('#context_' + context).height() +5;
         break;
      } 
   }
   context = '';
   for (r=0; r<scenario.length; r++) {
      if (context==scenario[r].context) continue;
      context = scenario[r].context.replace(/([*#])$/g,'\\$1');
      // Make div draggable
      $('#context_' + context).draggable({
         handle: 'th',
         opacity: 0.35,
         containment: [50, 150, 2000, 4000],
         stack: {group: '#scenario div', min: 10},
         drag: function(event,ui){
            update_canvas();
         },
         stop: function(event,ui){
            contexts_pos[this.id] = $(this).position();
            update_canvas();
         }
      });
      // Automatic positionning !
      if (context!='Entrant') {
         $('#context_' + context).css('left',
               left + context.replace(/[^_]/g,'').length * 40);
         $('#context_' + context).css('top', top);
         top += $('#context_' + context).height() + 5;
      }
      if (!redraw && contexts_pos['context_'+context]) { // Manually positionned by dragging
         $('#context_' + context).css('left', contexts_pos['context_'+context].left);
         $('#context_' + context).css('top', contexts_pos['context_'+context].top);
         continue;
      }
      contexts_pos['context_'+context] = $('#context_' + context).position();
   }
   $("#scenario").height(top);
   update_canvas();
}

function edit_action(i) {
   add_or_edit = 'edit';
   current = i;
   var app = parseInt(scenario[i].application);
   var act = actions_by_id[app];
   switch (app) {

      case 1:
         $("#1_file").val(scenario[i].parameters);
         break;

      case 2: // Menu
         var a = scenario[i].parameters.split('::');
         $("#3_announce").val(a[0]);
         $("#3_error").val(a[1]);
         $("#3_abandon").val(a[2]);
         $("#3_choice").val(a[3]);
         break;

      case 3: // Input
         var a = scenario[i].parameters.split('::');
         $("#4_announce").val(a[0]);
         $("#4_error").val(a[1]);
         $("#4_abandon").val(a[2]);
         $("#4_var").val(a[3]);
         $("input[@name='4_input_type']:checked").val(a[4]);
         $("#4_len").val(a[5]);
         break;

      case 4: // Hangup
         break;

      case 5: // TTS
         $("#2_tts").val(scenario[i].parameters);
         break;

      case 6: // Record
         var a = scenario[i].parameters.split('::');
         $("#6_announce").val(a[0]);
         $('#6_duration').val(a[1]);
         $("input[@name='6_bip']:checked").val(a[2]);
         break;

      case 7: // Transfer
         var a = scenario[i].parameters.split('::');
         $("#7_number").val(a[0]);
         $("#7_timeout").val(a[1]);
         $("#7_noanswer").val(a[2]);
         $("#7_busy").val(a[3]);
         $("#7_error").val(a[4]);
         break;

      case 8: // Service Web
         var a = scenario[i].parameters.split('::');
         $("#8_request").val(a[0]);
         $("#8_var").val(a[1]);
         break;

      case 9: // Boucle
         var a = scenario[i].parameters.split('::');
         $("#9_action").val(a[0]);
         $('#9_loop').val(a[1]);
         break;

      case 10: // Test
         var a = scenario[i].parameters.split('::');
         $("#10_var").val(a[0]);
         $("#10_value").val(a[2]);
         $("#10_ope").val(a[1]);
         $("#10_if_true").val(a[3]);
         $("#10_if_false").val(a[4]);
         break;

      case 11: // Time based test
         var a = scenario[i].parameters.split('::');
         $('#11_begin').val(a[0]);
         $('#11_end').val(a[1]);
         $('#11_dow').val(a[2].split(','));
         $('#11_day').val(a[3].split(','));
         $('#11_month').val(a[4].split(','));
         $('#11_if_true').val(a[5]);
         $('#11_if_false').val(a[6]);
         break;

      case 12: // Bloc
         break;

      case 13: // Variable
         var a = scenario[i].parameters.split('::');
         $("#13_name").val(a[0]);
         if (a[1]=='__1__' || a[1]=='__2__') {
            $("#13_predefined").val(a[1]);
            $("#13_value").val('');
         } else {
            $("#13_predefined").val(-1);
            $("#13_value").val(a[1]);
         }
         break;

      case 14: // Goto
         $("#14_goto").val(scenario[i].parameters);
         break;

      case 15: // Select
         var a = scenario[i].parameters.split('::');
         $("#15_announce").val(a[0]);
         $("#15_error").val(a[1]);
         $("#15_abandon").val(a[2]);
         $("#15_choice").val(a[3]);
         $("#15_var").val(a[4]);
         break;

      case 16: // Label
         $("#16_name").val(scenario[i].parameters);
         break;

      case 17: // Save to database
        $("#17_variable").val(scenario[i].parameters);
         break;

      case 18: // Holidays
         var a = scenario[i].parameters.split('::');
         $('#18_if_true').val(a[0]);
         $('#18_if_false').val(a[1]);
         break;

      case 19: // Voicemail
         var a = scenario[i].parameters.split('::');
         $("#19_mailbox").val(a[0]);
         $("#19_msg").val(a[1]);
         break;

      case 20: //Queue
         $("#20_queuename").val(scenario[i].parameters);
         break;

      case 21: //QueueLog
         var a = scenario[i].parameters.split('::');
         $("#21_queuename").val(a[0]);
         $("#21_event").val(a[1]);
         $("#21_info").val(a[2]);
         $("#21_agent").val(a[3]);
         break;

      case 22: // Open playback
         $("#22_message").val(scenario[i].parameters);
         break;

   }
   $("#comments").val(scenario[i].comments);
   $("#type_action").val(app);
   action_parameters();
   $('#action_form').dialog('open');
   unload_warning=1;
}

function add_action(i) {
   add_or_edit = 'add';
   scenario.splice(i+1,0,new Object);
   scenario[i+1].context = scenario[i].context;
   scenario[i+1].extension = '';
   scenario[i+1].priority = '';
   scenario[i+1].application = -1;
   scenario[i+1].parameters = '';
   scenario[i+1].comments = '';
   scenario[i+1].target = 0;
   current = i+1;
   display(false);
   $("#type_action")[0].selectedIndex=0;
   $("#comments").val('');
   for (i=1; i<$("#type_action")[0].options.length; i++)
      $("#action_params_" + i).hide();
   $('#action_form').dialog('open');
   unload_warning=1;
}

function action_parameters() {
   for (i=1; i<$("#type_action")[0].options.length; i++)
      $("#action_params_" + i).hide();
   $("#action_params_" + $("#type_action").val()).show();
}

function up_action(i) {
   var s=scenario[i];
   scenario.splice(i-1,0,s);
   scenario.splice(i+1,1);
   display(false);
   unload_warning=1;
}

function down_action(i) {
   var s=scenario[i];
   scenario.splice(i,1);
   scenario.splice(i+1,0,s);
   display(false);
   unload_warning=1;
}

function del_action(i) {
   if (!confirm("Supprimer cette action ?")) return
   scenario.splice(i,1);
   display(false);
   unload_warning=1;
}

function submit() {
   // Convert array of objects to array of arrays 
   var sce = new Array();
   for (i in scenario)
      sce.push([scenario[i].comments, 
            scenario[i].context, 
            scenario[i].extension, 
            scenario[i].priority, 
            scenario[i].application, 
            scenario[i].parameters].join('::'));

   var positions = new Array();
   for (i in contexts_pos)
      positions.push([i, 
            contexts_pos[i]['top'], 
            contexts_pos[i]['left']].join('::'))

   $.post(
      'save_scenario',
      {'id': ${tmpl_context.app_id}, 'scenario': sce, 'positions': positions},
      function(data,status){
         if (status=='success') {
            if (data.result==0)
               alert('Sauvegarde effectuée ;\nnouveau scénario activé.');
            else
               alert('Sauvegarde:\nERREUR ' + data.result);
         } else {
            alert('Sauvegarde:\nERREUR requête ' + status);
         }
         unload_warning=0;
      },
      'json'
   );
   return true;
}

function pdf_export() {
   with (document.pdf_export_form) {
      id.value = ${tmpl_context.app_id};
      submit();
   }
}

function canvas_join(c2d, offset, src, tgt) {

   src.offset = src.offset();
   if (!src.offset) return;
   tgt.offset = tgt.offset();
   if (!tgt.offset) return;

   // Random color 
   var r = parseInt(200*Math.random());
   var g = parseInt(200*Math.random());
   var b = parseInt(200*Math.random());
   c2d.fillStyle = c2d.strokeStyle = 'rgb('+r+','+g+','+b+')';

   // Line begin: on left or right side of table ?
   if (src.offset.left+src.width()>=tgt.offset.left) {
      var src_left = src.offset.left-offset.left;
      var src_top = src.offset.top-offset.top;
      var src_corner = src_left-25;
   } else {
      var src_left = src.offset.left+src.width()-offset.left;
      var src_top = src.offset.top-offset.top;
      var src_corner = src_left+25;
   }

   // Line end: on left or right side of table ?
   if (tgt.offset.left+tgt.width()>=src.offset.left) {
      var tgt_left = tgt.offset.left-offset.left-4;
      var tgt_top = tgt.offset.top-offset.top;
      var tgt_arrow = tgt_left-8;
      var tgt_corner = tgt_left-15;
   } else {
      var tgt_left = tgt.offset.left+tgt.width()-offset.left+8;
      var tgt_top = tgt.offset.top-offset.top;
      var tgt_arrow = tgt_left+8;
      var tgt_corner = tgt_left+15;
   }

   /* Link = 3 segments :      -- src 
                               \
                                `-> tgt */
   c2d.beginPath();
   c2d.moveTo(src_left, src_top+10);
   c2d.lineTo(src_corner, src_top+10);
   c2d.lineTo(tgt_corner, tgt_top+10);
   c2d.lineTo(tgt_left, tgt_top+10);
   c2d.stroke();
   c2d.closePath();

   // Arrow at target
   c2d.beginPath();
   c2d.lineTo(tgt_arrow, tgt_top+14);
   c2d.lineTo(tgt_arrow, tgt_top+6);
   c2d.lineTo(tgt_left, tgt_top+10);
   c2d.fill();
   c2d.closePath();
}

function update_canvas() {
   var canvas = $('#canvas')[0];
   canvas.width = $('#canvas').width();
   canvas.height = $('#canvas').height();
   var offset = $('#canvas').offset();
   var c2d = canvas.getContext("2d");
   c2d.clearRect(0, 0, canvas.width, canvas.height);

   for (r=0; r<scenario.length; r++) { // Search for branches
      switch (parseInt(scenario[r].application)) {

         case 2: // Menu
            var a = scenario[r].parameters.split('::');
            var ctxt = scenario[r].context + '_Menu_';
            var choices = a[3].split('');
            for (i=0; i<choices.length; i++) {
               canvas_join(c2d, $('#canvas').offset(),
                  $('#row_' + r), $('#'+ctxt+choices[i].replace(/([*#])$/g,'\\$1')) );
            }
            break;

         case 10: // Test
            var a = scenario[r].parameters.split('::');
            var if_true = a[3], if_false = a[4];
            switch (if_true.substr(0,1)) {
               case '-': break;
               case 'c':
                  canvas_join(c2d, $('#canvas').offset(), $('#row_' + r),
                        $('#'+if_true.substr(2)) );
                  break;
               case 'l':
                  canvas_join(c2d, $('#canvas').offset(), $('#row_' + r),
                        $('#row_'+labels[if_true.substr(2)]) );
                  break;
               default:
                  alert('update_canvas: unknown Test (true) ' + if_true);
                  break;
            }

            switch (if_false.substr(0,1)) {
               case '-': break;
               case 'c':
                  canvas_join(c2d, $('#canvas').offset(), $('#row_' + r),
                        $('#'+if_false.substr(2)) );
                  break;
               case 'l':
                  canvas_join(c2d, $('#canvas').offset(), $('#row_' + r),
                        $('#row_'+labels[if_false.substr(2)]) );
                  break;
               default:
                  alert('update_canvas: unknown Test (false) ' + if_false);
                  break;
            }
            break;

         case 9: // Loop
            var a = scenario[r].parameters.split('::');
            canvas_join(c2d, $('#canvas').offset(), $('#row_' + r),
                  $('#'+a[0].substr(2)) );
            break;

         case 11: // Time based test
            var a = scenario[r].parameters.split('::');
            var if_true=a[5], if_false=a[6];
            if (if_true!=-2 && if_true!=-1) {
               let what = if_true.substr(0, 1);
               let target = (what=='l') ? 'row_' + labels[if_true.substr(2)] : if_true.substr(2);
               canvas_join(c2d, $('#canvas').offset(), $('#row_' + r), $('#' + target));
            }
            if (if_false!=-2 && if_false!=-1) {
               let what = if_false.substr(0, 1);
               let target = (what=='l') ? 'row_' + labels[if_false.substr(2)] : if_false.substr(2);
               canvas_join(c2d, $('#canvas').offset(), $('#row_' + r), $('#' + target));
            }
            break;

         case 7: // Transfer
               var a = scenario[r].parameters.split('::');
               var number=a[0], timeout=a[1], noanswer=a[2], busy=a[3], error=a[4];
               if (noanswer!='-2') {
                  canvas_join(c2d, $('#canvas').offset(), $('#row_' + r),
                              $('#'+ noanswer.substr(2)) );
               }
               if (error!='-2') {
                  canvas_join(c2d, $('#canvas').offset(), $('#row_' + r),
                              $('#' + error.substr(2)) );
               }
               if (busy!='-2') {
                  canvas_join(c2d, $('#canvas').offset(), $('#row_' + r),
                              $('#' + busy.substr(2)) );
               }
            break;

         case 14: // Goto
            switch (scenario[r].parameters.substr(0,1)) {
               case 'a':
                  // Goto application: nothing to show!
                  break;
               case 'c':
                  canvas_join(c2d, $('#canvas').offset(), $('#row_' + r),
                        $('#'+scenario[r].parameters.substr(2)) );
                  break;
               case 'l':
                  target = labels[scenario[r].parameters.substr(2)];
                  canvas_join(c2d, $('#canvas').offset(), $('#row_' + r),
                        $('#row_'+target) );
                  break;
               default:
                  alert('update_canvas: unknown Goto ' + scenario[r].parameters);
                  break;
            }
            break;

         case 18: // Holidays
            var a = scenario[r].parameters.split('::');
            var if_true=a[0], if_false=a[1];
            if (if_true!=-2)
               canvas_join(c2d, $('#canvas').offset(), $('#row_' + r), 
                     $('#'+if_true.substr(2)) );
            if (if_false!=-2)
               canvas_join(c2d, $('#canvas').offset(), $('#row_' + r), 
                     $('#'+if_false.substr(2)) );
            break;

      }
   }
}

function sort_scenario(a, b) {
   /* Sort scenario by context / exten / priority. Needed to check 
	if step is first or last in context, to allow move yup / down */
      if (a.context < b.context) return -1;
      if (a.context > b.context) return 1;
      if (a.extension < b.extension) return -1;
      if (a.extension > b.extension) return 1;
      return a.priority - b.priority;
}

//]]>
   </script>
</head>

<body>
      <h1>${title}</h1>
      N'oubliez pas de
      <span style="font-weight: bold;"><a href="#" onclick="submit();">valider</a></span> 
      après modification du scénario. 
      <a href="#" onclick="display(true)">Redessiner</a> l'écran. 
      <a href="#" onclick="pdf_export()">Exporter</a> au format PDF. 
      <br/>
      <canvas id="canvas"></canvas>
      <div id="scenario"></div>

<!-- Dialogue nouvelle action -->
<div id="action_form" title="Nouvelle action">
      Action:
   <select id="type_action" onchange="action_parameters()">
   </select>

   <!-- Playback: 1 -->
   <div id="action_params_1" style="display: none">
      Sélectionnez le fichier à jouer:
      <select id="1_file">
      </select>
   </div>

   <!-- Menu: 2 -->
   <div id="action_params_2" style="display: none">
      <table>
         <tr><td>Message annonce:</td>
            <td><select id="3_announce"></select></td></tr>
         <tr><td>Message d'erreur</td>
            <td><select id="3_error"></select></td></tr>
         <tr><td>3 erreurs (continuer ou message puis raccrocher):</td>
            <td><select id="3_abandon"></select></td></tr>
         <tr><td>Entrez les choix autorisés:</td>
            <td><input type="text" id="3_choice"/></td></tr>
      </table>
   </div>

   <!-- Select: 15 -->
   <div id="action_params_15" style="display: none">
      <table>
         <tr><td>Message annonce:</td>
            <td><select id="15_announce"></select></td></tr>
         <tr><td>Message d'erreur</td>
            <td><select id="15_error"></select></td></tr>
         <tr><td>Message d'abandon:</td>
            <td><select id="15_abandon"></select></td></tr>
         <tr><td>Entrez les choix autorisés:</td>
            <td><input type="text" id="15_choice"/></td></tr>
         <tr><td>Nom de la variable:</td>
            <td><input type="text" id="15_var"/></td></tr>
      </table>
   </div>

   <!-- Input: 3 -->
   <div id="action_params_3" style="display: none">
      <table>
         <tr><td>Message annonce:</td>
            <td><select id="4_announce"></select></td></tr>
         <tr><td>Message d'erreur</td>
            <td><select id="4_error"></select></td></tr>
         <tr><td>Message d'abandon:</td>
            <td><select id="4_abandon"></select></td></tr>
         <tr><td>Type de saisie:</td>
            <td><input type="radio" name="4_input_type" value="fixed"/> longueur fixe = 
               <input type="text" id="4_len" size="4" maxlength="2"/></td></tr>
         <tr><td>&nbsp;</td>
            <td><input type="radio" name="4_input_type" value="star"/> terminé par *</td></tr>
         <tr><td>&nbsp;</td>
            <td><input type="radio" name="4_input_type" value="pound"/> terminé par #</td></tr>
         <tr><td>Nom de la variable:</td>
            <td><input type="text" id="4_var"/></td></tr>
      </table>
   </div>

   <!-- Hangup: 4 -->
   <div id="action_params_4" style="display: none">
      <i>Aucun paramètre</i>
   </div>

   <!-- Text to speech: 5 -->
   <div id="action_params_5" style="display: none">
      <table>
         <tr><td>Entrez le texte:</td>
            <td><input type="text" id="2_tts"/></td></tr>
         <!-- tr><td>Langue:</td>
            <td><input type="radio" name="2_language" value="true" checked="checked"/>Oui</td></tr>
         <tr><td>&nbsp;</td>
            <td><input type="radio" name="2_language" value=""/>Non</td></tr -->
      </table>
   </div>

   <!-- Record: 6 -->
   <div id="action_params_6" style="display: none">
      <table>
         <tr><td>Message annonce:</td>
            <td><select id="6_announce"></select></td></tr>
         <tr><td>Durée maximale (secondes):</td>
            <td><input type="text" id="6_duration"/></td></tr>
         <tr><td>Jouer bip</td>
            <td><input type="radio" name="6_bip" value="true" checked="checked"/>Oui</td></tr>
         <tr><td>&nbsp;</td>
            <td><input type="radio" name="6_bip" value="false"/>Non</td></tr>
      </table>
   </div>

   <!-- Transfer: 7 -->
   <div id="action_params_7" style="display: none">
      <table>
         <tr><td>Numéro appelé:</td>
            <td><input type="text" id="7_number"/></td></tr>
         <tr><td>Durée sonnerie:</td>
            <td><input type="text" id="7_timeout" size="3"/> sec</td></tr>
         <tr><td>Action sur non réponse:</td>
            <td><select id="7_noanswer"></select></td></tr>
         <tr><td>Action sur occupation:</td>
            <td><select id="7_busy"></select></td></tr>
         <tr><td>Action sur erreur:</td>
            <td><select id="7_error"></select></td></tr>
      </table>
   </div>

   <!-- Web service: 8 -->
   <div id="action_params_8" style="display: none">
      <table>
         <tr><td>Requête HTTP:</td>
            <td><input type="text" id="8_request"/></td></tr>
         <tr><td>Nom variable résultat:</td>
            <td><input type="text" id="8_var"/></td></tr>
      </table>
   </div>

   <!-- Loop: 9 -->
   <div id="action_params_9" style="display: none">
      <table>
         <tr><td>Action à répéter:</td>
            <td><select id="9_action"></select></td></tr>
         <tr><td>Nombre de boucles:</td>
            <td><input type="text" id="9_loop"/></td></tr>

      </table>
   </div>

   <!-- Test variable: 10 -->
   <div id="action_params_10" style="display: none">
      <table>
         <tr><td>Nom variable:</td>
            <td><input type="text" id="10_var"/></td></tr>
         <tr><td>Test:</td>
            <td><select id="10_ope">
                  <option value="eq">=</option>
                  <option value="ne">#</option>
                  <option value="le">&le;</option>
                  <option value="lt">&lt;</option>
                  <option value="ge">&ge;</option>
                  <option value="gt">&gt;</option>
         </select></td></tr>
         <tr><td>Valeur:</td>
            <td><input type="text" id="10_value"/></td></tr>
         <tr><td>Si vrai:</td>
            <td><select id="10_if_true"></select></td></tr>
         <tr><td>Si faux:</td>
            <td><select id="10_if_false"></select></td></tr>
      </table>
   </div>

   <!-- Date / time based test: 11 -->
   <div id="action_params_11" style="display: none">
      <table>
         <tr><td>Plage horaire:</td>
            <td>de <input type="text" id="11_begin" size="6"/> à 
               <input type="text" id="11_end" size="6"/></td></tr>
         <tr><td>Jour de la semaine:</td>
            <td><select id="11_dow" multiple="multiple" size="4">
                  <option value="mon">Lundi</option>
                  <option value="tue">Mardi</option>
                  <option value="wed">Mercredi</option>
                  <option value="thu">Jeudi</option>
                  <option value="fri">Vendredi</option>
                  <option value="sat">Samedi</option>
                  <option value="sun">Dimanche</option>
                  </select></td></tr>
         <tr><td>Jour du mois:</td>
            <td><select id="11_day" multiple="multiple" size="4">
                  <option value="1">1</option>
                  <option value="2">2</option>
                  <option value="3">3</option>
                  <option value="4">4</option>
                  <option value="5">5</option>
                  <option value="6">6</option>
                  <option value="7">7</option>
                  <option value="8">8</option>
                  <option value="9">9</option>
                  <option value="10">10</option>
                  <option value="11">11</option>
                  <option value="12">12</option>
                  <option value="13">13</option>
                  <option value="14">14</option>
                  <option value="15">15</option>
                  <option value="16">16</option>
                  <option value="17">17</option>
                  <option value="18">18</option>
                  <option value="19">19</option>
                  <option value="20">20</option>
                  <option value="21">21</option>
                  <option value="22">22</option>
                  <option value="23">23</option>
                  <option value="24">24</option>
                  <option value="25">25</option>
                  <option value="26">26</option>
                  <option value="27">27</option>
                  <option value="28">28</option>
                  <option value="29">29</option>
                  <option value="30">30</option>
                  <option value="31">31</option>
                  </select></td></tr>
         <tr><td>Mois:</td>
            <td><select id="11_month" multiple="multiple" size="4">
                  <option value="jan">Janvier</option>
                  <option value="feb">Février</option>
                  <option value="mar">Mars</option>
                  <option value="apr">Avril</option>
                  <option value="may">Mai</option>
                  <option value="jun">Juin</option>
                  <option value="jul">Juillet</option>
                  <option value="aug">Août</option>
                  <option value="sep">Septembre</option>
                  <option value="oct">Octobre</option>
                  <option value="nov">Novembre</option>
                  <option value="dec">Décembre</option>
                  </select></td></tr>
         <tr><td>Si vrai:</td>
            <td><select id="11_if_true"></select></td></tr>
         <tr><td>Si faux:</td>
            <td><select id="11_if_false"></select></td></tr>
      </table>
   </div>

   <!-- Bloc: 12 -->
   <div id="action_params_12" style="display: none">
      Nom du bloc: <input type="text" id="12_name"/>
   </div>

   <!-- Variable: 13 -->
   <div id="action_params_13" style="display: none">
      <table>
         <tr><td>Nom de la variable:</td>
            <td><input type="text" id="13_name"/></td></tr>
         <tr><td>Valeur prédéfinie:</td>
            <td><select id="13_predefined">
                  <option value="-1"> - - - </option>
                  <option value="__1__">Numéro téléphone appelant</option>
                  <option value="__2__">Identifiant d'appel</option>
                  </select></td></tr>
         <tr><td>Valeur libre:</td>
            <td><input type="text" id="13_value"/></td></tr>
      </table>
   </div>

   <!-- Goto: 14 -->
   <div id="action_params_14" style="display: none">
      Saut vers:
      <select id="14_goto"></select>
   </div>

   <!-- Label: 16 -->
   <div id="action_params_16" style="display: none">
      Nom de l'étiquette:
      <input type="text" id="16_name"/>
   </div>

   <!-- Save variable / value to database: 17 -->
   <div id="action_params_17" style="display: none">
      Nom de la variable à sauvegarder:
      <input type="text" id="17_variable"/>
   </div>

   <!-- Holidays: 18 -->
   <div id="action_params_18" style="display: none">
      <table>
         <tr><td>Si vrai:</td>
            <td><select id="18_if_true"></select></td></tr>
         <tr><td>Si faux:</td>
            <td><select id="18_if_false"></select></td></tr>
      </table>
   </div>

   <!-- Voicemail: 19 -->
   <div id="action_params_19" style="display: none">
      <table>
         <tr><td>Nom de la boîte vocale:</td>
            <td><input type="text" id="19_mailbox"/></td></tr>
         <tr><td>Message d'accueil:</td>
           <td><select id="19_msg">
                  <option value="0">Aucun</option>
                  <option value="1">Indisponible</option>
                  <option value="2">Occupé</option>
               </select></td></tr>
      </table>
   </div>

   <!-- Queue: 20 -->
   <div id="action_params_20" style="display: none">
      Nom du groupe d'appel:
      <select id="20_queuename"></select>
   </div>

   <!-- QueueLog: 21 -->
   <div id="action_params_21" style="display: none">
      <table>
         <tr><td>Nom du groupe d'appel:</td>
            <td><select id="21_queuename"></select></td></tr>
         <tr><td>Agent:</td>
            <td><input type="text" id="21_agent"/></td></tr>
         <tr><td>Evénement:</td>
            <td><select id="21_event"></select></td></tr>
         <tr><td>Information:</td>
            <td><input type="text" id="21_info"/></td></tr>
      </table>
   </div>

   <!-- Open playback: 22 -->
   <div id="action_params_22" style="display: none">
      Entrez le fichier à jouer:
      <input type="text" id="22_file"/>
   </div>

   <!-- Conference: 23 -->
   <div id="action_params_23" style="display: none">
      Entrez le nom de la salle de conférence:
      <input type="text" id="23_name"/>
   </div>

   <!-- AGI: 24 -->
   <div id="action_params_24" style="display: none">
      Entrez le nom du programme à exécuter
      <input type="text" id="24_script"/>
   </div>

   <!-- SayDigits: 25 -->
   <div id="action_params_25" style="display: none">
      Entrez les chiffres à énoncer
      <input type="text" id="25_saydigits"/>
   </div>

   <div>
      Commentaire: <input type="text" name="comments" id="comments"/>
   </div>
</div>
<form name="pdf_export_form" action="pdf_export" method="post">
   <input type="hidden" name="id"/>
</form>
</body>
</html>
