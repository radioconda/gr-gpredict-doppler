#!/usr/bin/env python
'''
   Copyright 2015 Wolfgang Nagele

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
'''
from gnuradio import gr
import sys
import threading
import time
import socket
import pmt

class doppler_runner(threading.Thread):
  def __init__(self, bc, gpredict_host, gpredict_port, verbose):
    threading.Thread.__init__(self)

    self.gpredict_host = gpredict_host
    self.gpredict_port = gpredict_port
    self.verbose = verbose
    self.blockclass = bc

    self.stopThread = False
    self.clientConnected = False
    self.sock = None
    self.server = None

  def run(self):
    try:
      bind_to = (self.gpredict_host, self.gpredict_port)
      self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      self.server.bind(bind_to)
      self.server.listen(0)
    except Exception as e:
      print("[doppler] Error starting listener: %s" % str(e))
      sys.exit(1)

    time.sleep(0.5) # TODO: Find better way to know if init is all done

    while not self.stopThread:
      print("[doppler] Waiting for connection on: %s:%d" % bind_to)
      self.clientConnected = False
      self.sock, addr = self.server.accept()
      self.clientConnected = True
      print("[doppler] Connected from: %s:%d" % (addr[0], addr[1]))

      cur_freq = 0
      cur_tx_freq = 0
      while not self.stopThread:
        try:
          data = self.sock.recv(1024)
        except:
          data = None
          
        if not data or self.stopThread:
          break

        # Allow for multiple commands to have come in at once.  For instance Frequency and AOS / LOS
        data = data.decode('ASCII').rstrip('\n') # Prevent extra '' in array
        commands = data.split('\n')
        
        for curCommand in commands:
          foundCommand = False
        
          if curCommand.startswith('F'):
            freq = int(curCommand[1:].strip())
            if cur_freq != freq:
              if self.verbose: print("[doppler] New frequency: %d" % freq)
              
              self.blockclass.sendFreq(freq)
              cur_freq = freq
              
            self.sock.sendall("RPRT 0\n".encode("UTF-8"))
            foundCommand = True
          elif curCommand.startswith('f'):
            sendMsgStr = "f: %d\n" % cur_freq
            self.sock.sendall(sendMsgStr.encode("UTF-8"))
            foundCommand = True
          elif curCommand.startswith('I'):
            tx_freq = int(curCommand[1:].strip())
            if cur_tx_freq != tx_freq:
              if self.verbose: print("[doppler] New tx frequency: %d" % tx_freq)
              self.blockclass.sendTxFreq(tx_freq)
              cur_tx_freq = tx_freq
            self.sock.sendall("RPRT 0\n".encode("UTF-8"))
            foundCommand = True
          elif curCommand.startswith('i'):
            sendMsgStr = "i: %d\n" % cur_tx_freq
            self.sock.sendall(sendMsgStr.encode("UTF-8"))
            foundCommand = True
          elif curCommand.startswith('S'):
            self.sock.sendall("RPRT 0\n".encode("UTF-8"))
          elif curCommand == 'q':
            # Radio sent a q on quit/disconnect.
            foundCommand = True
        
          if curCommand.startswith('AOS'):
            # Received Acquisition of signal.  Send state up
            if self.verbose: print("[doppler] received AOS")
            self.sock.sendall("RPRT 0\n".encode("UTF-8"))
            self.blockclass.sendState(True)
          elif curCommand.startswith('LOS'):
            # Received loss of signal.  Send state down
            if self.verbose: print("[doppler] received LOS")
            self.sock.sendall("RPRT 0\n".encode("UTF-8"))
            self.blockclass.sendState(False)
          elif not foundCommand:
            print("[doppler] received unknown command: %s" % curCommand)

      self.sock.close()
      self.clientConnected = False
      self.sock = None
      if self.verbose: print("[doppler] Disconnected from: %s:%d" % (addr[0], addr[1]))

    # print("[doppler] Shutting down server.")
    self.server.shutdown(socket.SHUT_RDWR)
    self.server.close()
    self.server = None
   

class doppler(gr.sync_block):
  def __init__(self, gpredict_host, gpredict_port, verbose):
    gr.sync_block.__init__(self, name = "GPredict Doppler", in_sig = None, out_sig = None)
    
    # Init block variables
    self.port = gpredict_port
    self.thread = doppler_runner(self, gpredict_host, gpredict_port, verbose)
    self.thread.start()
    self.message_port_register_out(pmt.intern("freq"))
    self.message_port_register_out(pmt.intern("tx_freq"))
    self.message_port_register_out(pmt.intern("state"))

  def stop(self):
    self.thread.stopThread = True
    
    if self.thread.clientConnected:
      self.thread.sock.close()
    else:
      # Have to force a connection to unblock the accept
      try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("localhost",self.port))
        time.sleep(0.1)
        self.sock.shutdown(socket.SHUT_RDWR)
        s.close()
      except:
        pass
              
    self.thread.join()
        
    return True
    
  def sendFreq(self,freq):
    p = pmt.from_double(freq)
    self.message_port_pub(pmt.intern("freq"),pmt.cons(pmt.intern("freq"),p))
  def sendTxFreq(self,freq):
    p = pmt.from_double(freq)
    self.message_port_pub(pmt.intern("tx_freq"),pmt.cons(pmt.intern("tx_freq"),p))
    
  def sendState(self,state):
    if (state):    
      newState = 1
    else:
      newState = 0
      
    self.message_port_pub(pmt.intern("state"),pmt.cons( pmt.intern("state"), pmt.from_long(newState) ))
