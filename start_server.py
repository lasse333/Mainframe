import asyncio
import websockets
import json
import socket
import os
import time

players = {}
game = {}
game_state = "join"
clicks = 150


async def handler(websocket, path):
    global players
    global game
    global game_state

    async for message in websocket:
        await check_disconnects(players)
        if game_state != "end":
            await check_playercount()


        package = json.loads(message)
        print(package)            


        if package["c"] == "qr":
            game_state = "join"
            players["host"] = {"name": "host"}
            players["host"]["ws"] = websocket
            # https://zxing.appspot.com/generator
            # https://zxing.org/w/chart?cht=qr&chs=350x350&chld=L&choe=UTF-8&chl=http%3A%2F%2F
            # https://goqr.me/api/doc/create-qr-code/#param_color
            # http://api.qrserver.com/v1/create-qr-code/?size=350x350&color=0f0&bgcolor=000&data=http%3A%2F%2F
            # http://api.qrserver.com/v1/create-qr-code/?size=350x350&color=000&bgcolor=0f0&data=http%3A%2F%2F
            package["r"] = {"img": "http://api.qrserver.com/v1/create-qr-code/?size=350x350&color=000&bgcolor=0f0&data=http%3A%2F%2F" + socket.gethostbyname(socket.gethostname()) + "%2F", "link": "http://" + socket.gethostbyname(socket.gethostname()) + "/"}



        elif package["c"] == "join":
            if game_state == "join":
                if len(players.keys()) < 9:
                    await players["host"]["ws"].send(json.dumps({"c": "playerjoin", "r": package["d"] + " joined"}))
                    package["r"] = {"name": package["d"], "ip": websocket.remote_address[0]}
                    players[websocket.remote_address[0]] = {"name": package["d"], "ws": websocket, "ip": websocket.remote_address[0]}
                else:
                    await websocket.close(reason="the game is full")
            elif game_state == "starting":
                await websocket.close(reason="The game is about to start...")
            elif game_state == "start":
                await websocket.close(reason="The game has already started")
            

        elif package["c"] == "playerlist":
            package["r"] = json.dumps(new_json_obj(players))



        elif package["c"] == "kick":
            await players[package["d"]["ip"]]["ws"].close(reason=package["d"]["r"])
            package["r"] = players[package["d"]["ip"]]["name"] + " has been kicked"
            del players[package["d"]["ip"]]


        elif package["c"] == "leave":
            package["r"] = "You have left"
            await websocket.send(json.dumps(package))
            await remove_player(package["d"]["ip"], package["d"]["r"])


        elif package["c"] == "click":
            if game_state == "start":
                if websocket.remote_address[0] not in game.keys():
                    game[websocket.remote_address[0]] = {"clicks": 1, "name": players[websocket.remote_address[0]]["name"]}
                elif "clicks" not in game[websocket.remote_address[0]].keys():
                    game[websocket.remote_address[0]]["clicks"] = 1
                else:
                    game[websocket.remote_address[0]]["clicks"] += 1
                package["r"] = game[websocket.remote_address[0]]
                await players["host"]["ws"].send(json.dumps({"c": "gameupdate", "r": game}))
                if package["r"]["clicks"] >= clicks:
                    await game_over(websocket.remote_address[0])



        elif package["c"] == "ready":
            if websocket.remote_address[0] not in game.keys():
                game[websocket.remote_address[0]] = {"ready": True, "name": players[websocket.remote_address[0]]["name"]}
            elif "ready" not in game[websocket.remote_address[0]].keys():
                game[websocket.remote_address[0]]["ready"] = True
            else:
                if game[websocket.remote_address[0]]["ready"] != True:
                    game[websocket.remote_address[0]]["ready"] = True
                else:
                    game[websocket.remote_address[0]]["ready"] = False

            package["r"] = game[websocket.remote_address[0]]
            await players["host"]["ws"].send(json.dumps({"c": "gameupdate", "r": game}))

        
        elif package["c"] == "reset":
            game = {}             

            await players["host"]["ws"].send(json.dumps({"c": "gameupdate", "r": game}))


        if websocket.open:
            await websocket.send(json.dumps(package))

            if len(game.keys()) == len(players.keys())-1 and len(game.keys()) > 1 and game_state == "join":
                if ready_check(game):
                    await countdown(5)



def new_json_obj(obj):
    objs = list(obj.keys())
    new_obj = {}

    for x in range(len(objs)):
        if objs[x] != "host":
            new_obj[objs[x]] = {"name": obj[objs[x]]["name"], "ip": obj[objs[x]]["ip"]}


    return new_obj

def ready_check(obj):
    all_ready = True
    keys = list(obj.keys())
    for x in range(len(keys)):
        if "ready" in obj[keys[x]].keys():
            if obj[keys[x]]["ready"]:
                continue
            else:
                return False
        else:
            return False

    return True




async def countdown(time):
    global players
    global game_state
    global game

    player = list(players.keys())
    for x in range(time+1):
        for y in range(len(player)):
            if time-x > 0:
                game_state = "starting"
                await players[player[y]]["ws"].send(json.dumps({"c":"countdown","r":time-x}))
            else:
                game_state = "start"


                for gamer in game.keys():
                    game[gamer]["ready"] = False
                    game[gamer]["clicks"] = 0


                await players[player[y]]["ws"].send(json.dumps({"c":"start", "r": clicks}))
        
        if time-x > 0:
            await asyncio.sleep(1)
        else:
            await players["host"]["ws"].send(json.dumps({"c": "gameupdate", "r": game}))



async def remove_player(player, reason="Disconnected"):
    global game
    global players
    
    if player in game.keys():
        del game[player]

    if player in players.keys():
        try:
            await players[player]["ws"].close(reason=reason)
        finally:
            await players["host"]["ws"].send(json.dumps({"c": "playerleft", "r": players[player]["name"] + " left"}))
            del players[player]



async def check_disconnects(obj):
    obj_keys = list(obj.keys())

    for x in range(len(obj_keys)):
        if obj_keys[x] != "host":
            if obj[obj_keys[x]]["ws"].closed:
                await remove_player(obj_keys[x])



async def check_playercount():
    global players
    global game_state
    global game

    player = list(players.keys())

    for x in range(len(player)):
        if player[x] == "host":
            player.pop(x)
            break

    if len(player) <= 1:
        if game_state != "join":
            game = {}
            await broadcast_clients(json.dumps({"c": "resetclient"}))
        game_state = "join"


async def broadcast_clients(msg):
    global players
    keys = list(players.keys())

    for x in range(len(keys)):
        if keys[x] == "host":
            continue
        else:
            await players[keys[x]]["ws"].send(msg)


async def game_over(player):
    global players
    global game
    global game_state

    game_state = "end"
    await broadcast_clients(json.dumps({"c": "gameover", "r": players[player]["name"] + " has won the game"}))
    await players["host"]["ws"].send(json.dumps({"c": "gameover", "r": players[player]["name"] + " has won the game"}))
    



start_server = websockets.serve(handler, "0.0.0.0", 21000)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()