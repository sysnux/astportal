<?xml version="1.0" encoding="UTF-8"?>
<Screen>
  <LeftStatusBar>
    <Layout width="57">
      <DisplayBitmap isfile="true">
        <Bitmap>/app/resource/etc/account_s_bg.bmp</Bitmap>
        <X>0</X>
        <Y>0</Y>
      </DisplayBitmap>
      <DisplayList>
        <X>0</X>
        <Y>3</Y>
      </DisplayList>
    </Layout>
    <Account height="21">
      <DisplayElement>
        <DisplayBitmap isfile="true">
          <Bitmap>/app/resource/etc/account_line_bg.bmp</Bitmap>
          <X>4</X>
          <Y>0</Y>
        </DisplayBitmap>
        <DisplayRectangle x="1" y="0" width="4" height="19" bgcolor="Light6"></DisplayRectangle>
        <DisplayBitmap isfile="true" renew-rate="second" isrenew="true">
          <Bitmap>/app/resource/etc/account_r.bmp</Bitmap>
          <X>1</X>
          <Y>0</Y>
          <displayCondition>
            <conditionType>accountRegistered</conditionType>
          </displayCondition>
        </DisplayBitmap>
        <DisplayBitmap isfile="true" isflash="true" renew-rate="second">
          <Bitmap>/app/resource/etc/account_nr.bmp</Bitmap>
          <X>1</X>
          <Y>0</Y>
          <displayCondition negate="true">
            <conditionType>accountRegistered</conditionType>
          </displayCondition>
        </DisplayBitmap>

      </DisplayElement>

      <DisplayElement>
        <DisplayString font="unifont" color="Black" bgcolor="Light5" height="16" width="48" renew-rate="second">
          <DisplayStr>${a}</DisplayStr>
          <X>6</X>
          <Y>1</Y>
          <displayCondition>
            <conditionType>accountRegistered</conditionType>
          </displayCondition>
        </DisplayString>

        <DisplayString font="unifont" width="48" height="16" color="Light2" bgcolor="Light5" shadow-color="White" renew-rate="second">
          <DisplayStr>${a}</DisplayStr>
          <X>6</X>
          <Y>1</Y>
          <displayCondition negate="true">
            <conditionType>accountRegistered</conditionType>
          </displayCondition>
        </DisplayString>

      </DisplayElement>

      <DisplayElement>
        <DisplayBitmap isfile="true" bgcolor="Light6" renew-rate="minute">
          <Bitmap>/app/resource/icon/vm1.bmp</Bitmap>
          <X>39</X>
          <Y>1</Y>
          <displayCondition>
            <conditionType>hasVoiceMail</conditionType>
          </displayCondition>
        </DisplayBitmap>
        <DisplayBitmap isfile="true" isflash="true" bgcolor="None" renew-rate="minute">
          <Bitmap>/app/resource/icon/vm2.bmp</Bitmap>
          <X>39</X>
          <Y>1</Y>
          <displayCondition>
            <conditionType>hasVoiceMail</conditionType>
          </displayCondition>
        </DisplayBitmap>
        <DisplayBitmap isfile="true" bgcolor="Light5" >
          <Bitmap>/app/resource/icon/im1.bmp</Bitmap>
          <X>39</X>
          <Y>1</Y>
          <displayCondition>
            <conditionType>hasIM</conditionType>
          </displayCondition>
        </DisplayBitmap>
        <DisplayBitmap isfile="true" isflash="true" bgcolor="None" >
          <Bitmap>/app/resource/icon/im2.bmp</Bitmap>
          <X>39</X>
          <Y>1</Y>
          <displayCondition>
            <conditionType>hasIM</conditionType>
          </displayCondition>
        </DisplayBitmap>
        <DisplayBitmap isfile="true" bgcolor="Light5" >
          <Bitmap>/app/resource/icon/im_vm1.bmp</Bitmap>
          <X>39</X>
          <Y>1</Y>
          <displayCondition>
            <conditionType>hasVM_IM</conditionType>
          </displayCondition>
        </DisplayBitmap>
        <DisplayBitmap isfile="true" isflash="true" bgcolor="None" >
          <Bitmap>/app/resource/icon/im_vm2.bmp</Bitmap>
          <X>39</X>
          <Y>1</Y>
          <displayCondition>
            <conditionType>hasVM_IM</conditionType>
          </displayCondition>
        </DisplayBitmap>

      </DisplayElement>

    </Account>
  </LeftStatusBar>

  <SoftkeyBar>
    <Layout height="15">
      <DisplayBitmap isfile="true">
        <Bitmap>/app/resource/etc/softkey_bg.bmp</Bitmap>
        <X>0</X>
        <Y>0</Y>
      </DisplayBitmap>
      <DisplayList>
        <X>2</X>
        <Y>2</Y>
      </DisplayList>

    </Layout>
    <ButtonShape id="0" width="59" height="14">
      <DisplayElement>
        <DisplayBitmap isfile="true">
          <Bitmap>/app/resource/etc/softkey_button_b.bmp</Bitmap>
          <X>0</X>
          <Y>0</Y>
        </DisplayBitmap>
      </DisplayElement>
      <DisplayElement>
        <DisplayString font="unifont" halign="center" color="White" bgcolor="Black" width="54" height="11">
          <DisplayStr>$A</DisplayStr>
          <X>2</X>
          <Y>1</Y>
        </DisplayString>
      </DisplayElement>
    </ButtonShape>
    <ButtonShape id="1" width="59" >
      <DisplayElement>
        <DisplayBitmap isfile="true">
          <Bitmap>/app/resource/etc/softkey_button_w.bmp</Bitmap>
          <X>0</X>
          <Y>0</Y>
        </DisplayBitmap>
      </DisplayElement>
      <DisplayElement>
        <DisplayString font="unifont" halign="center" color="Black" bgcolor="White" width="54" height="11">
          <DisplayStr>$A</DisplayStr>
          <X>2</X>
          <Y>1</Y>
        </DisplayString>
      </DisplayElement>
    </ButtonShape>

  </SoftkeyBar>


  <IdleScreen>

    <ShowStatusLine>true</ShowStatusLine>

    <!-- frame -->
    <DisplayElement>
      <DisplayRectangle x="0" y="0" width="123" height="11" bgcolor="White" fgcolor="Light6"></DisplayRectangle>
      <DisplayRectangle x="0" y="11" width="123" height="1" bgcolor="Light4" ></DisplayRectangle>
    </DisplayElement>

    <!-- should remove in future -->
    <DisplayBitmap isfile="true" >
      <Bitmap>/app/resource/icon/empty.bmp</Bitmap>
      <X>91</X>
      <Y>12</Y>
    </DisplayBitmap>
    <!-- Top bar content -->
    <DisplayElement>
      <DisplayString font="unifont" width="70" bgcolor="Light6" fgcolor="White" height="12">
        <DisplayStr>$f</DisplayStr>
        <X>1</X>
        <Y>-1</Y>
      </DisplayString>
      <DisplayString font="unifont" halign="right" width="50" bgcolor="White" fgcolor="Light6" height="12">
        <DisplayStr>$T</DisplayStr>
        <X>72</X>
        <Y>-1</Y>
      </DisplayString>
    </DisplayElement>

    <DisplayElement>
	
	  <!-- COMPANY LOGO -->
      <DisplayString font="bold" halign="left" width="105">
        <DisplayStr>${b}</DisplayStr>
        <X>2</X>
        <Y>12</Y>
      </DisplayString>

      <DisplayString halign="left" width="105" color="Dark3">
        <DisplayStr>${display_name}</DisplayStr>
        <X>2</X>
        <Y>28</Y>
      </DisplayString>

      <!-- IP -->
      <!--DisplayString font="numberfont" halign="center" width="105" color="Dark3">
        <DisplayStr>$I</DisplayStr>
        <X>0</X>
        <Y>34</Y>
        <displayCondition negate="true">
          <conditionType>missCall</conditionType>
        </displayCondition>
      </DisplayString-->

    </DisplayElement>
    <DisplayElement>

      <!-- IP Address -->
      <!--DisplayString font="unifont" color="Dark3" halign="center" width="105" bgcolor="White">
        <DisplayStr>$I</DisplayStr>
        <X>0</X>
        <Y>30</Y>
      </DisplayString-->
      <!-- Forward Call Log -->
      <DisplayString font="unifont" color="Dark3" width="105" halign="center" bgcolor="White">
        <DisplayStr>$j</DisplayStr>
        <X>0</X>
        <Y>30</Y>
        <displayCondition>
          <conditionType>hasFowardedCallLog</conditionType>
        </displayCondition>
      </DisplayString>
      <!-- Miss call -->
      <DisplayString font="unifont" color="Dark3" width="105" halign="center" bgcolor="White">
        <DisplayStr>$c</DisplayStr>
        <X>0</X>
        <Y>30</Y>
        <displayCondition>
          <conditionType>missCall</conditionType>
        </displayCondition>
      </DisplayString>

      <!-- 5V Error -->
      <DisplayString font="unifont" halign="center"  color="Dark3" width="105"  bgcolor="White">
        <DisplayStr>$v</DisplayStr>
        <X>0</X>
        <Y>30</Y>
        <displayCondition>
          <conditionType>wrongPower</conditionType>
        </displayCondition>
      </DisplayString>

      <!-- core dump -->
      <DisplayString font="unifont" halign="center"  color="Dark3" width="105"  bgcolor="White">
        <DisplayStr>$+1512</DisplayStr>
        <X>0</X>
        <Y>30</Y>
        <displayCondition>
          <conditionType>crash</conditionType>
        </displayCondition>
      </DisplayString>
    </DisplayElement>


    <DisplayElement>
      <!-- WRITING -->
      <DisplayBitmap isfile="true">
        <Bitmap>/app/resource/icon/icon_save.bmp</Bitmap>
        <X>107</X>
        <Y>12</Y>
        <displayCondition>
          <conditionType>writing</conditionType>
        </displayCondition>
      </DisplayBitmap>
      <!-- DND -->
      <DisplayBitmap isfile="true">
        <Bitmap>/app/resource/icon/dnd2.bmp</Bitmap>
        <X>107</X>
        <Y>12</Y>
        <displayCondition>
          <conditionType>dnd</conditionType>
        </displayCondition>
      </DisplayBitmap>
      <DisplayBitmap isfile="true" isflash="true">
        <Bitmap>/app/resource/icon/dnd.bmp</Bitmap>
        <X>107</X>
        <Y>12</Y>
        <displayCondition>
          <conditionType>dnd</conditionType>
        </displayCondition>
      </DisplayBitmap>
      <!-- NETWORK DOWN -->
      <DisplayBitmap isfile="true" >
        <Bitmap>/app/resource/icon/network_down2.bmp</Bitmap>
        <X>107</X>
        <Y>12</Y>
        <displayCondition negate = "true">
          <conditionType>networkUp</conditionType>
        </displayCondition>
      </DisplayBitmap>
      <DisplayBitmap isfile="true" isflash="true">
        <Bitmap>/app/resource/icon/network_down.bmp</Bitmap>
        <X>107</X>
        <Y>12</Y>
        <displayCondition negate = "true">
          <conditionType>networkUp</conditionType>
        </displayCondition>
      </DisplayBitmap>

      <DisplayBitmap isfile="true">
        <Bitmap>/app/resource/icon/empty.bmp</Bitmap>
        <X>107</X>
        <Y>12</Y>
        <displayCondition>
          <conditionType>keypadLock</conditionType>
        </displayCondition>
      </DisplayBitmap>
      <!-- CALL FORWARDED -->
      <DisplayBitmap isfile="true">
        <Bitmap>/app/resource/icon/fwd_noanswer.bmp</Bitmap>
        <X>107</X>
        <Y>28</Y>
        <displayCondition>
          <conditionType>delayedFwded</conditionType>
        </displayCondition>
      </DisplayBitmap>
      <DisplayBitmap isfile="true">
        <Bitmap>/app/resource/icon/fwd_busy.bmp</Bitmap>
        <X>107</X>
        <Y>28</Y>
        <displayCondition>
          <conditionType>busyFwded</conditionType>
        </displayCondition>
      </DisplayBitmap>
      <DisplayBitmap isfile="true">
        <Bitmap>/app/resource/icon/fwd_busy_noanswer.bmp</Bitmap>
        <X>107</X>
        <Y>28</Y>
        <displayCondition>
          <conditionType>busyNoAnswerFwded</conditionType>
        </displayCondition>
      </DisplayBitmap>
      <DisplayBitmap isfile="true">
        <Bitmap>/app/resource/icon/fwd_all.bmp</Bitmap>
        <X>107</X>
        <Y>28</Y>
        <displayCondition>
          <conditionType>callFwded</conditionType>
        </displayCondition>
      </DisplayBitmap>

      <DisplayBitmap isfile="true">
        <Bitmap>/app/resource/icon/empty.bmp</Bitmap>
        <X>107</X>
        <Y>28</Y>
        <displayCondition>
          <conditionType>keypadLock</conditionType>
        </displayCondition>
      </DisplayBitmap>
      <!-- Headset -->
      <DisplayBitmap isfile="true" >
        <Bitmap>/app/resource/icon/headset.bmp</Bitmap>
        <X>91</X>
        <Y>12</Y>
        <displayCondition>
          <conditionType>headsetMode</conditionType>
        </displayCondition>
      </DisplayBitmap>
      <DisplayBitmap isfile="true">
        <Bitmap>/app/resource/icon/empty.bmp</Bitmap>
        <X>91</X>
        <Y>12</Y>
        <displayCondition>
          <conditionType>keypadLock</conditionType>
        </displayCondition>
      </DisplayBitmap>
      <!-- CORE DUMP -->
      <DisplayBitmap isfile="true">
        <Bitmap>/app/resource/icon/coredump.bmp</Bitmap>
        <X>107</X>
        <Y>28</Y>
        <displayCondition>
          <conditionType>coredump</conditionType>
        </displayCondition>
      </DisplayBitmap>
      <!-- KeypadLock -->
      <DisplayBitmap isfile="true">
        <Bitmap>/app/resource/icon/lock_g.bmp</Bitmap>
        <X>107</X>
        <Y>28</Y>
        <displayCondition>
          <conditionType>keypadLock</conditionType>
        </displayCondition>
      </DisplayBitmap>

    </DisplayElement>






    <SoftKeys>
      <!-- JDG Switch to weather screen -->
      <!--SoftKey useshapeid="1">
        <Action>
          <SwitchSCR/>
        </Action>
        <displayCondition>
          <conditionType>SubScreen</conditionType>
        </displayCondition>
      </SoftKey>
      <SoftKey>
        <Action>
          <XmlService/>
        </Action>
        <displayCondition>
          <conditionType>XmlApp</conditionType>
        </displayCondition>
      </SoftKey>
      <SoftKey>
        <Action>
          <SignIn/>
        </Action>
        <displayCondition>
          <conditionType>signIn</conditionType>
        </displayCondition>
      </SoftKey>
      <SoftKey>
        <Action>
          <SignOut/>
        </Action>
        <displayCondition>
          <conditionType>signOut</conditionType>
        </displayCondition>
      </SoftKey-->

      <SoftKey>
        <Action>
          <BackSpace/>
        </Action>
        <displayCondition>
          <conditionType>backSpace</conditionType>
        </displayCondition>
      </SoftKey>
      <SoftKey>
        <Action>
          <CANCEL/>
        </Action>
        <displayCondition>
          <conditionType>backSpace</conditionType>
        </displayCondition>
      </SoftKey>
      <SoftKey>
        <Action>
          <MissedCalls/>
        </Action>
        <displayCondition>
          <conditionType>missCall</conditionType>
        </displayCondition>
      </SoftKey>
      <SoftKey>
        <Action>
          <FwdedCalls/>
        </Action>
        <displayCondition>
          <conditionType>hasFowardedCallLog</conditionType>
        </displayCondition>
      </SoftKey>
      <!-- JDG Forward all / Cancel -->
      <!-- SoftKey>
        <Action>
          <FwdAll/>
        </Action>
        <displayCondition>
          <conditionType>callFwdCancelled</conditionType>
        </displayCondition>
      </SoftKey>
      <SoftKey>
        <Action>
          <CancelFwd/>
        </Action>
        <displayCondition>
          <conditionType>callFwded</conditionType>
        </displayCondition>
      </SoftKey-->
      <SoftKey>
        <Action>
          <Redial/>
        </Action>
        <displayCondition>
          <conditionType>hasDialedCalllog</conditionType>
        </displayCondition>
      </SoftKey>
    </SoftKeys>
  </IdleScreen>

  <!-- IdleScreen>
    <ScreenShow>weatherShow</ScreenShow>

    <ShowStatusLine>false</ShowStatusLine>

    <DisplayElement>
      <DisplayRectangle x="0" y="0" width="179" height="15" bgcolor="Black" fgcolor="Dark3" shadow-color="Light3"></DisplayRectangle>
      <DisplayString font="unifont" color="White" bgcolor="Black" fgcolor="Dark3">
        <DisplayStr>$L, $S, $g</DisplayStr>
        <X>2</X>
        <Y>0</Y>
      </DisplayString>
    </DisplayElement>


    <DisplayBitmap isfile="true" isrenew="true">
      <Bitmap>/tmp/weather.bmp</Bitmap>
      <X>2</X>
      <Y>16</Y>
    </DisplayBitmap>
    <DisplayString font="unifont" color="Dark3">
      <DisplayStr>$w, $x%</DisplayStr>
      <X>33</X>
      <Y>16</Y>
      <displayCondition>
        <conditionType>alwaysDisplay</conditionType>
      </displayCondition>
    </DisplayString>
    <DisplayString font="unifont" color="Dark3">
      <DisplayStr>$0t</DisplayStr>
      <X>33</X>
      <Y>30</Y>
      <displayCondition>
        <conditionType>alwaysDisplay</conditionType>
      </displayCondition>
    </DisplayString>



    <SoftKeys>
      <SoftKey useshapeid="1">
        <Action>
          <SwitchSCR/>
        </Action>
      </SoftKey>

    </SoftKeys>
  </IdleScreen-->


</Screen>
