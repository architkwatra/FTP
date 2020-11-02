
from socket import socket, AF_INET, SOCK_DGRAM
import sys
from threading import Thread
import multiprocessing
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
slidingWindow = set()
lastSentPacket = -1
thread_lock = multiprocessing.Lock()
CLIENT_SOCKET = socket(AF_INET, SOCK_DGRAM)

sent = False
timer_start = timer_end = 0

def calculate_checksum(data):
    checksum = 0
    i = 0
    while True:
        if i >= len(data):
            break
        firstByte = ord(data[i])
        secondByte = 0xffff
        if i+1 < len(data): 
            secondByte = ord(data[i+1])
        temp = checksum + (firstByte << 8) + secondByte
        checksum = (temp & 0xffff) + (temp >> 16)
        i+=2
    return (checksum ^ 0xffff)

def setAlarmAndTimer():
    alarm(0)
    setitimer(ITIMER_REAL, RTT)
    
def handler(timeout_th, frame):
    global lastAckPacket, SENDER_HOST, SENDER_PORT
    senderInfo = (SENDER_HOST, SENDER_PORT)
    n = len(slidingWindow)
    if lastAckPacket == lastSentPacket - n:
        print("Timeout enclountered for sequence number = ", lastAckPacket + 1)
        thread_lock.acquire()
        temp = lastAckPacket+1
        i = temp
        while i < temp+n:
        # for i in range(temp, temp + n):

            # alarm(0)
            # setitimer(ITIMER_REAL, RTT)
            setAlarmAndTimer()

            packet = None
            if i in BUFFER:
                packet = BUFFER[i]
                CLIENT_SOCKET.sendto(packet, senderInfo)
                
            i += 1
        thread_lock.release()
            

def setSocket():
    ACK_SOCKET = socket(AF_INET, SOCK_DGRAM)
    ACK_SOCKET.bind((ACK_HOST, ACK_PORT))
    return ACK_SOCKET


def deleteAck(lastAckPacket):
    slidingWindow.remove(lastAckPacket)
    BUFFER.pop(lastAckPacket)

def ack_process(N, SENDER_HOST, SENDER_PORT):
    global lastAckPacket, lastSentPacket, sent, timer_end, timer_start, slidingWindow, BUFFER
    # ACK_SOCKET = socket(AF_INET, SOCK_DGRAM)
    # ACK_SOCKET.bind((ACK_HOST, ACK_PORT))
    ACK_SOCKET = setSocket()

    while True:
        # recv is a blocking call
        # change 65535 to 4096 for best usage
        recievedPacket = ACK_SOCKET.recv(65535)
        reply = pickle.loads(recievedPacket)
        # sequenceNumber, padding, reply_type = reply
        if reply[2] == TYPE_ACK:
            # extracting the last packet seq that was delivered successfully
            curAckSeqNum = reply[0] - 1
            if lastAckPacket >= 0:
                thread_lock.acquire()
            
            # End of file
            if curAckSeqNum == maxSequenceNumber:
                CLIENT_SOCKET.sendto(pickle.dumps(("0", "0", TYPE_EOF, "0")), (SEND_HOST, SEND_PORT))
                thread_lock.release()
                sent = True
                # timer_end = datetime.now()
                # total_time = datetime.now() - timer_start
                print("total time = ", datetime.now() - timer_start) #   total_time
                break
            
            elif curAckSeqNum > lastAckPacket:
                while lastAckPacket < curAckSeqNum:
                    # alarm(0)
                    # setitimer(ITIMER_REAL, RTT)
                    setAlarmAndTimer()

                    lastAckPacket += 1
                    deleteAck(lastAckPacket)

                    while len(slidingWindow) < min(len(BUFFER), N):
                        if lastSentPacket < maxSequenceNumber:
                            packet = BUFFER.get(lastSentPacket+1)
                            CLIENT_SOCKET.sendto(packet, (SENDER_HOST, SENDER_PORT))
                            slidingWindow.add(lastSentPacket + 1)
                            lastSentPacket += 1
                thread_lock.release()
            else:
                thread_lock.release()

            
def rdt_send(N, SEND_HOST, SEND_PORT):
    global lastSentPacket, lastAckPacket, slidingWindow,client_buffer, t_start

    t_start = datetime.now()
    size_client_buffer = len(BUFFER)

    while len(slidingWindow) < min(size_client_buffer, N):
        if lastAckPacket == -1:
            packet = BUFFER.get(lastSentPacket + 1)
            CLIENT_SOCKET.sendto(packet, (SEND_HOST, SEND_PORT))
            
            # alarm(0)
            # setitimer(ITIMER_REAL, RTT)
            setAlarmAndTimer()

            lastSentPacket += 1
            slidingWindow.add(lastSentPacket)



if __name__ == "__main__":

    sequence_number = 0
    print(sys.argv)
    if len(sys.argv) < 6:
        print("Please enter the following:")
        print("1. Server IP address 2. Server Port Number 3. File Name 4. Window Size 5. MSS Value")

    else:
        SENDER_HOST = sys.argv[1]
        SENDER_PORT = int(sys.argv[2]) 
        FILE_NAME = sys.argv[3] 
        N = int(sys.argv[4]) 
        MSS =  int(sys.argv[5])
        # try:
        # rb mode means read binary mode 
        with open(FILE_NAME, 'rb') as f:
            while True:
                chunk = f.read(MSS)
                if chunk:
                    maxSequenceNumber = sequence_number
                    #get the checksum for the chunk
                    chunk_checksum = calculate_checksum(str(chunk))
                    BUFFER[sequence_number] = pickle.dumps([sequence_number, chunk_checksum, TYPE_DATA, chunk])
                    sequence_number += 1
                break
        # except Exception as e:
        #     print("XXXXXX", e)
        #     sys.exit("Please check the below error")
            

        # handler is a custom handler when the signal is recieved
        # The signal.signal() function allows defining custom handlers to 
        # be executed when a signal is received
        signal(SIGALRM, handler)
        ack_thread = Thread(target=ack_process, args = (N, SENDER_HOST, SENDER_PORT))
        ack_thread.start()
        rdt_send(N, SENDER_HOST,SENDER_PORT)

        while not sent:
            i = 0
            # spinning
        ack_thread.join()
        CLIENT_SOCKET.close()

