from socket import socket, AF_INET, SOCK_DGRAM
import sys
from threading import Thread
import multiprocessing
from multiprocessing import *
from datetime import datetime
from signal import alarm, signal, setitimer, SIGALRM, ITIMER_REAL
import pickle
import collections
from collections import *
from constants import *

SENDER_HOST = SENDER_PORT = ""
maxSequenceNumber = 0
lastAckPacket = -1
BUFFER = {}
timerStart = timerEnd = 0
slidingWindow = set()
lastSentPacket = -1
lock = Lock()
CLIENT_SOCKET = socket(AF_INET, SOCK_DGRAM)
sent = False
EOF_data = ("0", "0", TYPE_EOF, "0")

TYPE_EOF = "1111111111111111"
ACK_HOST = '0.0.0.0'
TYPE_DATA = "0101010101010101"
TYPE_ACK = "1010101010101010"
ACK_PORT = 23000
RTT = 0.1

def shift(num ,nBits, d = "l"):
    if d == "r":
        return (num >> nBits)
    return (num << nBits)

def calculate_checksum(segment):
    checksum = 0
    i = 0
    while True:
        if i >= len(segment):
            break
        firstByte = ord(segment[i])
        secondByte = 0xffff
        if i+1 < len(segment): 
            secondByte = ord(segment[i+1])
        temp = checksum + shift(firstByte, 8) + secondByte
        checksum = (temp & 0xffff) + shift(temp, 16, "r")
        i+=2
    ret = (checksum ^ 0xffff)
    # print(ret)
    return ret

def setAlarmAndTimer():
    alarm(0)
    setitimer(ITIMER_REAL, RTT)
    
def handler(timeout_th, frame):
    global lastAckPacket, SENDER_HOST, SENDER_PORT
    hostInfo = (SENDER_HOST, SENDER_PORT)
    n = len(slidingWindow)
    if lastAckPacket == lastSentPacket - n:
        print("OOPS, TIMEOUT!! sequence number = ", lastAckPacket + 1)
        lock.acquire()
        temp = lastAckPacket+1
        i = temp
        while True:
            if i >= temp+n: 
                break
            setAlarmAndTimer()
            if i in BUFFER:
                CLIENT_SOCKET.sendto(BUFFER[i], hostInfo)
            i += 1
        lock.release()
            
def setSocket():
    ACK_SOCKET = socket(AF_INET, SOCK_DGRAM)
    ACK_SOCKET.bind((ACK_HOST, ACK_PORT))
    return ACK_SOCKET

def deleteAck(lastAckPacket):
    if lastAckPacket in slidingWindow:
        slidingWindow.remove(lastAckPacket)
    if lastAckPacket in BUFFER:
        del BUFFER[lastAckPacket]
    # BUFFER.pop(lastAckPacket)

def getAndPrintTotoalTime(timerStart):
    timerEnd = datetime.now()
    total_time = timerEnd - timerStart
    print("total time = ", total_time) #   total_time

def runThreadProcess(N, SENDER_HOST, SENDER_PORT):
    global EOF_data, lastAckPacket, lastSentPacket, sent, timerEnd, timerStart, slidingWindow, BUFFER
    ACK_SOCKET = setSocket()
    check = True
    hostInfo = (SENDER_HOST, SENDER_PORT)
    while check:
        # recv is a blocking call
        # change 65535 to 4096 for best usage         
        recievedPacket = ACK_SOCKET.recv(4096)
        reply = pickle.loads(recievedPacket)
        if reply[2] == TYPE_ACK:
            # extracting the last packet seq that was delivered successfully
            curAckSeqNum = reply[0] - 1
            if lastAckPacket >= -1:
                lock.acquire()
            
            # End of file
            if curAckSeqNum == maxSequenceNumber:
                temp = pickle.dumps(EOF_data)
                CLIENT_SOCKET.sendto(temp, hostInfo)
                lock.release()
                sent = True
                getAndPrintTotoalTime(timerStart)
                check = False
                break
            
            elif curAckSeqNum > lastAckPacket:
                while lastAckPacket < curAckSeqNum:
                    setAlarmAndTimer()
                    lastAckPacket += 1
                    deleteAck(lastAckPacket)
                    while True:
                        mVal = min(len(BUFFER), N)
                        if mVal <= len(slidingWindow):
                            break
                        if lastSentPacket < maxSequenceNumber:
                            segment = ""
                            key = lastSentPacket+1
                            segment = BUFFER.get(key)
                            CLIENT_SOCKET.sendto(segment, hostInfo)
                            slidingWindow.add(lastSentPacket + 1)
                            lastSentPacket += 1
                        
                        
                lock.release()
            else:
                lock.release()
            
            

            
def rdt_send(N, SENDER_HOST, SENDER_PORT):
    
    global lastSentPacket, lastAckPacket, slidingWindow, BUFFER, timerStart
    hostInfo = (SENDER_HOST, SENDER_PORT)
    timerStart = datetime.now()
    bufferSize = len(BUFFER)

    while len(slidingWindow) < min(bufferSize, N):
        if lastAckPacket == -1:
            packet = BUFFER.get(lastSentPacket + 1)
            CLIENT_SOCKET.sendto(packet, hostInfo)
            setAlarmAndTimer()
            lastSentPacket += 1
            slidingWindow.add(lastSentPacket)

if __name__ == "__main__":

    def dumpPickle(data):
        return pickle.dumps(data)
        
    if len(sys.argv) != 6:
        print("Please input the following as arguments")
        print('1. Server IP address 2. Server Port Number 3. File Name 4. Window Size 5. MSS Value')
    else:
        SENDER_HOST = sys.argv[1]
        SENDER_PORT = int(sys.argv[2])
        FILE_NAME = sys.argv[3] 
        N = int(sys.argv[4])
        MSS = int(sys.argv[5])
        sequenceNumber = 0
        try:
            with open(FILE_NAME, 'rb') as f:
                while True:
                    segment = f.read(MSS)
                    if not segment:
                        break
                    else:
                        maxSequenceNumber = sequenceNumber
                        BUFFER[sequenceNumber] = dumpPickle([sequenceNumber, calculate_checksum(str(segment)), TYPE_DATA, segment])
                        sequenceNumber += 1
        except Exception as e:
            print(e)
            sys.exit("Failed to open file!")

        signal(SIGALRM, handler)
        ack_thread = Thread(target=runThreadProcess, args=(N, SENDER_HOST, SENDER_PORT,))
        ack_thread.start()
        rdt_send(N, SENDER_HOST, SENDER_PORT)
        while not sent:
            # spin
            i = 2

        # Block the calling thread until the process whose join() method is called 
        # terminates or until the optional timeout occurs.
        ack_thread.join()
        CLIENT_SOCKET.close()
