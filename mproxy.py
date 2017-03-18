import sys
import argparse
import logging
import socket
import ssl
from thread import *
import pdb

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
    parser.add_argument('-l', '--log', nargs='?', default=None, const=os.getcwd(), help='logs all requests and responses')
    args = parser.parse_args()

    print args
    validate_port(args.port)

    logdir = args.log

    if logdir:
        if not os.path.exists(logdir):
            try:
                os.makedirs(logdir)
            except OSError as ex:
                if ex.errno != errno.EEXIST:
                    raise
        if not logdir.endswith("/"):
            logdir = logdir + "/"
    if not os.path.exists(CERTS_DIR):
        try:
            os.makedirs(CERTS_DIR)
        except OSError as ex:
            if ex.errno != errno.EEXIST:
                raise

    return args.port, args.numworker, args.timeout, logdir


def proxy_server(webserver, port, conn, data, addr):
    buffer_size = 4096
    try:

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((webserver, port))
        print "------------------DATA SENT FROM PROXY TO SERVER------------------"
        print data
        s.send(data)

        while 1:
            # read reply or data to from end web server
            reply = s.recv(buffer_size)
            print "------------------RESPONSE FROM SERVER (need to fwd to client)------------------"
            print reply
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

def is_ssl_req(data):
    first_line = data.split('\n')[0]
    return (first_line.split(' ')[0] == 'CONNECT')

def replace_with_proper_url(url, webserver):
    if "http://" in url:
        url = url[7:]

    if webserver in url:
        url = url[len(webserver):]

    return url

def sanitize_data(data, webserver):
    data_arr = data.split('\n')

    # Replace first line with route, not full domain
    first_line = data_arr[0].split(" ")
    first_line[1] = replace_with_proper_url(first_line[1], webserver)
    first_line_str = " ".join(first_line)
    data_arr[0] = first_line_str

    # Remove keep alive connection, replace with close connection
    conn_keep_alive_ind = data_arr.index("Connection: keep-alive\r")
    if conn_keep_alive_ind is not -1:
        data_arr[conn_keep_alive_ind] = "Connection: close\r"

    # Remove encoding
    accept_enc_index = [idx for idx, s in enumerate(data_arr) if 'Accept-Encoding:' in s][0]
    data_arr.pop(accept_enc_index)

    # Done sanitizing!

    # print "-----------------------------data before:-----------------------------------"
    # print data
    data = ""
    data = "\n".join(data_arr)

    # print "-------------------------------data after:----------------------------------"
    # print data
    return data

def https_proxy_server(port, conn, data, addr, host):
    x = 5


def conn_string(conn, data, addr):
    # Client Browser requests
    try:
        # pdb.set_trace()
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

        is_https_request = is_ssl_req(data)
        data = sanitize_data(data, webserver)
        if is_https_request:
            https_proxy_server(port, conn, data, addr, webserver)
        else:
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
        print "Initialized and binded to socket - SUCCESS"
    except:
        print "Err with socket init"
        sys.exit(2)

    accept_conn(s)

def main():
    port, num_workers, timeout, log_dir = parse_input_args()
    connect_socket(num_workers, port)

if __name__ == '__main__':
    main()
