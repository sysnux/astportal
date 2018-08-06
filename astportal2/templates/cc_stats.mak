<%inherit file="local:templates.master"/>

   <style>
      .rotated { 
         -moz-transform: rotate(-45deg);
         -webkit-transform: rotate(-45deg);
         -o-transform: rotate(-45deg);
         -ms-transform: rotate(-45deg);
      }
   </style>

   <script type="text/javascript">
//<![CDATA[
 
var previousPoint = null;

$().ready(function () {
   $("#data_flot").bind("plothover", flothover);
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
   // Flot tooltips
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
   /* Function called after jqgrid component loads data.
      Data from the grid is used to update the graph.  */

   var plot_data = new Array(); // Flot data
   var flot_series = ${tmpl_context.flot_series | n}.split(','); // Series to actually plot
   var series = new Array(); // Flot series
   for (var i=0; i<flot_series.length+1; i++) {
      series[i] = new Array(); // Each serie is an array of points (x,y)
   }

   // Grab graph series from grid columns
   for (var row=0; row<data.rows.length; row++) {
      series[0].push( [row, data.rows[row].cell[0]] );
      for (var i=0; i<flot_series.length; i++) {
         var col = 1+parseInt(flot_series[i]);
         if (data.rows[row].cell[col]) {
            series[i+1].push( [row, parseInt(data.rows[row].cell[col])] );
         } else {
            series[i+1].push( [row, null] );
         }
      }
   }

   var colnames = $('#data_grid').jqGrid('getGridParam','colNames');
   // Then fill data to plot
   for (var i=0; i<flot_series.length; i++) {
      plot_data.push({ label: colnames[1+parseInt(flot_series[i])], 
            data: series[i+1] });
   }
   var options = {
      grid: { clickable: false, hoverable: true},
      lines: { show: true },
      points: { show: true },
      xaxis: { ticks: series[0] }
   };
   $.plot($('#data_flot'), plot_data, options);
   if (${tmpl_context.flot_labels_rotated})
      $('div .tickLabels .tickLabel').addClass('rotated');
}

function csv() {
   with(document.forms[0]) {
      action = 'csv';
      submit();
   }
}

//]]>
   </script>
      <h1>${title}</h1>
% if debug:
		${debug}<br />
% endif

      
      <!-- Form -->
         ${tmpl_context.form(values) | n}
         Export <a href="#" onclick="csv();">CSV</a>

      <!-- Flot -->
         ${tmpl_context.data_flot() | n}

      <!-- JqGrid -->
      ${tmpl_context.data_grid() | n}

