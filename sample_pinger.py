import os
import sys
import struct
import time
import select
import socket
import binascii

ICMP_ECHO_REQUEST = 8

def checksum(str):
    csum = 0
    countTo = (len(str) / 2) * 2

    count = 0
    while count < countTo:
        thisVal = ord(str[count+1]) * 256 + ord(str[count])
        csum = csum + thisVal
        csum = csum & 0xffffffff
        count = count + 2

    if countTo < len(str):
        csum = csum + ord(str[len(str) - 1])
        csum = csum & 0xffffffff

    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer

def receiveOnePing(mySocket, ID, timeout, destAddr): # Done
    global rtt_min, rtt_max, rtt_sum, rtt_cnt
    timeLeft = timeout
    while 1:
        startedSelect = time.time()
        whatReady = select.select([mySocket], [], [], timeLeft)
        howLongInSelect = (time.time() - startedSelect)
        if whatReady[0] == []: # Timeout
            return "Request timed out."

        timeReceived = time.time()
        recPacket, addr = mySocket.recvfrom(1024)

        #Fill in start
        #Fetch the ICMP header from the IP packet
        header = recPacket[20:28]
        type, code, checksum, pID, sequence = struct.unpack('bbHHh', header)
        if(pID == ID):
            return timeReceived - startedSelect
        #Fill in end
        timeLeft = timeLeft - howLongInSelect
        if timeLeft <= 0:
            return "Request timed out."

def sendOnePing(mySocket, destAddr, ID):
    # Header is type (8), code (8), checksum (16), id (16), sequence (16)

    myChecksum = 0
    # Make a dummy header with a 0 checksum.
    # struct -- Interpret strings as packed binary data
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    data = struct.pack("d", time.time())
    # Calculate the checksum on the data and the dummy header.
    myChecksum = checksum(header + data)

    # Get the right checksum, and put in the header
    if sys.platform == 'darwin':
        myChecksum = socket.htons(myChecksum) & 0xffff
        #Convert 16-bit integers from host to network byte order.
    else:
        myChecksum = socket.htons(myChecksum)

    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    packet = header + data

    mySocket.sendto(packet, (destAddr, 1)) # AF_INET address must be tuple, not str
    #Both LISTS and TUPLES consist of a number of objects
    #which can be referenced by their position number within the object

def doOnePing(destAddr, timeout): #Done?
    icmp = socket.getprotobyname("icmp")
    #SOCK_RAW is a powerful socket type. For more details see: http://sock-raw.org/papers/sock_raw
    
    #Fill in start

    #Create Socket here
    try:
        mySocket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
    except socket.error as e:
        raise
    #Fill in end
    try:
        host = socket.gethostbyname(destAddr)
    except socket.gaierror:
        raise

    myID = os.getpid() & 0xFFFF #Return the current process i
    sendOnePing(mySocket, destAddr, myID)
    delay = receiveOnePing(mySocket, myID, timeout, destAddr)

    mySocket.close()
    return delay

def ping(host, timeout=1):
    global rtt_min, rtt_max, rtt_sum, rtt_cnt
    rtt_min = float('+inf')
    rtt_max = float('-inf')
    rtt_sum = 0
    rtt_cnt = 0
    cnt = 0
    #timeout=1 means: If one second goes by without a reply from the server,
    #the client assumes that either the client's ping or the server's pong is lost
    dest = socket.gethostbyname(host)
    print("Pinging " + dest + " using Python:")
    #Send ping requests to a server separated by approximately one second
    try:
        while True:
            cnt += 1
            print(doOnePing(dest, timeout))
            time.sleep(1)
    except KeyboardInterrupt:
        if cnt != 0:
            print('--- {} ping statistics ---'.format(host))
            print('{} packets transmitted, {} packets received, {:.1f}% packet loss'.format(cnt, rtt_cnt, 100.0 - rtt_cnt * 100.0 / cnt))
            if rtt_cnt != 0:
                print('round-trip min/avg/max {:.3f}/{:.3f}/{:.3f} ms'.format(rtt_min, rtt_sum / rtt_cnt, rtt_max))

if __name__ == '__main__':
    ##ping('127.0.0.1') # Sending packets to local host 127.0.0.1
    ping('stonybrook.edu') # Sending packets to stonybrook.edu
    ping('google.com') # North America
    ping('http://global.gmarket.co.kr/Home/Main') # Asia
    ping('https://mechboards.co.uk/') # Europe
    ping('https://www.bcb.gov.br/en') # South America

