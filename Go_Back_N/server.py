import pickle
from random import random
import sys
import os
from socket import socket, AF_INET, SOCK_DGRAM

TYPE_DATA = "0101010101010101"
TYPE_EOF = "1111111111111111"
ACK_HOST = '0.0.0.0'
TYPE_ACK = "1010101010101010"
ACK_PORT = 23000
DATA_PAD = "0000000000000000"

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

    def setSockt(self, ackPacket, ackInfo):
        ACK_SOCKET = socket(AF_INET, SOCK_DGRAM)
        ACK_SOCKET.sendto(ackPacket, ackInfo)
        return ACK_SOCKET

    def getPickledData(self, ACK_HOST_NAME, seqNumber):
        ackInfo = (ACK_HOST_NAME, ACK_PORT)    
        segmentData = [seqNumber, DATA_PAD, TYPE_ACK]
        return (pickle.dumps(segmentData), ackInfo)


    def sendAcknowledgement(self, seqNumber, ACK_HOST_NAME):    
        data = self.getPickledData(ACK_HOST_NAME, seqNumber)
        ACK_SOCKET = self.setSockt(data[0], data[1])
        ACK_SOCKET.close()


    def runServer(self, PACKET_LOSS_PROB):
        lastRecPckt = -1
        done = False
        print("Server started")
        while not done:
            receivedData, addr = SERVER_SOCKET.recvfrom(4096)
            ACK_HOST_NAME = addr[0]
            receivedData = pickle.loads(receivedData)
            seqNumber, checksum, packetType, packetData = receivedData

            if packetType == TYPE_EOF:
                done = True
                print("File transfer complete, closing the connection")
                SERVER_SOCKET.close()
            elif packetType == TYPE_DATA:
                randomNumber = random()
                if randomNumber >= PACKET_LOSS_PROB:
                    authChecksum = self.calculateChecksum(str(packetData), checksum)
                    if authChecksum == 0:
                        if seqNumber == lastRecPckt+1:
                            self.sendAcknowledgement(seqNumber+1, ACK_HOST_NAME)
                            lastRecPckt += 1
                            # a Opens a file for appending at the end of the file without 
                            # truncating it. Creates a new file if it does not exist.
                            # b Opens in binary mode.
                            with open(FILE_NAME, 'ab') as file:
                                file.write(packetData)
                        else: 
                            self.sendAcknowledgement(lastRecPckt + 1, ACK_HOST_NAME)
                    else:
                        print("Packet has been dropped due to improper checksum with seq no = ", seqNumber)
                else:
                    print("Packet loss, sequence number = ", seqNumber)


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Please enter the following details")
        print('1. Server Port 2. File Name 3. Loss probability')
    else:
        SERVER_PORT = int(sys.argv[1])
        FILE_NAME = sys.argv[2]
        server = Server()
        SERVER_SOCKET = socket(AF_INET, SOCK_DGRAM)
        HOST_NAME = '0.0.0.0'
        SERVER_SOCKET.bind((HOST_NAME, SERVER_PORT))
        if os.path.isfile(FILE_NAME):
            os.remove(FILE_NAME)
        server.runServer(float(sys.argv[3]))