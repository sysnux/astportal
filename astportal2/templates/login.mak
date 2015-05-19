<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Connexion</title>
    <style type="text/css">
        #loginBox
        {
            width: 30%;
            margin: auto;
            margin-top: 10%;
            padding-left: 10%;
            padding-right: 10%;
            padding-top: 5%;
            padding-bottom: 5%;
            font-family: verdana;
            font-size: 10px;
            background-color: #eee;
            border: 2px solid #ccc;
        }

        #loginBox h1
        {
            font-size: 42px;
            font-family: "Trebuchet MS";
            margin: 0;
            color: #ddd;
        }

        #loginBox p
        {
            position: relative;
            top: -1.5em;
            padding-left: 4em;
            font-size: 12px;
            margin: 0;
            color: #666;
        }

        #loginBox table
        {
            table-layout: fixed;
            border-spacing: 0;
            width: 100%;
        }

        #loginBox td.label
        {
            width: 33%;
            text-align: right;
        }

        #loginBox td.field
        {
            width: 66%;
        }

        #loginBox td.field input
        {
            width: 100%;
        }

        #loginBox td.buttons
        {
            text-align: right;
        }
     </style>
</head>

<body>
   <div id="main_content">
<% flash = tg.flash_obj.render('flash', use_js=False) %>
% if flash:
		<div>
			${flash | n}
		</div>
%endif
   </div>
   <div id="loginBox">
      <h1>Login</h1>
      <form action="${tg.url('/login_handler', params = dict(came_from=came_from.encode('utf-8'), __logins = login_counter.encode('utf-8')))}" method="POST" class="loginfields">
         <table>
            <tr>
               <td class="label"><label for="user_name">Utilisateur:</label></td>
               <td class="field"><input type="text" id="login" name="login"/></td>
            </tr>
            <tr>
               <td class="label"><label for="password">Mot de passe:</label></td>
               <td class="field"><input type="password" id="password" name="password"/></td>
            </tr>
            <tr>
               <td colspan="2" class="buttons"><input type="submit" name="submit_button" value="Connexion"/></td>
            </tr>
         </table>
      </form>
   </div>
</body>
</html>
