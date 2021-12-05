import requests
import json
import plotly.graph_objects as go
import plotly.express as px
import matplotlib.pyplot as plt
import dash
from dash import  dcc
from dash import  html

import pandas as pd
import numpy as np
import datetime
from dash.dependencies import Output, Input
import validators
from flask import send_from_directory


#Como primer paso validamos si nuestra API se encuentra operativa
try:
    validators.url("https://api.kraken.com/0/public/OHLC")
    print('Conexión operativa: "//api.kraken.com/0/public/OHLC"')
except:
    print("Revisar la conexión del API")


#Definimos nuestro DataFrame Local
data_proyecto=pd.DataFrame()
data_cripto_1=pd.DataFrame()
data_cripto_2=pd.DataFrame()



#Vamos a crear una funcion por criptomoneda, y se captura por Split
def fetch_OHLC_data(symbol, timeframe):
    """This function will get Open/High/Low/Close, Volume and tradecount data for the pair passed and save to CSV"""
    pair_split = symbol.split('/')  #utilizamos el simbolo "/" para seprar las monedas a analizar
    symbol = pair_split[0] + pair_split[1]

    url = f'https://api.kraken.com/0/public/OHLC?pair={symbol}&interval={timeframe}'
    response = requests.get(url)
    if response.status_code == 200:  # validación de la respuesta del servidor
        j = json.loads(response.text)
        result = j['result']
        keys = []
        for item in result:
            keys.append(item)
        if keys[0] != 'last':
            data = pd.DataFrame(result[keys[0]],
                                columns=['unix', 'open', 'high', 'low', 'close', 'vwap', 'volume', 'tradecount'])
        else:
            data = pd.DataFrame(result[keys[1]],
                                columns=['unix', 'open', 'high', 'low', 'close', 'vwap', 'volume', 'tradecount'])

        data['date'] = pd.to_datetime(data['unix'], unit='s')
        data['volume_from'] = data['volume'].astype(float) * data['close'].astype(float)
        data_proyecto=data
        data_proyecto.insert(10,"Name",pair_split[0] + pair_split[1],True)
        # Calculamos el VWAP:
        v = pd.to_numeric(data_proyecto['volume_from'].values, downcast='integer')
        tp = pd.to_numeric(data_proyecto['close'].values, downcast='integer')
        data_proyecto = data_proyecto.assign(vwap_=((tp * v).cumsum() / v.cumsum()).round(2).astype(object))

        #Si hay un problema en obtener los datos lo pintamos, caso contrario lo guardamos en un file como backup
        if data is None:
            print("Did not return any data from Kraken for this symbol")
        else:
            if timeframe == '1':
                tf = 'minute'
            elif timeframe == '60':
                tf = 'hour'
            elif timeframe == '1440':
                tf = 'day'
            else:
                tf = ''
            data.to_csv(f'Kraken_{symbol}_{tf}.csv', index=False)

    else:
        print("Did not receieve OK response from Kraken API")

    return data_proyecto

#Creamos otra función para obtener la información de la segunda moneda
def fetch_OHLC_data_2(symbol, timeframe):
    """This function will get Open/High/Low/Close, Volume and tradecount data for the pair passed and save to CSV"""
    pair_split = symbol.split('/')  #utilizamos el simbolo "/" para seprar las monedas a analizar
    symbol = pair_split[2] + pair_split[3]
    url = f'https://api.kraken.com/0/public/OHLC?pair={symbol}&interval={timeframe}'
    response = requests.get(url)
    if response.status_code == 200:  # validación de la respuesta del servidor
        j = json.loads(response.text)
        result = j['result']
        keys = []
        for item in result:
            keys.append(item)
        if keys[0] != 'last':
            data = pd.DataFrame(result[keys[0]],
                                columns=['unix', 'open', 'high', 'low', 'close', 'vwap', 'volume', 'tradecount'])
        else:
            data = pd.DataFrame(result[keys[1]],
                                columns=['unix', 'open', 'high', 'low', 'close', 'vwap', 'volume', 'tradecount'])

        data['date'] = pd.to_datetime(data['unix'], unit='s')
        data['volume_from'] = data['volume'].astype(float) * data['close'].astype(float)
        data.insert(10,"Name",pair_split[2] + pair_split[3],True)
        # Calculamos el VWAP:
        v = pd.to_numeric(data['volume_from'].values, downcast='integer')
        tp = pd.to_numeric(data['close'].values, downcast='integer')
        data = data.assign(vwap_=((tp * v).cumsum() / v.cumsum()).round(2).astype(object))

        #Si hay un problema en obtener los datos lo pintamos, caso contrario lo guardamos en un file como backup
        if data is None:
            print("Did not return any data from Kraken for this symbol")
        else:
            if timeframe == '1':
                tf = 'minute'
            elif timeframe == '60':
                tf = 'hour'
            elif timeframe == '1440':
                tf = 'day'
            else:
                tf = ''
            data.to_csv(f'Kraken_{symbol}_{tf}.csv', index=False)

    else:
        print("Did not receieve OK response from Kraken API")

    return data

