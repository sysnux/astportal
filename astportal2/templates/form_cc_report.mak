<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml"
  xmlns:py="http://genshi.edgewall.org/"
  xmlns:xi="http://www.w3.org/2001/XInclude">

<head>
   <meta content="text/html; charset=utf-8" http-equiv="Content-Type" py:replace="''"/>
   <title py:content="title">ToscaWidget Form</title>
    <link rel="stylesheet" type="text/css" media="screen" href="${tg.url('/css/style.css')}" />

</head>
<body>
      <h1 py:content="title">ToscaWidget Form</h1>

      <div py:replace="tmpl_context.form(values)">Input Form</div>

   </body>
</html>
