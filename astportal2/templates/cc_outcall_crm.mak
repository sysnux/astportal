<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml"
  xmlns:py="http://genshi.edgewall.org/"
  xmlns:xi="http://www.w3.org/2001/XInclude">

<xi:include href="master.html"/>

<head>
   <meta content="text/html; charset=utf-8" http-equiv="Content-Type" py:replace="''"/>
   <title py:content="title">Jquery Grid</title>

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
   $('#phone4').html( $('#phone4 a').text() );
   $('#phone5').html( $('#phone5 a').text() );
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
   <h1 py:content="title">Customer data</h1>

      
   <table>
      <tr>
         <th style="padding: 3px 10px;">Code client</th>
         <th style="padding: 3px 10px;">Email</th>
      </tr>
      <tr>
         <td><a href="#" title="Afficher la fiche client" 
            py:attrs="crm_click" py:content="code">CRM</a>
            </td>
         <td><a id="email" title="Envoyer un courrier électronique"
            py:attrs="email_href" py:content="email">email</a>
            </td>
      </tr>
      <tr><td colspan="5">&nbsp;</td></tr>
      <tr rowspan="2"><th colspan="5">Téléphones</th></tr>
      <tr>
         <th style="padding: 3px 10px">Domicile</th>
         <th style="padding: 3px 10px">Bureau 1</th>
         <th style="padding: 3px 10px">Bureau 2</th>
         <th style="padding: 3px 10px" id="gsm1">Vini perso.</th>
         <th style="padding: 3px 10px" id="gsm2">Vini pro.</th>
      </tr>
      <tr>
         <td id="phone1"><a href="#" title="Appeler au domicile"
            py:attrs="ph1_click" py:content="phone1">phone1</a>
            </td>
         <td id="phone2"><a href="#" title="Appeler au bureau"
            py:attrs="ph2_click" py:content="phone2">phone2</a>
            </td>
         <td id="phone3"><a href="#" title="Appeler au bureau"
            py:attrs="ph3_click" py:content="phone3">phone3</a>
            </td>
         <td id="phone4"><a href="#" title="Appeler sur vini perso."
            py:attrs="ph4_click" py:content="phone4">phone4</a>
            </td>
         <td id="phone5"><a href="#" title="Appeler au sur vini pro."
            py:attrs="ph5_click" py:content="phone5">phone5</a>
            </td>
      </tr>
   </table>

   <div id="data" py:if="tmpl_context.grid" style="display: none">
      <!-- JQgrid -->
      ${tmpl_context.grid()}
   </div>

   <div id="other">
      <div class="l_left">
      <a href="#" py:attrs="prev_cust">&lt; Client précédent</a>
      </div><div class="l_right">
      <a href="#" py:attrs="next_cust">Client suivant &gt;</a>
      </div><div class="l_center">
      <a href="#" py:attrs="back_list">Retour à la liste des clients</a>
      </div>
   </div>

   <span id="span_form" style="display: none;">
      <!-- Form -->
      ${tmpl_context.form(values)}
   </span>

</body>
</html>
