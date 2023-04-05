import dash.dependencies
import dash_daq as daq
from dash import html, Input, Output, dcc, Dash, State
import dash_bootstrap_components as dbc
import time
from datetime import datetime
import RPi.GPIO as GPIO
import Freenove_DHT as DHT
#  For Sending And Receiving Email (Old Version)
import smtplib, ssl
import imaplib
import easyimap as imap
import email
import traceback

# For Sending And Receiving Email
from email_reader import *
# For Getting Values From MQTT Broker
import random
from paho.mqtt import client as mqtt_client
# For DB profile storage
import sqlite3
from sqlite3 import Error

# Circuit Start ================================================================

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

ledPin = 19
GPIO.setup(ledPin, GPIO.OUT)

DHTPin = 17 #define the pin of DHT11
dht = DHT.DHT(DHTPin) #create a DHT class object
dht.readDHT11()

#  For DC Motor
Motor1 = 22 # Enable Pin
Motor2 = 27 # Input Pin
Motor3 = 5 # Input Pin
GPIO.setup(Motor1,GPIO.OUT)
GPIO.setup(Motor2,GPIO.OUT)
GPIO.setup(Motor3,GPIO.OUT)

# Circuit End ==================================================================

# Variables Start===============================================================
global currentTempValue
currentTempValue = 0.0
global currentHumidity
currentTemperature = 0
currentHumidity = 0
global current_light_intensity
current_light_intensity = 0.0

global is_sent
is_sent = False
response = False

# To be used for user preferences
global tagID, username, uTempThreshold, uHumidityThreshold, uLightThreshold

emailSent = False
emailLightSent = False
global emailReceived
emailReceived = False
global message, message2
message=''
message2=''

tagID = "NaN"
username = ""
uTempThreshold = 24.0
uHumidityThreshold = 0
uLightThreshold = 400


# Var For Reading Email
receiverEmail = 'vlasveaci@gmail.com'

# For MQTT Broker
broker = '192.168.0.159'
#topic = "light-intensity"
port = 1883
topic = "get-light-intensity"
# generate client ID with pub prefix randomly
client_id = f'python-mqtt-{random.randint(0, 100)}'

# Variables End ================================================================

# UI Start =====================================================================

# Dash App that includes Bootstrap and Font Awesome Icons
app = dash.Dash(__name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP,dbc.icons.FONT_AWESOME]
)

# Web page title
app.title = 'CasaConnect'

# Time Variable for Display
global current_time
t = time.localtime()
current_time = time.strftime("%H:%M%p", (time.localtime()))

userPhoto = html.Img(src=app.get_asset_url('avatar.png'),width='15%', height='15%', style={'border-radius': '50%'})

#Preferences
offcanvas = html.Div(children=[
        dbc.Offcanvas(
            html.Div(
            [
                html.Div(style={'text-align': 'center'},children=[
                      html.Img(src=app.get_asset_url('avatar.png'), width='50%', height='50%', className=" mb-3", style={'border-radius': '50%'})
            ]),
                dbc.Row(
                [
                    dbc.Col(html.Div("Name: ")),
                    dbc.Col(html.Div(dbc.Input(id="username", placeholder="username", size="md", className=" mb-4", readonly=True))),
                ]),
                dbc.Row(
                [
                    dbc.Col(html.Div("Ideal Temperature: ")),
                    dbc.Col(html.Div(dbc.Input(id="tempThreshold",placeholder="ideal_temp", size="md", className="mb-3", readonly=True))),
                ]),
                dbc.Row(
                [
                    dbc.Col(html.Div("Ideal Humidity: ")),
                    dbc.Col(html.Div(dbc.Input(id="humidityThreshold",placeholder="ideal_humidity", size="md", className="mb-3", readonly=True))),
                ]),
                dbc.Row(
                [
                    dbc.Col(html.Div("Ideal light intensity: ")),
                    dbc.Col(html.Div(dbc.Input(id='lightIntensity',placeholder="ideal_light_intensity", size="md", className="mb-3", readonly=True))),
                ]),
                dbc.Row(
                [
                 #Thermometer Slider Will be used in User preference setting.
                    dcc.Slider(
                        id='thermometer-slider',
                        value=20,
                        step=1,
                        min=15,
                        max=30,
                    ),
                ])
            ]),
            id="offcanvas-backdrop",
            title="User information",
             backdrop=False,
             scrollable=True,
            is_open=False,
        )])



