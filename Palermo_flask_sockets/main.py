from flask import Flask, render_template, redirect,request, url_for
from flask_socketio import SocketIO, send, emit
import editdistance
from numpy.random import randint, choice, permutation
from pygame import mixer
import pyttsx3
from gtts import gTTS
from time import sleep
import operator
import logging
import numpy as np
import webbrowser
browser= webbrowser.get("C:/Program Files (x86)/Google/Chrome/Application/chrome.exe %s")





app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, logger = False)

logging.getLogger('socketio').setLevel(logging.ERROR)
logging.getLogger('engineio').setLevel(logging.ERROR)

###################################
# GLOBAL VARIABLES
#
#
mixer.init()
players = {}
players_ip = {}
ip_players = {}
player_role = {}
role_player = {}

player_socket = {}
socket_player = {}
votes = {}
vote_to_kill = [""]

nec_chars = ["killer","framer"] #"/mafia"]
opt_chars = ["vigilante", "jesus","bomber","doctor","framer","medium","inspector_1","inspector_2","informant"]
bad_guys = []
bad_roles = ["killer","framer","mafia"]
jailed = [] #here for later
players_sleep = {}

has_killed = [False]
has_protected = [False]
has_vigilanted = [False]
has_converted=[False]
framed = []
jihad_target = []
is_protected = [].copy()
global_day = True

kill_save=[False]

undercover_badguy = [] 
undercover_prob = [0.5]
################################
testing = [False]
if(testing[0]):
    players["test1"]=1 
    players["test2"]=1 
    players["test3"]=1
#
#
############################
# Helper Functions

def check_end(time):
    if time == "night":
        if countLivingBadguys() > countActivePlayers():
            return "bad"
        elif countLivingBadguys() == 0:
            return "good"
        else:
            return "false"
        
        

def countLivingBadguys():
    bad = 0
    for i in bad_guys:
        if isAlive(player_role[i]):
            bad+=1
    return bad

def countLivingPlayers():
    alive = 0
    for key,val in players.items():
        if(val not in [0,3]):
            alive+=1
    return alive

def countActivePlayers():
    return countLivingPlayers() - len(jailed)

def isAlive(crole):
    try:
        if players[role_player[crole]] == 3:
            return False
        else:
            return True
    except Exception:
        return False



def knn( tmp , a=True):
    min_dist = 0
    min_i = 0
    if a:
        min_dist = editdistance.eval(tmp, "Pass")
        min_i = "Pass"
    else:
        min_dist = editdistance.eval(tmp, list(players.keys())[0])
        min_i = list(players.keys())[0]

    for i in players.keys():
        if(min_dist>editdistance.eval(tmp, i)):
            min_dist = editdistance.eval(tmp, i)
            min_i = i
    return min_i

def playSound(sound):
    if sound == "ressurect":
        mixer.music.load("C:\\Users\\Panagiotis\\Desktop\\palermo_sif\\server\\sounds\\ressurect.mp3") 
        mixer.music.play()
    if sound == "vigilant":
        mixer.music.load("C:\\Users\\Panagiotis\\Desktop\\palermo_sif\\server\\sounds\\vigilant.mp3") 
        mixer.music.play()
    if sound == "jihad":
        mixer.music.load("C:\\Users\\Panagiotis\\Desktop\\palermo_sif\\server\\sounds\\jihad.mp3") 
        mixer.music.play()    
        sleep(1)
        mixer.music.load("C:\\Users\\Panagiotis\\Desktop\\palermo_sif\\server\\sounds\\jihad.mp3") 
        mixer.music.play()

def speak(crole, message):
    # language = 'en'
    # myobj = gTTS(text=message, lang=language, slow=False)
    # myobj.save("C:\\Users\\Panagiotis\\Desktop\\palermo_sif\\server\\sounds\\killer.mp3")
    # mixer.music.load("C:\\Users\\Panagiotis\\Desktop\\palermo_sif\\server\\sounds\\killer.mp3") 
    
    #mixer.music.play()
    engine = pyttsx3.init()
    engine.say(message)
    engine.setProperty("rate",110)
    engine.setProperty("volume",0.9)
    engine.runAndWait()

