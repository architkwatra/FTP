from random import random
import sys
import os
import pickle
from socket import socket, AF_INET, SOCK_DGRAM

TYPE_DATA = "0101010101010101"
TYPE_ACK  = "0011001100110011"
TYPE_NACK = "1100110011001100"
TYPE_EOF  = "1111111111111111"
DATA_PAD = "0000000000000000"
ACK_PORT = 23000
ACK_HOST = '0.0.0.0'
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
        ackSocket = socket(AF_INET, SOCK_DGRAM)
        ackSocket.sendto(ackPacket,(ACK_HOST_NAME, ACK_PORT))
        ackSocket.close()

    def sendAcknowledgement(self, ackNumber, ACK_HOST_NAME, isNegAck = False):
        typee = TYPE_ACK if not isNegAck else TYPE_NACK
        self.handleSocketFn(pickle.dumps((ackNumber, DATA_PAD, typee)), ACK_HOST_NAME)

    

    def runServer(self, LOSS_PROB, minWindow, maxWindow, BUFFER):
        completed=False
        print("Server Started")
        while not completed:
            recData, addr = SERVER_SOCKET.recvfrom(4096)            
            recData = pickle.loads(recData)
            segementSeqNumber = recData[0]
            checksum = recData[1]
            segmentType = recData[2] 
            segment = recData[3]
            ACK_HOST_NAME = addr[0]
            if segmentType == TYPE_EOF:
                completed = True
                print("File transfer complete, closing server")
                SERVER_SOCKET.close()
            elif segmentType == TYPE_DATA:
                if random()>=LOSS_PROB:
                    if self.calculateChecksum(str(segment), checksum) != 0:
                        print("Packet ", segementSeqNumber, " has been dropped due to improper checksum")
                    else:
                        if segementSeqNumber >= minWindow and segementSeqNumber <= maxWindow:
                            BUFFER[segementSeqNumber] = segment
                            if segementSeqNumber == minWindow:
                                temp = segementSeqNumber
                                while True:
                                    if temp not in BUFFER:
                                        break
                                    else:
                                        minWindow += 1
                                        maxWindow += 1
                                        with open(FILE_NAME, 'ab') as file:
                                            file.write(segment)
                                        BUFFER.pop(temp)
                                        temp += 1
                                self.sendAcknowledgement(temp, ACK_HOST_NAME)
                            else:
                                temp = minWindow
                                while temp <= maxWindow:
                                    if temp not in BUFFER:
                                        self.sendAcknowledgement(temp, ACK_HOST_NAME, True)
                                        temp += 1
                                    else:
                                        break
                        elif segementSeqNumber > maxWindow:
                            temp = minWindow
                            while temp <= maxWindow:
                                self.sendAcknowledgement(temp, ACK_HOST_NAME, True)
                                temp += 1
                else:
                    print("Packet loss, sequence number = ", segementSeqNumber)

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print('Need 4 arguments: 1) Server Port Number 2) File Name 3) probability 4) MSS Value')
    else:
        BUFFER = dict()
        server = Server()
        SERVER_PORT = int(sys.argv[1]) 
        FILE_NAME = sys.argv[2] 
        LOSS_PROB = float(sys.argv[3]) 
        
        minWindow = 0
        maxWindow = int(sys.argv[4])

        SERVER_SOCKET = socket(AF_INET, SOCK_DGRAM)
        

        SERVER_SOCKET.bind((HOST_NAME, SERVER_PORT))
        if os.path.isfile(FILE_NAME):
            os.remove(FILE_NAME)
        
        server.runServer(LOSS_PROB, minWindow, maxWindow, BUFFER)