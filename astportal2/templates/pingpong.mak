<!DOCTYPE html>
<html lang="en">
<head>
   <meta charset="utf-8" />
   <title>SocketIO Test</title>

   <script src="/js/jquery.min.js"></script>
   <script src="/js/socket.io-1.2.0.js"></script>

<script type="text/javascript">
//<![CDATA[

$().ready(function() {

   var socket = io.connect('/pingpong', {'resource': 'socketio'});

   $('.ping').click(function(event){
      socket.emit('ping', {'type': $(this).data('attack')});
   });

   socket.on('pong', function(data){
      $('#result').append(data.sound + '<br/>');
   });

});
//]]>
</script>

</head><body>
   <h2>SocketIO Test</h2>
 
   <div>
      <a class="ping" href="#" data-attack="ping">Ping</a>
      <a class="ping" href="#" data-attack="fireball">Fireball</a>
   </div>

   <div id="result"></div>

</body>
</html>
