# NicoBot
Nicovideo Player bot for Discord, written from the scratch.

## What is this?
This bot is made to stream songs from Nicovideo to Discord. probably not useful to most of you guys, but will be very useful to fellow weebs.
But, this bot is special. why, you ask? because, *This bot doesn't use discord.py.*
That's right, I wrote my own library, just to listen to some weeb musics while on VC.
If you're still interested, let me explain these further.

## How does it stream things from Nicovideo?
First of all, I implemented this in my another bot already, [at here.](https://github.com/KokoseiJ/DiscordBot/blob/master/modules/nico.py)
Code is a mess, but I did my best at that time.

Thankfully, not like Youtube, Nicovideo's system is easy enough to reverse-engineer without even reading JS scripts.

Most videos in Nicovideo are hosted from their DMC server, which will provide videos in MPEG-TS format.
There's absolutely no cryptic protections, so It is a piece of cake to scrape videos from there. But how?

You grab informations needed to create a sessions with DMC API, form it nicely, send it to DMC API,
send some heartbeats so it won't disconnect, and grab .m3u8. now you can slap this into FFMPEG and send it to Discord server.

Those informations come with HTML, but there are APIs that gets called in smartphone mode that retrieves only video stream infos. You can use that as well.

Some old videos won't be available in MPEG-TS format, or they won't give it during eco mode hours to reduce server loads.
In this case, They will give you an mp4 file. This format is called SmileVideo internally.
If DMC information is null, You're gonna have to grab this thing.

Accessing this type of video is very straightforward- You just grab the url and download it. no sessions, no heartbeats. Straight to the server.

But, please notice that when DMC is available, SmileVideos won't work. So you can't just always grab SmilVideo URLs even if you're lazy to implement heartbeats.

I've yet to implement them but there are other file formats as well- such as flv.
Those exist, but they won't be provided if you don't specify that you're using flash player in the cookie.
They will be served through DMC server without problems these days, so that's not a problem.

## Care to talk about your new Discord API library?
Well, I just made it because I can ¯\\\_(ツ)\_/¯
I just wanted to understand its underlying protocols, as well as practice to write a big package.

Also, since Discord.py heavily depends on coroutine and that coufuses the hell out of beginners and make them write a spaghetti,
I thought we might need a corountine-less library. That's why I didn't use a famous `websockets` library, and went with websocket-client instead.

It currently uses urllib to communicate with their HTTP endpoints, websocket-client to communicate with Gateway.
Since It doesn't use coroutine on purpose, It currently uses threading library to parallelly run websockets and heartbeats.

I currently implemented a pygame-like event handling- You use a generator to yield events, so It could be used without declaring a new function.
I'm planning to implement a handler-like event handling system, since It's not really ideal. It might be useful for simple usages, though.

Voice connection is available! If you're using `bot.py`, You can trigger it using `?connect {vc_channel_id}`. It depends on ffmpeg, so be sure to have it.

Since I only implemented functions that I need, lots of API calls and models are missing.
I'm going to implement those as well, and when It becomes good enough I will separately release it.

I know that code is quite complicated and there are no comments, I'm gonna add all that later. was kinda busy for a while.

I'm well aware that threading in python has a disadvantage due to Global Interpreter Lock. so I'm planning to migrate to multiprocessing.
also, Since websocket-client is not really good performance-wise, I'm considering to migrate to autobahn.
but, `websockets` is not an option, since It depends on coroutine heavily.
[They stated that its purpose is to provide a convenient asynchronous API.](https://github.com/aaugustin/websockets/issues/173)

## Contributions?
Oh yes, I definitely need them! I'll happily accept any forms of contributions, just send me a PR! I'll review it right away.

Contact kokoseij@gmail.com If you need any questions. Thanks!
