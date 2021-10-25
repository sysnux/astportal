<!DOCTYPE html>
<html>

<head>
    <meta charset="utf-8"/>
    <title>Fin d'appel</title>
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
	  <h1>Fin d'appel</h1>
<table>
<tr><th>Groupe d'appels</th><td>${queue}</td></tr>
<tr><th>Numéro client</th><td>${custom1}</td></tr>
<tr><th>Identifiant</th><td>${uid}</td></tr>
<tr><th>Qualification</th><td><select>
    <option> - - -</options>	
    <option>Réglement</options>	
    <option>Fuite</options>	
    <option>Coupure</options>	
    <option>Réclamation</options>	
  </select></td></tr>
<tr><th>Commentaires</th><td><textarea>...</textarea></td></tr>
<tr><td>&nbsp;</td><td><button>Valider</button></td></tr>
</table>
   </div>

   <!-- Pied -->
   <div id="footer">
      <p>Copyright &#169; 2007-2021 <a href="http://www.sysnux.pf">SysNux</a>, powered by:</p>
      <img src="${tg.url('/images/under_the_hood_blue.png')}" alt="TurboGears under the hood" />
   </div>

</body>

</html>
