import sys
import argparse
import logging
import socket
import ssl
from thread import *

def validate_port(port):
    if not port:
        print "ERROR: port number is required"
        exit(0)

    if port > 65535 or port < 1025:
        print "ERROR: port number out of proper range"
        exit(0)


def parse_input_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--version', action='version', version='mproxy version 0.1 by Alok Gupta', help='shows app version info')
    parser.add_argument('-n', '--numworker', nargs='?', type=int, default='10', help='number of workers to be used for concurent requests')
    parser.add_argument('-p', '--port', nargs='?', type=int, help='port to connect to')
    parser.add_argument('-t', '--timeout', nargs='?', type=int, default='-1', help='wait time for server response before timing out')
    parser.add_argument('-l', '--log', nargs=1, help='logs to directory')
    args = parser.parse_args()

    print args
    validate_port(args.port)

    return args.port, args.numworker, args.timeout, args.log


def proxy_server(webserver, port, conn, data, addr):
    buffer_size = 4096
    try:

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((webserver, port))
        print "------------------DATA SENT FROM PROXY TO SERVER------------------"
        print data
        s.send(data)
        print "------------------------------------------------------------------"

        while 1:
            # read reply or data to from end web server
            reply = s.recv(buffer_size)
            print "------------------RESPONSE FROM SERVER (need to fwd to client)------------------"
            print reply
            print "--------------------------------------------------------------------------------"
            if(len(reply) > 0):
                conn.send(reply)
                dar = float(len(reply))
                dar = float(dar / 1024)
                dar = "%.3s" % (str(dar))
                dar = "%s KB" % (dar)
                print "Request Done: %s => %s <=" % (str(addr[0]), str(dar))
            else:
                break
        s.close()
        conn.close()
    except socket.error, (value, message):
        s.close()
        conn.close()
        sys.exit(1)


def conn_string(conn, data, addr):
    # Client Browser requests
    try:
        first_line = data.split('\n')[0]
        url = first_line.split(' ')[1]
        http_pos = url.find("://")

        temp = url if http_pos == -1 else url[(http_pos + 3):]
        port_pos = temp.find(":")

        webserver_pos = temp.find("/")
        if webserver_pos == -1:
            webserver_pos = len(temp)
        webserver = ""

        port = -1
        if port_pos == -1 or webserver_pos < port_pos:
            port = 80
            webserver = temp[:webserver_pos]
        else:
            port = int((temp[(port_pos + 1):])[webserver_pos - port_pos - 1])
            webserver = temp[:port_pos]
        print "------------------------------------------------------"
        print "WEBSERVER:", webserver
        print "------------------------------------------------------"

        is_https_request = (first_line.split(' ')[0] == 'CONNECT')

        proxy_server(webserver, port, conn, data, addr)
    except:
        pass

def accept_conn(s):
    buffer_size = 4096
    while True:
        try:
            conn, addr = s.accept()
            data = conn.recv(buffer_size)
            print "------------------DATA FROM CLIENT TO FORWARD TO SERVER------------------"
            print data
            print "-------------------------------------------------------------------------"

            start_new_thread(conn_string, (conn, data, addr))
        except:
            s.close()
            print "Proxy server shutting down...."
            sys.exit(1)

def connect_socket(num_workers, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', port))
        s.listen(num_workers)
        print "Initializing sockets...done"
        print "Sockets binded successfully"
        print "Server started successfully", port
    except:
        print "Unable to initialize socket"
        sys.exit(2)

    accept_conn(s)

def main():
    port, num_workers, timeout, log_dir = parse_input_args()
    connect_socket(num_workers, port)

if __name__ == '__main__':
    main()
