#!/usr/bin/env python
#-----------------------------------------------------------------------------#
#           Group on Data Assimilation Development - GDAD/CPTEC/INPE          #
#-----------------------------------------------------------------------------#
#BOP
#
# !SCRIPT:
#
# !DESCRIPTION:
#
# !CALLING SEQUENCE:
#
# !REVISION HISTORY: 
# 22 jun 2023 - J. G. de Mattos - Initial Version
#
# !REMARKS:
# Run the folowing command after updating this script:
# panel convert monitor.py --to pyodide-worker --out .
#
#EOP
#-----------------------------------------------------------------------------#
#BOC


import sqlite3
from datetime import datetime, date
import numpy as np
import pandas as pd
import panel as pn
import holoviews as hv
import hvplot.pandas
from bokeh.models.formatters import DatetimeTickFormatter
import os
import requests

class MonitoringApp:
    def __init__(self):
        # Inicialização do Panel
        pn.extension()
        
        # Valores baseados em Trenberth and Smith (2005)
        self.mean = {
            'pdryini': 98.305,
            'mean_ps': 98.550,
            'mean_pw': 0.244,
            'qneg': None,
            'qsat': None
        }
        self.delta = {
            'pdryini': 0.01,
            'mean_ps': 0.01,
            'mean_pw': 0.010,
            'qneg': None,
            'qsat': None
        }
        
        self.load_data()
        self.create_widgets()
        self.create_layout()

#    def download_file(self,path):
#        self.r = requests.get(path)
#        self.filename = path.split("/")[-1]
#        self.fullname = str(os.getcwd())+"/"+self.filename
#    
#        with open(self.fullname, 'wb') as f:
#            f.write(self.r.content)
        
    def load_data(self):
        try:
