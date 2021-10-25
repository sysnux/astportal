<!DOCTYPE html>
<html>

<head>
    <meta charset="utf-8"/>
    <title>Appel entrant</title>
    <link rel="stylesheet" href="${tg.url('/css/style.css')}" />
    <script type="text/javascript">
//<![CDATA[

//]]>
    </script>
</head>
<body>

   <!-- Entête -->
   <div id="header">
   </div>

   <!-- Contenu -->
   <div id="main_content" style="padding: 15px; min-height: 100px">
	  <h1>Appel entrant</h1>
<table>
<tr><th>Groupe d'appels</th><td>${queue}</td></tr>
<tr><th>Durée attente</th><td>${holdtime} secondes</td></tr>
<tr><th>Numéro client</th><td>${custom1}</td></tr>
<tr><th>Appelant</th><td>${callerid}</td></tr>
<tr><th>Canal</th><td>${channel}</td></tr>
<tr><th>Identifiant</th><td>${uid}</td></tr>
</table>
   </div>

   <!-- Pied -->
   <div id="footer">
      <p>Copyright &#169; 2007-2021 <a href="http://www.sysnux.pf">SysNux</a>, powered by:</p>
      <img src="${tg.url('/images/under_the_hood_blue.png')}" alt="TurboGears under the hood" />
   </div>

</body>

</html>
