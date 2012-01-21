#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Voicemail files manipulation (delete, move)
# voicemail.py action mailbox message folder to
#  . action = [delete|move]

import sys, os
dir_vm='/var/spool/asterisk/voicemail'

def delete(mailbox, message, folder):
   dir = '%s/default/%s/%s' % (dir_vm, mailbox, folder)
   try:
      os.chdir(dir)
   except:
      sys.stderr.write('Error: chdir %s, exiting\n' % dir)
      sys.exit(2)

   # Delete message
   for e in ('gsm', 'WAV', 'wav', 'txt'):
      try:
         os.unlink('msg%04d.%s' % (message, e))
      except:
         pass

   # Rename following messages
   for f in sorted(os.listdir('.')):
      m = int(f[3:7])
      if m<message:
         continue
      print 'rename', f, m-1, f[-3:]
      ext = f[-3:]
      print 'rename', f
      os.rename(f, 'msg%04d.%s' % (m-1, f[-3:]))


#---------- Main
if len(sys.argv) not in (4,5):
   sys.stderr.write('error: arguments, existing\n')
   sys.exit(1)

action = sys.argv[1]
mailbox = sys.argv[2]
message = int(sys.argv[3])
folder = sys.argv[4]

if action=='delete':
   delete(mailbox, message, folder)

elif action=='move' and len(sys.argv)==5:
   delete(mailbox, message, folder, sys.argv[4])

else:
   sys.stderr.write('Error: unknown action %s, exiting\n' % dir)
   sys.exit(1)


