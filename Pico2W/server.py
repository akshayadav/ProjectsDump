#!/usr/bin/env python3
"""Threaded TCP JSON receiver for Pico temperature payloads.

Usage:
  python3 server.py [port]

Listens on 0.0.0.0:5005 by default and prints received JSON payloads.
Accepts multiple clients concurrently; each JSON message must be newline-delimited.
Each valid JSON message is appended to a logfile and the server replies with a JSON ACK.
"""
import socket
import json
import time
import sys
import threading
import os

HOST = '0.0.0.0'
PORT = 5005
LOGFILE = 'pico_temps.log'

def log_received(addr, obj):
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    line = f"{ts} - {addr} - {json.dumps(obj)}\n"
    try:
        with open(LOGFILE, 'a') as f:
            f.write(line)
    except Exception as e:
        print('Log write error:', e)

def handle_client(conn, addr):
    print(f"Connected from {addr}")
    buffer = ''
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            buffer += data.decode('utf-8', errors='replace')
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {addr} - Non-JSON: {line}")
                    # Reply with error ack
                    try:
                        err = json.dumps({'status': 'error', 'reason': 'invalid_json'}) + '\n'
                        conn.sendall(err.encode('utf-8'))
                    except Exception:
                        pass
                    continue

                # Log and print
                print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {addr} - {obj}")
                log_received(addr, obj)

                # Send ACK back to client
                ack = {
                    'status': 'ok',
                    'received': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                try:
                    conn.sendall((json.dumps(ack) + '\n').encode('utf-8'))
                except Exception:
                    pass
    except Exception as e:
        print(f"Error with {addr}:", e)
    finally:
        try:
            conn.close()
        except Exception:
            pass
        print(f"Connection closed {addr}")

def main(host=HOST, port=PORT):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((host, port))
    srv.listen(5)
    print(f"Listening on {host}:{port} (TCP)")
    try:
        while True:
            conn, addr = srv.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()
    except KeyboardInterrupt:
        print('\nShutting down')
    finally:
        srv.close()

if __name__ == '__main__':
    port = PORT
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print('Invalid port, using default 5005')
    main(HOST, port)