#            self.download_file("https://raw.githubusercontent.com/GAD-DIMNT-CPTEC/GSIMonitor/main/data/costFile_Oper.db")           
            con = sqlite3.connect("costFile_Oper.db")
            self.df = pd.read_sql_query("select * from costCons order by date", con, parse_dates=["date"], index_col='date')
            self.df.replace(-1e38,np.nan)
            self.dc = pd.read_sql_query("select * from costFunc order by date", con, parse_dates=["date"], index_col='date')
            self.dc.replace(-1e38,np.nan)

            # Encontre as datas mínima e máxima no DataFrame dc
            self.min_date = self.dc.index.min().date()
            self.max_date = self.dc.index.max().date()

        except Exception as e:
            print(f"Erro ao de dados: {e}")
            self.dc = pd.DataFrame()  # Inicializa um DataFrame vazio em caso de erro
            self.df = pd.DataFrame()  # Inicializa um DataFrame vazio em caso de erro
        
    def create_widgets(self):
        # Widgets do Panel
        self.Hour = pn.widgets.RadioBoxGroup(name="Hour Cycle", options=self.df.hour.unique().tolist())#, inline=True)
        self.Outer = pn.widgets.RadioBoxGroup(name="Outer Loop", options=self.df.outer.unique().tolist())#, inline=True)
        self.Vars = pn.widgets.Select(name='Variables', options=self.df.keys()[2:].tolist())#, inline=True)
        self.use_mean = pn.widgets.Switch(name='Monthly Mean')#, inline=True)
        self.column_name = pn.widgets.Select(name='Column to Plot', options=self.dc.columns.tolist()[3:])#, inline=True)
        
        # Widget para selecionar a data e a hora
        self.date_time_picker = pn.widgets.DatetimePicker(
            name="Selecione uma Data e Hora",
            start=self.min_date,  # Data mínima
            end=self.max_date,    # Data máxima
            value=datetime(self.min_date.year, self.min_date.month, self.min_date.day, 0, 0)  # Inicialize com 00:00
        )


        # Widget para selecionar o intervalo de tempo
        self.date_range_slider = pn.widgets.DateRangeSlider(
            name="Select Date Range",
            start=self.df.index.min(),
            end=self.df.index.max(),
            value=(self.df.index.min(), self.df.index.max())
        )


    def create_layout(self):

        self.tab1 = pn.Column(
            pn.bind(self.plotMassFig, self.Vars, self.Outer, self.use_mean, self.date_range_slider.param.value),
            sizing_mode="stretch_both"
        )

        self.tab2 = pn.Column(
                    sizing_mode="stretch_both"
        )    
        
        # Conteúdo da aplicação
        tabs = pn.Tabs(dynamic=True, active=0)
        tabs.append(("Constrains", self.tab1))
        tabs.append(("Minimization Plots", self.tab2))

        # Layout da barra lateral
        sidebar1 = pn.Column(
            self.Vars,
            pn.Row(pn.pane.HTML("<span style='display: inline-block; margin-top: 9px;'>Select OuterLoop:</span>"), self.Outer),
            pn.Row(pn.pane.HTML("<span style='display: inline-block; margin-top: 0px;'>Use a média: </span>"), self.use_mean),
            self.date_range_slider
        )
        
        sidebar2 = pn.Column(
            self.date_time_picker,
            self.column_name
            )

        col = pn.Column(sidebar1)
        
        @pn.depends(self.column_name, self.date_time_picker, watch=True)
        def update_tab2(column_name, date_time_picker):
            self.tab2.clear()
            selected_date_time = date_time_picker.strftime("%Y-%m-%d %H:%M:%S")  # Não é necessário .value aqui
            self.tab2.append(self.plot_column(column_name,date_time_picker))

        @pn.depends(tabs.param.active, watch=True)
        def insert_widget(active_tab):
            print (active_tab)
            if active_tab == 0: 
                col[0] = sidebar1
            else:
                col[0] = sidebar2

        # Criar o template da aplicação
        #self.app = pn.template.MaterialTemplate(
        self.app = pn.template.FastListTemplate(
            site="SMNA Dashboard",
            title="GSIMonitor",
            header_background="#1976d2",
        )


        self.app.main.append(tabs)
        self.app.sidebar.append(col)


    def plotMassFig(self, var, outer, use_mean, date_range):
        # Implemente sua lógica aqui
        plots = []
        for hour in ["0"] + list(np.arange(6, 24, 6)):
            query = f"hour == {hour} & outer == {outer}"
            df_filtered = self.df.query(query)
    
            if date_range:
                start_date, end_date = date_range
                df_filtered = df_filtered[(df_filtered.index >= start_date) & (df_filtered.index <= end_date)]
    
            if use_mean:
                df_resampled = df_filtered.resample('M').mean()
                p = df_resampled.hvplot("date", var, title=f"{hour} UTC").options(autorange="x")
            else:
                p = df_filtered.hvplot("date", var, title=f"{hour} UTC").options(autorange="x")
    
            if self.mean[var] is not None:
                l1 = hv.HLine(self.mean[var])
                l2 = hv.HLine(self.mean[var] + self.delta[var])
                l3 = hv.HLine(self.mean[var] - self.delta[var])
                sp = hv.HSpan(self.mean[var] + self.delta[var], self.mean[var] - self.delta[var])
    
                l1.opts(color="red", line_dash="dashed", line_width=1.0)
                l2.opts(color="blue", line_dash="dashed", line_width=1.0)
                l3.opts(color="blue", line_dash="dashed", line_width=1.0)
                sp.opts(color="lightgray")
    
                plots.append(sp * (l1 * l2 * l3) * p)
            else:
                plots.append(p)
    
        layout = hv.Layout(plots).cols(2)
        layout.opts(
            sizing_mode="stretch_both",
            title=f"{var}: OuterLoop {outer}",
            fontsize={"title": "20pt"},
        )
    
        return layout
    def get_last_dates_with_hour(self,dataframe, num_last_days, hour=None):
        """Calcula as últimas datas com base no número especificado e na hora desejada."""
        # Filtra o DataFrame para as datas com a hora desejada
        if hour is not None:
            filtered_dates = dataframe.index.unique()[dataframe.index.unique().hour == hour]
        else:
            filtered_dates =  dataframe.index.unique()
        # Seleciona as últimas datas com base no número especificado
        last_dates = filtered_dates[-num_last_days:]
        return last_dates

    def calculate_mean_and_std_with_hour(self,dataframe, groupby, num_last_days, hour=None):
        """Calcula a média e o desvio padrão das últimas séries temporais com base na hora especificada."""
        # Seleciona as datas dos últimos num_last_days dias
        date_range = self.get_last_dates_with_hour(dataframe,num_last_days,hour)    
        last_days_data = dataframe[dataframe.index.isin(date_range)]
        # Calcula a média e o desvio padrão
        mean_data = last_days_data.groupby(groupby).mean().reset_index()
        std_data = last_days_data.groupby(groupby).std().reset_index()
        return mean_data, std_data


    def plot_column(self, column_name, date_time, num_last_dates=4, num_last_days=7):
        print('-->>column:', column_name)
        print('-->>dateTime:', date_time)
        
        if not column_name:
            print("Selecione pelo menos uma variável para plotar.")
            return
    
        data_subset = self.dc[self.dc.index == date_time]
    
        if data_subset.empty:
            print(f"A data '{date_time}' não foi encontrada no DataFrame.")
            return
    
        data_subset = data_subset.reset_index(drop=True)
        
        # Crie um DataFrame para armazenar todas as séries temporais
        all_data = pd.DataFrame(index=range(1, len(data_subset) + 1))
        
        # Adicione a série temporal original
        if column_name == 'gnorm':
            all_data[column_name] = np.log(data_subset[column_name])
        else:
            all_data[column_name] = data_subset[column_name]
        
        # Adicione as séries temporais para as últimas datas
        last_dates = pd.date_range(end=date_time,periods=num_last_dates,freq='6H')
        #print(last_dates)
        for date in last_dates:
            print(date)
            if date != date_time:
                data_subset = self.dc[self.dc.index == date]
                data_subset = data_subset.reset_index(drop=True)
                all_data[f"{column_name} ({date})"] = data_subset[column_name]
    
        mean, std = self.calculate_mean_and_std_with_hour(self.dc, ['outer', 'inner'], num_last_days)

        # Calcule as bordas superior e inferior da banda de dispersão
        X         = range(1, len(data_subset) + 1)
        std_upper = mean[column_name] + std[column_name]
        std_lower = mean[column_name] - std[column_name]
    
        # Crie o gráfico HoloViews com todas as séries temporais
        plot = all_data.hvplot.line(xlabel='Inner Loops', ylabel=column_name,
                                title=f'{column_name} ( {date_time} ) and Last {num_last_dates} Cycles',
                                responsive=True)
        plot_mean = mean.hvplot.line(y=column_name, color='black', line_width=3, label=f"Mean {column_name} (Last {num_last_days} Days)",
                                responsive=True)
        plot_std_band = hv.Area((X, std_upper, std_lower),vdims=['y', 'y2'], label=f'std {column_name} (Last {num_last_days} Days)')
        #return plot * plot_mean
        return (plot_std_band.options(alpha=0.25) * plot * plot_mean  )




    def run(self):
        # Servir a aplicação
        self.app.servable()
        #self.app.show()

#print('name:',__name__)
#if __name__ == "__main__":
#    print('Olá mundo')
monitoring_app = MonitoringApp()
monitoring_app.run()
    
# EOC
# -----------------------------------------------------------------------------

