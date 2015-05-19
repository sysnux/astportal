<%inherit file="local:templates.master"/>

   <script type="text/javascript">
//<![CDATA[
      
$(document).ready(function() {
   $(window).bind('resize', function() {
      $('#grid').setGridWidth($('#data').width()-10, true);
   });
});

function echo() {
   $.post("${tg.url('echo')}",{});
   // $(document).ajaxError(data_fetch_failed);
}

function originate(num) {
   $.post("${tg.url('originate')}", {'exten': num});
   // $(document).ajaxError(data_fetch_failed);
}

function add(x) {
   location = 'new/'
}

function del(xid,msg) {
   if (confirm(msg)) {
      with (document.form_delete) {
         _id.value = xid;
         submit();
      }
   }
}
//]]>
   </script>

		<h1>${title}</h1>

      <!--a href="#" onclick="echo()">Test echo</a><br/><br/-->

      <div id="data">
         <!-- JQuery Grid -->
         ${tmpl_context.grid() | n}
      </div>

      <!-- -->
      <form name="form_delete" action="delete" method="POST">
         <input type="hidden" name="_id" />
         <input type="hidden" name="_method" value="DELETE" />
      </form>

      <br/>
      <a href="csv">Export CSV</a><br/><br/>

