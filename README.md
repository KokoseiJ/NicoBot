# Nicobot
Music bot that plays music from Nicovideo, written from the scratch, without using Discord.py.

[![Build Status](https://jenkins.kokoseij.xyz/buildStatus/icon?job=NicoBot)](https://jenkins.kokoseij.xyz/job/NicoBot/)

[![Lines of Code](https://sonar.kokoseij.xyz/api/project_badges/measure?project=KokoseiJ_NicoBot&metric=ncloc)](https://sonar.kokoseij.xyz/dashboard?id=KokoseiJ_NicoBot) [![Coverage](https://sonar.kokoseij.xyz/api/project_badges/measure?project=KokoseiJ_NicoBot&metric=coverage)](https://sonar.kokoseij.xyz/dashboard?id=KokoseiJ_NicoBot) 

[![Reliability Rating](https://sonar.kokoseij.xyz/api/project_badges/measure?project=KokoseiJ_NicoBot&metric=reliability_rating)](https://sonar.kokoseij.xyz/dashboard?id=KokoseiJ_NicoBot) [![Maintainability Rating](https://sonar.kokoseij.xyz/api/project_badges/measure?project=KokoseiJ_NicoBot&metric=sqale_rating)](https://sonar.kokoseij.xyz/dashboard?id=KokoseiJ_NicoBot) [![Security Rating](https://sonar.kokoseij.xyz/api/project_badges/measure?project=KokoseiJ_NicoBot&metric=security_rating)](https://sonar.kokoseij.xyz/dashboard?id=KokoseiJ_NicoBot)

[![Quality gate](https://sonar.kokoseij.xyz/api/project_badges/quality_gate?project=KokoseiJ_NicoBot)](https://sonar.kokoseij.xyz/dashboard?id=KokoseiJ_NicoBot)

## What is this bot?
Just like its name, It plays songs from [Nicovideo](https://nicovideo.jp) server. Streaming-related code is mostly from [`nico.py` module from my previous bot](https://github.com/KokoseiJ/DiscordBot/blob/master/modules/nico.py), while Discord-side API wrapper was completely written from the scratch.

It currently uses `urllib` to communicate with their HTTP endpoints, `websocket-client` to communicate with Gateway. 
Since It doesn't use coroutine on purpose, It currently uses threading library to parallelly run websockets and heartbeats.

since `websocket-client` is written in pure Python and could cause a bottleneck in some cases, installing `wsaccel` package from pip is recommended.

Use [this link](https://discordapp.com/api/oauth2/authorize?client_id=769981832006598718&scope=bot%20applications.commands&permissions=104201280) to invite the test bot: IA!
**WARNING: This bot is being used to test codes, and can be offline/unfunctionable time to time!**

## Why though? wasn't Discord.py enough?
Well, I just made it because I can ¯\\\_(ツ)\_/¯

I just wanted to understand its underlying protocols, as well as practice to write a big package.

Also, since `Discord.py` heavily depends on coroutine which coufuses the hell out of beginners and make them write a spaghetti,
I thought we might need a corountine-less library. That's why I didn't use a famous `websockets` library, and went with `websocket-client` instead. [They stated that its purpose is to provide a convenient asynchronous API, not synchronous one.](https://github.com/aaugustin/websockets/issues/173)

And... well, as of August 2021, Discord.py is no longer being maintained. so... yeah.

## Using threading instead of multiprocessing?! Cast it into the fire, DESTROY IT!!
![No.](https://media1.tenor.com/images/27364728e09d58e670154b50a59ca9c8/tenor.gif?itemid=5743603)

I'm well aware that threading in python has a disadvantage due to Global Interpreter Lock. but since there are bottlenecks in HTTP requests, I don't think bottlenecks caused by GIL will affect the performance largely. of course, I didn't do any tests yet. I'll do it later though, and if it appears to degrade performance, I will migrate to multiprocessing library.

## Development Roadmap
- [x] implement HTTP API requests

- [x] Wire up discord object classes to Gateway events

- [x] Implement Voice Connection based on WebSocketThread

- [x] Implement handlers

- [x] Implement Slash Commands

- [ ] Implement other interactions

- [ ] Implement Message Components

- [ ] Unify function behaviours and code styles


## Contributions?
I'll happily accept any forms of contributions. but please do the followings:

1. Run tests to ensure the code is working correctly - Test suite is being prepared, so before that please do it manually.

2. Format your code properly using black or any other reformatting tools.

3. Properly comment your code following [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html#s3.8-comments-and-docstrings).

PR will be merged after I'm done reviewing the changes.

Contact kokoseij@gmail.com If you need any questions. Thanks!
