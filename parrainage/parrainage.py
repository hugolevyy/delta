import sys
import dash
import flask
from dash import dcc
from dash import html
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import plotly.express as px

class Parrainage():

    def __init__(self, application = None):
        self.df = pd.read_csv("parrainage/data/parrainagestotal.csv", sep=";")
        self.candidats_occurences = self.df['Candidat'].value_counts()
        self.candidats_list = self.candidats_occurences[self.candidats_occurences > 500].keys()
        
        self.main_layout = html.Div(children=[
            html.H3(children='Évolution du taux de natalité vs le niveau moyen de revenu par pays'),

            html.Div('Déplacez la souris sur une bulle pour avoir les graphiques du pays en bas.'), 

            html.Div([
                    html.Div([ dcc.Graph(id='par-main-graph'), ], style={'width':'80%', }),
                    html.Div([
                        html.Div('Candidat'),
                        dcc.RadioItems(
                            id='par-candidat',
                            options=[{'label': candidat, 'value': candidat} for candidat in self.candidats_list],
                            value='Log',
                            labelStyle={'display':'block'},
                        ),
                        html.Br()
                    ], style={'margin-left':'15px', 'width': '15em', 'float':'right'}),
                ], style={
                    'padding': '10px 50px', 
                    'display':'flex',
                    'justifyContent':'center'
                }),            
            
            html.Br(),
            dcc.Markdown("""
            #### À propos

            * Inspiration initiale : [conférence de Hans Rosling](https://www.ted.com/talks/hans_rosling_new_insights_on_poverty)
            * [Version Plotly](https://plotly.com/python/v3/gapminder-example/)
            * Données : [Banque mondiale](https://databank.worldbank.org/source/world-development-indicators)
            * (c) 2022 Olivier Ricou
            """),
           

        ], style={
                #'backgroundColor': 'rgb(240, 240, 240)',
                 'padding': '10px 50px 10px 50px',
                 }
        )
        
        if application:
            self.app = application
            # application should have its own layout and use self.main_layout as a page or in a component
        else:
            self.app = dash.Dash(__name__)
            self.app.layout = self.main_layout

        # I link callbacks here since @app decorator does not work inside a class
        # (somhow it is more clear to have here all interaction between functions and components)
        self.app.callback(
            dash.dependencies.Output('par-main-graph', 'figure'),
            [ dash.dependencies.Input('par-crossfilter-xaxis-type', 'value'),
              dash.dependencies.Input('par-crossfilter-year-slider', 'value')])(self.update_graph)
        self.app.callback(
            dash.dependencies.Output('par-div-country', 'children'),
            dash.dependencies.Input('par-main-graph', 'hoverData'))(self.country_chosen)
        self.app.callback(
            dash.dependencies.Output('par-button-start-stop', 'children'),
            dash.dependencies.Input('par-button-start-stop', 'n_clicks'),
            dash.dependencies.State('par-button-start-stop', 'children'))(self.button_on_click)
        # this one is triggered by the previous one because we cannot have 2 outputs for the same callback
        self.app.callback(
            dash.dependencies.Output('par-auto-stepper', 'max_interval'),
            [dash.dependencies.Input('par-button-start-stop', 'children')])(self.run_movie)
        # triggered by previous
        self.app.callback(
            dash.dependencies.Output('par-crossfilter-year-slider', 'value'),
            dash.dependencies.Input('par-auto-stepper', 'n_intervals'),
            [dash.dependencies.State('par-crossfilter-year-slider', 'value'),
             dash.dependencies.State('par-button-start-stop', 'children')])(self.on_interval)
        self.app.callback(
            dash.dependencies.Output('par-income-time-series', 'figure'),
            [dash.dependencies.Input('par-main-graph', 'hoverData'),
             dash.dependencies.Input('par-crossfilter-xaxis-type', 'value')])(self.update_income_timeseries)
        self.app.callback(
            dash.dependencies.Output('par-fertility-time-series', 'figure'),
            [dash.dependencies.Input('par-main-graph', 'hoverData'),
             dash.dependencies.Input('par-crossfilter-xaxis-type', 'value')])(self.update_fertility_timeseries)
        self.app.callback(
            dash.dependencies.Output('par-pop-time-series', 'figure'),
            [dash.dependencies.Input('par-main-graph', 'hoverData'),
             dash.dependencies.Input('par-crossfilter-xaxis-type', 'value')])(self.update_pop_timeseries)


    def update_graph(self, regions, xaxis_type, year):
        dfg = self.df.loc[year]
        dfg = dfg[dfg['region'].isin(regions)]
        fig = px.scatter(dfg, x = "incomes", y = "fertility", 
                         #title = f"{year}", cliponaxis=False,
                         size = "population", size_max=60, 
                         color = "region", color_discrete_map = self.continent_colors,
                         hover_name="Country Name", log_x=True)
        fig.update_layout(
                 xaxis = dict(title='Revenus net par personnes (en $ US de 2020)',
                              type= 'linear' if xaxis_type == 'Linéaire' else 'log',
                              range=(0,100000) if xaxis_type == 'Linéaire' 
                                              else (np.log10(50), np.log10(100000)) 
                             ),
                 yaxis = dict(title="Nombre d'enfants par femme", range=(0,9)),
                 margin={'l': 40, 'b': 30, 't': 10, 'r': 0},
                 hovermode='closest',
                 showlegend=False,
             )
        return fig

    def create_time_series(self, country, what, axis_type, title):
        return {
            'data': [go.Scatter(
                x = self.years,
                y = self.df[self.df["Country Name"] == country][what],
                mode = 'lines+markers',
            )],
            'layout': {
                'height': 225,
                'margin': {'l': 50, 'b': 20, 'r': 10, 't': 20},
                'yaxis': {'title':title,
                          'type': 'linear' if axis_type == 'Linéaire' else 'log'},
                'xaxis': {'showgrid': False}
            }
        }


    def get_country(self, hoverData):
        if hoverData == None:  # init value
            return self.df['Country Name'].iloc[np.random.randint(len(self.df))]
        return hoverData['points'][0]['hovertext']

    def country_chosen(self, hoverData):
        return self.get_country(hoverData)

    # graph incomes vs years
    def update_income_timeseries(self, hoverData, xaxis_type):
        country = self.get_country(hoverData)
        return self.create_time_series(country, 'incomes', xaxis_type, 'PIB par personne (US $)')

    # graph children vs years
    def update_fertility_timeseries(self, hoverData, xaxis_type):
        country = self.get_country(hoverData)
        return self.create_time_series(country, 'fertility', xaxis_type, "Nombre d'enfants par femme")

    # graph population vs years
    def update_pop_timeseries(self, hoverData, xaxis_type):
        country = self.get_country(hoverData)
        return self.create_time_series(country, 'population', xaxis_type, 'Population')

    # start and stop the movie
    def button_on_click(self, n_clicks, text):
        if text == self.START:
            return self.STOP
        else:
            return self.START

    # this one is triggered by the previous one because we cannot have 2 outputs
    # in the same callback
    def run_movie(self, text):
        if text == self.START:    # then it means we are stopped
            return 0 
        else:
            return -1

    # see if it should move the slider for simulating a movie
    def on_interval(self, n_intervals, year, text):
        if text == self.STOP:  # then we are running
            if year == self.years[-1]:
                return self.years[0]
            else:
                return year + 1
        else:
            return year  # nothing changes

    def run(self, debug=False, port=8050):
        self.app.run_server(host="0.0.0.0", debug=debug, port=port)


if __name__ == '__main__':
    ws = Parrainage()
    ws.run(port=8055)
