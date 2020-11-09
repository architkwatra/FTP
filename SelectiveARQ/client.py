from socket import socket, AF_INET, SOCK_DGRAM
import sys
import pickle
from constants import TYPE_ACK, TYPE_DATA, TYPE_EOF, ACK_HOST, ACK_PORT, RTT, TYPE_NACK
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
ACK_PORT = 65000
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


def shift(num ,nBits, d = "l"):
        if d == "r":
            return (num >> nBits)
        return (num << nBits)

def calculateChecksum(segment):
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

def setSocket():
    ACK_SOCKET = socket(AF_INET, SOCK_DGRAM)
    ACK_SOCKET.bind((ACK_HOST, ACK_PORT))
    return ACK_SOCKET

def getAndPrintTotoalTime(timerStart):
    timerEnd = datetime.now()
    total_time = timerEnd - timerStart
    print("total time = ", total_time) #   total_time

def setAlarmAndTimer():
    alarm(0)
    setitimer(ITIMER_REAL, RTT)

def extractAndSend(isRdtSend = False):
    global lastSentPacket, slidingWindow, BUFFER
    segment = 0
    hostInfo = (SENDER_HOST, SENDER_PORT)
    segment = BUFFER.get(lastSentPacket + 1)
    CLIENT_SOCKET.sendto(segment, hostInfo)
    if isRdtSend:
        setAlarmAndTimer()
    slidingWindow.add(lastSentPacket + 1)
    lastSentPacket += 1

def dumpPickle(data):
    return pickle.dumps(data)

def runThreadProcess(N, SENDER_HOST, SENDER_PORT):
    global lastAckPacket, lastSentPacket, sent, timerEnd, timerStart, slidingWindow, BUFFER
    ACK_SOCKET = setSocket()
    hostInfo = (SENDER_HOST, SENDER_PORT)
    while True:
        received_packet = ACK_SOCKET.recv(65535)
        reply = pickle.loads(received_packet)
        sequence_no, padding, type = reply
        if type == TYPE_ACK:
            currentAckSeqNumber = sequence_no - 1
            print ("Received ACK, sequence number = " + str(currentAckSeqNumber))
            if lastAckPacket >= -1:
                thread_lock.acquire()
                if currentAckSeqNumber == maxSeqNumber:
                    temp = pickle.dumps(EOF_data)
                    CLIENT_SOCKET.sendto(temp, hostInfo)
                    thread_lock.release()
                    sent = True
                    getAndPrintTotoalTime(timerStart)
                    break
                elif currentAckSeqNumber > lastAckPacket:
                    while lastAckPacket < currentAckSeqNumber:
                        setAlarmAndTimer()
                        lastAckPacket = lastAckPacket + 1
                        slidingWindow.remove(lastAckPacket)
                        BUFFER.pop(lastAckPacket)
                        while len(slidingWindow) < min(len(BUFFER), N):
                            if lastSentPacket < maxSeqNumber:
                                extractAndSend(True)
                    thread_lock.release()
                else:
                    thread_lock.release()

        elif type == TYPE_NACK:
            thread_lock.acquire()
            current_nack_seq_number = sequence_no
            print("Received NACK, sequence number = ", current_nack_seq_number)
            if current_nack_seq_number == lastAckPacket + 1:
                setAlarmAndTimer()
            packet = BUFFER.get(current_nack_seq_number)
            CLIENT_SOCKET.sendto(packet, (SENDER_HOST, SENDER_PORT))
            thread_lock.release()


def rdt_send(N, SENDER_HOST, SENDER_PORT):
    global lastSentPacket, lastAckPacket, slidingWindow,BUFFER, timerStart
    timerStart = datetime.now()
    size_BUFFER = len(BUFFER)
    while len(slidingWindow) < min(size_BUFFER, N):
        if lastAckPacket == -1:
            extractAndSend(True)


def handler(timeout_th, frame):
    global lastAckPacket
    n = len(slidingWindow)
    if lastAckPacket == lastSentPacket - n:
        print("Timeout, sequence number = " + str(lastAckPacket + 1))
        thread_lock.acquire()
        setAlarmAndTimer()
        packet = BUFFER.get(lastAckPacket + 1)
        CLIENT_SOCKET.sendto(packet, (SENDER_HOST, SENDER_PORT))
        thread_lock.release()



if __name__ == "__main__":
    if len(sys.argv) < 6:
        print('Need 5 arguments: 1) Server IP address 2) Server Port Number 3) File Name 4) Window Size 5) MSS Value')
    else:
        SENDER_HOST, SENDER_PORT, FILE_NAME, N, MSS = sys.argv[1], int(sys.argv[2]), sys.argv[3], int(sys.argv[4]), int(
            sys.argv[5])

        sequence_number = 0
        try:
            with open(FILE_NAME, 'rb') as f:
                while True:
                    chunk = f.read(MSS)
                    if chunk:
                        maxSeqNumber = sequence_number
                        chunk_checksum = calculateChecksum(str(chunk))
                        BUFFER[sequence_number] = pickle.dumps(
                            [sequence_number, chunk_checksum, TYPE_DATA, chunk])
                        sequence_number += 1
                    else:
                        break
        except Exception as e:
            print(e)
            sys.exit("Failed to open file!")

        signal(SIGALRM, handler)
        ack_thread = Thread(target=runThreadProcess, args=(N, SENDER_HOST, SENDER_PORT,))
        ack_thread.start()
        rdt_send(N, SENDER_HOST, SENDER_PORT)
        while True:
            if sent:
                break
        ack_thread.join()
        CLIENT_SOCKET.close()