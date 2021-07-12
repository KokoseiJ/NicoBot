# Nicobot
Music bot that plays music from Nicovideo, written from the scratch, without using Discord.py.

## What is this bot?
Just like its name, It plays songs from [Nicovideo](https://nicovideo.jp) server. Streaming-related code is mostly from [`nico.py` module from my previous bot](https://github.com/KokoseiJ/DiscordBot/blob/master/modules/nico.py), while Discord-side API wrapper was completely written from the scratch.

It currently uses `urllib` to communicate with their HTTP endpoints, `websocket-client` to communicate with Gateway. 
Since It doesn't use coroutine on purpose, It currently uses threading library to parallelly run websockets and heartbeats.

## Why though? wasn't Discord.py enough?
Well, I just made it because I can ¯\\\_(ツ)\_/¯

I just wanted to understand its underlying protocols, as well as practice to write a big package.

Also, since `Discord.py` heavily depends on coroutine which coufuses the hell out of beginners and make them write a spaghetti,
I thought we might need a corountine-less library. That's why I didn't use a famous `websockets` library, and went with `websocket-client` instead. [They stated that its purpose is to provide a convenient asynchronous API, not synchronous one.](https://github.com/aaugustin/websockets/issues/173)

## Using threading instead of multiprocessing?! Cast it into the fire, DESTROY IT!!
![No.](https://media1.tenor.com/images/27364728e09d58e670154b50a59ca9c8/tenor.gif?itemid=5743603)

I'm well aware that threading in python has a disadvantage due to Global Interpreter Lock. but since there are bottlenecks in HTTP requests, I don't think bottlenecks caused by GIL will affect the performance largely. of course, I didn't do any tests yet. I'll do it later though, and if it appears to degrade performance, I will migrate to multiprocessing library.

## Development Roadmap
- [x] implement Channel HTTP API requests

- [x] implement Guild HTTP API requests

- [x] implement User HTTP API requests

- [x] implement Message HTTP API requests

- [x] implement Member HTTP API requests

- [x] Wire up discord object classes to Gateway events

- [x] Implement Voice Connection based on WebSocketThread

- [ ] Implement handlers

- [ ] Unify function behaviours and code styles

- [ ] maybe implement slash commands?

## Contributions?
Oh yes, I definitely need them! I'll happily accept any forms of contributions, just send me a PR! I'll review it right away.

Contact kokoseij@gmail.com If you need any questions. Thanks!
