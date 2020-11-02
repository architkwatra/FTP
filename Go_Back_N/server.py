from constants import TYPE_ACK, TYPE_DATA, TYPE_EOF, ACK_PORT, DATA_PAD
import pickle
from random import random
import sys
import os
from socket import socket, AF_INET, SOCK_DGRAM


# def calculate_checksum(data):
#     checksum = 0
#     i = 0
#     while True:
#         if i >= len(data):
#             break
#         firstByte = ord(data[i])
#         secondByte = 0xffff
#         if i+1 < len(data): 
#             secondByte = ord(data[i+1])
#         temp = checksum + (firstByte << 8) + secondByte
#         checksum = (temp & 0xffff) + (temp >> 16)
#         i+=2
#     return (checksum ^ 0xffff)

def calculate_checksum(data, checksum):
    i = 0
    while True:
        if i >= len(data):
            break
        data = str(data)
        firstByte = ord(data[i])
        secondByte = 0xffff
        if i+1 < len(data): 
            secondByte = ord(data[i+1])
        temp = checksum + (firstByte << 8) + secondByte
        checksum = (temp & 0xffff) + (temp >> 16)
        i+=2

    return (checksum^0xffff)

def setSockt(ackPacket, ackInfo):
    ACK_SOCKET = socket(AF_INET, SOCK_DGRAM)
    ACK_SOCKET.sendto(ackPacket, ackInfo)
    return ACK_SOCKET

def sendAcknowledgement(seqNumber, ACK_HOST_NAME):    
    ackInfo = (ACK_HOST_NAME, ACK_PORT)    
    picketData = [seqNumber, DATA_PAD, TYPE_ACK]
    ackPacket = pickle.dumps(picketData)
    ACK_SOCKET = setSockt(ackPacket, ackInfo)
    ACK_SOCKET.close()


def main(PACKET_LOSS_PROB):
    lastRecPckt = -1
    done = False
    while not done:
        receivedData, addr = SERVER_SOCKET.recvfrom(65535)
        ACK_HOST_NAME = addr[0]
        receivedData = pickle.loads(receivedData)
        seqNumber, checksum, packetType, packetData = receivedData
        if packetType == TYPE_DATA:
            if random() >= PACKET_LOSS_PROB:
                if calculate_checksum(packetData, checksum) != 0:
                    print("Packet ", seqNumber, " has been dropped due to improper checksum")
                else:
                    if seqNumber == lastRecPckt+1:
                        sendAcknowledgement(seqNumber+1, ACK_HOST_NAME)
                        lastRecPckt += 1
                        # a Opens a file for appending at the end of the file without 
                        # truncating it. Creates a new file if it does not exist.

                        # b Opens in binary mode.
                        with open(FILE_NAME, 'ab') as file:
                            file.write(packetData)
                    else: sendAcknowledgement(lastRecPckt + 1, ACK_HOST_NAME)
            else:
                print("Packet loss, sequence number = ", seqNumber)
        elif packetType == TYPE_EOF:
            done = True
            SERVER_SOCKET.close()


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Please enter the following details")
        print('1. Server Port 2. File Name 3. MSS Value')
    else:
        SERVER_PORT, FILE_NAME, PACKET_LOSS_PROB = int(sys.argv[1]), sys.argv[2], float(sys.argv[3])
        SERVER_SOCKET = socket(AF_INET, SOCK_DGRAM)
        HOST_NAME = '0.0.0.0'

        SERVER_SOCKET.bind((HOST_NAME, SERVER_PORT))
        if os.path.isfile(FILE_NAME):
            os.remove(FILE_NAME)
        main(PACKET_LOSS_PROB)