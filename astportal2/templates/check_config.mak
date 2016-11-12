<%inherit file="local:templates.master"/>

   <script type="text/javascript">
//<![CDATA[

$(document).ready(function() {
   $("#tabs").tabs();
   $('#grid').setGridWidth($('#data').width()-10, true);
   $(window).bind('resize', function() {
      $('#grid').setGridWidth($('#data').width()-10, true);
   });

});

//]]>
   </script>

      <h1>${title}</h1>


	<table>
		<tr>
			<th>Variable</th>
			<th>Valeur</th>
			<th>Etat</th>
		</tr>
		<tr><td>prefix_src</td>
			<td>${prefix_src}</td>
			<td><img src="/images/${'ok' if prefix_src_status else 'error'}.png" widht="16" height="16"></td></tr>
		<tr><td>default_dnis</td>
			<td>${default_dnis}</td>
			<td><img src="/images/${'ok' if default_dnis_status else 'error'}.png" widht="16" height="16"></td></tr>
		<tr><td>default_cid</td>
			<td>${default_cid}</td>
			<td><img src="/images/${'ok' if default_cid_status else 'error'}.png" widht="16" height="16"></td></tr>
		<tr><td>default_faxto</td>
			<td>${default_faxto}</td>
			<td><img src="/images/${'ok' if default_faxto_status else 'error'}.png" widht="16" height="16"></td></tr>
		<tr><td>default_faxfrom</td>
			<td>${default_faxfrom}</td>
			<td><img src="/images/${'ok' if default_faxfrom_status else 'error'}.png" widht="16" height="16"></td></tr>
		<tr><td>hide_numbers</td>
			<td>${hide_numbers}</td>
			<td><img src="/images/${'ok' if hide_numbers_status else 'error'}.png" widht="16" height="16"></td></tr>
		<tr><td>company</td>
			<td>${company}</td>
			<td><img src="/images/${'ok' if company_status else 'error'}.png" widht="16" height="16"></td></tr>
		<tr><td>asterisk_manager</td>
			<td>${asterisk_manager}</td>
			<td><img src="/images/${'ok' if asterisk_manager_status else 'error'}.png" widht="16" height="16"></td></tr>
		<tr><td>server_sip</td>
			<td>${server_sip}</td>
			<td><img src="/images/${'ok' if server_sip_status else 'error'}.png" widht="16" height="16"></td></tr>
		<tr><td>server_sip2</td>
			<td>${server_sip2}</td>
			<td><img src="/images/${'ok' if server_sip2_status else 'error'}.png" widht="16" height="16"></td></tr>
		<tr><td>server_firmware</td>
			<td>${server_firmware}</td>
			<td><img src="/images/${'ok' if server_firmware_status else 'error'}.png" widht="16" height="16"></td></tr>
		<tr><td>server_config</td>
			<td>${server_config}</td>
			<td><img src="/images/${'ok' if server_config_status else 'error'}.png" widht="16" height="16"></td></tr>
		<tr><td>server_syslog</td>
			<td>${server_syslog}</td>
			<td><img src="/images/${'ok' if server_syslog_status else 'error'}.png" widht="16" height="16"></td></tr>
		<tr><td>server_ntp</td>
			<td>${server_ntp}</td>
			<td><img src="/images/${'ok' if server_ntp_status else 'error'}.png" widht="16" height="16"></td></tr>
		<tr><td>server_utc_diff</td>
			<td>${server_utc_diff}</td>
			<td><img src="/images/${'ok' if server_utc_diff_status else 'error'}.png" widht="16" height="16"></td></tr>
		<tr><td>command_fping</td>
			<td>${command_fping}</td>
			<td><img src="/images/${'ok' if command_fping_status else 'error'}.png" widht="16" height="16"></td></tr>
		<tr><td>command_arp</td>
			<td>${command_arp}</td>
			<td><img src="/images/${'ok' if command_arp_status else 'error'}.png" widht="16" height="16"></td></tr>
		<tr><td>command_sox8</td>
			<td>${command_sox8}</td>
			<td><img src="/images/${'ok' if command_sox8_status else 'error'}.png" widht="16" height="16"></td></tr>
		<tr><td>command_sendfax</td>
			<td>${command_sendfax}</td>
			<td><img src="/images/${'ok' if command_sendfax_status else 'error'}.png" widht="16" height="16"></td></tr>
		<tr><td>directory_firmware</td>
			<td>${directory_firmware}</td>
			<td><img src="/images/${'ok' if directory_firmware_status else 'error'}.png" widht="16" height="16"></td></tr>
		<tr><td>directory_config</td>
			<td>${directory_config}</td>
			<td><img src="/images/${'ok' if directory_config_status else 'error'}.png" widht="16" height="16"></td></tr>
		<tr><td>directory_asterisk</td>
			<td>${directory_asterisk}</td>
			<td><img src="/images/${'ok' if directory_asterisk_status else 'error'}.png" widht="16" height="16"></td></tr>
		<tr><td>directory_monitor</td>
			<td>${directory_monitor}</td>
			<td><img src="/images/${'ok' if directory_monitor_status else 'error'}.png" widht="16" height="16"></td></tr>
		<tr><td>directory_utils</td>
			<td>${directory_utils}</td>
			<td><img src="/images/${'ok' if directory_utils_status else 'error'}.png" widht="16" height="16"></td></tr>
		<tr><td>directory_tmp</td>
			<td>${directory_tmp}</td>
			<td><img src="/images/${'ok' if directory_tmp_status else 'error'}.png" widht="16" height="16"></td></tr>
		<tr><td>directory_fax</td>
			<td>${directory_fax}</td>
			<td><img src="/images/${'ok' if directory_fax_status else 'error'}.png" widht="16" height="16"></td></tr>
		<tr><td>sounds_languages</td>
			<td>${sounds_languages}</td>
			<td><img src="/images/${'ok' if sounds_languages_status else 'error'}.png" widht="16" height="16"></td></tr>
		<tr><td>directory_moh</td>
			<td>${directory_moh}</td>
			<td><img src="/images/${'ok' if directory_moh_status else 'error'}.png" widht="16" height="16"></td></tr>
		<tr><td>directory_sounds</td>
			<td>${directory_sounds}</td>
			<td><img src="/images/${'ok' if directory_sounds_status else 'error'}.png" widht="16" height="16"></td></tr>
		<tr><td>sip_type</td>
			<td>${sip_type}</td>
			<td><img src="/images/${'ok' if sip_type_status else 'error'}.png" widht="16" height="16"></td></tr>
		<tr><td>gxp_vlan</td>
			<td>${gxp_vlan}</td>
			<td><img src="/images/${'ok' if gxp_vlan_status else 'error'}.png" widht="16" height="16"></td></tr>
		<tr><td>gxp_keypad</td>
			<td>${gxp_keypad}</td>
			<td><img src="/images/${'ok' if gxp_keypad_status else 'error'}.png" widht="16" height="16"></td></tr>
	</table>
