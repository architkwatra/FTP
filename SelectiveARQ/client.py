from socket import socket, AF_INET, SOCK_DGRAM
import sys
import pickle
# from constants import TYPE_ACK, TYPE_DATA, TYPE_EOF, ACK_HOST, ACK_PORT, RTT, TYPE_NACK
from signal import alarm, setitimer, SIGALRM, signal, ITIMER_REAL
from threading import Thread
import multiprocessing
from datetime import datetime
import collections
from collections import *

maxSeqNumber = 0
lastAckPacket = -1
lastSentPacket = -1

SENDER_HOST = ''
SENDER_PORT = ''


TYPE_DATA = "0101010101010101"
TYPE_ACK  = "0011001100110011"
TYPE_NACK = "1100110011001100"
TYPE_EOF  = "1111111111111111"
ACK_PORT = 23000
ACK_HOST = '0.0.0.0'
RTT = 0.1
EOF_data = ["0", "0", TYPE_EOF, "0"]


thread_lock = multiprocessing.Lock()
slidingWindow = set()
BUFFER = dict()
CLIENT_SOCKET = socket(AF_INET, SOCK_DGRAM)


sent = False
timerStart = 0
timerEnd = 0

class Client:
    def shift(self, num ,nBits, d = "l"):
            if d == "r":
                return (num >> nBits)
            return (num << nBits)

    def calculateChecksum(self, segment):
        checksum = 0
        i = 0
        while True:
            if i >= len(segment):
                break
            firstByte = ord(segment[i])
            secondByte = 0xffff
            if i+1 < len(segment): 
                secondByte = ord(segment[i+1])
            temp = checksum + self.shift(firstByte, 8) + secondByte
            checksum = (temp & 0xffff) + self.shift(temp, 16, "r")
            i+=2
        ret = (checksum ^ 0xffff)
        # print(ret)
        return ret

    def setSocket(self, ):
        ACK_SOCKET = socket(AF_INET, SOCK_DGRAM)
        ACK_SOCKET.bind((ACK_HOST, ACK_PORT))
        return ACK_SOCKET

    def getAndPrintTotoalTime(self, timerStart):
        timerEnd = datetime.now()
        total_time = timerEnd - timerStart
        print("total time = ", total_time) #   total_time

    def setAlarmAndTimer(self, ):
        alarm(0)
        setitimer(ITIMER_REAL, RTT)

    def extractAndSend(self, isRdtSend = False):
        global lastSentPacket, slidingWindow, BUFFER
        segment = 0
        hostInfo = (SENDER_HOST, SENDER_PORT)
        segment = BUFFER.get(lastSentPacket + 1)
        CLIENT_SOCKET.sendto(segment, hostInfo)
        if isRdtSend:
            self.setAlarmAndTimer()
        slidingWindow.add(lastSentPacket + 1)
        lastSentPacket += 1

    def dumpPickle(self, data):
        return pickle.dumps(data)

    def runThreadProcess(self, N, SENDER_HOST, SENDER_PORT):
        global lastAckPacket, lastSentPacket, sent, timerEnd, timerStart, slidingWindow, BUFFER
        ACK_SOCKET = self.setSocket()
        hostInfo = (SENDER_HOST, SENDER_PORT)
        while True:
            received_packet = ACK_SOCKET.recv(4096)
            reply = pickle.loads(received_packet)
            sequence_no, padding, type = reply
            if type == TYPE_ACK:
                currentAckSeqNumber = reply[0] - 1
                if lastAckPacket >= -1:
                    thread_lock.acquire()
                    if currentAckSeqNumber == maxSeqNumber:
                        temp = self.dumpPickle(EOF_data)
                        CLIENT_SOCKET.sendto(temp, hostInfo)
                        thread_lock.release()
                        sent = True
                        self.getAndPrintTotoalTime(timerStart)
                        break
                    elif currentAckSeqNumber > lastAckPacket:
                        while lastAckPacket < currentAckSeqNumber:
                            self.setAlarmAndTimer()
                            lastAckPacket = lastAckPacket + 1
                            slidingWindow.remove(lastAckPacket)
                            BUFFER.pop(lastAckPacket)
                            while len(slidingWindow) < min(len(BUFFER), N):
                                if lastSentPacket < maxSeqNumber:
                                    self.extractAndSend(True)
                        thread_lock.release()
                    else:
                        thread_lock.release()

            elif type == TYPE_NACK:
                thread_lock.acquire()
                nackSeqNumber = reply[0]
                temp = lastAckPacket + 1
                if nackSeqNumber == temp:
                    self.setAlarmAndTimer()
                packet = BUFFER.get(nackSeqNumber)
                CLIENT_SOCKET.sendto(packet, hostInfo)
                thread_lock.release()


    def rdt_send(self, N, SENDER_HOST, SENDER_PORT):
        global lastSentPacket, lastAckPacket, slidingWindow,BUFFER, timerStart
        buffSize = len(BUFFER)
        timerStart = datetime.now()
        l = min(buffSize, N)
        while len(slidingWindow) < l:
            if lastAckPacket == -1:
                self.extractAndSend(True)

    def handler(self, timeout_th, frame):
        global lastAckPacket
        hostInfo = (SENDER_HOST, SENDER_PORT)
        n = len(slidingWindow)
        diff = lastSentPacket - n
        if lastAckPacket == diff:
            print("Timeout, sequence number = ", lastAckPacket + 1)
            thread_lock.acquire()
            self.setAlarmAndTimer()
            key = lastAckPacket + 1
            packet = BUFFER.get(key)
            CLIENT_SOCKET.sendto(packet, hostInfo)
            thread_lock.release()


if __name__ == "__main__":
    if len(sys.argv) < 6:
        print('Need 5 arguments: 1) Server IP address 2) Server Port Number 3) File Name 4) Window Size 5) MSS Value')
    else:
        SENDER_HOST = sys.argv[1] 
        SENDER_PORT = int(sys.argv[2]) 
        FILE_NAME = sys.argv[3] 
        N = int(sys.argv[4])
        MSS = int(sys.argv[5])

        client = Client()

        sequenceNumber = 0
        try:
            with open(FILE_NAME, 'rb') as f:
                while True:
                    chunk = f.read(MSS)
                    if chunk:
                        maxSeqNumber = sequenceNumber
                        chunk_checksum = client.calculateChecksum(str(chunk))
                        data = [sequenceNumber, chunk_checksum, TYPE_DATA, chunk]
                        BUFFER[sequenceNumber] = client.dumpPickle(data)
                        sequenceNumber += 1
                    else:
                        break
        except Exception as e:
            print(e)
            sys.exit("Failed to open file!")

        signal(SIGALRM, client.handler)
        args = (N, SENDER_HOST, SENDER_PORT,)
        ack_thread = Thread(target = client.runThreadProcess, args = args)
        ack_thread.start()
        client.rdt_send(N, SENDER_HOST, SENDER_PORT)
        while True:
            if sent:
                break
        ack_thread.join()
        CLIENT_SOCKET.close()