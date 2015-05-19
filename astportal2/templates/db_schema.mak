<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml"
  xmlns:py="http://genshi.edgewall.org/"
  xmlns:xi="http://www.w3.org/2001/XInclude">

<xi:include href="master.html"/>

<head>
   <meta content="text/html; charset=utf-8" http-equiv="Content-Type" py:replace="''"/>
   <title py:content="title">Title</title>
   <link type="text/css" href="/toscawidgets/resources/tw.jquery.base/static/css/ui.all.css" rel="stylesheet" />
   <!--[if IE]><script type="text/javascript" src="../excanvas.compiled.js"></script><![endif]-->
   <script type="text/javascript"
      src="/toscawidgets/resources/tw.jquery.base/static/javascript/ui/minified/jquery-ui.min.js"></script>

	<style type="text/css">
      canvas {
         position:absolute;
         width: 2000px;
         height: 4000px;
         margin-left: -30px;
      }
   </style>

   <script type="text/javascript">
//<![CDATA[

var db_tables = new Object();
var db_fk = new Object();
var tables_pos = new Object();
var current=-1, unload_warning=1;

window.onbeforeunload = function () {
   if (unload_warning)
      return 'Modifications non enregistrées';
}

$(document).ready(
   function() {
      $('#action_form').dialog({ 
         autoOpen: false,  modal: true, width: '450px',
         buttons: { "Valider": function() {valide_action()}, "Annuler": function() {annule()}} });
      $.post(
      '/db_schema/fetch_db',
      function(data,stat){
         db_tables = data.tables;
         db_fk = data.fk
         var msg = '';
         for (t in db_tables) {
            msg += t + ' : ';
            for (c in db_tables[t].cols) {
               msg += db_tables[t].cols[c].name + ' ' + db_tables[t].cols[c].type + ', ';
            } 
            msg += '\n';
         }
         display();
      },
      'json'
      );
      unload_warning=0;
   }
);

function display(redraw) {
   var divs = '';
   for (t in db_tables) {
      divs += '<div id="table_' + t + '" title="' + t;
      divs += '" style="background: #fff; border:1px solid #5A9BD0; margin: 5px; position: absolute;">';
      divs += '<table><tbody><tr><th id="' + t + '" colspan="2" style="background: #5A9BD0; color: #fff; cursor: move">' + t + '</th></tr>\n';
      row=0;
      for (c in db_tables[t].cols) {
         var col = db_tables[t].cols[c];
         divs += '<tr id="' + t + '_' + col.name + '"';
         if ((row++)%2) divs += ' style="background: #9df">';
         else divs += ' style="background: #fff">';
         divs += '<td>' + col.name + '</td>';
         divs += '<td>' + col.type + '</td></tr>';
      }
      divs += '</tbody></table></div>\n';
   }

   $("#db_schema").html(divs);

   var top=0, left;
   for (t in db_tables) {
      var pos;
      // Make div draggable
      $('#table_' + t).draggable({
         handle: 'th',
         opacity: 0.35,
         containment: 'parent',
         stack: {group: '#db_schema div', min: 10},
         drag: function(event,ui){
            update_canvas();
         },
         stop: function(event,ui){
            tables_pos[this.id] = $(this).position();
            update_canvas();
         }
      });
      // Automatic positionning !
      if (top==0) { // Origin
         pos = $('#table_' + t).position();
         left = pos.left+5;
         top = pos.top + $('#table_' + t).height() +5;
      } else {
         $('#table_' + t).css('left', left);
         $('#table_' + t).css('top', top);
         top += $('#table_' + t).height() + 5;
         left += 10;
      }
      if (!redraw && tables_pos['table_'+t]) { // Manually positionned by dragging
         $('#table_' + t).css('left', tables_pos['table_'+t].left);
         $('#table_' + t).css('top', tables_pos['table_'+t].top);
         continue;
      }
      tables_pos['table_'+t] = $('#table_' + t).position();

   }
   $("#db_schema").height(top);
   update_canvas();
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
      var tgt_left = tgt.offset.left+tgt.width()-offset.left+4;
      var tgt_top = tgt.offset.top-offset.top;
      var tgt_arrow = tgt_left+8;
      var tgt_corner = tgt_left+15;
   }

   /* Line = 3 segments :      -- src 
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
   for (k in db_fk) {
      canvas_join(c2d, $('#canvas').offset(),
         $('#'+db_fk[k].from), $('#'+db_fk[k].to));
   }
}

//]]>
   </script>
</head>

<body>
   <h1 py:content="title">Titre</h1>
   <a href="#" onclick="display(true)">Redessiner</a> l'écran.<br/>
   <canvas id="canvas"></canvas>
   <div id="db_schema"></div>
</body>
</html>
