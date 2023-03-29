import dash.dependencies
import dash_daq as daq
from dash import html, Input, Output, dcc, Dash
import dash_bootstrap_components as dbc
import time
import RPi.GPIO as GPIO
import Freenove_DHT as DHT
#  For Sending And Receiving Email
import smtplib, ssl
import imaplib
import email
import traceback
# For Getting Values From MQTT Broker
import random
from paho.mqtt import client as mqtt_client

# Circuit Start ================================================================

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

ledPin = 21
GPIO.setup(ledPin, GPIO.OUT)
# fanPin =
# GPIO.setup(fanPin, GPIO.OUT)

DHTPin = 17 #define the pin of DHT11
dht = DHT.DHT(DHTPin) #create a DHT class object
dht.readDHT11()

#  For DC Motor
# Motor1 = 22 # Enable Pin
# Motor2 = 27 # Input Pin
# Motor3 = 5 # Input Pin
# GPIO.setup(Motor1,GPIO.OUT)
# GPIO.setup(Motor2,GPIO.OUT)
# GPIO.setup(Motor3,GPIO.OUT) 

# Circuit End ==================================================================

# Variables Start===============================================================

currentTemperature = 0
currentHumidity = 0

global is_sent
is_sent = False
response = False

# Var For Sending Email
# emailSender = '2069192@iotvanier.com'
# emailSender = '2042827@iotvanier.com'
emailSender = 'DJCGrocery@gmail.com'
# emailReceivers = ['2042827@iotvanier.com']
emailReceivers = ['dinal.dd.patel@gmail.com']

# Var For Reading Email
# ORG_EMAIL   = "@iotvanier.com"
# FROM_EMAIL  = "2069192" + ORG_EMAIL
# FROM_PWD    = "2069192"
# SMTP_SERVER = "192.168.0.11"
ORG_EMAIL   = "@gmail.com"
FROM_EMAIL  = "DJCGrocery" + ORG_EMAIL
FROM_PWD    = "123dJcGrocery"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT   = 993

# For MQTT Broker
broker = 'broker.emqx.io'
port = 1883
topic = "light-intensity"
# generate client ID with pub prefix randomly
client_id = f'python-mqtt-{random.randint(0, 100)}'
# username = 'emqx'
# password = 'public'

# Variables End ================================================================

# UI Start =====================================================================

# Dash App that includes Bootstrap and Font Awesome Icons
app = dash.Dash(__name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP,dbc.icons.FONT_AWESOME]
)

# Web page title
app.title = 'CasaConnect'

# Time Variable for Display
t = time.localtime()
current_time = time.strftime("%H:%M%p", t)

# Header navigation Links
nav = html.Div(children='Log In', style={'text-align': 'center'})

# Page header containing Logo and future Log-In feature
header = html.Header(children=[
    html.Section(children=[
        html.Div(id='Logo-full', children=[
        html.Img(src=app.get_asset_url('logo_full.png'), width='400rem', ),
        ], className=""),

                dbc.NavbarSimple(children=[
                    dbc.NavItem(dbc.NavLink(nav), style={'text-align': 'end'}),
                ]),
            ], className="container d-flex justify-content-between py-3")
    ],className='bg-light shadow-lg'
)

# Card that controls the LED
# Used ID: led-power-button
ledCard = html.Div(children=[
                    html.Div(children='Lighting:', className='display-6 ms-3'),
                        html.Div(children=[
                            html.Div(children=[], className='d-flex justify-content-center mt-4 mb-3', id='led-power-button-result'),
                            daq.PowerButton(
                                id='led-power-button',
                                className='mt-3 mb-2',
                                color='#ffe100',
                                size=75,
                                on=False
                            ),
                        ],className="card rounded-4 w-100 bg-light py-2 px-4 m-3 h-75 shadow-sm"),
                    ], className='w-25')

# Card that controls the Fan
# Used ID: fan-power-button
fanCard = html.Div(children=[
                        html.Div(children='Fan:', className='display-6 ms-3'),
                        html.Div(children=[
                            html.Div(children=[], className='d-flex justify-content-center mt-4 mb-3', id='fan-power-button-result'),
                            daq.PowerButton(
                                id='fan-power-button',
                                className='mt-3 mb-2',
                                color='#9eff00',
                                size=75,
                                on=False
                            ),
                        ],className="card rounded-4 w-100 bg-light py-2 px-4 m-3 h-75 shadow-sm"),
                    ], className='w-25 ')

