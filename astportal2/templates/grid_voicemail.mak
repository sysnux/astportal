<%inherit file="local:templates.master"/>

   <script type="text/javascript">
//<![CDATA[
      
$(document).ready(function() {
   $(window).bind('resize', function() {
      $('#grid').setGridWidth($('#data').width()-10, true);
   });

   // Move to dialog
   $('#move_dialog').dialog({ 
      autoOpen: false,  modal: true, width: '450px',
      buttons: { "Valider": function() {valid_move()}, 
      "Annuler": function() {$('#move_dialog').dialog('close');}} });

});

function change_folder() {
   $('#folder_form').attr('action', '/voicemail/index');
   $('#folder_form').submit();
}

function del(mb, xid, msg) {
   if (confirm(msg)) {
      $('#folder_form_mb').val(mb);
      $('#folder_form_id').val(xid);
      $('#folder_form').attr('action', 'delete');
      $('#folder_form').submit();
   }
}

function listen(mb, id, act) {
   $('#folder_form_mb').val(mb);
   $('#folder_form_id').val(id);
   $('#folder_form').attr('action', act);
   $('#folder_form').submit();
}

var move_mb = move_id = move_from = move_to = null;
function move(mb,id) {
   move_mb = mb;
   move_id = id;
   move_from = $('#folder_form_folder').val();
   // Fill move_to select
   $.post(
      'fetch_folders',
      {folder: move_from},
      function(data,stat) {
         folders = data.folders;
         var o = '<option value="-1"> - - - </option>\n';
         for (f in folders) {
            o += '<option value="' + f + '">'; 
            o += folders[f] + '</option>\n';
         }
         $('#move_select').html(o);
         $('#move_dialog').dialog('open');
      },
      'json'
   );
}

function valid_move() {
   move_to = $('#move_select').val();
   $('#move_dialog').dialog('close');
   $('#folder_form_mb').val(move_mb);
   $('#folder_form_id').val(move_id);
   $('#folder_form_to').val(move_to);
   $('#folder_form').attr('action', 'move');
   $('#folder_form').submit();
}

//]]>
   </script>


   <h1>${title}</h1>
% if debug:
                ${debug}<br>
% endif

      <!-- Select folder / delete message form -->
% if tmpl_context.form:
         ${tmpl_context.form(values) | n}
% endif

      <div id="data">
         <!-- JQuery Grid -->
         ${tmpl_context.grid() | n}
      </div>

      <!-- Custom messages -->
      <br/>
% if tmpl_context.form2:
         ${tmpl_context.form2(values2) | n}
% endif

      <!-- Move to dialog -->
      <div id="move_dialog" style="display: none">
         Déplacer vers :
         <select id="move_select"></select>
      </div>

