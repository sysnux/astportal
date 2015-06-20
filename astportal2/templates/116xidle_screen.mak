<?xml version="1.0" encoding="UTF-8"?>
<Screen>

  <IdleScreen>
    <ShowStatusLine>false</ShowStatusLine>
    <DisplayElement>
      <DisplayString font="unifont" width="70" height="12">
        <DisplayStr>${f}</DisplayStr>
        <X>0</X>
        <Y>0</Y>
      </DisplayString>
      <DisplayString font="unifont" halign="right" width="50" height="12">
        <DisplayStr>${T}</DisplayStr>
        <X>77</X>
        <Y>0</Y>
      </DisplayString>
    </DisplayElement>
    <!-- LOGO -->
    <DisplayElement>
	<!-- COMPANY NAME  -->
      <DisplayString font="unifont" halign="center" width="128" bgcolor="White">
        <DisplayStr>${b}</DisplayStr>
        <X>0</X>
        <Y>12</Y>
      </DisplayString>
    </DisplayElement>
    <!-- forwarded call msg -->
    <DisplayElement>
      <DisplayString font="unifont" halign="center" width="128" bgcolor="White">
        <DisplayStr>${j}</DisplayStr>
        <X>0</X>
        <Y>12</Y>
        <displayCondition>
          <conditionType>hasFowardedCallLog</conditionType>
        </displayCondition>
      </DisplayString>
    </DisplayElement>
    <DisplayElement>
      <DisplayBitmap isfile="true">
        <Bitmap>/app/resource/icon/misscall_13.bmp</Bitmap>
        <X>6</X>
        <Y>13</Y>
        <displayCondition>
          <conditionType>missCall</conditionType>
        </displayCondition>
      </DisplayBitmap>
      <!-- TEXT CONTENTS -->
      <DisplayString font="unifont" width="102" bgcolor="White">
        <DisplayStr>$c</DisplayStr>
        <X>25</X>
        <Y>12</Y>
        <displayCondition>
          <conditionType>missCall</conditionType>
        </displayCondition>
      </DisplayString>
    </DisplayElement>
    <DisplayElement>
      <DisplayString font="unifont" halign="center" width="128" bgcolor="White">
        <DisplayStr>$+1226</DisplayStr>
        <X>0</X>
        <Y>12</Y>
        <displayCondition negate="true">
          <conditionType>networkUp</conditionType>
        </displayCondition>
      </DisplayString>
    </DisplayElement>
    <!-- 5V Error -->
    <DisplayElement>
      <DisplayString font="unifont" halign="center" width="128" bgcolor="White">
        <DisplayStr>$v</DisplayStr>
        <X>0</X>
        <Y>12</Y>
        <displayCondition>
          <conditionType>wrongPower</conditionType>
        </displayCondition>
      </DisplayString>
    </DisplayElement>
      <!-- core dump -->
      <DisplayString font="unifont" halign="center" width="128"  bgcolor="White">
        <DisplayStr>$+1512</DisplayStr>
        <X>0</X>
        <Y>12</Y>
        <displayCondition>
          <conditionType>crash</conditionType>
        </displayCondition>
      </DisplayString>
      <!-- NEW IM Messsages -->
      <DisplayString font="unifont" halign="center" width="128"  bgcolor="White">
        <DisplayStr>$+1539</DisplayStr>
        <X>0</X>
        <Y>12</Y>
        <displayCondition>
          <conditionType>hasIM</conditionType>
        </displayCondition>
      </DisplayString>
    <!-- KeypadLock -->
    <DisplayElement>
      <DisplayString font="unifont" halign="center" width="128" bgcolor="White">
        <DisplayStr>$k</DisplayStr>
        <X>0</X>
        <Y>12</Y>
        <displayCondition>
          <conditionType>keypadLock</conditionType>
        </displayCondition>
      </DisplayString>
    </DisplayElement>
    <SoftKeys>
      <SoftKey>
        <Action>
          <SwitchSCR/>
        </Action>
        <displayCondition>
          <conditionType>SubScreen</conditionType>
        </displayCondition>
      </SoftKey>
      <SoftKey>
        <Action>
          <Headset/>
        </Action>
        <displayCondition>
          <conditionType>alwaysDisplay</conditionType>
        </displayCondition>
      </SoftKey>
      <SoftKey>
        <Action>
          <BSCallCenter/>
        </Action>
        <displayCondition>
          <conditionType>bsCallCenter</conditionType>
        </displayCondition>
      </SoftKey>
      <SoftKey>
        <Action>
          <CallCenter/>
        </Action>
        <displayCondition>
          <conditionType>publishCallCenter</conditionType>
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
      </SoftKey>
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
      <!-- SoftKey>
        <Action>
          <FwdAll/>
        </Action>
        <displayCondition>
          <conditionType>callFwdCancelled</conditionType>
        </displayCondition>
      </SoftKey -->
      <SoftKey>
        <Action>
          <CancelFwd/>
        </Action>
        <displayCondition>
          <conditionType>callFwded</conditionType>
        </displayCondition>
      </SoftKey>
      <SoftKey>
        <Action>
          <LDAP/>
        </Action>
        <displayCondition>
          <conditionType>LDAPConfigured</conditionType>
        </displayCondition>
      </SoftKey>
      <SoftKey>
        <Action>
          <CallParked/>
        </Action>
        <displayCondition>
          <conditionType>hasBWCallParks</conditionType>
        </displayCondition>
      </SoftKey>
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
    <DisplayString font="unifont">
      <DisplayStr>$L, $S, $g</DisplayStr>
      <X>2</X>
      <Y>-2</Y>
    </DisplayString>
    <DisplayString font="unifont">
      <DisplayStr>$w, $0t</DisplayStr>
      <X>2</X>
      <Y>13</Y>
    </DisplayString>
    <SoftKeys>
      <SoftKey>
        <Action>
          <SwitchSCR/>
        </Action>
        <displayCondition>
          <conditionType>SubScreen</conditionType>
        </displayCondition>
      </SoftKey>
      <SoftKey>
        <Action>
          <Headset/>
        </Action>
        <displayCondition>
          <conditionType>alwaysDisplay</conditionType>
        </displayCondition>
      </SoftKey>
    </SoftKeys>
  </IdleScreen -->

  <IdleScreen>
    <ShowStatusLine>false</ShowStatusLine>
    <DisplayString>
      <DisplayStr>Adresse IP:</DisplayStr>
      <X>2</X>
      <Y>0</Y>
    </DisplayString>
    <DisplayString>
      <DisplayStr>$I</DisplayStr>
      <X>2</X>
      <Y>13</Y>
    </DisplayString>
    <SoftKeys>
      <SoftKey>
        <Action>
          <SwitchSCR/>
        </Action>
        <displayCondition>
          <conditionType>SubScreen</conditionType>
        </displayCondition>
      </SoftKey>
      <SoftKey>
        <Action>
          <Headset/>
        </Action>
        <displayCondition>
          <conditionType>alwaysDisplay</conditionType>
        </displayCondition>
      </SoftKey>
    </SoftKeys>
  </IdleScreen>

  <IdleScreen>
    <ShowStatusLine>false</ShowStatusLine>
    <DisplayString>
      <DisplayStr>Renvoyés:</DisplayStr>
      <X>2</X>
      <Y>0</Y>
    </DisplayString>
    <DisplayString>
      <DisplayStr>${CFS_IN}</DisplayStr>
      <X>2</X>
      <Y>13</Y>
    </DisplayString>
    <SoftKeys>
      <SoftKey>
        <Action>
          <SwitchSCR/>
        </Action>
        <displayCondition>
          <conditionType>SubScreen</conditionType>
        </displayCondition>
      </SoftKey>
      <SoftKey>
        <Action>
          <Headset/>
        </Action>
        <displayCondition>
          <conditionType>alwaysDisplay</conditionType>
        </displayCondition>
      </SoftKey>
    </SoftKeys>
  </IdleScreen>

</Screen>
