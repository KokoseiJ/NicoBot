from discordapi.slash import SlashCommand, String, Integer
import json


@SlashCommand.create("Command for testing", (
    String("lmao", "zzlol~"),
    Integer("number_for_test", ".")
))
def testcmd(ctx, lmao, number_for_test):
    return


print(type(testcmd))
print(json.dumps(testcmd._json(), indent=4))