def distribute_roles():
    chosen_chars = nec_chars + list(choice(opt_chars, len(players)- len(nec_chars),replace = False))
            
    assignments = permutation(chosen_chars)
    
    for i in range(len(players)):
        player_role[list(players.keys())[i]] = assignments[i]
        role_player[assignments[i]] = list(players.keys())[i]    

        if assignments[i] in bad_roles:
            bad_guys.append(list(role_player.values())[i])
    for i in players.keys():
        players_sleep[i] = 0

    print(bad_guys)
    print(player_role)
    print(role_player)
    ###############################
    #
    # UNDERCOVER BAD GUY
    #
    if np.random.rand()<=undercover_prob[0]:
        pick = np.random.choice(list(players.keys()),size = 1)[0]
        while pick in bad_guys:
            pick = np.random.choice(list(players.keys()),size = 1)[0]
        bad_guys.append(pick)
        undercover_badguy.append(pick)





    ###############################
    #
    #  UNCOMMENT FOR LOVERS
    #  random_picks = choice(chosen_chars,2,replace = False)
    #  while(random_picks[0] in ["mafia","killer","framer"] or random_picks[1] in ["mafia","killer","framer"]):
    #       random_picks = choice(chosen_chars,2,replace = False)
    #pub_event_list["You are in love with "+str(players_decrypt[chars_decrypt[random_picks[0]]])]=random_picks[1]
    #pub_event_list["You are in love with "+str(players_decrypt[chars_decrypt[random_picks[1]]])]=random_picks[0]

def count_votes(a):
    votes ={}
    for key,val in a.items():
        if key not in jailed:
            if val in votes.keys():
                votes[val]+=1
            else:
                votes[val]=1
    return votes  

def vote_winner(counted):
    voted = max(counted.items(), key=operator.itemgetter(1))[0]

    if "Pass" in counted.keys():
        if counted["Pass"] == countActivePlayers():
            
            return "Pass"

    if(kill_save[0]):
        print(counted)
        

        if counted["Kill"] == counted["Save"]:
            return "Save"
    if not kill_save[0]:

        while voted == "Pass" or players[voted] !=1:
            cpy = counted.copy()
            
            cpy[voted]=0
            voted = max(cpy.items(), key=operator.itemgetter(1))[0]

    if(voted!="Pass"):
        return voted

    elif counted["Pass"] < countActivePlayers():
        cpy = counted.copy()
        cpy["Pass"]=0
        voted = max(cpy.items(), key=operator.itemgetter(1))[0]
        return voted
        


def voting(msg): #collects and counts votes
    print(msg)
    name,vote = msg.split("$")
    if(vote == ""):
        votes[name] = "Pass"
        counted = count_votes(votes)
        print(counted)
        emit("votes_update",counted,broadcast = True, include_self = True)
        return counted
    choice = ""
    if(not vote_to_kill[0]):
        choice = knn(vote)
    else:
        choice = vote
    votes[name] = choice
    counted = count_votes(votes)

    return counted

def transitionTo(time):
    if time == "day":
        global_day = True
        emit("sunrise",broadcast = True, include_self = True)
        has_killed[0]=False
        has_protected[0]=False
        is_protected.clear()
        
        return
    if(time == "night"):
        global_day = False
        if check_end("night") == "bad":
            emit("pub_event","The game has ended, Bad Guys Win!",broadcast = True)
        elif check_end("night") == "good":
            emit("pub_event","The game has ended, Good Guys Win!", broadcast = True)
        else:
            emit("sunset",broadcast = True, include_self = True)
        
        return
def kill_player(name):
    players[name]=3
    emit("has_died",room = player_socket[name])
    emit("lobby_update",players,broadcast = True, include_self = True)

def roleInGame(role):
    for key,val in player_role.items():
        if val in role or role in val: 
            return True
    return False
#        
#
# End Helper Functions
#############################
#
# EVENTS
#Note on events: Each socket has an independant session. SO, calling emit() in one of these events, will send data to the current socket. (broadcast = True sends to all sockets)
#
#
@socketio.on("ready")  # when someone presses ready
def handle_ready(name): #
    players[name]=1
    emit("lobby_update",players, broadcast = True, include_self = True)
    if(countLivingPlayers() == len(players) and len(players)>=2):
        distribute_roles()
        emit("all_ready", broadcast = True, include_self = True)
    

@socketio.on("getrole") # when someone presses get role
def handle_getrole(name):
    emit("rec_role",player_role[name])
    if(countLivingPlayers() == len(players) and len(players)>=2):
        emit("pub_event","The Game has started!")


@socketio.on('register') # when someone presses register
def handle_register(name):
    if len(name)<2:
        return
    if name in players.keys():
        return
    players[name] = 0
    players_ip[name] = request.remote_addr
    ip_players[request.remote_addr] = name
    print("registered",name, players_ip[name])
    emit("redirect",{'url':url_for("lobby")})
    
@socketio.on("connected_lobby") # when someone connects to lobby
def handle_lobby_connect(message):
    #emit("getName",ip_players[request.remote_addr])
    emit("lobby_update",players, broadcast = True, include_self = True)
    emit("day")    

