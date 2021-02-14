import socket

s1 = socket.socket()
s2 = socket.socket()
s1.connect(("127.0.0.1", 11037))
s2.connect(("127.0.0.1", 11038))

while True:
    meow = input(">>> ")
    if meow.startswith("1:"):
        s1.send(meow[2:].encode())
    elif meow.startswith("2:"):
        s2.send(meow[2:].encode())
    else:
        continue
