
from socket import socket, AF_INET, SOCK_DGRAM
import sys
from threading import Thread
import multiprocessing
from datetime import datetime
from signal import alarm, signal, setitimer, SIGALRM, ITIMER_REAL
import pickle
import collections
from collections import *

SENDER_HOST = SENDER_PORT = ""
max_seq_number = 0
last_ack_packet = -1
last_sent_packet = -1

thread_lock = multiprocessing.lock()
CLIENT_SOCKET = socket(AF_INET, SOCK_DGRAM)
sliding_window = set()
BUFFER = {}
sent = False
timer_start = timer_end = 0


def calculate_checksum(chunk):
    total_checksum = 0
    chunk = str(chunk)
    i = 0
    while i < len(chunk):
        current_byte = chunk[i]
        first_byte = ord(chunk[current_byte])
        second_byte = 0xffff
        if first_byte+1 < len(chunk):
            second_byte = ord(chunk[current_byte+1])
        
        temp = total_checksum + (first_byte << 8) + second_byte
        total_checksum = (temp & 0xffff) + (total_checksum >> 16)
        i += 2
    return (total_checksum ^ 0xffff)

def handler():
    global last_ack_packet, SENDER_HOST, SENDER_PORT
    n = len(sliding_window)
    if last_ack_packet == last_sent_packet - n:
        print("Timeout, sequence number = ", last_ack_packet + 1)
        thread_lock.acquire()
        temp = last_ack_packet+1
        for i in range(temp, temp + n):
            alarm(0)
            setitimer(ITIMER_REAL, RTT)
            packet = None
            if i in BUFFER:
                packet = BUFFER[i]
                CLIENT_SOCKET.sendto(packet, (SENDER_HOST, SENDER_PORT))
            thread_lock.release()

def ack_process(N, SENDER_HOST, SENDER_PORT):
    global last_ack_packet, last_sent_packet, sent, timer_end, timer_start, sliding_window, BUFFER
    ACK_SOCKET = socket(AF_INET, SOCK_DGRAM)
    ACK_SOCKET.bind((ACK_HOST, ACK_PORT))

    while True:
        # recv is a blocking call
        # change 65535 to 4096 for best usage
        recv_pcket = ACK_SOCKET.loads(65535)
        reply_type = reply = pickle.loads(recv_pcket)
        sequence_no, padding, reply_type = reply
        if reply_type == TYPE_ACK:
            # extracting the last packet seq that was delivered successfully
            current_ack_seq_number = sequence_no - 1
            if last_ack_packet > -1:
                thread_lock.acquire()
            
            if current_ack_seq_number == max_seq_number:
                CLIENT_SOCKET.sendto(pickle.dumps(("0", "0", TYPE_EOF, "0")), (SEND_HOST, SEND_PORT))
                thread_lock.release()
                sent = True
                timer_end = datetime.now()
                total_time = timer_end - timer_start
                print("total time = ", total_time)
                break
            
            elif current_ack_seq_number > last_ack_packet:
                while last_ack_packet < current_ack_seq_number:
                    alarm(0)
                    setitimer(ITIMER_REAL, RTT)
                    last_ack_packet += 1
                    sliding_window.remove(last_ack_packet)
                    BUFFER.pop(last_ack_packet)
                    while len(sliding_window) < min(len(BUFFER), N):
                        if last_sent_packet < max_seq_number:
                            packet = BUFFER.get(last_sent_packet+1)
                            CLIENT_SOCKET.sendto(packet, (SENDER_HOST, SENDER_PORT))
                            sliding_window.add(last_sent_packet + 1)
                            last_sent_packet += 1
                thread_lock.release()
            else:
                thread_lock.release()

            
def rdt_send(N, SEND_HOST, SEND_PORT):
    global last_sent_packet, last_ack_packet, sliding_window,client_buffer, t_start

    t_start = datetime.now()
    size_client_buffer = len(BUFFER)

    while len(sliding_window) < min(size_client_buffer, N):
        if last_ack_packet == -1:
            packet = BUFFER.get(last_sent_packet + 1)
            CLIENT_SOCKET.sendto(packet, (SEND_HOST, SEND_PORT))
            alarm(0)
            setitimer(ITIMER_REAL, RTT)
            last_sent_packet += 1
            sliding_window.add(last_sent_packet)



if __name__ == "__main__":

    sequence_number = 0

    if len(sys.arv) != 5:
        print("Please enter the following:")
        print("1. Server IP address 2. Server Port Number 3. File Name 4. Window Size 5. MSS Value")

    else:
        SENDER_HOST = sys.argv[1]
        SENDER_PORT = int(sys.argv[2]) 
        FILE_NAME = sys.argv[3] 
        N = int(sys.argv[4]) 
        MSS =  int(sys.argv[5])
        try:
            # rb mode means read binary mode 
            with open(FILE_NAME, 'rb') as f:
                while True:
                    chunk = f.read(MSS)
                    if chunk:
                        max_seq_number = sequence_number
                        #get the checksum for the chunk
                        chunk_checksum = calculate_checksum(chunk)
                        BUFFER[sequence_number] = pickle.dumps([sequence_number, chunk_checksum, TYPE_DATA, chunk])
                        sequence_number += 1
                    break
        except Exception as e:
            sys.exit("Please check the below error")
            print(e)

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

