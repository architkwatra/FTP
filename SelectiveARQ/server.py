from random import random
import sys
import os
import pickle
from socket import socket, AF_INET, SOCK_DGRAM

TYPE_DATA = "0101010101010101"
FIRST_SEQ = 0
TYPE_ACK  = "0011001100110011"
TYPE_NACK = "1100110011001100"
NACK_TYPE = ""
TYPE_EOF  = "1111111111111111"
DATA_PAD = "0000000000000000"
ACK_PORT = 23000
PORT_INFO = ""
ACK_PACKET_HOST = '0.0.0.0'
HOST_NAME = '0.0.0.0'

class Server:

    def shift(self, num ,nBits, d = "l"):
        if d == "r":
            return (num >> nBits)
        return (num << nBits)

    def calculateChecksum(self, segment, checksum):
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

    def handleSocketFn(self, ackPacket, ACK_HOST_NAME):
        global ACK_PORT
        try:
            while True:
                # print(ackPacket, ACK_HOST_NAME)
                ackSocket = socket(AF_INET, SOCK_DGRAM)
                ackSocket.sendto(ackPacket,(ACK_HOST_NAME, ACK_PORT))
                ackSocket.close() 
                break
        except Exception as e:
            print(e)

    def sendAcknowledgement(self, ackNumber, ACK_HOST_NAME, isNegAck = False):
        try:
            typee = TYPE_ACK if not isNegAck else TYPE_NACK
            self.handleSocketFn(pickle.dumps((ackNumber, DATA_PAD, typee)), ACK_HOST_NAME)
        except Exception as e:
            print(e)

    def runServer(self, LOSS_PROB, BUFFER, minWindow, maxWindow):
        try:
            done = False
            print("Server Started")
            while not done:
                d = SERVER_SOCKET.recvfrom(4096)            
                recData = d[0]
                addr = d[1] 
                recData = pickle.loads(recData)
                segementSeqNumber = recData[0]
                checksum = recData[1]
                segmentType = recData[2] 
                segment = recData[3]
                ACK_HOST_NAME = addr[0]
                if segmentType == TYPE_EOF:
                    done = True if not done else False
                    print("File transfer complete, closing server")
                    SERVER_SOCKET.close()
                elif segmentType == TYPE_DATA:
                    randomNumber = random()
                    if 0 <= randomNumber <= 1.0:
                        if randomNumber >= LOSS_PROB:
                            totalCheckSum = self.calculateChecksum(str(segment), checksum)
                            if totalCheckSum != 0:
                                print("Packet has been dropped due to improper checksum with sequence number = ", segementSeqNumber)
                            else:
                                inc = 1
                                if segementSeqNumber >= minWindow and segementSeqNumber <= maxWindow:
                                    BUFFER[segementSeqNumber] = segment if BUFFER else None
                                    if segementSeqNumber == minWindow:
                                        temp = segementSeqNumber
                                        while temp in BUFFER:
                                            with open(FILE_NAME, 'ab') as file:
                                                file.write(segment)
                                            minWindow += inc
                                            j = 0
                                            for i in range(temp):
                                                # print(maxWindow)
                                                j += inc
                                            maxWindow += 1
                                            if len(BUFFER) > 0:
                                                BUFFER.pop(temp)
                                            temp += inc

                                            if temp not in BUFFER:
                                                inc = 0
                                                break

                                        self.sendAcknowledgement(temp, ACK_HOST_NAME)
                                    else:
                                        temp = minWindow
                                        while True:
                                            if temp > maxWindow: break
                                            if temp not in BUFFER:
                                                self.sendAcknowledgement(temp, ACK_HOST_NAME, True)
                                                temp += 1
                                            else:
                                                for i in range(temp):
                                                    # print(maxWindow)
                                                    i = 0
                                                break
                                elif segementSeqNumber > maxWindow:
                                    temp = minWindow
                                    inc = 1
                                    while True:
                                        if temp > maxWindow: break
                                        self.sendAcknowledgement(temp, ACK_HOST_NAME, True)
                                        temp += inc
                                        for i in range(temp):
                                            # print(maxWindow)
                                            i = 0
                        else:
                            print("Packet loss, sequence number = ", segementSeqNumber)
                    else:
                        print("random number generation issue")
        
        except Exception as e:
            print(e)

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print('Need 4 arguments: 1) Server Port Number 2) File Name 3) probability 4) MSS Value')
    else:
        def setSocket():
            SERVER_SOCKET = socket(AF_INET, SOCK_DGRAM)
            SERVER_SOCKET.bind((HOST_NAME, SERVER_PORT))
            return SERVER_SOCKET
        def checkForFile(name):
            if os.path.isfile(name):
                os.remove(name)

        BUFFER = dict()
        server = Server()
        SERVER_PORT = int(sys.argv[1]) 
        FILE_NAME = sys.argv[2] 
        LOSS_PROB = float(sys.argv[3]) 
        minWindow = 0
        maxWindow = int(sys.argv[4])
        SERVER_SOCKET = setSocket()
        checkForFile(FILE_NAME)
        server.runServer(LOSS_PROB, BUFFER, minWindow, maxWindow)