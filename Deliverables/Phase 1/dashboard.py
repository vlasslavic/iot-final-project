import dash.dependencies
import dash_daq as daq
from dash import html, Input, Output, dcc, Dash
import dash_bootstrap_components as dbc

import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(21, GPIO.OUT)


app = dash.Dash(__name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP,dbc.icons.FONT_AWESOME]
)

# Web page title
app.title = 'CasaConnect'

nav = html.Div(children='Log In', style={'text-align': 'center'})
         

header = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink(nav), style={'text-align': 'end'})
    ],
    brand=[html.Div(id='Logo-full', children=[
         html.Img(src=app.get_asset_url('logo_full.png'), width='400rem',  ),
        ], className="w-100")],
    brand_href="/",
    color="light",
    dark=False,
    sticky='top', 
    className="d-flex justify-content-between shadow-lg "
)


body = html.Main(children=[
        dbc.Container(children=[
             html.H1(id='', className='container mt-3', children='Dashboard:'),
             html.Hr(children=[]),
                dbc.Row([
                    html.Div(children=[
                        html.Div(children='Lighting:', className='display-6 ms-3'),
                        html.Div(children=[
                            html.Div(children=[], className='d-flex justify-content-center mt-4 mb-3', id='led-power-button-result'),
                            daq.PowerButton(
                                id='led-power-button',
                                className='mb-2',
                                color='#ffe100',
                                size=75,
                                on=False
                            ),    
                        ],className="card rounded-4 w-100 bg-light py-2 px-4 m-3 shadow-sm"),
                    ], className='w-25'),
                ], className='mb-3'),
                                          
            ], className=" rounded-4 card m-4 shadow")
            # ])     
        ], className="flex-shrink-0 d-flex justify-content-center"
    );

footer = html.Footer([
            html.Div(className="container text-center ", children=[
                  html.Small(children=['2023 © CasaConnect by ', html.Span(children='GREEN', className='text-success', style={'filter': 'drop-shadow(0 0 80px green)'}), ' Team'])
            ]),
            ],id='sticky-footer', className="fixed-bottom py-4 bg-dark text-white-50 ")



app.layout = html.Div(id="theme-switch-div", children=[
    header,
    body,
    footer
    ]);

@app.callback(
    Output('led-power-button-result', 'children'),
    Input('led-power-button', 'on')
)
def update_output(on):
    if on:
        GPIO.output(21, GPIO.HIGH)
        img = html.I(className="fa-solid fa-lightbulb", style={'font-size': '10rem', 'color': '#ffe100', 'filter': 'drop-shadow(0 0 50px #eac86c)'})
        return img
            
    else:
        GPIO.output(21, GPIO.LOW)
        img = html.I(className="fa-regular fa-lightbulb", style={'font-size': '10rem', 'color':'#1b8bd1'})
        return img


def main():
    app.run_server(debug=True, host='localhost', port=8050)

main()