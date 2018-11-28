<%inherit file="local:templates.master"/>

   <style>
.l_center {
   overflow: hidden;
   text-align: center;
   margin-left: auto;
   margin-right: auto;
   width: 220px;
   margin-top: 10px;
}
.l_left {
   float: left;
   width: 150px;
}
.l_right {
   float: right;
   width: 150px;
   text-align: right;
}
   </style>

   <script type="text/javascript">
//<![CDATA[
      
var unload_warning=false;
window.onbeforeunload = function () {
   if (unload_warning)
      return 'Modifications non enregistrées';
}

$(document).ready(function() {
   $(window).bind('resize', function() {
      $('#grid').setGridWidth($('#data').width()-10, true);
   });
   $('#form0_begin\\.container').hide();
   $('#form0_duration\\.container').hide();
   $('#form0_alarm_type\\.container').hide();
   $('#form0_alarm_dest\\.container').hide();
});

function load_complete(data) {
   if (data.rows.length>0) {
      $("#data").show();
      $('#grid').setGridWidth($('#data').width()-10, true);
   }
}

function postdata(to,p) {
  var f = document.createElement('form');
  f.method = "post";
  f.action = to;
  for (var k in p) {
    var i = document.createElement('input') ;
    i.setAttribute('type', 'hidden') ;
    i.setAttribute('name', k) ;
    i.setAttribute('value', p[k]);
    f.appendChild(i) ;
  }
  document.body.appendChild(f) ;
  f.submit() ;
}

function originate(num, cust, id) {
   unload_warning = true;
   $('#other').hide();
   $('#span_form').show('slow');
   // Make phone numbers not clickable (replace link by text)
   $('#phone1').html( $('#phone1 a').text() );
   $('#phone2').html( $('#phone2 a').text() );
   $('#phone3').html( $('#phone3 a').text() );
   $('#form0_phone').val(num);
   $.post(
      '${tg.url('originate')}',
      {'exten': num, 'cust': cust},
      function (data) {$('#form0_out_id').val(data.status);}
   );
   // $(document).ajaxError(data_fetch_failed);
}

function crm(url) {
   wincrm = window.open(url, 'CRM', 'location=no,width=600,height=400');
}

function result_change() { 
   // Called on "select result" change
   var sel = $("#form0_result").val();
   if (sel==0) {
      $('#form0_begin\\.container').show();
      $('#form0_duration\\.container').show();
      $('#form0_alarm_type\\.container').show();
   } else {
      $('#form0_begin\\.container').hide();
      $('#form0_duration\\.container').hide();
      $('#form0_alarm_type\\.container').hide();
      $('#form0_alarm_dest\\.container').hide();
   }
}

function alarm_change() { 
   // Called on "select alarm" change
   switch (parseInt($("#form0_alarm_type").val())) {
      case -1:
      case 0:
         $('#form0_alarm_dest\\.container').hide();
         break;
      case 1:
         $('#form0_alarm_dest\\.container').show();
         $('#form0_alarm_dest\\.container').val($('#email').text());
         break;
      case 2:
         $('#form0_alarm_dest\\.container').show();
         $('#form0_alarm_dest\\.container').val(
            $('#gsm1').text() || $('#gsm2').text());
         break;
   }
}

function my_submit() {
   var sel = $("#form0_result").val();
   if (sel==-1) {
      alert('Veuillez sélectionner un résultat');
      return;
   }
   if (sel==0) { // Prise RDV
      if ($("#form0_begin").val()=='' || $("#form0_duration").val()==-1) {
         alert('Pour un RDV, vous devez définir son heure de début et sa durée');
         return;
      }
      if ($("#form0_alarm_type").val()==-1) { // Choix type rappel
         alert('Pour un RDV, vous devez choisir un type de rappel');
         return;
      } else if ($("#form0_alarm_type").val()==1 && $("#form0_alarm_dest").val()=='') {
         alert('Vous devez définir l\'adresse pour le rappel par email.');
         return;
      } else if ($("#form0_alarm_type").val()==2 && $("#form0_alarm_dest").val()=='') {
         alert('Vous devez définir le numéro GSM pour le rappel par SMS.');
         return;
      }
   }
   unload_warning = false;
   $('#form0').submit();
}

//]]>
   </script>
</head>

<body>
   <h1>${title}</h1>

      
   <table>
      <tr>
         <th style="padding: 3px 10px;">Nom client</th>
         <th style="padding: 3px 10px;">Position client</th>
         <th style="padding: 3px 10px;">Solde total</th>
      </tr>
      <tr>
         <td>${client_name}</td>
         <td>${client_position}</td>
         <td>${total_amount}</td>
      </tr>
      <tr><td colspan="5">&nbsp;</td></tr>
      <tr rowspan="2"><th colspan="5">Téléphones</th></tr>
      <tr>
         <td id="phone1"><a href="#" title="Appeler"
            ${ph1_click | n}>${phone1 | n}</a>
            </td>
         <td id="phone2"><a href="#" title="Appeler"
            ${ph2_click | n}>${phone2 | n}</a>
            </td>
         <td id="phone3"><a href="#" title="Appeler"
            ${ph3_click | n}>${phone3 | n}</a>
            </td>
      </tr>
   </table>

   <div id="data" py:if="tmpl_context.grid" style="display: none">
      <!-- JQgrid -->
      ${tmpl_context.grid() | n}
   </div>

   <div id="other">
      <div class="l_left">
      <a href="#" ${prev_cust | n}>&lt; Client précédent</a>
      </div><div class="l_right">
      <a href="#" ${next_cust | n}>Client suivant &gt;</a>
      </div><div class="l_center">
      <a href="#" ${back_list | n}>Retour à la liste des clients</a>
      </div>
   </div>

   <span id="span_form" style="display: none;">
      <!-- Form -->
      ${tmpl_context.form(values) | n}
   </span>