#Definimos las monedas a analizar
if __name__ == "__main__":
    pair = "ETH/EUR/BTC/EUR"

#Llamamos a las funciones para que retornen los datos y luego concatenarlos
data_cripto_1 = fetch_OHLC_data(symbol=pair, timeframe='1')
data_cripto_2 = fetch_OHLC_data_2(symbol=pair, timeframe='1')
data_proyecto = pd.concat([data_cripto_1,data_cripto_2],axis=0)


#Empezamos a crear la estructura Dash
app = dash.Dash(__name__)
app.title = "Analisis Criptomoneda"

app.layout = html.Div(
    children=[
        html.Div(
            children=[
                html.P(children="💶", className="header-emoji"),
                html.H1(
                    children="Analisis de Criptomonedas", className="header-title"
                ),
                html.P(
                    children="Analizar el comportamiento del precio(EUR) de la criptomoneda"
                    " y la variación de VWAP"
                    " entre las últimas 3 horas de ejecución con el API  de Kraken",
                    className="header-description",
                ),
            ],
            className="header",
        ),
        html.Div(
            children=[
                html.Div(
                    children=[
                        html.Div(children="Moneda", className="menu-title"),
                        dcc.Dropdown(
                            id="filtro-moneda",
                            options=[
                                {"label": moneda, "value": moneda}
                                for moneda in np.sort(data_proyecto.Name.unique())
                            ],
                            value="BTCEUR",
                            clearable=False,
                            className="dropdown",
                        ),
                    ]
                ),
                html.Div(
                    children=[
                        html.Div(children="Intervalo de tiempo", className="menu-title"),
                        dcc.Dropdown(
                            id="filtro-intervalo",
                            #options=[
                                #{"label": avocado_type, "value": avocado_type}
                            options=[
                                 {"label": '1hr', "value": '60'},
                                 {"label": '2hr', "value": '120'},
                                 {"label": '3hr', "value": '180'},
                                #for avocado_type in data.type.unique()
                            ],
                            value="60",
                            clearable=False,
                            searchable=False,
                            className="dropdown",
                        ),
                    ],
                ),
                html.Div(
                    children=[
                        html.Div(
                            children="Rango de Fecha",
                            className="menu-title"
                            ),
                        dcc.DatePickerRange(
                            id="rango-fecha",
                            min_date_allowed=data_proyecto.date.min().date(),
                            max_date_allowed=data_proyecto.date.max().date(),
                            start_date=data_proyecto.date.min().date(),
                            end_date=data_proyecto.date.max().date(),
                        ),
                    ]
                ),
            ],
            className="menu",
        ),
        html.Div(
            children=[
                html.Div(
                    children=dcc.Graph(
                        id="grafica-precio", config={"displayModeBar": False},
                    ),
                    className="card",
                ),
                html.Div(
                    children=dcc.Graph(
                        id="grafica-volumen", config={"displayModeBar": False},
                    ),
                    className="card",
                ),
            ],
            className="wrapper",
        ),
    ]
)


@app.callback(
    [Output("grafica-precio", "figure"), Output("grafica-volumen", "figure")],
    [
        Input("filtro-moneda", "value"),
        Input("filtro-intervalo", "value"),
        Input("rango-fecha", "start_date"),
        Input("rango-fecha", "end_date"),
    ],
)
def update_charts(moneda, intervalo, start_date, end_date):
    mask = (
        (data_proyecto.Name == moneda)
        & (data_proyecto.date >= max(data_proyecto['date']) - datetime.timedelta(minutes=int(intervalo)))

    )
    filtered_data = data_proyecto.loc[mask, :]


    ####Segundo gráfico con el mismo formato:
    grafico_barras_volumen = {'data': [
        go.Bar(
            x=filtered_data['date'],
            y=filtered_data['volume_from'],
            name='Volumen', text=round(filtered_data['volume_from'], 2))
    ],
        "layout": {
            "title": {
                "text": "Análisis de volumen :" + moneda,
                "x": 0.05,
                "xanchor": "left"
            },
            "xaxis": {"fixedrange": True},
            "yaxis": {"fixedrange": True},
            "colorway": ["636dfb"],
        }
    }


    grafica_criptomoneda_vwap = {'data': [
        go.Candlestick(x=filtered_data['date'],
                       open=filtered_data['open'],
                       high=filtered_data['high'],
                       low=filtered_data['low'],
                       close=filtered_data['close'],name='AAPL'
                       ),
        go.Scatter(x=filtered_data['date'], y=filtered_data['vwap'], mode='lines',line=dict(color='royalblue', width=1),name='vwap')
    ],
        "layout": {
            "title": {
                "text": "Análisis VWAP :" + moneda,
                "x": 0.05,
                "xanchor": "left"
            },
            "xaxis": {"fixedrange": True},
            "yaxis": {"fixedrange": True},
            "colorway": ["7f7f7f"],
        }
    }



    return grafica_criptomoneda_vwap,grafico_barras_volumen


if __name__ == "__main__":
    app.run_server(debug=True,port=8080)