#Login Acordion
collapse= html.Div(children=[
        html.Div(className='fs-2',id='userTab'),
        dbc.Button(
            children=["Change User"],
            id="collapse-button",
            className="mb-3",
            color="dark",
            outline=True,
            n_clicks=0,
        ),

        dbc.Collapse(
            dbc.Card(dbc.CardBody(dbc.Form(
                dbc.Row(
            [

            dbc.Col(
                dbc.Input(id="id-input", type="text", placeholder="Enter User ID"),
                className="me-3",
            ),
            dbc.Col(dbc.Button("Submit",id="submit-button", color="primary"), width="auto"),
            ],
            className="g-2",
            )
            ))),
            id="collapse",
            is_open=False,
        ),
    ])

# Header navigation Links
nav = html.Div(children=[collapse,offcanvas], style={'text-align': 'center'})

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
                    html.Div(children=['Climate:',html.Div(className='d-flex flex-column fs-6' ,children=[html.Div( id='emailMessage',children=[]),html.Div(id='emailMessageLight',children=[])]), html.Button(id='', className='btn btn-primary mt-1', children=['Adjust'])], className='display-6 ms-3 d-flex justify-content-between align-items-center me-3'),
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

                            html.Div(id='', children=[
                            daq.GraduatedBar(
                                color={"gradient":True,"ranges":{"#1b8bd1":[0,6],"#ffe100":[6,10]}},
                                id='current_light_intensity',
                                label='Current Illumination',
                                showCurrentValue=True,
                                value=5,
                                step=10,
                                max=1025,
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
             html.H1(id='', className='container mt-3 d-flex justify-content-between', children=['Dashboard:', html.Div(id='systemTime',children=['It is ',current_time], className="display-6", style={'color':'#1b8bd1'})]),
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

#System Time Display
@app.callback(
    Output('systemTime', 'children'),
    Input('interval', 'n_intervals'))
def update_time(n_intervals):
    global current_time
    current_time = time.strftime("%H:%M%p", (time.localtime()))
    timeString = 'It is ',current_time
    return timeString

# Temperature and Humidity Reading and Displaying
@app.callback(
    Output('current-thermometer', 'value'),
    Output('current-humidity', 'value'),
    Input('interval', 'n_intervals'))
def update_sensor(n_intervals):
    #get if

    dht.readDHT11()
    currentTemperature = dht.temperature
    currentTempValue = dht.temperature
    #currentTemperature = 25;
    currentHumidity = dht.humidity
    #currentHumidity = 25;
    return currentTemperature, currentHumidity

@app.callback(
    Output('emailMessage', 'children'),
    Input('interval', 'n_intervals'),
     [Input('current-thermometer', 'value')])
def check_temp(n_intervals,value):
    global emailSent, emailReceived, uTempThreshold
    emailReceivedContent = getEmails(receiverEmail);
    global message

    if float(value) > float(uTempThreshold) and not emailSent:
        emailSent = send_email(receiverEmail,'Ambient Temperature Exceeded','The current temperature is '+str(value)+'°C. Would you like to turn on the fan?')
        if emailSent:
            message = 'Too Hot Email Sent.'
        else:
            message = 'Too Hot Email Error'
    elif emailReceivedContent:
        toggle_fan(True)
        message = 'Too Hot: Responded.'
    elif float(value) < float(uTempThreshold):
        toggle_fan(False)
        emailSent = False
        print(value)
        message = 'Temp: No email sent'

    return message

@app.callback(
    Output('emailMessageLight', 'children'),
    Input('interval', 'n_intervals'),
    [Input('current_light_intensity', 'value')])
def check_light(n_intervals,value):
    global emailLightSent, uLightThreshold
    global message2

    if int(value) < int(uLightThreshold) and not emailLightSent:
        GPIO.output(ledPin, GPIO.HIGH)
        currtime = time.strftime("%H:%M%p", (time.localtime()))
        emailLightSent = send_email(receiverEmail,'Ambient Light', 'The Light is ON at '+str(currtime)+'.')
        if emailLightSent:
            message2 = 'Too Dark Email Sent.'
            GPIO.output(ledPin, GPIO.HIGH)
        else:
            message2 = 'Too Dark Email Error.'
            GPIO.output(ledPin, GPIO.LOW)
    elif int(value) > int(uLightThreshold):
        emailLightSent = False
        GPIO.output(ledPin, GPIO.LOW)
        print('Cur Light: ',int(value),' Light Tresh: ',int(uLightThreshold))
        message2 = 'Light: No email sent'

    return message2


def connect_mqtt() -> mqtt_client:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


#def on_message_print(client, userdata, message):
   # print("%s %s" % (message.topic, message.payload))

#subscribe.callback(on_message_print, topic, hostname=broker, port=1883)

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
def toggle_fan(on):
    if on:
        #GPIO.output(fanPin, GPIO.HIGH)
        GPIO.output(Motor1,GPIO.HIGH)
        GPIO.output(Motor2,GPIO.LOW)
        GPIO.output(Motor3,GPIO.HIGH)
        img = html.I(className="fa-solid fa-fan rotating", style={'font-size': '10rem', 'color': '#9eff00', 'filter': 'drop-shadow(0 0 20px #009eff)'})
        return img
    else:
        #GPIO.output(fanPin, GPIO.LOW)
        GPIO.output(Motor1,GPIO.LOW)
        GPIO.output(Motor2,GPIO.LOW)
        GPIO.output(Motor3,GPIO.LOW)
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

def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
        global username, uTempThreshold, uHumidityThreshold, uLightIntensity, flag
        if (msg.topic == topic):
            print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")

            global current_light_intensity
            current_light_intensity = msg.payload.decode()



    client.subscribe(topic)
    client.on_message = on_message


@app.callback(Output('current_light_intensity', 'value'),
                Output('current_light_intensity', 'label'),
              #Output('username', 'value'),
              #Output('tempThreshold', 'value'),
              #Output('humidityThreshold', 'value'),
              #Output('lightIntensity', 'value'),
              Input('interval', 'n_intervals'))
def update_light_intensity(n_intervals):
    global current_light_intensity
    resultLabel = "Current Illumination: "+str(current_light_intensity)
    return current_light_intensity, resultLabel

@app.callback(
    Output("collapse", "is_open"),
    [Input("collapse-button", "n_clicks")],
    [State("collapse", "is_open")],
)
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
    Output("offcanvas-backdrop", "is_open"),
    Input("submit-button","n_clicks"),
    State("offcanvas-backdrop", "is_open"))
def toggle_offcanvas(n1, is_open):
    if n1:
        return not is_open
    return is_open


@app.callback(
    Output("userTab", 'children'),
    Output('collapse-button', 'children'),
    [Input("submit-button","n_clicks"), Input("id-input", "value")],
)
def check_validity(n,value):
    global username,uTempThreshold,uHumidityThreshold,uLightThreshold
    buttonText='Change User'
    if n:
        user = logIn(value)
        username = user[1]
        uTempThreshold = user[2]
        uHumidityThreshold = user[3]
        uLightThreshold = user[4]

    return username,buttonText


@app.callback(
              Output('username', 'value'),
              Output('tempThreshold', 'value'),
              Output('humidityThreshold', 'value'),
              Output('lightIntensity', 'value'),
              Input('interval', 'n_intervals'))
def update_light_intensity_user_info(n_n_intervals):
    return  username, uTempThreshold, uHumidityThreshold, uLightThreshold

# DB user preferences
def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)

    return conn

def logIn(user_id):
    global username, uTempThreshold, uHumidityThreshold, uLightThreshold
    db_file = "casaConnect.db"
    conn = create_connection(db_file)
    cur = conn.cursor()

    try:
        cur.execute("SELECT * FROM users WHERE userID = ?", [user_id])
        user = cur.fetchone()

        if not user:
            print("log in failed")
        else:
            username = user[1]
            uTempThreshold = user[2]
            uHumidityThreshold = user[3]
            uLightThreshold = user[4]
#             str, str, float, int, int
#             userID, name, tempThreshold, humidityThreshold, lightIntensityThreshold
            print(username, uTempThreshold, uHumidityThreshold, uLightThreshold)

            return user
            #send_email("Log In", username + " entered at " + currtime)

    finally:
        cur.close()

# Use the above 'port' property in case "Port already in use error" e.g set 'port=8051'
def main():
    client = connect_mqtt()
    subscribe(client)
    client.loop_start()

    app.run_server(debug=True, host='localhost', port=8050)

main()

# Back-end End==============================================================