<?xml version="1.0" encoding="UTF-8"?>
<Screen>
  <LeftStatusBar>
    <Layout width="90">
      <DisplayBitmap isfile="true">
        <Bitmap>/app/resource/etc/account_s_bg.bmp</Bitmap>
        <X>0</X>
        <Y>0</Y>
      </DisplayBitmap>
      <DisplayList>
        <X>0</X>
        <Y>0</Y>
      </DisplayList>
    </Layout>
    <Account height="23">
      <DisplayElement>
        <DisplayBitmap isfile="true">
          <Bitmap>/app/resource/etc/account_line_bg.bmp</Bitmap>
          <X>6</X>
          <Y>0</Y>
        </DisplayBitmap>
        <DisplayRectangle x="1" y="0" width="6" height="23" bgcolor="Light6"></DisplayRectangle>
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
        <DisplayString font="unifont" width="78" height="16" bgcolor="Light5" renew-rate="second">
          <DisplayStr>$a</DisplayStr>
          <X>8</X>
          <Y>3</Y>
          <displayCondition>
            <conditionType>accountRegistered</conditionType>
          </displayCondition>
        </DisplayString>

        <DisplayString font="unifont" width="78" height="16" color="Light2" bgcolor="Light5" shadow-color="White" renew-rate="second">
          <DisplayStr>$a</DisplayStr>
          <X>8</X>
          <Y>3</Y>
          <displayCondition negate="true">
            <conditionType>accountRegistered</conditionType>
          </displayCondition>
        </DisplayString>

      </DisplayElement>

      <DisplayElement>
        <DisplayBitmap isfile="true" bgcolor="Light6" renew-rate="minute">
          <Bitmap>/app/resource/icon/vm1.bmp</Bitmap>
          <X>71</X>
          <Y>4</Y>
          <displayCondition>
            <conditionType>hasVoiceMail</conditionType>
          </displayCondition>
        </DisplayBitmap>
        <DisplayBitmap isfile="true" isflash="true" bgcolor="None" renew-rate="minute">
          <Bitmap>/app/resource/icon/vm2.bmp</Bitmap>
          <X>71</X>
          <Y>4</Y>
          <displayCondition>
            <conditionType>hasVoiceMail</conditionType>
          </displayCondition>
        </DisplayBitmap>
        <DisplayBitmap isfile="true" bgcolor="Light5" >
          <Bitmap>/app/resource/icon/im1.bmp</Bitmap>
          <X>71</X>
          <Y>4</Y>
          <displayCondition>
            <conditionType>hasIM</conditionType>
          </displayCondition>
        </DisplayBitmap>
        <DisplayBitmap isfile="true" isflash="true" bgcolor="None" >
          <Bitmap>/app/resource/icon/im2.bmp</Bitmap>
          <X>71</X>
          <Y>4</Y>
          <displayCondition>
            <conditionType>hasIM</conditionType>
          </displayCondition>
        </DisplayBitmap>
        <DisplayBitmap isfile="true" bgcolor="Light5" >
          <Bitmap>/app/resource/icon/im_vm1.bmp</Bitmap>
          <X>71</X>
          <Y>4</Y>
          <displayCondition>
            <conditionType>hasVM_IM</conditionType>
          </displayCondition>
        </DisplayBitmap>
        <DisplayBitmap isfile="true" isflash="true" bgcolor="None" >
          <Bitmap>/app/resource/icon/im_vm2.bmp</Bitmap>
          <X>71</X>
          <Y>4</Y>
          <displayCondition>
            <conditionType>hasVM_IM</conditionType>
          </displayCondition>
        </DisplayBitmap>

      </DisplayElement>
    </Account>
  </LeftStatusBar>
  <SoftkeyBar>
    <Layout height="22" >

      <DisplayBitmap isfile="true">
        <Bitmap>/app/resource/etc/softkey_bg.bmp</Bitmap>
        <X>0</X>
        <Y>1</Y>
      </DisplayBitmap>
      <DisplayList>
        <X>2</X>
        <Y>4</Y>
      </DisplayList>

    </Layout>
    <ButtonShape id="0" width="79" height="17">
      <DisplayElement>
        <DisplayBitmap isfile="true">
          <Bitmap>/app/resource/etc/softkey_button_b.bmp</Bitmap>
          <X>0</X>
          <Y>0</Y>
        </DisplayBitmap>
      </DisplayElement>
      <DisplayElement>
        <DisplayString font="unifont" halign="center" color="White" bgcolor="Black" width="75">
          <DisplayStr>$A</DisplayStr>
          <X>1</X>
          <Y>2</Y>
        </DisplayString>
      </DisplayElement>
    </ButtonShape>
    <ButtonShape id="1" width="79" >
      <DisplayElement>
        <DisplayBitmap isfile="true">
          <Bitmap>/app/resource/etc/softkey_button_w.bmp</Bitmap>
          <X>0</X>
          <Y>0</Y>
        </DisplayBitmap>
      </DisplayElement>
      <DisplayElement>
        <DisplayString font="unifont" halign="left" color="Black" bgcolor="White" width="70">
          <DisplayStr>$A</DisplayStr>
          <X>1</X>
          <Y>2</Y>
        </DisplayString>
      </DisplayElement>
    </ButtonShape>

  </SoftkeyBar>





  <IdleScreen>

    <ShowStatusLine>true</ShowStatusLine>

    <!-- TOP -->
    <DisplayElement>
      <!-- frame -->
      <DisplayRectangle x="1" y="0" width="230" height="1" bgcolor="Light6" ></DisplayRectangle>
      <DisplayRectangle x="1" y="2" width="230" height="33" bgcolor="White" fgcolor="Light6"></DisplayRectangle>
      <!--DisplayRectangle x="1" y="35" width="230" height="1" bgcolor="Light4" ></DisplayRectangle-->

      <!-- WEATHER -->
      <!--DisplayBitmap isfile="true" isrenew="true">
        <Bitmap>/tmp/weather.bmp</Bitmap>
        <X>199</X>
        <Y>2</Y>
      </DisplayBitmap-->

      <!-- DATE -->
      <DisplayString font="bold" fgcolor="White" bgcolor="Light6" width="194" >
        <DisplayStr>$f</DisplayStr>
        <X>2</X>
        <Y>3</Y>
      </DisplayString>
      <!-- IP -->
      <DisplayString font="unifont" fgcolor="White" bgcolor="Light6" width="145" >
        <DisplayStr>$NAME</DisplayStr>
        <X>2</X>
        <Y>20</Y>
      </DisplayString>
      <!-- TIME -->
      <DisplayString font="unifont" halign="right" bgcolor="White" fgcolor="Light6" width="50" height="13" renew-rate="second">
        <DisplayStr>$T</DisplayStr>
        <X>178</X>
        <Y>2</Y>
      </DisplayString>
      <!-- Forwarded numbers -->
      <DisplayString font="unifont" fgcolor="White" bgcolor="Light6" width="145" >
        <DisplayStr>$CFS_IN</DisplayStr>
        <X>2</X>
        <Y>100</Y>
      </DisplayString>
    </DisplayElement>

	<!--COMPANY LOGO-->
    <DisplayElement>
      <DisplayBitmap isfile="false">
        <!--Bitmap>/app/resource/logo/gs_logo.bmp</Bitmap-->
        <X>40</X>
        <Y>50</Y>