@socketio.on('message') # general message event for testing 
def handle_message(message):
    print('received message: ')
    print(message)
    send(message, broadcast = True) # send to all, false for send to the one who sent

@socketio.on("send_socket") # when a character connects, we save their socket so we can talk to them 
def save_socket(msg):
    
    player_socket[msg] = request.sid
    socket_player[request.sid] = msg
    if(len(undercover_badguy) == 1):
        if(undercover_badguy[0] == msg):
            emit("priv_event","You are an undercover agent for the bad guys. Use your abilities to help them.", room = player_socket[undercover_badguy[0]])


@socketio.on("nightfall")
def nightfall(name):
    emit("night")
    emit("night",room=player_socket[name])
    

@socketio.on("dawn")
def dawn(name):
    emit("day")
    emit("day",room=player_socket[name])

@socketio.on("vote") # When someone votes. Handles both regular and kill/save voting
def vote(msg):
    counted = {}
    counted = voting(msg)
    if(kill_save[0]):
        if "Kill" not in counted.keys():
           counted["Kill"] = 0
        if "Save" not in counted.keys():
           counted["Save"] = 0

    
    emit("votes_update",counted, broadcast = True, include_self = True)
    print("/// ",len(votes),countActivePlayers())
    if(len(votes) == countActivePlayers()):

        voted = vote_winner(counted)
        print(voted)
        print("all voted")
        if(kill_save[0]): #kill-save voting

            
            if(voted == "Kill"):
                players[vote_to_kill[0]] = 3
                emit("lobby_update",players,broadcast = True, include_self = True)
                emit("pub_event",vote_to_kill[0]+" was executed by the People!", broadcast = True, include_self = True)
                emit("has_died",room = player_socket[vote_to_kill[0]]) #how to talk to a specific player

            else:
                players[vote_to_kill[0]] = 1
                emit("lobby_update",players,broadcast = True, include_self = True)
                emit("pub_event","The People of Palermo have spared "+vote_to_kill[0]+"!", broadcast = True, include_self = True)

            emit("vote_end",broadcast = True, include_self = True)
            kill_save[0] = False
            counted.clear()
            votes.clear()
            

        else: #regular voting
            if(voted == "Pass"): #only true if everyone votes Pass
                emit("vote_end",broadcast = True, include_self = True)
                votes.clear()
                
                return
            players[voted] = 2
            emit("lobby_update",players,broadcast = True, include_self = True)
            
            vote_to_kill[0] = voted
            emit("vote_kill_save",voted, broadcast = True, include_self = True)
            votes.clear()
            kill_save[0] = True

@socketio.on("killer_kill") #convention for charcter-specific events
def killer_kill_handle(msg):
    if(players[role_player["killer"]] == 3 and not has_killed[0]): #Instead of timer, killer has a "skip"button when dead
        has_killed[0]=True
        speak("","The Killer has made his move")
        return

    if msg == "" or has_killed[0]:
        return
    choice = knn(msg)
    if players[choice] != 1:
        return
    if choice in is_protected:
        emit('pub_event', 'The Killer has FAILED to kill!!', broadcast = True, include_self = True)
        emit('priv_event', 'You have FAILED to kill!!')
        emit('has_killed')
        has_killed[0] = True
        speak("","The Killer has made his move")
        return
    
    has_killed[0] = True
    kill_player(choice)
    emit('pub_event', 'The Killer has killed poor {0}!!'.format(choice), broadcast = True, include_self = True)
    speak("","The Killer has made his move")
# players = {}
# players_ip = {}
# ip_players = {}
# player_role = {}
# role_player = {}

# player_socket = {}
# socket_player = {}
# votes = {}

@socketio.on("inspector_inspect")
def inspector_inspect(target):
    choice = knn(target)
    print("inspect "+choice)
    role = player_role[choice]
    judgement = ""
    if choice in bad_guys:
        if(np.random.random()<=0.7):
            judgement = "guilty"
        else:
            judgement = "innocent"
    else:
        if(np.random.random()<=0.7):
            judgement = "innocent"
        else:
            judgement = "guilty"
    
    if choice in framed:#framed always looks guilty
        judgement = "guilty"
    mess = choice + " seems "+judgement

    if(roleInGame("jesus")):
        if role_player["jesus"] == choice:
            mess ="You have seen The Light"
    emit("priv_event",mess) #emits to self. for multiple inspector disambiguation 

