<?xml version="1.0"?>
<!-- This file creates identical result to GXP-2000 default behavior -->
<Screen>
	<IdleScreen>
		<ShowStatusLine>true</ShowStatusLine>

		<DisplayString font="f8">
			<DisplayStr>$W, $M $d</DisplayStr>
			<X>0</X>
			<Y>0</Y>
		</DisplayString>

		<DisplayBitmap>
			<X>50</X>
			<Y>12</Y>
			<Bitmap>
Qk0GAgAAAAAAAD4AAAAoAAAAUAAAACYAAAABAAEAAAAAAMgBAAATCwAAEwsAAAIAAAACAAAA////
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD8AH//A///4AAAAAP/gD//g///8A
AAAA//4D//4////AAAAB//8B//8f///gAAAD//+B//8////gAAAP8D/AAB+/AAPwAAAP4A/AAA+/
AAPwAAAfgAfgAA++AAHwAAAfAAPwAB+/AAHwAAAfAAPwAB+/AAfgAAAeAAHwH/8////gAAAeAAHw
f/8////gAAA+AAHx//4////AAAA+AAEx//w////AAAA+AAED//A////gAAA+AAEB8AA+AAPwAAAf
AAIA4AA+AAHwAAAfAAIA4AA+AAHwAAAfgAZB4AA/AAHwAAAPwAwB4AAfAAPwAAAH8j8D//gf///g
AAAD//+D//wP///AAAAD//8A//4P///AAAAA//wAf/4D//+AAAAAP/AAL/8Bf/wAAAAAAoAAAAAA
AAAAAAA=
			</Bitmap>
		</DisplayBitmap>

		<DisplayString font="f13h" halign="Center" a1reg="false">
			<DisplayStr>AAA $N</DisplayStr>
			<X>65</X>
			<Y>12</Y>
		</DisplayString>

		<!-- DisplayString font="f13b" halign="Center" a1reg="true">
			<DisplayStr>BBB $N</DisplayStr>
			<X>65</X><Y>12</Y>
			</DisplayString>

		<DisplayString font="f13h" halign="Center" a1reg="false">
			<DisplayStr>CCC $X</DisplayStr>
			<X>65</X>
			<Y>26</Y>
		</DisplayString -->

		<DisplayString font="f13h" halign="Left" a1reg="false">
			<DisplayStr>${exten}</DisplayStr>
			<X>0</X>
			<Y>26</Y>
		</DisplayString>

		<DisplayString font="f13b" halign="Left" a1reg="true">
			<DisplayStr>${exten}</DisplayStr>
			<X>0</X>
			<Y>26</Y>
		</DisplayString>

		<DisplayString halign="Left" valign="Bottom">
			<DisplayStr>${ascii_name}</DisplayStr>
			<X>0</X>
			<Y>48</Y>
		</DisplayString>

	</IdleScreen>
</Screen>