# Card that displays the Temperature, Humidity, and Light Intensity
# Used ID's: current-thermometer, current-humidity, current-light-intensity
metricsCard = html.Div(children=[
                    dcc.Interval(id='interval', interval=3000, n_intervals=0),
                    html.Div(children=['Climate:', html.Button(id='', className='btn btn-primary mt-1', children=['Adjust'])], className='display-6 ms-3 d-flex justify-content-between align-items-center me-3'),
                    html.Div(children=[
                            html.Div(id='', children=[
                                daq.Thermometer(
                                    id='current-thermometer',
                                    label='Current temperature',
                                    labelPosition='top',
                                    value=currentTemperature,
                                    min=15,
                                    max=30,
                                    className="",
                                    showCurrentValue=True,
                                    units="C",
                                ),
                            ], className="d-inline-flex flex-column h-75"),
                            #Thermometer Slider Will be used in User preference setting.
                            #     dcc.Slider(
                            #         id='thermometer-slider',
                            #         value=20,
                            #         step=1,
                            #         min=15,
                            #         max=30,
                            #     ),
                            html.Div(id='', children=[
                            daq.GraduatedBar(
                                color={"gradient":True,"ranges":{"#1b8bd1":[0,6],"#ffe100":[6,10]}},
                                id='current-light-intensity',
                                label='Current Illumination',
                                showCurrentValue=True,
                                value=5,
                                max=10,
                                min=0,
                                className="h-25"

                            ),
                            daq.Gauge(
                                color={"gradient":True,"ranges":{"#ff001e":[0,25], "#ffe100":[25,30], "#9eff00":[30,60], "#ffe101":[60,70], "#ff002e":[70,100]}},
                                showCurrentValue=True,
                                id='current-humidity',
                                units="%",
                                value=currentHumidity,
                                label='Current Humidity',
                                max=100,
                                min=0,
                                className="h-75"
                            )
                            ], className="d-inline-flex flex-column"),
                    ],className="card d-flex justify-content-around flex-row rounded-4 w-90 h-75 bg-light py-2 m-3 mb-0 shadow-sm"),
                ], className='w-50')

# Page body that assembles all the components
body = html.Main(children=[
        dbc.Container(children=[
             html.H1(id='', className='container mt-3 d-flex justify-content-between', children=['Dashboard:', html.Div(children=['It is ',current_time], className="display-6", style={'color':'#1b8bd1'})]),
             html.Hr(children=[]),
                dbc.Row([
                    ledCard,
                    fanCard,
                    metricsCard,
                ], className='mb-3'),

            ], className=" rounded-4 card m-4 shadow")
            # ])
        ], className="flex-shrink-0 d-flex justify-content-center"
    );

# Page footer containing credits information
footer = html.Footer([
            html.Div(className="container text-center ", children=[
                  html.Small(children=['2023 © CasaConnect by ', html.Span(children='GREEN', className='text-success', style={'filter': 'drop-shadow(0 0 80px green)'}), ' Team'])
            ]),
            ],id='sticky-footer', className="fixed-bottom py-4 bg-dark text-white-50 ")

# Page layout that assembles Header, Body and Footer
app.layout = html.Div(id="theme-switch-div", children=[
    header,
    body,
    footer
    ]);


# UI End =====================================================================

# Back-end Start==============================================================

# Temperature and Humidity Reading qnd Displaying
@app.callback(
    Output('current-thermometer', 'value'),
    Output('current-humidity', 'value'),
    Input('interval', 'n_intervals'))
def update_sensor(n_intervals):
#     global is_sent
    dht.readDHT11()
#     temperatureValue = dht.temperature;
    temperatureValue = 25;
    currentHumidity = dht.humidity;
#     currentHumidity = 25;
    
    if(temperatureValue > 24 and is_sent == False):
#         send_email(str(temperatureValue))
        send_email_temp(str(temperatureValue))
    elif(is_sent == True):
        print ('email already sent')
        
    check_for_reply()
    
    if(response == True):
        read_email()

    return temperatureValue, currentHumidity

# Sending Email for Temperature
def send_email_temp(temperatureValue):
    global is_sent
    is_sent = True
    message = "From: " + emailSender + """
To: To Person <'dinal.dd.patel@gmail.com'>
Subject: Current Temperature Reading

The current temperature is """ + temperatureValue + ". Would you like to turn on the fan?"

#     try:
    
    smtpObj = smtplib.SMTP('192.168.0.11') 
#     smtpObj = smtplib.SMTP('192.168.50.15')
    smtpObj.sendmail(emailSender, emailReceivers, message)         
    print ("Successfully sent email")
    
#     except SMTPException:
#        print ("Error: unable to send email")

# Sending Email for Light Intensity
def send_email_light(light):
    global is_sent
    is_sent = True
    t = time.localtime()
    current_time = time.strftime("%H:%M%p", t)
    message = "From: " + emailSender + """
To: To Person <'dinal.dd.patel@gmail.com'>
Subject: Current Temperature Reading

The list is ON at """ + current_time 

#     try:
    
    smtpObj = smtplib.SMTP('192.168.0.11') 
#     smtpObj = smtplib.SMTP('192.168.50.15')
    smtpObj.sendmail(emailSender, emailReceivers, message)         
    print ("Successfully sent email")
    
#     except SMTPException:
#        print ("Error: unable to send email")

def send_email_wth_gmail(temp):
    global is_sent
    is_sent = True
    port = 587  # For SSL
    smtp_server = "smtp.gmail.com"