@socketio.on("jesus_rez")
def jesus_rez(target):
    choice = knn(target)
    role = player_role[choice]
    if players[choice] !=3:
        emit("priv_event",choice+" is alive",room = player_socket[role_player["jesus"]])
        return
    else:
        players[choice]=1
        emit("ressurected","",room = player_socket[choice])
        playSound("ressurect")
        emit("pub_event",choice+" has been ressurected!", broadcast = True,include_self = True)
        emit("lobby_update",players, broadcast = True, include_self = True)

       
@socketio.on("framer_frame")
def framer_frame(target):
    choice = knn(target)
    role = player_role[choice]
    # if players[choice] ==3:
    #     emit("priv_event",choice+" is dead",room = player_socket[role_player["jesus"]])
    #     return
    #else:
    if(role == "jesus"): #cannot frame jesus but thinks they did. 
        emit("priv_event","You framed "+choice, room = player_socket[role_player["framer"]])
        return


    if(len(framed) == 1):
        framed.clear()
        framed.append(choice)
    else:
        framed.append(choice)
    emit("priv_event","You framed "+choice, room = player_socket[role_player["framer"]])
 


@socketio.on("doctor_protect")
def doctor_protect(target):
    if(players[role_player["doctor"]] == 3): #instead of timer, has skip button
        speak("","The Doctor has acted")
        has_protected[0]=True
        return
    choice = knn(target)

    if len(is_protected) >0:
        is_protected.clear()
    is_protected.append(choice)
    has_protected[0]=True
    emit("priv_event","You are being protected",room = player_socket[choice])
    emit("priv_event","You protected "+choice,room = player_socket[role_player["doctor"]])
    emit("has_protected","", room = player_socket[role_player["doctor"]])
    speak("","The Doctor has acted")
    

@socketio.on("vigilante_vigilant")
def vigilante_vigilant(target):
    choice = knn(target)
    role = player_role[choice]
    if(players[choice] == 3): #instead of timer, has skip button
        emit("priv_event",choice+" already dead",room = player_socket[role_player["vigilante"]])
        return
        
    kill_player(choice)
    print(bad_guys)
    if(choice not in bad_guys):
        kill_player(role_player["vigilante"])
        emit("pub_event","The vigilante has failed!", broadcast = True, include_self = True)
        

    
    emit("pub_event","The vigilante has killed "+choice, broadcast = True, include_self = True)
    playSound("vigilant")



@socketio.on("mafia_convert")
def mafia_convert(target): #converts during the night
    if(players[role_player["mafia"]] == 3): #instead of timer, has skip button
        speak("","The Doctor has acted")
        has_protected[0]=True
        return

    if(target == ""):
        speak("","The Mafia has acted")
        return
    choice = knn(target)
    role = player_role[choice]
    if(players[choice] == 3): #instead of timer, has skip button
        emit("priv_event","Cannot convert dead player",room = player_socket[role_player["mafia"]])
        return
    if(role == "jesus"):
        emit("priv_event","You cannot convert Jesus",room = player_socket[role_player["mafia"]])
        has_converted[0]=True
        emit("has_converted","",room = player_socket[role_player["mafia"]])
    if(choice in bad_guys):
        emit("priv_event","Player already bad",room = player_socket[role_player["mafia"]])
        return

    bad_guys.append(choice) #now a bad guy
    print(bad_guys)
    emit("priv_event","You have been converted by "+role_player["mafia"],room = player_socket[choice])
    emit("priv_event","You converted "+choice,room = player_socket[role_player["mafia"]])
    emit("has_converted","",room = player_socket[role_player["mafia"]])
    speak("","The Mafia has acted")

@socketio.on("bomber_target")
def bomber_target(target):
    if(target == ""):
        return
    choice = knn(target)
    role = player_role[choice]
    if(players[choice] == 3): #instead of timer, has skip button
        emit("priv_event",choice+" already dead",room = player_socket[role_player["bomber"]])
        return
        
    if len(jihad_target)>0:
        jihad_target.clear()

    jihad_target.append(choice)
    emit("priv_event","Targeted the infidel "+choice,room = player_socket[role_player["bomber"]])
    


@socketio.on("bomber_dead")
def bomber_dead(msg):
    if global_day == True:
        print("died in day")
        if len(jihad_target)!=0:
            kill_player(jihad_target[0])
            emit('pub_event', 'The bomber has killed '+jihad_target[0], broadcast = True, include_self = True)
            playSound("jihad")

@socketio.on("informant_inform")
def informant_inform(msg):
    choice = knn(msg["target"])
    text = msg["message"]
    emit("priv_event",text,room = player_socket[choice])


