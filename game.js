var ws = new WebSocket("ws://" + location.hostname + ":21000/")
var mainElement = document.getElementsByTagName("main")[0]
var headerElement = document.getElementsByTagName("header")[0]
var nameDisplay = headerElement.getElementsByClassName("name")[0]
var buttons = headerElement.getElementsByClassName("buttons")[0]
var players
var game = {}
var this_client
var start = Date.now()
var clicks = 100
var pinger

ws.onopen = function (event) {
    console.log(event)
    if (location.hostname == "localhost") {

        ws.send(JSON.stringify({"c":"qr"}))

    } else {

        let person = prompt("Please enter your name:");
        if (person == null || person == "") {
            location.reload();
        } else {
            ws.send(JSON.stringify({"c":"join", "d": person}));
        }
        
    }
}

ws.onmessage = function (event) {
    package = JSON.parse(event.data)
    console.log(package)

    if (package.c == "qr") {
        mainElement.innerHTML = "<section class='qr'><img src='" + package.r.img + "'></section><section class='playerlist'></section><section id='gameinfo'><img class='logo' src='Mainframe.png'></section>"
        nameDisplay.innerHTML = package.r.link
        //buttons.innerHTML = `<button onclick="ws.send(JSON.stringify({'c':'reset'}))">Reset</button>`
        ws.send(JSON.stringify({"c":"playerlist"}))
        pinger = setInterval(() => {
            ws.send(JSON.stringify({"c":"ping", "d": Date.now()-start}))
        }, 10000);
    } else if (package.c == "join") {
        nameDisplay.innerHTML = package.r.name
        mainElement.innerHTML = `<section class='playerinfo'>
                                    <img class='logo' src='Mainframe.png'>
                                    <h2 id="ready">Not ready</h2>
                                    <button onclick="ws.send(JSON.stringify({'c':'ready'}))">Ready up</button>
                                </section>`
        buttons.innerHTML = '<button onclick="leave()"><i class="fas fa-times"></i></button>'
        this_client = package.r
    } else if (package.c == "playerjoin") {
        ws.send(JSON.stringify({"c":"playerlist"}))
    } else if (package.c == "playerleft") {
        ws.send(JSON.stringify({"c":"playerlist"}))
    } else if (package.c == "playerlist") {
        package.r = JSON.parse(package.r)
        document.getElementsByClassName("playerlist")[0].innerHTML = ""

        players = package.r

        for (i = 0;i < Object.keys(package.r).length;i++) {
            var ready = '<i class="fas fa-times"></i>'
            if (Object.keys(game).includes(Object.keys(package.r)[i])) {
                
                if (game[Object.keys(package.r)[i]].ready) {
                    var ready = '<i class="fas fa-check"></i>'
                }     
            }
            document.getElementsByClassName("playerlist")[0].innerHTML += `<div class="player" id="${Object.keys(package.r)[i]}">
                                                                               <span class="name">${package.r[Object.keys(package.r)[i]].name}</span>
                                                                               <span id="${Object.keys(package.r)[i]}-ready">${ready}</span>
                                                                               <button onclick="kick('${Object.keys(package.r)[i]}')">Kick</button>
                                                                           </div>`
        }

       if (Object.keys(package.r).length <= 1) {
        document.getElementsByClassName("qr")[0].style.display = ""
        document.getElementsByClassName("playerlist")[0].style.display = ""
        nameDisplay.style.display = ""
        document.getElementById("gameinfo").style.gridColumnStart = ""
        document.getElementById("gameinfo").innerHTML = "<section id='gameinfo'><img class='logo' src='Mainframe.png'>"
       }
    
    } else if (package.c == "gameupdate") {
        document.getElementById("gameinfo").innerHTML = "<section id='gameinfo'><img class='logo' src='Mainframe.png'>"
        //document.getElementById("gameinfo").innerHTML = "<h1>Clicker game</h1>"
        game = package.r
        for (i=0;i<Object.keys(players).length;i++) {
            if (Object.keys(game).includes(Object.keys(players)[i])) {
                if (game[Object.keys(players)[i]].ready) {
                    document.getElementById(Object.keys(players)[i] + "-ready").innerHTML = '<i class="fas fa-check"></i>'
                } else {
                    document.getElementById(Object.keys(players)[i] + "-ready").innerHTML = '<i class="fas fa-times"></i>'
                }
                game[Object.keys(players)[i]].name = players[Object.keys(players)[i]].name
                if (Object.keys(game[Object.keys(players)[i]]).includes("clicks")) {
                    document.getElementById("gameinfo").innerHTML += `<p>${game[Object.keys(players)[i]].name}: ${(game[Object.keys(players)[i]].clicks/clicks*100).toFixed(0)}%</p>
                    <div class="progress"><div><div style="width: ${game[Object.keys(players)[i]].clicks/clicks*100}%"></div></div></div>`
                }
            }
        }
    
    } else if (package.c == "kick") {
        ws.send(JSON.stringify({"c":"playerlist"}))
    } else if (package.c == "click") {
        document.getElementById("clicks").innerText = package.r.clicks
    } else if (package.c == "ready") {
        if (package.r.ready) {
            document.getElementById("ready").innerText = "Ready"
        } else {
            document.getElementById("ready").innerText = "Not ready"
        }
    } else if (package.c == "countdown") {
        if (location.hostname != "localhost") {
            document.getElementsByClassName("playerinfo")[0].innerHTML = `<img class='logo' src='Mainframe.png'>
                                                                          <h2>${package.r}</h2>`
        } else {
            document.getElementsByClassName("qr")[0].style.display = "none"
            document.getElementsByClassName("playerlist")[0].style.display = "none"
            nameDisplay.style.display = "none"
            document.getElementById("gameinfo").style.gridColumnStart = "1"
            document.getElementById("gameinfo").innerHTML = `<h1 style="font-size: 100px;">${package.r}</h1>`
        }
    } else if (package.c == "start") {
        if (location.hostname != "localhost") {
            document.getElementsByClassName("playerinfo")[0].innerHTML = `<img class='logo' src='Mainframe.png'>
                                                                          <h2 id="clicks">0</h2>
                                                                          <button onclick="ws.send(JSON.stringify({'c':'click'}))">Hack</button>`
        } else {
            clicks = package.r
        }
    } else if (package.c == "resetclient") {
        ws.send(JSON.stringify({"c":"join", "d": this_client.name}));
    } else if (package.c == "gameover") {
        if (location.hostname != "localhost") {
            document.getElementsByClassName("playerinfo")[0].innerHTML = `<h1>GAME OVER</h1>`
            
            setTimeout(() => {
                leave("Disconnected")
            }, 5000);
        } else {
            clearInterval(pinger)
            document.getElementById("gameinfo").innerHTML = `<h1 style="font-size: 100px;">${package.r}</h1>`
            setTimeout(() => {
                ws.send(JSON.stringify({"c":"qr"}))
            }, 6000);
        }
    }
};

ws.onclose = function (event) {
    if (event.reason != "" && event.reason != null) {

        console.log(event.reason)
        alert(event.reason)

    }
}

function kick(player, reason) {
    r = reason || "You have been kicked"
    ws.send(JSON.stringify({"c":"kick", "d": {"ip": player, "r": r}}))

}

function leave(reason) {
    this_client["r"] = reason || "You have left"
    ws.send(JSON.stringify({"c":"leave", "d": this_client}))
}

