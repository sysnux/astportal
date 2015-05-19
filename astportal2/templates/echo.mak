<%inherit file="local:templates.master"/>


<script type="text/javascript">
//<![CDATA[

var ws = null;

$().ready(function() {

   // Create WebSocket
   ws = new WebSocket('ws://${host}/ws/');
   ws.onopen = function(evt) { display('Connected', 'green'); };
   ws.onclose = function(evt) { display('Disconnected', 'red'); ws = null; };
   ws.onmessage = function(evt) { display('Received: ' + evt.data, 'blue'); };
   ws.onerror = function(evt) { display(evt.data, 'red'); };

   // Send data
   $("#input").keyup(function(event) {
      if (event.keyCode == 13) {
         send_message($('#input').val());
         $('#input').val('');
      }
   });

   // Close properly
   $(window).on('beforeunload', function () {
      if (ws)
         ws.close();
   });
});

function send_message(msg) {
   if (ws) {
      display("Sent: " + msg, 'green'); 
      ws.send(msg);
   } else
      display("ERROR sending: " + msg, 'red');
}

function display(msg, color) {
   var html = $('#output').html();
   if (color)
      msg = '<span style="color: ' + color + ';">' + msg + '</span>';
   $('#output').html(html + msg + '<br/>');
}

//]]>
</script>

   <h2>${title}</h2>
   Message : <input id="input" type="text" />
   <div id="output"></div>

