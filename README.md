# Nicobot
Music bot that plays music from Nicovideo, written from the scratch, without using Discord.py.

[![Build Status](https://jenkins.kokoseij.xyz/buildStatus/icon?job=NicoBot)](https://jenkins.kokoseij.xyz/job/NicoBot/)

[![Lines of Code](https://sonar.kokoseij.xyz/api/project_badges/measure?project=KokoseiJ_NicoBot&metric=ncloc)](https://sonar.kokoseij.xyz/dashboard?id=KokoseiJ_NicoBot) [![Coverage](https://sonar.kokoseij.xyz/api/project_badges/measure?project=KokoseiJ_NicoBot&metric=coverage)](https://sonar.kokoseij.xyz/dashboard?id=KokoseiJ_NicoBot) 

[![Reliability Rating](https://sonar.kokoseij.xyz/api/project_badges/measure?project=KokoseiJ_NicoBot&metric=reliability_rating)](https://sonar.kokoseij.xyz/dashboard?id=KokoseiJ_NicoBot) [![Maintainability Rating](https://sonar.kokoseij.xyz/api/project_badges/measure?project=KokoseiJ_NicoBot&metric=sqale_rating)](https://sonar.kokoseij.xyz/dashboard?id=KokoseiJ_NicoBot) [![Security Rating](https://sonar.kokoseij.xyz/api/project_badges/measure?project=KokoseiJ_NicoBot&metric=security_rating)](https://sonar.kokoseij.xyz/dashboard?id=KokoseiJ_NicoBot)

[![Quality gate](https://sonar.kokoseij.xyz/api/project_badges/quality_gate?project=KokoseiJ_NicoBot)](https://sonar.kokoseij.xyz/dashboard?id=KokoseiJ_NicoBot)

## What is this bot?
Just like its name, It plays songs from [Nicovideo](https://nicovideo.jp) server. Streaming-related code is mostly from [`nico.py` module from my previous bot](https://github.com/KokoseiJ/DiscordBot/blob/master/modules/nico.py), while Discord-side API wrapper is completely written from the scratch.

It currently uses `urllib` to communicate with their HTTP endpoints, `websocket-client` to communicate with Gateway. 
Since It doesn't use coroutine on purpose, It currently uses threading library to parallelly run websockets and heartbeats.

Additionally, installing [`wsaccel`](https://github.com/methane/wsaccel) package from pip is recommended, since UTF8 implementation in `websocket-client` can cause bottlenecks. wsaccel solves this by providing an alternative C implementation.

Use [this link](https://discordapp.com/api/oauth2/authorize?client_id=769981832006598718&scope=bot%20applications.commands&permissions=104201280) to invite the test bot: "IA -ARIA ON THE PLANETES-".
**WARNING: This bot is being used to test codes, and can be offline/unfunctionable time to time!**

## Why though? wasn't Discord.py enough?
Well, I just made it because I can ¯\\\_(ツ)\_/¯

More specifically, since `Discord.py` heavily depends on coroutine which coufuses the hell out of beginners and make them write a spaghetti,
I thought we might need a corountine-less library. That's why I didn't use a famous `websockets` library([They stated that its purpose is to provide a convenient asynchronous API, not synchronous one.](https://github.com/aaugustin/websockets/issues/173)), and went with `websocket-client` instead.

## Using threading instead of multiprocessing?! Cast it into the fire, DESTROY IT!!
![No.](https://media1.tenor.com/images/27364728e09d58e670154b50a59ca9c8/tenor.gif?itemid=5743603)

I'm well aware that threading in python has a disadvantage due to Global Interpreter Lock. but since there are overheads in HTTP requests, I expect performance degradation caused by GIL to be ignorable. There's no test done regarding this, but I'm planning to do one. If it appears to degrade performance, I will gradually migrate to multiprocessing library.

## Features
- [x] Full Gateway V9 Implementation

- [x] HTTP API requests

- [x] Voice Connection

- [x] Slash Command

- [ ] User Command

- [ ] Message Command

- [ ] Message Components

- [ ] Autocomplete

- [ ] Modal

## Contributions?
I'll happily accept any forms of contributions. but please do the followings:

1. Run tests to ensure the code is working correctly - Test suite is being prepared, so before that please do it manually.

2. Format your code properly using black or any other reformatting tools.

3. Properly comment your code following [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html#s3.8-comments-and-docstrings).

PR will be merged after I'm done reviewing the changes.

## Contact

You can reach out to me on:

E-mail: kokoseij@gmail.com

Discord: KokoseiJ#2113

Or [issue tracker](https://github.com/KokoseiJ/NicoBot/issues) if you're trying to reach out regarding the bug or issue.

Please contact me if you have any questions. Thanks.
