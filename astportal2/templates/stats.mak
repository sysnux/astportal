<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml"
  xmlns:py="http://genshi.edgewall.org/"
  xmlns:xi="http://www.w3.org/2001/XInclude">

<xi:include href="master.html"/>

<head>
   <meta content="text/html; charset=utf-8" http-equiv="Content-Type" py:replace="''"/>
   <title py:content="title">Jquery FlexiGrid</title>
   
   <!--[if IE]><script language="javascript" type="text/javascript" src="excanvas.js"></script><![endif]-->

   <script type="text/javascript">
//<![CDATA[
 
var previousPoint = null;
var data_hourly = null;
var options_hourly = null;

$().ready(function () {
   $('#data_grid').setGridWidth($('#calls').width()-10, true);
   $('#hourly_grid').setGridWidth($('#calls').width()-10, true);
   $(window).bind('resize', function() {
      $('#data_grid').setGridWidth($('#calls').width()-10, true);
      $('#hourly_grid').setGridWidth($('#calls').width()-10, true);
   });
   $("#data_flot").bind("plothover", flothover);
   $("#hourly_flot").bind("plothover", flothover);
   // $("#tabs").tabs();
   // Creating tabs here leads to an error when loading hourly_flot, so delay
   // creation until the end of function load_hourly_complete, see below.
});

function flothover(event, pos, item) {
   $("#x").text(pos.x.toFixed(2));
   $("#y").text(pos.y.toFixed(2));

   if (item) {
      if (previousPoint != item.datapoint) {
         previousPoint = item.datapoint;
         $("#tooltip").remove();
         var x = item.datapoint[0].toFixed(2),
            y = item.datapoint[1]; // .toFixed(2);
                    
         showTooltip(item.pageX, item.pageY,
            item.series.label + ' : ' + y);
      }
   } else {
      $("#tooltip").remove();
      previousPoint = null;
   }
}

function showTooltip(x, y, contents) {
        $('<div id="tooltip">' + contents + '</div>').css( {
            position: 'absolute',
            display: 'none',
            top: y + 5,
            left: x + 5,
            border: '1px solid #fdd',
            padding: '2px',
            'background-color': '#fee',
            opacity: 0.80
        }).appendTo("body").fadeIn(200);
}

function load_complete(data) {
   /* Fonction appelée lors de la mise à jour du composant jqgrid.
      Mise à jour du graphique avec les données du tableau.  */

   var labels = new Array();
   var series = new Array();

   labels.push('display');
   labels.push('appels');
   labels.push('Durée');
   series[0] = new Array();
   series[1] = new Array();
   for (row in data.rows) {
      series[0].push( [row, data.rows[row]['cell'][0]] );
      series[1].push( [row, parseInt(data.rows[row]['cell'][1])] );
   }
   var data = new Array();
   var serie = { label: labels[1], data: series[1] };
   data.push(serie);
   var options = {
      grid: { clickable: true, hoverable: true},
      lines: { show: true },
      points: { show: true },
      xaxis: { ticks: series[0] }
   };
   $.plot($('#data_flot'), data, options);
}

function load_hourly_complete(data) {
   /* Fonction appelée lors de la mise à jour du composant jqgrid.
      Mise à jour du graphique avec les données du tableau.  */

   var labels = new Array();
   var series = new Array();
   labels.push('display');
   labels.push('appels');
   labels.push('Durée');
   series[0] = new Array();
   series[1] = new Array();
   series[2] = new Array();
   for (row in data.rows) {
      series[0].push( [row, data.rows[row]['cell'][0]] );
      series[1].push( [row, parseInt(data.rows[row]['cell'][1])] );
   }
   data_hourly = new Array();
   var serie = { label: labels[1], data: series[1] };
   data_hourly.push(serie);
   options_hourly = {
      grid: { clickable: true, hoverable: true},
      lines: { show: true },
      points: { show: true },
      xaxis: { ticks: series[0] },
   };
   $.plot($('#hourly_flot'), data_hourly, options_hourly);
   $("#tabs").tabs();
}

function daily(m) {
   with(document.forms[0]) {
      action = '';
      daily.value = m;
      submit();
   }
}

function csv() {
   with(document.forms[0]) {
      action = 'csv';
      submit();
   }
}

//]]>
   </script>
</head>

<body>
      <h1 py:content="title">Paginate Data Grid</h1>
      
      <div id="tabs">
         <ul>
            <li><a href="#calls">Appels</a></li>
            <li><a href="#hourly">Distribution horaire</a></li>
         </ul>

         <div id="calls">
            <!-- Form -->
            ${tmpl_context.form(values)}
            Export <a href="#" onclick="csv();">CSV</a>

            <!-- Flot -->
            <div id='data_flot_div' style="margin:10px auto; width:600px;" py:if="tmpl_context.data_flot">
               ${tmpl_context.data_flot()}
            </div>

            <!-- JqGrid -->
            ${tmpl_context.data_grid()}
         </div>

         <div id="hourly">
            <!-- Flot -->
            <div id='hourly_flot_div' style="margin:10px auto; width:600px;" py:if="tmpl_context.data_flot">
               ${tmpl_context.hourly_flot()}
            </div>

            <!-- JqGrid -->
            ${tmpl_context.hourly_grid()}
         </div>
      </div>

   </body>
</html>
