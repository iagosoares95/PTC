# -*- coding: utf-8 -*-

import enlace
import arq
from enum import Enum
import time 
import random

class Session:

    def __init__(self,arq,timeout):
        self.States=Enum('States', 'disc hand1 hand2 con check half1 half2')
        self.states=self.States.disc
        self.arq=arq
        self.timeout=timeout
        self.max_no_resp=3
        self.send_data=bytearray()
        self.proto=b'\xff'
        self.CR=b'\x00'
        self.CC=b'\x01'
        self.CA=b'\x07'
        self.DR=b'\x04'
        self.DC=b'\x05'
        self.received_data=bytearray()
        self.begin_conex=False
        self.send_time=time.time()

    def start(self):
        if(not(self.states in [self.States.disc,self.States.disc,self.States.disc]) and (self.begin_conex==True)):
            return
        self.states=self.States.disc
        self.begin_conex=True
        self.handle()

    def ends(self):
        print('Iniciando desconexão')
        self.send_DR()
        self.estado=self.States.half1
        while(True):
            if(self.handle()==True):
                self.states=self.States.disc
                return bytearray()

    def send(self,data):
        if(self.state()!="con"):
            #self.start()
            return
        self.send_data=bytearray()
        self.send_data=b'\x00'+data
        while(True):
            if(self.handle()==False):
                return
            else:
                return self.ends()

    def receive(self):
        print('Estado da sessão:',self.states)
        self.received_data=self.arq.receive()
        if(self.handle()==False):
            data=self.received_data
            self.received_data=bytearray()
            return data
        else:
            return bytearray()

    def timeout_func(self):
        if(self.states==self.States.hand1):
            time_diff=time.time()-self.send_time
            if(time_diff>self.timeout):
                self.send_CR()
        if(self.states==self.States.hand2):
            time_diff=time.time()-self.send_time
            if(time_diff>self.timeout):
                self.states=self.States.disc
                self.begin_conex=False
        if(self.states in[self.States.half1, self.States.half2]):
            time_diff=time.time()-self.send_time
            if(time_diff>self.timeout):
                self.send_DR()

    def send_CR(self):
        self.send_data=bytearray()
        self.send_data=self.send_data+self.proto+self.CR
        self.arq.send(self.send_data)
        self.send_time=time.time()
        print("Requisição de conexão enviada:",self.send_data)

    def send_DR(self):
        self.send_data=bytearray()
        self.send_data=self.proto+self.DR
        self.arq.send(self.send_data)
        self.send_time=time.time()

    def disc_func(self):
        data=self.arq.receive()
        if(data!=bytearray()):
            return self.states.hand2
        if(self.begin_conex==True):
            print('Iniciando conexão')
            self.send_CR()
            self.send_time=time.time()
            return self.States.hand1
        else:
            if((self.received_data[1:2]==self.CC[0:1]) and (self.received_data[2:3]==self.proto[0:1])):
                print('Recebeu um CR')
                self.send_data=bytearray()
                self.send_data=self.CC+self.proto
                self.arq.send(self.send_data)
                return self.States.hand2
            return self.States.disc

    def hand1_func(self):
        if((self.received_data[2:3]==self.CC[0:1]) and (self.received_data[2:3]==self.proto[0:1])):
            print('Conexão estabelecida, CC recebido')
            self.send_data=bytearray()
            self.send_data=self.CA+self.proto
            self.arq.send(self.send_data)
            return self.States.con
        return self.States.hand1

    def hand2_func(self):
        if((self.received_data[1:2]==self.CA) and (self.received_data[2:3]==self.proto)):
            print('Conexão estabelecida, CA recebido')
            return self.States.con
        return self.States.hand2

    def con_func(self):
        if(self.send_data!=bytearray()):
            self.arq.send(self.send_data)
            self.send_data=bytearray()
            return self.States.con
        if((self.received_data[1:2]==self.DR) and (self.received_data[2:3]==self.proto)):
            print('Pedido de desconexão, DR recebido')
            self.send_DR()
            return self.States.half2
        return self.States.con

    def half1_func(self):
        if((self.received_data[1:2]==self.DR) and (self.received_data[2:3]==self.proto)):
            print('Pedido de desconexão, DR recebido, enviando DC')
            self.send_data=bytearray()
            self.send_data=self.DC+self.proto
            self.arq.send(self.send_data)
            return self.States.disc
        return self.States.half1

    def half2_func(self):
        if((self.received_data[1:2]==self.DC) and (self.received_data[2:3]==self.proto)):
            print('Sessão finalizada')
            return self.States.disc
        return self.States.half2

    def handle(self):
        if(self.states==self.States.disc):
            self.states=self.disc_func()
            return False
        if(self.states==self.States.hand1):
            self.states=self.hand1_func()
            return False
        if(self.states==self.States.hand2):
            self.states=self.hand2_func()
            return False
        if(self.states==self.States.con):
            self.states=self.con_func()
            return False
        if(self.states==self.States.half1):
            self.states=self.half1_func()
            if(self.states==self.States.disc):
                return True
            return False
        if(self.states==self.States.half2):
            self.states=self.half2_func()
            if(self.states==self.States.disc):
                return True
            return False
    
    def state(self):
        return self.states
