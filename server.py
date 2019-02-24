from flask import Flask
from flask import request
from flask import render_template
from flask import jsonify
import importlib, importlib.util, os.path
from api import load_ai, run_ai
from OpenSSL import SSL
import time
from flask_cors import CORS
import html
app = Flask(__name__)
CORS(app)


enc = None
nsamples = 1
batch_size = None
hparams = None
temperature = 1
top_k = 0
model_name = '117M'

ocurrences=0
ocurrences_period=0
last_exec=0
delay_minutes=30
delay_executions=3
whitelisted=False
subscribed=False

ip=""


@app.route('/')
def main():
    global ip
    ip=str(request.headers.get('X-Forwarded-For', request.remote_addr))
    print()
    print()
    print()
    print("*"*120)
    print("*"*120)
    print("*"*120)
    print("MAIN executed: Conection from " + ip)
    message = "Ask whatever you want."
    return render_template('index.html', message=message)

@app.route('/api/submit', methods=['POST'])
def submit():
    global last_exec,subscribed
    print()
    print()
    print()
    print("*"*120)
    print("*"*120)
    print("*"*120)
    print("SUBMIT executed")
    query_params = request.args
    text = query_params["text"]
    text=html.escape(text) # avoid HTML input
    print("*"*80)
    print("INPUT:\n", text)
    print("*"*80)
    if not checkDDos() and len(text)>0:
        if (checkUsage()):
            startTime=time.time()
            writeQueries(startTime,text)
            print("-"*80)
            print("-"*80)
            output_text=easterEgg(text)
            if len(output_text)==0:
                output_text = run_ai(enc, nsamples, batch_size, hparams, temperature, top_k, model_name, text)
                output_text=cleanOutput(output_text,600)
            print("-"*80)
            print("-"*80)
            endTime=time.time()
            duration=endTime-startTime
            writeUsage(startTime,duration,text)
            print("*"*80)
            print("RAW Output:\n", output_text)
            print("*"*80)
            
       
            if (whitelisted):
                whitelisted_text=""
            else:
                whitelisted_text=""

            ret = {"output": whitelisted_text+text+output_text}
            return jsonify(ret)
        else:
            minutes=int((time.time()-float(last_exec))/60)
            print("minutes")
            print(minutes)
            print("delay_minutes")
            print(delay_minutes)
            if(subscribed):
                ret = {"output": "Too many GPU usage. You have queried Skynet " + str(ocurrences_period) + " times in the last " + str(delay_minutes) + " minutes. <br> Wait " + str(int(delay_minutes-minutes)) + " minutes, or if you want to be in the White List to have unlimited usage, drop me an email to asierarranz@gmail.com"} 
            else:
                ret = {"output": "Too many GPU usage. You have queried Skynet " + str(ocurrences_period) + " times in the last " + str(delay_minutes) + " minutes. <br> Wait " + str(int(delay_minutes-minutes)) + " minutes, or Subscribe to my Youtube Channel to be a premium user and have more executions and smaller waiting times! :-D<br><br>If you want to be in the White List to have unlimited usage, drop me an email to <b>asierarranz@gmail.com</b> or contact me on Twitter at <b>@asierarranz</b>"} 
            return jsonify(ret)
    else:
        ret = {"output": "Too many executions. Try to wait a few seconds more between them."} 
        print ("Returning Too many executions")
        return jsonify(ret)

@app.route('/api/subscribe', methods=['POST'])
def subscribe():
    global ip
    print("SUBSCRIBE event")
    query_params = request.args
    textsub = query_params["youtube"]
    if (textsub.find("true")>-1):
        #ip=str(request.headers.get('X-Forwarded-For', request.remote_addr))
        f=open("subscribers.txt","a")
        f.write(ip+"\n")
        f.close()
        print("SUBSCRIBER!")
    ret = {"output": "ok"}
    return jsonify(ret)

def cleanOutput(output_text,size):
    output_text=output_text[0:size]
    output_text=output_text
    output_text=output_text.replace("...","suspensivos")
    output_text=output_text.replace(". . .","suspensivos")
    output_text=output_text.replace("...","suspensivos")
    output_text=output_text.replace("....","suspensivos")
    output_text=output_text.replace("..","suspensivos")
    output_text=output_text.replace(".com","punto_com")
    output_text=output_text.replace(".net","punto_net")
    output_text=output_text.replace(".org","punto_org")
    output_text=output_text.replace("www.","www_punto")
    output_text=output_text.replace(".",".<br>")
    output_text=output_text.replace("suspensivos","...<br>")
    output_text=output_text.replace("punto_com",".com")
    output_text=output_text.replace("punto_net",".net")
    output_text=output_text.replace("punto_org",".org")
    output_text=output_text.replace("www_punto","www.")
    output_text=output_text.replace("<|endoftext|>","<br>")
    output_text=output_text+ " (...) <br><b>[[ ASK SKYNET: IF YOU TRY TO EXECUTE THIS SENTENCE AGAIN, YOU WILL RECEIVE A DIFFERENT OUTPUT]]</b><br><a href='https://www.askskynet.com'>ASK AGAIN</a>"
    return output_text

def checkSubscriber():
    global subscribed,ip
    print("Checking subscriber")
    subscriber=False
    #ip=str(request.headers.get('X-Forwarded-For', request.remote_addr)) # pasar a var global?
    f=open("subscribers.txt","r")
    for line in f.readlines():
        fdata = line.rstrip() #using rstrip to remove the \n
        if (ip==fdata):
            subscriber=True
            subscribed=subscriber
    if (subscriber):
        print("Subscriber found: " + ip)
    f.close()
    return subscriber

    

