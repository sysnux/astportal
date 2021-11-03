<%inherit file="local:templates.master"/>

<%def name="title()">
A ${code} Error has Occurred 
</%def>

<h1>Error ${code}</h1>

<div>${message |n}</div>