@socketio.on("sleep_control")
def handle_sleep_control(msg):
    print(socket_player[request.sid] , msg)
    kailes = [].copy()
    if msg == 'sleep':
        players_sleep[ socket_player[request.sid] ] = 1
        
        for player, isAsleep in players_sleep.items():
            if players[player] == 1 and player not in jailed and isAsleep == 0:
                kailes.append(player)
        print(kailes)
        if len(kailes) <= 3 and len(kailes) != 0:
            mesg = ''
            for i in kailes:
                mesg += ' '+ i
            emit('pub_event', 'The following players'+ mesg + ' are not yet asleep!!', broadcast = True, include_self = True)

        print(len(kailes))
        if len(kailes) == 0:
            transitionTo('night')
            kailes.clear()

    else:
        players_sleep[ socket_player[request.sid] ] = 0
        
        for player, isAsleep in players_sleep.items():
            if players[player] == 1 and player not in jailed and isAsleep == 1:
                kailes.append(player)
        
        if len(kailes) <= 3 and len(kailes) != 0:
            mesg = ''
            for i in kailes:
                mesg += ' '+i
            emit('pub_event', 'The following players'+ mesg + ' are not yet awake!!', broadcast = True, include_self = True)

        if not kailes:
            transitionTo('day')
            kailes.clear()
    
    # Determine if all are asleep or awake

@socketio.on("speak")
def handle_speak(msg):
    if(msg['to'] == "all"):
        speak("",msg["mess"])
        return
    mess = '<font color = "red">'+msg["mess"]+'</font>'
    if(msg['to'] == "medium"):
        emit("priv_event",mess,room = player_socket[role_player["medium"]])


#Routing
connected_to_pages = [False, False, False, False,False,False,False, False, False,False,False]

@app.route("/<name>/killer")
def killer(name):
    if not connected_to_pages[0]:
        connected_to_pages[0] = True
        return render_template("killer.html")
    else:
        return "<h1>Orestis-proof security systems engaged</h1>"

@app.route("/<name>/citizen")
def citizen(name):
    if not connected_to_pages[1]:
        connected_to_pages[1] = True
        return render_template("citizen.html")
    else:
        return "<h1>Orestis-proof security systems engaged</h1>"
@app.route("/<name>/inspector")
def inspector(name):
    # if not connected_to_pages[3]:
    #     connected_to_pages[3] = True
    #     return render_template("inspector.html")
    # else:
    #     return "<h1>Orestis-proof security systems engaged</h1>"
    return render_template("inspector.html") #for multiple inspectors?
@app.route("/<name>/medium")
def medium(name):
    if not connected_to_pages[2]:
        connected_to_pages[2] = True
        return render_template("medium.html")
    else:
        return "<h1>Orestis-proof security systems engaged</h1>"

@app.route("/<name>/doctor")
def doctor(name):
    if not connected_to_pages[4]:
        connected_to_pages[4] = True
        return render_template("doctor.html")
    else:
        return "<h1>Orestis-proof security systems engaged</h1>"


@app.route("/<name>/jesus")
def jesus(name):
    if not connected_to_pages[5]:
        connected_to_pages[5] = True
        return render_template("jesus.html")
    else:
        return "<h1>Orestis-proof security systems engaged</h1>"

@app.route("/<name>/vigilante")
def vigilante(name):
    if not connected_to_pages[6]:
        connected_to_pages[6] = True
        return render_template("vigilante.html")
    else:
        return "<h1>Orestis-proof security systems engaged</h1>"

@app.route("/<name>/framer")
def framer(name):
    if not connected_to_pages[7]:
        connected_to_pages[7] = True
        return render_template("framer.html")
    else:
        return "<h1>Orestis-proof security systems engaged</h1>"

@app.route("/<name>/bomber")
def bomber(name):
    if not connected_to_pages[8]:
        connected_to_pages[8] = True
        return render_template("bomber.html")
    else:
        return "<h1>Orestis-proof security systems engaged</h1>"      

@app.route("/<name>/mafia")     
def mafia(name):
    if not connected_to_pages[8]:
        connected_to_pages[8] = True
        return render_template("mafia.html")
    else:
        return "<h1>Orestis-proof security systems engaged</h1>"

@app.route("/<name>/informant")     
def informant(name):
    if not connected_to_pages[9]:
        connected_to_pages[9] = True
        return render_template("informant.html")
    else:
        return "<h1>Orestis-proof security systems engaged</h1>"


@app.route("/")
def register():
    
    return render_template("register.html")

@app.route("/lobby",methods=["GET","POST"])
def lobby():
 
    return render_template("lobby.html",name= request.form["username"])

if __name__ == '__main__':
    
    socketio.run(app,host = "0.0.0.0",port = 28001, log_output = False, debug = True)
