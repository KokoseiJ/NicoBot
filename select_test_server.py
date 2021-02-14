import select
import socket

s1 = socket.socket()
s2 = socket.socket()

s1.bind(("127.0.0.1", 11037))
s2.bind(("127.0.0.1", 11038))
s1.listen()
s2.listen()

c1, _ = s1.accept()
c2, _ = s2.accept()

while True:
    try:
        meow, _, _ = select.select([c1, c2], [], [])
        print("received!")
        for x in meow:
            if x is c1:
                print("c1:", c1.recv(4096).decode())
            elif x is c2:
                print("c2:", c2.recv(4096).decode())
    finally:
        s1.close()
        s2.close()