<Bitmap>Qk2eEwAAAAAAADYEAAAoAAAAiAAAAB0AAAABAAgAAAAAAGgPAAATCwAAEwsAAAABAAAAAQAAAAAAAAEBAQACAgIAAwMDAAQEBAAFBQUABgYGAAcHBwAICAgACQkJAAoKCgALCwsADAwMAA0NDQAODg4ADw8PABAQEAAREREAEhISABMTEwAUFBQAFRUVABYWFgAXFxcAGBgYABkZGQAaGhoAGxsbABwcHAAdHR0AHh4eAB8fHwAgICAAISEhACIiIgAjIyMAJCQkACUlJQAmJiYAJycnACgoKAApKSkAKioqACsrKwAsLCwALS0tAC4uLgAvLy8AMDAwADExMQAyMjIAMzMzADQ0NAA1NTUANjY2ADc3NwA4ODgAOTk5ADo6OgA7OzsAPDw8AD09PQA+Pj4APz8/AEBAQABBQUEAQkJCAENDQwBEREQARUVFAEZGRgBHR0cASEhIAElJSQBKSkoAS0tLAExMTABNTU0ATk5OAE9PTwBQUFAAUVFRAFJSUgBTU1MAVFRUAFVVVQBWVlYAV1dXAFhYWABZWVkAWlpaAFtbWwBcXFwAXV1dAF5eXgBfX18AYGBgAGFhYQBiYmIAY2NjAGRkZABlZWUAZmZmAGdnZwBoaGgAaWlpAGpqagBra2sAbGxsAG1tbQBubm4Ab29vAHBwcABxcXEAcnJyAHNzcwB0dHQAdXV1AHZ2dgB3d3cAeHh4AHl5eQB6enoAe3t7AHx8fAB9fX0Afn5+AH9/fwCAgIAAgYGBAIKCggCDg4MAhISEAIWFhQCGhoYAh4eHAIiIiACJiYkAioqKAIuLiwCMjIwAjY2NAI6OjgCPj48AkJCQAJGRkQCSkpIAk5OTAJSUlACVlZUAlpaWAJeXlwCYmJgAmZmZAJqamgCbm5sAnJycAJ2dnQCenp4An5+fAKCgoAChoaEAoqKiAKOjowCkpKQApaWlAKampgCnp6cAqKioAKmpqQCqqqoAq6urAKysrACtra0Arq6uAK+vrwCwsLAAsbGxALKysgCzs7MAtLS0ALW1tQC2trYAt7e3ALi4uAC5ubkAurq6ALu7uwC8vLwAvb29AL6+vgC/v78AwMDAAMHBwQDCwsIAw8PDAMTExADFxcUAxsbGAMfHxwDIyMgAycnJAMrKygDLy8sAzMzMAM3NzQDOzs4Az8/PANDQ0ADR0dEA0tLSANPT0wDU1NQA1dXVANbW1gDX19cA2NjYANnZ2QDa2toA29vbANzc3ADd3d0A3t7eAN/f3wDg4OAA4eHhAOLi4gDj4+MA5OTkAOXl5QDm5uYA5+fnAOjo6ADp6ekA6urqAOvr6wDs7OwA7e3tAO7u7gDv7+8A8PDwAPHx8QDy8vIA8/PzAPT09AD19fUA9vb2APf39wD4+PgA+fn5APr6+gD7+/sA/Pz8AP39/QD+/v4A////AFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFi2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2trzAxKGYmJiYmJi0w7+8ure2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tpwmCgAAAAAAAAAAAAAQJzphsbi2tra2vMOnqKioqLvBwcG+vry8uLe2tra2tr2+vr64tra7vr6+ur6+vr62uL6+v7i4v76+vra2tra2u76+v7a+vr6/uLa2vL6+v7i+vr68tri+vr+4tb++vry2trm+vr+7tra7vr6/tra2tra2tra2tra2traQAAAAAAAAAAAAAAAAAAAAAACct7a2uU4AAAAAAAAAAAAAIyBBSHaXsba2trg4HyAeg7e3XSAgHWslICAfrYsgIBuQkxkgICG8tra2uFogIBeuLCAgHZi3uEcgIBmLISAeQrqSHyAakcEYICBCubaFHSAdYre7XR8gHLC2tra2tra2tra2tra2vDIAAAAAAAAAAAAAAAAAAAAABay2trsKAAAAAAAAAAAAAAAAAAAAAEW4tra2ogAAACVraSAAAACULQAAAJuRAAAAYjwAAAA6t7a2trZdAAAAfXIAAAA/aGoSAAAAuQAAAAK8mQAAAE7DDwAAFLy2lQAAAB64uHUAAACGuLa2tra2tra2tra2trasBgAAAAAAADFrkKWpuqYqAAAauba3kAAAAAAAAAAAAAAAAAAAAAAAnLe2trsxAAAAAAAAAAAAu1QAAACKogAAACocAAAAnLa2tra2ewAAAFbAEgAAAAAAAAAAC8cfAAABrKgAAAAhwDQAAAC/trAAAAAWtLaaAAAAZLm2tra2tra2tra2tra2tksAAAAAAJi9tra2tra2tBMAADO4trgjAAAAAAAABRciMktLS0xwamm3tra2fwAAAAAAAAAAGcCFAAAAebAAAAAABAAAPb62tra2tpMAAAAzuGAAAAAAAAAAAD3ASgAAAZq1AAAAB7tRAAAArrbBAAAADrC2oQMAADi8tra2tra2tra2tra2tra+FQAAAABhura2tra3uLa4BAAAZLi2fAAAAAAAXrS0tra2tra2tra2tra2tr8RAAAMgggAADm8uAAAAF3AAAAAAAAAAoq4tra2tranAAAAFrWyAAAAFoUAAABeu30AAAAFBgAAAAauagAAAH+3vh8AAAestqoGAAAHvra2tra2tra2tra2tra2tpIAAAAAArS2tra2NCtwt3QAAACGtr0wAAAAAaS2tra3v8PDw8PDw8C3tra3igAAALANAABot7kGAAA0wjMAAAAAAAAAVbe2tra2wAAAAA+wumUAAAq1AAAAhLaoAAAAAAAAAAADooQAAABSuLtRAAAAqLa0CgAAALO2tra2tra2tra2tra2tra8ZAAAAABduLa2uGQABqvBNgAADLG2oAAAAACQtra4hiYAAAAAAAAbkbi2trINAABXAAAAgLa4GAAADcRhAAABSRsAAAC0tra2uMApAAAKr7iqBAAAWwAAAJq2twAAAAAAAAAAAZmZAAAAMLm7ggAAAJO5vBUAAACjtra2tra2tra2tra2tra2trUlAAAAAKC2tra/AABGvKMDAAAevLlRAAAAWLq2wBIAAAAAAAAAAACgtra4aAAAAAAAAJi2tywAAADFhwAAAItyAAAAkbe2t3x6OAAAA4BlqjkAAAAAAACstrcQAAAeXlkAAACRqwAAAA6lZnkAAABRd4E5AAAAira2tra2tra2tra2tra2tra2uCIAAAANi7tuDwAAALW4SAAAAHW3txgBAADAtr0sAAAYl65aAAAAEbK2trwWAAAAAACxtrY5AAAAm7MAAAASBgAAAIi3trdgAAAAAAAAAHq0AAAAAAAKvra3IQAAHcO1BAAAZMMAAAAKsQAAAAAAAAAlbQAAAHi2tra2tra2tra2tra2tra2trauMQAAAAAAAAAAAACWtrEBAAAAr7aVAAAAaLa2gAAASba2tAQAAABRvLa3WQAAAAAJv7a2VAAAAHa1CgAAAAAAAACwtra3ggAAAAAAAABVuDsAAAAAQru2ti0AAADCtA8AADbEKgAABrEGAAAAAAAAGZgAAABiuLa2tra2tra2tra2tra2tra2trddCgYEAwMDBAY4rra4LgAAADK2uHYAABS3tr4hADS4trl0AAAAAJi2trYAAgIAS7u2tnkAAgBZtRcCAgICAgGEtra2trgAAgICAgIBKreZAAICAHy4trZKAAIAobQeAgIaxFQAAgOnJQICAgICAg+4AAICQru2tra2tra2tra2tra2tra2tra2uLmwp6ampqq0uba2tm4AAAAAqbe3VQAAMrm2sZOYt7a2qQIAAABDuba4pJycnKm3travnJycpbahnJycnKKzuLa2tra4m5ycnJycnKC2uJucnJyytra2qZycm7O2oZycmriqnJycs6KcnJycnJyftp2cnKO3tra2tra2tra2tra2tra2tra2tra2tra2tre4urzAsYowAAAAAB+6troyAABrvra2tra2uLEDAAAAAK62tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2sqSdeF46DgAAAAAAAAAAl7a2wTsAAGWsrq6uqYUGAAAAAABJt7a2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tq4AAAAAAAAAAAAAAAAAAIe2tra3fQAABwoKCgMAAAAAAAASfLe2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra4jhoAAAAAAAAAAAgWOne3tra2trioXkQ1KSkpLkVOaICkwLi2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra9xJ+YmJiYu8LAvrq2tra2tra2tre5u7y8vLy5uLa2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2tra2trZAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBA</Bitmap>
      </DisplayBitmap>
    </DisplayElement>


    <!-- ICONS -->
    <DisplayElement>
      <!-- WRITING -->
      <DisplayBitmap isfile="true">
        <Bitmap>/app/resource/icon/icon_save.bmp</Bitmap>
        <X>213</X>
        <Y>37</Y>
        <displayCondition>
          <conditionType>writing</conditionType>
        </displayCondition>
      </DisplayBitmap>
      <!-- DND -->
      <DisplayBitmap isfile="true" renew-rate="second">
        <Bitmap>/app/resource/icon/dnd2.bmp</Bitmap>
        <X>213</X>
        <Y>37</Y>
        <displayCondition>
          <customCondition valueToCompare="#dnd" compareOP="eq" value="1"></customCondition>
        </displayCondition>
      </DisplayBitmap>
      <DisplayBitmap isfile="true" isflash="true" renew-rate="second">
        <Bitmap>/app/resource/icon/dnd.bmp</Bitmap>
        <X>213</X>
        <Y>37</Y>
        <displayCondition>
          <customCondition valueToCompare="#dnd" compareOP="eq" value="1"></customCondition>
        </displayCondition>
      </DisplayBitmap>
      <!-- NETWORK DOWN -->
      <DisplayBitmap isfile="true" >
        <Bitmap>/app/resource/icon/network_down2.bmp</Bitmap>
        <X>213</X>
        <Y>37</Y>
        <displayCondition negate="true">
          <conditionType>networkUp</conditionType>
        </displayCondition>
      </DisplayBitmap>
      <DisplayBitmap isfile="true" isflash="true">
        <Bitmap>/app/resource/icon/network_down.bmp</Bitmap>
        <X>213</X>
        <Y>37</Y>
        <displayCondition negate="true">
          <conditionType>networkUp</conditionType>
        </displayCondition>
      </DisplayBitmap>
      <!-- CORE DUMP -->
      <DisplayBitmap isfile="true">
        <Bitmap>/app/resource/icon/coredump.bmp</Bitmap>
        <X>1</X>
        <Y>37</Y>
        <displayCondition>
          <conditionType>coredump</conditionType>
        </displayCondition>
      </DisplayBitmap>
      <!-- CALL FORWARDED -->
      <DisplayBitmap isfile="true">
        <Bitmap>/app/resource/icon/fwd_noanswer.bmp</Bitmap>
        <X>195</X>
        <Y>37</Y>
        <displayCondition>
          <conditionType>delayedFwded</conditionType>
        </displayCondition>
      </DisplayBitmap>
      <DisplayBitmap isfile="true">
        <Bitmap>/app/resource/icon/fwd_busy.bmp</Bitmap>
        <X>195</X>
        <Y>37</Y>
        <displayCondition>
          <conditionType>busyFwded</conditionType>
        </displayCondition>
      </DisplayBitmap>
      <DisplayBitmap isfile="true">
        <Bitmap>/app/resource/icon/fwd_busy_noanswer.bmp</Bitmap>
        <X>195</X>
        <Y>37</Y>
        <displayCondition>
          <conditionType>busyNoAnswerFwded</conditionType>
        </displayCondition>
      </DisplayBitmap>
      <DisplayBitmap isfile="true">
        <Bitmap>/app/resource/icon/fwd_all.bmp</Bitmap>
        <X>195</X>
        <Y>37</Y>
        <displayCondition>
          <conditionType>callFwded</conditionType>
        </displayCondition>
      </DisplayBitmap>
      <!-- KEYPAD LOCK -->
      <DisplayBitmap isfile="true">
        <Bitmap>/app/resource/icon/lock_g.bmp</Bitmap>
        <X>213</X>
        <Y>70</Y>
        <displayCondition>
          <conditionType>keypadLock</conditionType>
        </displayCondition>
      </DisplayBitmap>

      <!-- Headset -->
      <DisplayBitmap isfile="true" >
        <Bitmap>/app/resource/icon/empty.bmp</Bitmap>
        <X>177</X>
        <Y>37</Y>
      </DisplayBitmap>
      <DisplayBitmap isfile="true" >
        <Bitmap>/app/resource/icon/headset.bmp</Bitmap>
        <X>177</X>
        <Y>37</Y>
        <displayCondition>
          <conditionType>headsetMode</conditionType>
        </displayCondition>
      </DisplayBitmap>

      <!-- MISSED CALLED -->
      <DisplayBitmap isfile="true">
        <Bitmap>/app/resource/icon/miss2.bmp</Bitmap>
        <X>159</X>
        <Y>37</Y>
        <displayCondition>
          <conditionType>missCall</conditionType>
        </displayCondition>
      </DisplayBitmap>
      <DisplayBitmap isfile="true" isflash="true">
        <Bitmap>/app/resource/icon/miss.bmp</Bitmap>
        <X>159</X>
        <Y>37</Y>
        <displayCondition>
          <conditionType>missCall</conditionType>
        </displayCondition>
      </DisplayBitmap>
    </DisplayElement>

    <DisplayElement>
      <DisplayString font = "unifont" halign="center" width="228">
        <DisplayStr>$j</DisplayStr>
        <X>0</X>
        <Y>119</Y>
        <displayCondition>
          <conditionType>hasFowardedCallLog</conditionType>
        </displayCondition>
      </DisplayString>
    </DisplayElement>

    <DisplayElement>
      <DisplayString font="unifont" halign="center" width="228">
        <DisplayStr>$c</DisplayStr>
        <X>0</X>
        <Y>119</Y>
        <displayCondition>
          <conditionType>missCall</conditionType>
        </displayCondition>
      </DisplayString>
    </DisplayElement>

    <!-- 5v error -->
    <DisplayElement>

      <DisplayBitmap isfile="true">
        <Bitmap>/app/resource/etc/whitebox_small.bmp</Bitmap>
        <X>0</X>
        <Y>119</Y>
        <displayCondition>
          <conditionType>wrongPower</conditionType>
        </displayCondition>
      </DisplayBitmap>

      <DisplayString font="unifont" halign="center">
        <DisplayStr>$v</DisplayStr>
        <X>0</X>
        <Y>119</Y>
        <displayCondition>
          <conditionType>wrongPower</conditionType>
        </displayCondition>
      </DisplayString>
    </DisplayElement>

    <!-- 5v error -->
    <DisplayElement>
      <DisplayBitmap isfile="true">
        <Bitmap>/app/resource/etc/whitebox_small.bmp</Bitmap>
        <X>0</X>
        <Y>119</Y>
        <displayCondition>
          <conditionType>kdump</conditionType>
        </displayCondition>
      </DisplayBitmap>
      <DisplayString font="unifont" halign="center" width="228">
        <DisplayStr>kdump</DisplayStr>
        <X>0</X>
        <Y>119</Y>
        <displayCondition>
          <conditionType>kdump</conditionType>
        </displayCondition>
      </DisplayString>
    </DisplayElement>
    <!-- application crashed -->
    <DisplayElement>
      <DisplayBitmap isfile="true">
        <Bitmap>/app/resource/etc/whitebox_small.bmp</Bitmap>
        <X>0</X>
        <Y>119</Y>
        <displayCondition>
          <conditionType>crash</conditionType>
        </displayCondition>
      </DisplayBitmap>
      <DisplayString font="unifont" halign="center" width="228">
        <DisplayStr>$+1512</DisplayStr>
        <X>0</X>
        <Y>119</Y>
        <displayCondition>
          <conditionType>crash</conditionType>
        </displayCondition>
      </DisplayString>
    </DisplayElement>




    <!-- NFS OK 
		<DisplayBitmap isfile="true">
			<Bitmap>/app/resource/icon/nfs_ok.bmp</Bitmap>
			<X>23</X>
			<Y>37</Y>
            <displayCondition>
                <conditionType>nfsMountOk</conditionType>
            </displayCondition>
		</DisplayBitmap>
		<DisplayBitmap isfile="true">
			<Bitmap>/app/resource/icon/nfs_failed.bmp</Bitmap>
			<X>23</X>
			<Y>37</Y>
            <displayCondition>
                <conditionType>nfsMountFailed</conditionType>
            </displayCondition>
		</DisplayBitmap>
		-->




    <SoftKeys>
      <SoftKey useshapeid="1">
        <Icon textoffset="18" x="3" y="4" isfile="true">/app/resource/icon/screen1.bmp</Icon>
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
      </SoftKey>
      <!--<SoftKey>
        <Action>
          <NewCall/>
        </Action>
        <displayCondition>
          <conditionType>alwaysDisplay</conditionType>
        </displayCondition>
      </SoftKey>-->
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
      <SoftKey>
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

  <IdleScreen>
    <ScreenShow>weatherShow</ScreenShow>
    <ShowStatusLine>true</ShowStatusLine>



    <!-- DND -->
    <DisplayElement>
      <DisplayBitmap isfile="true">
        <Bitmap>/app/resource/icon/dnd2.bmp</Bitmap>
        <X>2</X>
        <Y>0</Y>
        <displayCondition>
          <conditionType>dnd</conditionType>
        </displayCondition>
      </DisplayBitmap>
      <DisplayBitmap isfile="true" isflash="true">
        <Bitmap>/app/resource/icon/dnd.bmp</Bitmap>
        <X>2</X>
        <Y>0</Y>
        <displayCondition>
          <conditionType>dnd</conditionType>
        </displayCondition>
      </DisplayBitmap>
    </DisplayElement>

    <!-- NETWORK DOWN -->
    <DisplayElement>
      <DisplayBitmap isfile="true" >
        <Bitmap>/app/resource/icon/network_down2.bmp</Bitmap>
        <X>22</X>
        <Y>0</Y>
        <displayCondition negate="true">
          <conditionType>networkUp</conditionType>
        </displayCondition>
      </DisplayBitmap>
      <DisplayBitmap isfile="true" isflash="true">
        <Bitmap>/app/resource/icon/network_down.bmp</Bitmap>
        <X>22</X>
        <Y>0</Y>
        <displayCondition negate="true">
          <conditionType>networkUp</conditionType>
        </displayCondition>
      </DisplayBitmap>
    </DisplayElement>

    <!-- Headset -->
    <DisplayElement>
      <DisplayBitmap isfile="true" >
        <Bitmap>/app/resource/icon/empty.bmp</Bitmap>
        <X>42</X>
        <Y>0</Y>
      </DisplayBitmap>
      <DisplayBitmap isfile="true" >
        <Bitmap>/app/resource/icon/headset.bmp</Bitmap>
        <X>42</X>
        <Y>0</Y>
        <displayCondition>
          <conditionType>headsetMode</conditionType>
        </displayCondition>
      </DisplayBitmap>
    </DisplayElement>

    <!-- CALL FORWARDED -->
    <DisplayBitmap isfile="true">
      <Bitmap>/app/resource/icon/fwd_noanswer.bmp</Bitmap>
      <X>62</X>
      <Y>0</Y>
      <displayCondition>
        <conditionType>delayedFwded</conditionType>
      </displayCondition>
    </DisplayBitmap>
    <DisplayBitmap isfile="true">
      <Bitmap>/app/resource/icon/fwd_busy.bmp</Bitmap>
      <X>62</X>
      <Y>0</Y>
      <displayCondition>
        <conditionType>busyFwded</conditionType>
      </displayCondition>
    </DisplayBitmap>
    <DisplayBitmap isfile="true">
      <Bitmap>/app/resource/icon/fwd_busy_noanswer.bmp</Bitmap>
      <X>62</X>
      <Y>0</Y>
      <displayCondition>
        <conditionType>busyNoAnswerFwded</conditionType>
      </displayCondition>
    </DisplayBitmap>
    <DisplayBitmap isfile="true">
      <Bitmap>/app/resource/icon/fwd_all.bmp</Bitmap>
      <X>62</X>
      <Y>0</Y>
      <displayCondition>
        <conditionType>callFwded</conditionType>
      </displayCondition>
    </DisplayBitmap>

    <!-- MISSED CALLED -->
    <DisplayElement>
      <DisplayBitmap isfile="true">
        <Bitmap>/app/resource/icon/miss2.bmp</Bitmap>
        <X>82</X>
        <Y>0</Y>
        <displayCondition>
          <conditionType>missCall</conditionType>
        </displayCondition>
      </DisplayBitmap>
      <DisplayBitmap isfile="true" isflash="true">
        <Bitmap>/app/resource/icon/miss.bmp</Bitmap>
        <X>82</X>
        <Y>0</Y>
        <displayCondition>
          <conditionType>missCall</conditionType>
        </displayCondition>
      </DisplayBitmap>
      <!-- NUM OF MISSING CALL -->
      <DisplayString font="numberfont" color="Dark2" height="11" renew-rate="minute">
        <DisplayStr>$G</DisplayStr>
        <X>98</X>
        <Y>5</Y>
        <displayCondition>
          <conditionType>missCall</conditionType>
        </displayCondition>
      </DisplayString>
      <!-- CORE DUMP -->
      <DisplayBitmap isfile="true">
        <Bitmap>/app/resource/icon/coredump.bmp</Bitmap>
        <X>158</X>
        <Y>0</Y>
        <displayCondition>
          <conditionType>coredump</conditionType>
        </displayCondition>
      </DisplayBitmap>
    </DisplayElement>

    <DisplayElement>
      <DisplayString font="unifont" halign="right" width="50">
        <DisplayStr>$T</DisplayStr>
        <X>177</X>
        <Y>0</Y>
      </DisplayString>
    </DisplayElement>



    <!-- NUM OF RING VOLUMN 
        <DisplayString font="numberfont">
            <DisplayStr>$r</DisplayStr>
            <X>206</X>
            <Y>8</Y>
        </DisplayString>
		-->

    <!-- frame -->


    <DisplayElement>

      <!-- WEATHER -->
      <DisplayBitmap isfile="true" isrenew="true">
        <Bitmap>/tmp/weather.bmp</Bitmap>
        <!--<Bitmap>/app/resource/weather/mostly_cloudy_night.bmp</Bitmap>-->
        <X>4</X>
        <Y>38</Y>
      </DisplayBitmap>
      <DisplayRectangle x="1" y="16" width="230" height="17" bgcolor="Black" fgcolor="Dark5" shadow-color="Light1"></DisplayRectangle>
      <DisplayRectangle x="1" y="16" width="230" height="17" bgcolor="Black" fgcolor="Dark5" shadow-color="Light1"></DisplayRectangle>

      <DisplayString font="unifont" color="White" bgcolor="Black" fgcolor="Dark5">
        <DisplayStr>$L, $S, $g</DisplayStr>
        <X>3</X>
        <Y>17</Y>

      </DisplayString>
      <DisplayString font="unifont" color="Dark3">
        <DisplayStr>$+1215: $w </DisplayStr>
        <X>40</X>
        <Y>38</Y>
      </DisplayString>
      <DisplayString font="unifont" color="Dark3">
        <DisplayStr>$+1152: $x%</DisplayStr>
        <X>40</X>
        <Y>53</Y>
      </DisplayString>
      <DisplayString font="unifont" color="Dark3">
        <DisplayStr>$0t</DisplayStr>
        <X>40</X>
        <Y>68</Y>
        <displayCondition>
          <conditionType>alwaysDisplay</conditionType>
        </displayCondition>
      </DisplayString>
    </DisplayElement>





    <!-- Weather Forcast -->
    <DisplayElement>
      <DisplayRectangle x="1" y="86" width="230" height="17" bgcolor="Black" fgcolor="Dark5" shadow-color="Light1"></DisplayRectangle>
      <DisplayString font="unifont" color="White" bgcolor="Black" fgcolor="Dark5">
        <DisplayStr>$+1216</DisplayStr><!---$+1153-->
        <X>3</X>
        <Y>87</Y>>
      </DisplayString>

    </DisplayElement>

    <DisplayElement>
      <!-- WEATHER -->
      <DisplayBitmap isfile="true" isrenew="true">
        <Bitmap>/tmp/weather_0.bmp</Bitmap>
        <X>4</X>
        <Y>105</Y>
      </DisplayBitmap>
      <DisplayBitmap isfile="true" isrenew="true">
        <Bitmap>/tmp/weather_1.bmp</Bitmap>
        <X>123</X>
        <Y>105</Y>
      </DisplayBitmap>

      <DisplayString font="unifont" color="Dark3">
        <DisplayStr>$+1217</DisplayStr>
        <X>40</X>
        <Y>105</Y>
        <displayCondition>
          <conditionType>alwaysDisplay</conditionType>
        </displayCondition>
      </DisplayString>
      <DisplayString font="unifont" color="Dark3">
        <DisplayStr>$0l - $0h</DisplayStr>
        <X>40</X>
        <Y>120</Y>
        <displayCondition>
          <conditionType>alwaysDisplay</conditionType>
        </displayCondition>
      </DisplayString>

      <DisplayString font="unifont" color="Dark3">
        <DisplayStr>$+1153</DisplayStr>
        <X>163</X>
        <Y>105</Y>
      </DisplayString>
      <DisplayString font="unifont" color="Dark3">
        <DisplayStr>$1l - $1h</DisplayStr>
        <X>163</X>
        <Y>120</Y>
        <displayCondition>
          <conditionType>alwaysDisplay</conditionType>
        </displayCondition>
      </DisplayString>
    </DisplayElement>

    <SoftKeys>
      <SoftKey useshapeid="1">
        <Icon textoffset="18" x="3" y="4" isfile="true">/app/resource/icon/screen2.bmp</Icon>
        <Action>
          <SwitchSCR/>
        </Action>
        <displayCondition>
          <conditionType>alwaysDisplay</conditionType>
        </displayCondition>
      </SoftKey>

    </SoftKeys>
  </IdleScreen>

  <IdleScreen>
    <ScreenShow>stockShow</ScreenShow>
    <ShowStatusLine>true</ShowStatusLine>

    <!-- 
      Process 
    -->
    <!--<DisplayConditionBlock x="0" y="0">
      <displayCondition conditionType="dnd" negate= "true">        
        <displayContent>
          
        </displayContent>
      </displayCondition>
      
    </DisplayConditionBlock>-->
    <!-- @@TOP_STATUS@@ -->
    <DisplayElement>
      <DisplayBitmap isfile="true">
        <Bitmap>/app/resource/icon/dnd2.bmp</Bitmap>
        <X>2</X>
        <Y>0</Y>
        <displayCondition>
          <conditionType>dnd</conditionType>
        </displayCondition>
      </DisplayBitmap>
      <DisplayBitmap isfile="true" isflash="true">
        <Bitmap>/app/resource/icon/dnd.bmp</Bitmap>
        <X>2</X>
        <Y>0</Y>
        <displayCondition>
          <conditionType>custom</conditionType>
          <customCondition valueToCompare="#dnd" compareOP="eq" value="1"></customCondition>
        </displayCondition>
      </DisplayBitmap>
    </DisplayElement>

    <!-- NETWORK DOWN -->
    <DisplayElement>
      <DisplayBitmap isfile="true" >
        <Bitmap>/app/resource/icon/network_down2.bmp</Bitmap>
        <X>22</X>
        <Y>0</Y>
        <displayCondition negate="true">
          <conditionType>networkUp</conditionType>
        </displayCondition>
      </DisplayBitmap>
      <DisplayBitmap isfile="true" isflash="true">
        <Bitmap>/app/resource/icon/network_down.bmp</Bitmap>
        <X>22</X>
        <Y>0</Y>
        <displayCondition negate="true">
          <conditionType>networkUp</conditionType>
        </displayCondition>
      </DisplayBitmap>
    </DisplayElement>

    <!-- Headset -->
    <DisplayElement>
      <DisplayBitmap isfile="true" >
        <Bitmap>/app/resource/icon/empty.bmp</Bitmap>
        <X>42</X>
        <Y>0</Y>
      </DisplayBitmap>
      <DisplayBitmap isfile="true" >
        <Bitmap>/app/resource/icon/headset.bmp</Bitmap>
        <X>42</X>
        <Y>0</Y>
        <displayCondition>
          <conditionType>headsetMode</conditionType>
        </displayCondition>
      </DisplayBitmap>
    </DisplayElement>

    <!-- CALL FORWARDED -->
    <DisplayBitmap isfile="true">
      <Bitmap>/app/resource/icon/fwd_noanswer.bmp</Bitmap>
      <X>62</X>
      <Y>0</Y>
      <displayCondition>
        <conditionType>delayedFwded</conditionType>
      </displayCondition>
    </DisplayBitmap>
    <DisplayBitmap isfile="true">
      <Bitmap>/app/resource/icon/fwd_busy.bmp</Bitmap>
      <X>62</X>
      <Y>0</Y>
      <displayCondition>
        <conditionType>busyFwded</conditionType>
      </displayCondition>
    </DisplayBitmap>
    <DisplayBitmap isfile="true">
      <Bitmap>/app/resource/icon/fwd_busy_noanswer.bmp</Bitmap>
      <X>62</X>
      <Y>0</Y>
      <displayCondition>
        <conditionType>busyNoAnswerFwded</conditionType>
      </displayCondition>
    </DisplayBitmap>
    <DisplayBitmap isfile="true">
      <Bitmap>/app/resource/icon/fwd_all.bmp</Bitmap>
      <X>62</X>
      <Y>0</Y>
      <displayCondition>
        <conditionType>callFwded</conditionType>
      </displayCondition>
    </DisplayBitmap>

    <!-- MISSED CALLED -->
    <DisplayElement>
      <DisplayBitmap isfile="true">
        <Bitmap>/app/resource/icon/miss2.bmp</Bitmap>
        <X>82</X>
        <Y>0</Y>
        <displayCondition>
          <conditionType>missCall</conditionType>
        </displayCondition>
      </DisplayBitmap>
      <DisplayBitmap isfile="true" isflash="true">
        <Bitmap>/app/resource/icon/miss.bmp</Bitmap>
        <X>82</X>
        <Y>0</Y>
        <displayCondition>
          <conditionType>missCall</conditionType>
        </displayCondition>
      </DisplayBitmap>
      <!-- NUM OF MISSING CALL -->
      <DisplayString font="numberfont" color="Dark2" height="11" renew-rate="minute">
        <DisplayStr>$G</DisplayStr>
        <X>98</X>
        <Y>5</Y>
        <displayCondition>
          <conditionType>missCall</conditionType>
        </displayCondition>
      </DisplayString>
      <!-- CORE DUMP -->
      <DisplayBitmap isfile="true">
        <Bitmap>/app/resource/icon/coredump.bmp</Bitmap>
        <X>158</X>
        <Y>0</Y>
        <displayCondition>
          <conditionType>coredump</conditionType>
        </displayCondition>
      </DisplayBitmap>
    </DisplayElement>

    <DisplayElement>
      <DisplayString font="unifont" halign="right" width="50" renew-rate="second">
        <DisplayStr>$T</DisplayStr>
        <X>177</X>
        <Y>0</Y>
      </DisplayString>
    </DisplayElement>


    <DisplayElement>
      <DisplayRectangle x="1" y="16" width="230" height="17" bgcolor="Black" fgcolor="Dark5" shadow-color="Light1"></DisplayRectangle>
      <DisplayString font="unifont" color="White" bgcolor="Black" fgcolor="Dark5">
        <DisplayStr>$+1218</DisplayStr>
        <X>3</X>
        <Y>17</Y>
      </DisplayString>
    </DisplayElement>

    <DisplayElement>
      <DisplayBitmap isfile="true">
        <Bitmap>/app/resource/icon/refresh_i.bmp</Bitmap>
        <X>213</X>
        <Y>19</Y>
      </DisplayBitmap>
      <DisplayString font="unifont" color="Light1" halign="right" width="50" bgcolor="Black" fgcolor="Dark5" renew-rate="minute">
        <DisplayStr>$*T</DisplayStr>
        <X>161</X>
        <Y>17</Y>
      </DisplayString>
    </DisplayElement>
    <!-- LIST BEGIN HERE -->
    <!-- pagingRecordRefreshIntervalRate: in millisecond, equal or less than 0  means no automatic refresh for additional records -->
    <DisplaySet id="stock" x="1" y="35" maxNumberOfRecord="6" pagingRecordRefreshIntervalRate="3000" dataSourceName="$Stock" displayDirection="vertical">
      <ItemTemplate height="17">
        <DisplayRectangle x="2" y="15" width="222" height="1" bgcolor="Gray"></DisplayRectangle>
        <DisplayRectangle x="0" y="0" width="226" height="15" color="White" bgcolor="White" border-color="Light2">
          <displayCondition negate="true">
            <conditionType>stockValueIncrease</conditionType>
          </displayCondition>
        </DisplayRectangle>
        <DisplayRectangle x="0" y="0" width="226" height="15" color="White" bgcolor="White" fgcolor="Light5" border-color="Light2">
          <displayCondition>
            <conditionType>stockValueIncrease</conditionType>
          </displayCondition>
        </DisplayRectangle>



        <!--<DisplayBitmap isfile="true">
          <Bitmap>/app/resource/etc/line_bg_w.bmp</Bitmap>
          <X>0</X>
          <Y>0</Y>
          <displayCondition>
            <conditionType>stockValueIncrease</conditionType>
          </displayCondition>
        </DisplayBitmap>-->
        <!--<DisplayBitmap isfile="true">
          <Bitmap>/app/resource/etc/line_bg_g.bmp</Bitmap>
          <X>0</X>
          <Y>0</Y>
          <displayCondition negate="true">
            <conditionType>stockValueIncrease</conditionType>
          </displayCondition>
        </DisplayBitmap>-->

        <DisplayBitmap isfile="true">
          <Bitmap>/app/resource/icon/stock_up.bmp</Bitmap>
          <X>164</X>
          <Y>1</Y>
          <displayCondition>
            <conditionType>stockValueIncrease</conditionType>
          </displayCondition>
        </DisplayBitmap>
        <DisplayBitmap isfile="true">
          <Bitmap>/app/resource/icon/stock_down.bmp</Bitmap>
          <X>164</X>
          <Y>1</Y>
          <displayCondition negate="true">
            <conditionType>stockValueIncrease</conditionType>
          </displayCondition>
        </DisplayBitmap>

        <!-- symbol -->
        <DisplayString font="unifont" width="94" height="13" bgcolor="White" fgcolor="Light5">
          <DisplayStr>$*c</DisplayStr>
          <!-- Change to name $*c-->
          <X>2</X>
          <Y>1</Y>
        </DisplayString>

        <!-- 
          ConditionalDisplay will override the position of the display object (when given)
          it should be able to save the 
        -->
        <!--<ConditionalDisplay x="" y="" width="" height="">
          <Condition type="stockValueIncrease" negate="true">
            
            
          </Condition>
          
        </ConditionalDisplay>-->
        <DisplayString font="unifont" halign="right" width="50" height="13">
          <DisplayStr>$*p</DisplayStr>
          <!-- last time updated stock value -->
          <X>110</X>
          <Y>1</Y>
        </DisplayString>

        <DisplayString font="unifont" halign="right" color="Dark3" width="45" height="13">
          <DisplayStr>$*C</DisplayStr>
          <!--  stock changed value -->
          <X>180</X>
          <Y>1</Y>
          <displayCondition>
            <conditionType>stockValueIncrease</conditionType>
          </displayCondition>
        </DisplayString>
        <DisplayString font="unifont" halign="right" color="Black" width="45" height="13">
          <DisplayStr>$*C</DisplayStr>
          <!--  stock changed value -->
          <X>180</X>
          <Y>1</Y>
          <displayCondition negate="true">
            <conditionType>stockValueIncrease</conditionType>
          </displayCondition>
        </DisplayString>

      </ItemTemplate>
    </DisplaySet>
    <DisplayElement>
      <DisplayBitmap isfile="true" >
        <Bitmap>/app/resource/icon/arrow_up.bmp</Bitmap>
        <X>98</X>
        <Y>35</Y>
        <displayCondition>
          <conditionType>scrollUp</conditionType>
        </displayCondition>
      </DisplayBitmap>
      <DisplayBitmap isfile="true" >
        <Bitmap>/app/resource/icon/arrow_down.bmp</Bitmap>
        <X>98</X>
        <Y>131</Y>
        <displayCondition>
          <conditionType>scrollDown</conditionType>
        </displayCondition>
      </DisplayBitmap>
    </DisplayElement>

    <!-- $*T > stock update time -->
    <SoftKeys>
      <SoftKey useshapeid="1">
        <Icon textoffset="18" x="3" y="4" isfile="true">/app/resource/icon/screen3.bmp</Icon>
        <Action>
          <SwitchSCR/>
        </Action>
        <displayCondition>
          <conditionType>alwaysDisplay</conditionType>
        </displayCondition>
      </SoftKey>
      <SoftKey>
        <Action>
          <RefreshStock/>
        </Action>
        <displayCondition>
          <conditionType>alwaysDisplay</conditionType>
        </displayCondition>
      </SoftKey>
    </SoftKeys>
  </IdleScreen>


  <IdleScreen>
    <ScreenShow>currencyShow</ScreenShow>
    <ShowStatusLine>true</ShowStatusLine>

    <!-- @@TOP_STATUS@@ -->
    <DisplayElement>
      <DisplayBitmap isfile="true">
        <Bitmap>/app/resource/icon/dnd2.bmp</Bitmap>
        <X>2</X>
        <Y>0</Y>
        <displayCondition>
          <conditionType>dnd</conditionType>
        </displayCondition>
      </DisplayBitmap>
      <DisplayBitmap isfile="true" isflash="true">
        <Bitmap>/app/resource/icon/dnd.bmp</Bitmap>
        <X>2</X>
        <Y>0</Y>
        <displayCondition>
          <conditionType>dnd</conditionType>
        </displayCondition>
      </DisplayBitmap>
    </DisplayElement>

    <!-- NETWORK DOWN -->
    <DisplayElement>
      <DisplayBitmap isfile="true" >
        <Bitmap>/app/resource/icon/network_down2.bmp</Bitmap>
        <X>22</X>
        <Y>0</Y>
        <displayCondition negate="true">
          <conditionType>networkUp</conditionType>
        </displayCondition>
      </DisplayBitmap>
      <DisplayBitmap isfile="true" isflash="true">
        <Bitmap>/app/resource/icon/network_down.bmp</Bitmap>
        <X>22</X>
        <Y>0</Y>
        <displayCondition negate="true">
          <conditionType>networkUp</conditionType>
        </displayCondition>
      </DisplayBitmap>
    </DisplayElement>

    <!-- Headset -->
    <DisplayElement>
      <DisplayBitmap isfile="true" >
        <Bitmap>/app/resource/icon/empty.bmp</Bitmap>
        <X>42</X>
        <Y>0</Y>
      </DisplayBitmap>
      <DisplayBitmap isfile="true" >
        <Bitmap>/app/resource/icon/headset.bmp</Bitmap>
        <X>42</X>
        <Y>0</Y>
        <displayCondition>
          <conditionType>headsetMode</conditionType>
        </displayCondition>
      </DisplayBitmap>
    </DisplayElement>

    <!-- CALL FORWARDED -->
    <DisplayBitmap isfile="true">
      <Bitmap>/app/resource/icon/fwd_noanswer.bmp</Bitmap>
      <X>62</X>
      <Y>0</Y>
      <displayCondition>
        <conditionType>delayedFwded</conditionType>
      </displayCondition>
    </DisplayBitmap>
    <DisplayBitmap isfile="true">
      <Bitmap>/app/resource/icon/fwd_busy.bmp</Bitmap>
      <X>62</X>
      <Y>0</Y>
      <displayCondition>
        <conditionType>busyFwded</conditionType>
      </displayCondition>
    </DisplayBitmap>
    <DisplayBitmap isfile="true">
      <Bitmap>/app/resource/icon/fwd_busy_noanswer.bmp</Bitmap>
      <X>62</X>
      <Y>0</Y>
      <displayCondition>
        <conditionType>busyNoAnswerFwded</conditionType>
      </displayCondition>
    </DisplayBitmap>
    <DisplayBitmap isfile="true">
      <Bitmap>/app/resource/icon/fwd_all.bmp</Bitmap>
      <X>62</X>
      <Y>0</Y>
      <displayCondition>
        <conditionType>callFwded</conditionType>
      </displayCondition>
    </DisplayBitmap>

    <!-- MISSED CALLED -->
    <DisplayElement>
      <DisplayBitmap isfile="true">
        <Bitmap>/app/resource/icon/miss2.bmp</Bitmap>
        <X>82</X>
        <Y>0</Y>
        <displayCondition>
          <conditionType>missCall</conditionType>
        </displayCondition>
      </DisplayBitmap>
      <DisplayBitmap isfile="true" isflash="true">
        <Bitmap>/app/resource/icon/miss.bmp</Bitmap>
        <X>82</X>
        <Y>0</Y>
        <displayCondition>
          <conditionType>missCall</conditionType>
        </displayCondition>
      </DisplayBitmap>
      <!-- NUM OF MISSING CALL -->
      <DisplayString font="numberfont" color="Dark2" height="11" renew-rate="minute">
        <DisplayStr>$G</DisplayStr>
        <X>98</X>
        <Y>5</Y>
        <displayCondition>
          <conditionType>missCall</conditionType>
        </displayCondition>
      </DisplayString>
      <!-- CORE DUMP -->
      <DisplayBitmap isfile="true">
        <Bitmap>/app/resource/icon/coredump.bmp</Bitmap>
        <X>158</X>
        <Y>0</Y>
        <displayCondition>
          <conditionType>coredump</conditionType>
        </displayCondition>
      </DisplayBitmap>
    </DisplayElement>

    <DisplayElement>
      <DisplayString font="unifont" halign="right" width="50">
        <DisplayStr>$T</DisplayStr>
        <X>177</X>
        <Y>0</Y>
      </DisplayString>
    </DisplayElement>


    <DisplayElement>
      <DisplayRectangle x="1" y="16" width="230" height="17" bgcolor="Black" fgcolor="Dark5" shadow-color="Light1"></DisplayRectangle>
      <DisplayString font="unifont" color="White" bgcolor="Black" fgcolor="Dark5">
        <DisplayStr>$+1220</DisplayStr>
        <X>3</X>
        <Y>17</Y>
      </DisplayString>
    </DisplayElement>

    <!-- LIST BEGIN HERE -->
    <DisplaySet id="currency" x="1" y="35" maxNumberOfRecord="6" dataSourceName="$Currency" displayDirection="vertical">
      <ItemTemplate height="17">
        <DisplayRectangle x="2" y="15" width="222" height="1" bgcolor="Gray"></DisplayRectangle>
        <DisplayRectangle x="0" y="0" width="226" height="15" bgcolor="White" border-color="Light2"></DisplayRectangle>



        <!-- symbol -->
        <DisplayString font="unifont" width="100" height="13" bgcolor="Light5">
          <DisplayStr> $*x - $*y</DisplayStr>
          <X>1</X>
          <Y>1</Y>
        </DisplayString>

        <DisplayString font="unifont" width="50" height="13" halign="right" >
          <DisplayStr>$*r</DisplayStr>
          <X>175</X>
          <Y>1</Y>
        </DisplayString>


      </ItemTemplate>
    </DisplaySet>

    <DisplayElement>
      <DisplayBitmap isfile="true" >
        <Bitmap>/app/resource/icon/arrow_up.bmp</Bitmap>
        <X>98</X>
        <Y>35</Y>
        <displayCondition>
          <conditionType>scrollUp</conditionType>
        </displayCondition>
      </DisplayBitmap>
      <DisplayBitmap isfile="true" >
        <Bitmap>/app/resource/icon/arrow_down.bmp</Bitmap>
        <X>98</X>
        <Y>131</Y>
        <displayCondition>
          <conditionType>scrollDown</conditionType>
        </displayCondition>
      </DisplayBitmap>
    </DisplayElement>
    <!-- $*T > stock update time -->
    <SoftKeys>
      <SoftKey useshapeid="1">
        <Icon textoffset="18" x="3" y="4" isfile="true">/app/resource/icon/screen4.bmp</Icon>
        <Action>
          <SwitchSCR/>
        </Action>
      </SoftKey>
      <SoftKey>
        <Action>
          <ReverseCurrency/>
        </Action>
      </SoftKey>
      <SoftKey>
        <Action>
          <RefreshCurrency/>
        </Action>
      </SoftKey>
    </SoftKeys>
  </IdleScreen>






</Screen>