#     message = "From: " + emailSender + """
#     To: To Person <'dinal.dd.patel@gmail.com'>
#     Subject: Current Temperature Reading
# 
#     The current temperature is """ + temp + ". Would you like to turn on the fan?"
    message = """
    Subject: Current Temperature Reading

    The current temperature is """ + temp + ". Would you like to turn on the fan?"

    s = smtplib.SMTP(smtp_server, port)
    s.starttls()
    s.login(emailSender, FROM_PWD)
    s.sendmail(emailSender, emailReceivers, message)
    print ("Successfully sent email")


def check_for_reply():
    global response
#     try:
    mail = imaplib.IMAP4_SSL(SMTP_SERVER)
    mail.login(FROM_EMAIL,FROM_PWD)
    mail.select('inbox')
        
    data = mail.search(None, '(SUBJECT "Re: Current Temperature Reading")')
    if(data != None):
        response = True
    else:
        response = False
        
#  Reading Email
def read_email():
    try:
        mail = imaplib.IMAP4_SSL(SMTP_SERVER)
        mail.login(FROM_EMAIL,FROM_PWD)
        mail.select('inbox')
        
        data = mail.search(None, '(SUBJECT "Re: Current Temperature Reading")')
#	message_ids = messages[0].split(b'')
        mail_ids = data[1]
        id_list = mail_ids[0].split()   
        first_email_id = int(id_list[0])
        latest_email_id = int(id_list[-1])
#	latest_email_id = message_ids[-1]

#         for i in range(latest_email_id,first_email_id, -1):
        data = mail.fetch(str(i), '(RFC822)' )
        for response_part in data:
            arr = response_part[0]
            if isinstance(arr, tuple):
                msg = email.message_from_string(str(arr[1],'utf-8'))
                email_subject = msg['subject']
                email_from = msg['from']
                print('From : ' + email_from + '\n')
                print('Subject : ' + email_subject + '\n')
#	return email_subject
#	imap.close()
#	imap.logout()

    except Exception as e:
        traceback.print_exc() 
        print(str(e)

def connect_mqtt() -> mqtt_client:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
        print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")

    client.subscribe(topic)
    client.on_message = on_message


def run():
    client = connect_mqtt()
    subscribe(client)
    client.loop_forever()


# if __name__ == '__main__':
#     run()

# LED Control Callback Logic
@app.callback(
    Output('led-power-button-result', 'children'),
    Input('led-power-button', 'on')
)
def update_output(on):
    if on:
        GPIO.output(ledPin, GPIO.HIGH)
        img = html.I(className="fa-solid fa-lightbulb blob", style={'font-size': '10rem', 'color': '#ffe100', 'filter': 'drop-shadow(0 0 50px #eac86c)'})
        return img

    else:
        GPIO.output(ledPin, GPIO.LOW)
        img = html.I(className="fa-regular fa-lightbulb ", style={'font-size': '10rem', 'color':'#1b8bd1'})
        return img

# Fan Control Callback Logic
@app.callback(
    Output('fan-power-button-result', 'children'),
    Input('fan-power-button', 'on')
)
def update_output(on):
    if on:
        # GPIO.output(fanPin, GPIO.HIGH)
#         GPIO.output(Motor1,GPIO.HIGH)
#         GPIO.output(Motor2,GPIO.LOW)
#         GPIO.output(Motor3,GPIO.HIGH)
#         sleep(5)
# 
#         GPIO.output(Motor1,GPIO.HIGH)
#         GPIO.output(Motor2,GPIO.HIGH)
#         GPIO.output(Motor3,GPIO.LOW)
# 
#         sleep(5)
#         GPIO.output(Motor1,GPIO.LOW)
#         GPIO.cleanup() 
        img = html.I(className="fa-solid fa-fan rotating", style={'font-size': '10rem', 'color': '#9eff00', 'filter': 'drop-shadow(0 0 20px #009eff)'})
        return img

    else:
        # GPIO.output(fanPin, GPIO.LOW)
#         GPIO.output(Motor1,GPIO.LOW)
#         GPIO.output(Motor2,GPIO.LOW)
#         GPIO.output(Motor3,GPIO.LOW)
        img = html.I(className="fa-solid fa-fan ", style={'font-size': '10rem', 'color':'#1b8bd1'})
        return img

# Thermometer Logic to be used for User preference setting.
# @app.callback(
#     Output('current-thermometer', 'value'),
#     Input('thermometer-slider', 'value')
# )
# def update_thermometer(value):
#     return value

# Thermometer Color Change Logic
@app.callback(
    Output('current-thermometer', 'color'),
    [Input('current-thermometer', 'value')]
)
def update_therm_col(val):
    if val >= 27:
        return '#ff001e'
    elif val >= 25:
        return '#ffe100'
    elif val >= 20:
        return '#9eff00'
    elif val < 20:
        return '#1b8bd1'


# Use the above 'port' property in case "Port already in use error" e.g set 'port=8051'
def main():
    app.run_server(debug=True, host='localhost', port=8050)

main()

# Back-end End==============================================================