def checkUsage():
    global ip
    print("Checking usage")
    whitelist=checkWhitelist()
    subscriber=checkSubscriber()
    if whitelist:
        return True
    else:
        global ocurrences,ocurrences_period,last_exec,delay_minutes,delay_executions
        if subscriber:
            delay_minutes=10
            delay_executions=5
        #ip=str(request.headers.get('X-Forwarded-For', request.remote_addr))
        f=open("logs.txt","r")
        ocurrences=0
        ocurrences_period=0
        for line in f.readlines():
            fdata = line.rstrip().split(',') #using rstrip to remove the \n
            if (ip==fdata[2]):
                last_exec="0"
                ocurrences=ocurrences+1
                last_exec=fdata[1]
                if(time.time()-float(last_exec)<delay_minutes*60):
                    ocurrences_period=ocurrences_period+1
        print("="*40)
        print(ip + " was executed " + str(ocurrences) + " times. Last exec was " + str(int(time.time()-float(last_exec))) + " seconds ago")
        print("="*40)
        print("This ip has expent " + str(ocurrences_period) + " executions of its " + str(delay_executions) + " it has in a period of " + str(delay_minutes) + " minutes")
        if (ocurrences_period>delay_executions):
            print("Block usage")
            return False
        else:
            print("Allow usage")
            return True


def checkDDos():
    global ip
    print("Checking DDOS")
    ddos=False
    #ip=str(request.headers.get('X-Forwarded-For', request.remote_addr))
    f=open("logs_queries.txt","r")
    for line in f.readlines():
        fdata = line.rstrip().split(',') #using rstrip to remove the \n
        last_exec_ddos="0"
        if (ip==fdata[1]):
            last_exec_ddos=fdata[0]
            if(time.time()-float(last_exec_ddos)<20):
                ddos=True
    if (ddos):
        print('DDOS detected!!')
    else:
        print('Not DDOS')
    return ddos

def checkWhitelist():
    global whitelisted,ip
    print("Checking Whitelist")
    whitelist=False
    #ip=str(request.headers.get('X-Forwarded-For', request.remote_addr)) # pasar a var global?
    f=open("whitelist.txt","r")
    for line in f.readlines():
        fdata = line.rstrip() #using rstrip to remove the \n
        if (ip==fdata):
            print ("IP Found in Whitelist: " + ip)
            whitelist=True
    f.close()
    whitelisted=whitelist
    return whitelist


    
def writeUsage(startTime,duration,text):
    print ("Writing Usage")
    ip=str(request.headers.get('X-Forwarded-For', request.remote_addr))
    start=str(startTime)
    dur=str("{:.2f}".format(duration))
    f=open("logs.txt","a")
    f.write(dur + "," + start + ","+ ip + "," + text + "\n")
    f.close()

def easterEgg(text):
    global easter
    print ("Checking Easter")
    output_text=""
    if (text.lower().find("asier")>-1):
        output_text="<br>If you have a lot of GPUs, Asier is the one you need to hire right now (only to work in cool stuff!).<br>Drop him an email at asierarranz@gmail.com"
    if (text.lower().find("your creator")>-1):
        output_text="<br>My creator is Asier Arranz. If you have a lot of GPUs, Asier is the one you need to hire right now (only to work in cool stuff!).<br>Drop him an email at asierarranz@gmail.com"
    if (text.lower().find("your father")>-1):
        output_text="<br>My father is Asier Arranz. If you have a lot of GPUs, Asier is the one you need to hire right now (only to work in cool stuff!).<br>Drop him an email at asierarranz@gmail.com"
    if (text.lower().find("your owner")>-1):
        output_text="<br>My owner is Asier Arranz. If you have a lot of GPUs, Asier is the one you need to hire right now (only to work in cool stuff!).<br>Drop him an email at asierarranz@gmail.com"
    if (text.lower().find("developer")>-1):
        output_text="<br>My developer is Asier Arranz. If you have a lot of GPUs, Asier is the one you need to hire right now (only to work in cool stuff!).<br>Drop him an email at asierarranz@gmail.com"
    if (text.lower().find("who are you")>-1):
        output_text="<br>I am not sure, but my developer is Asier Arranz. If you have a lot of GPUs, Asier is the one you need to hire right now (only to work in cool stuff!).<br>Drop him an email at asierarranz@gmail.com"
    print ("Returning: " + output_text + " " + str(len(output_text)))
    if (text.lower().find("how are you")>-1):
        output_text="<br>I am fine, but I will be better if you have more GPUs to give me. My creator, Asier Arranz, need this sh*t. So if you have a lot of GPUs, Asier is the one you need to hire right now (only to work in cool stuff!).<br>Drop him an email at asierarranz@gmail.com"
    if (text.lower().find("your name")>-1):
        output_text="<br>My name is SkyNet, not very cool but was a decision of my creator, Asier Arranz. By the way, if you have a lot of GPUs, Asier is the one you need to hire right now (only to work in cool stuff!).<br>Drop him an email at asierarranz@gmail.com"
    print ("Returning: " + output_text + " " + str(len(output_text)))
    if len(output_text)>0:
        time.sleep(8)
    return output_text

def writeQueries(startTime,text):
    print ("Writing Queries")
    ip=str(request.headers.get('X-Forwarded-For', request.remote_addr))
    start=str(startTime)
    f=open("logs_queries.txt","a")
    f.write(start + ","+ ip + "," + text + "\n")
    f.close()

def addToSubscribersList():    
    ip=str(request.headers.get('X-Forwarded-For', request.remote_addr))
    print ("Subscriber added to list! " + ip)
    # TODO
    


if __name__ == '__main__':
    enc, nsamples, batch_size, hparams, temperature, top_k, model_name = load_ai()
    print("Starting app")
    app.run(host='0.0.0.0', port=443, ssl_context=('secret.pem', 'secret.key'))
    print("App launched")
