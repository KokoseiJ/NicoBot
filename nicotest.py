from niconico import NicoPlayer

import os

id = os.environ.get("ID")
pw = os.environ.get("PW")

player = NicoPlayer()
if id and pw:
    player.login(id, pw)

song = player.play("sm22792311")
song.prepare()
print(song.start())
try:
    song.heartbeat_thread.join()
except KeyboardInterrupt:
    pass
finally:
    song.stop_flag.set()
    song.heartbeat_thread.join()
