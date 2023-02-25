import dash.dependencies
import dash_daq as daq
from dash import html, Input, Output, dcc, Dash
import dash_bootstrap_components as dbc
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(21, GPIO.OUT)


app = dash.Dash(
    external_stylesheets=[dbc.themes.BOOTSTRAP,dbc.icons.FONT_AWESOME]
)

img = html.I(className="fa-regular fa-lightbulb w-100", style={'font-size': '10rem'})

# Web page title
app.title = 'CasaConnect'


nav = html.Div(children='Log In', style={'text-align': 'center'})
         

header = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink(nav), style={'text-align': 'end'})
    ],
    brand=[html.Div(id='Logo-full', children=[
         html.Img(src=app.get_asset_url('logo_full.png'), width='400rem',  className="d-flex justify-content-center"),
        ], className="d-flex justify-content-center")],
    brand_href="#",
    color="light",
    dark=False,
    sticky='top'
)

body = html.Div([
            header, 
            dbc.Container([
                dbc.Row([
                      html.Button(img, className='btn btn-light mt-3 w-25 py-4', type="button", id='led-image', n_clicks = 0),
                        ]),
                                          
                ]),
            # ])     
        ], className="body"
        );

app.layout = html.Div(id="theme-switch-div", children=[
    body
    ]);

@app.callback(Output('led-image', 'children'),
              Input('led-image', 'n_clicks'))
def update_output(n_clicks):
    if n_clicks % 2 == 1:
        GPIO.output(21, GPIO.HIGH)
        img = html.I(className="fa-solid fa-lightbulb", style={'font-size': '10rem', 'color': '#E4742E', 'filter': 'drop-shadow(0 0 50px #eac86c)'})
        return img
    else:
        GPIO.output(21, GPIO.LOW)
        img = html.I(className="fa-regular fa-lightbulb", style={'font-size': '10rem', 'color':'#1b8bd1'})
        return img


def main():
    app.run_server(debug=True, host='localhost', port=8050)

main()