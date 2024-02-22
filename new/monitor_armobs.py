#!/usr/bin/env python
# coding: utf-8

# # SMNA-Dashboard
#  
# Este notebook trata da apresentação do espaço utilizado pelos arquivos de observações disponíveis para a utilização com o SMNA. As informações apresentadas não representam quantidades ou tipos de dados envolvidos ou utiizados no processo de assimilação de dados, mas apenas o espaço em disco utilizado por estes. As informações mais importantes que podem ser obtidas com este dashboard são o espaço em disco total utilizado por diferentes tipos de observações, separadas por horário sinótico, período e tipo de dados.
#  
# **Nota:** Se o slider que permite ajustar o período a ser visualizado não atualizar a tabela por completo (e.g., o slider está ajustado até a data 13 de Setembro, mas a tabela mostra resultados apenas até o dia 4 de Setembro), pode ser um indicativo de que os arquivos de observação não se encontram no disco verificado. 
# 
# Para realizar o deploy do dashboard no GitHub, é necessário converter este notebook em um script executável, o que pode ser feito a partir da interface do Jupyter (`File` -> `Save and Export Notebook As...` -> `Executable Script`). A seguir, utilize o comando abaixo para converter o script em uma página HTML. Junto com a página, será gerado um arquivo JavaScript e ambos devem ser adicionados ao repositório, junto com o arquivo CSV.
#  
# ```
# panel convert SMNA-Dashboard.py --to pyodide-worker --out .
# ```
# 
# Para utilizar o dashboard localmente, utilize o comando a seguir:
# 
# ```
# panel serve SMNA-Dashboard.ipynb --autoreload --show
#  ```
#  
# ---
# Carlos Frederico Bastarz (carlos.bastarz@inpe.br), Setembro de 2023.

# In[1]:


import os
import glob
import pandas as pd
import hvplot.pandas
import holoviews as hv
import panel as pn

from datetime import timedelta

from math import pi

from bokeh.palettes import Category20c, Category20
from bokeh.plotting import figure
from bokeh.transform import cumsum

from bokeh.models.widgets.tables import DateFormatter

pn.extension(sizing_mode="stretch_width", notifications=True)


# In[2]:


dfs = pd.read_csv('https://raw.githubusercontent.com/GAD-DIMNT-CPTEC/SMNA-Dashboard-ArmObs/main/mon_rec_obs_final.csv', header=[0], 
                  parse_dates=[('Data do Download'), ('Data da Observação')])


# In[3]:


dfs['Diferença de Tempo'] = (dfs['Data do Download'] - dfs['Data da Observação']) - timedelta(hours=3)


# In[4]:


dfs


# In[5]:


start_date = pd.Timestamp('2023-01-01 00:00:00')
end_date = pd.Timestamp('2023-09-13 00:00:00')

date_range_slider = pn.widgets.DateRangeSlider(
    name='Intervalo',
    start=start_date, end=end_date,
    value=(start_date, end_date),
    step=24*3600*1000,
    orientation='horizontal'
)

units = ['KB', 'MB', 'GB', 'TB', 'PB']
otype = ['1bamua', '1bhrs4', 'airsev', 'atms', 'crisf4', 'eshrs3', 'esmhs', 'gome', 'gpsipw', 'gpsro', 'mtiasi', 'osbuv8', 'prepbufr', 'satwnd', 'sevcsr']
ftype = ['gdas', 'gfs']
synoptic_time_list = ['00Z', '06Z', '12Z', '18Z', '00Z e 12Z', '06Z e 18Z', '00Z, 06Z, 12Z e 18Z']

units_w = pn.widgets.Select(name='Unidade', options=units)
otype_w = pn.widgets.MultiChoice(name='Tipo de Observação', value=[otype[0]], options=otype, solid=False)
ftype_w = pn.widgets.MultiChoice(name='Tipo de Arquivo', value=[ftype[0]], options=ftype, solid=False)
synoptic_time = pn.widgets.RadioBoxGroup(name='Horário', options=synoptic_time_list, inline=False)

date_range = date_range_slider.value

######

dic_size = {}
def getSizeDic(dfsp, otype_w):
    dfsp_tot_down_otype = dfsp['Tamanho do Download (KB)'].loc[dfsp['Tipo de Observação'] == otype_w[-1]].sum(axis=0)
    dic_size[otype_w[-1]] = dfsp_tot_down_otype
    return dic_size    
    
def subDataframe(df, start_date, end_date):
    mask = (df['Data da Observação'] >= start_date) & (df['Data da Observação'] <= end_date)
    return df.loc[mask]

def subTimeDataFrame(synoptic_time):
    if synoptic_time == '00Z': time_fmt0 = '00:00:00'; time_fmt1 = '00:00:00'
    if synoptic_time == '06Z': time_fmt0 = '06:00:00'; time_fmt1 = '06:00:00'
    if synoptic_time == '12Z': time_fmt0 = '12:00:00'; time_fmt1 = '12:00:00'
    if synoptic_time == '18Z': time_fmt0 = '18:00:00'; time_fmt1 = '18:00:00'    
    
    if synoptic_time == '00Z e 12Z': time_fmt0 = '00:00:00'; time_fmt1 = '12:00:00'
    if synoptic_time == '06Z e 18Z': time_fmt0 = '06:00:00'; time_fmt1 = '18:00:00'
    
    if synoptic_time == '00Z e 06Z': time_fmt0 = '00:00:00'; time_fmt1 = '06:00:00'
    if synoptic_time == '12Z e 18Z': time_fmt0 = '12:00:00'; time_fmt1 = '18:00:00'    
    
    if synoptic_time == '00Z, 06Z, 12Z e 18Z': time_fmt0 = '00:00:00'; time_fmt1 = '18:00:00'   
    
    return time_fmt0, time_fmt1

def unitConvert(units_w):      
    if units_w == 'KB':
        factor = float(1)
        n1factor = 'Tamanho do Download (KB)'
        n2factor = 'Tamanho (KB)'
        n3factor = 'Total Armazenado (KB):'
    elif units_w == 'MB':
        factor = float(1 / (1024 ** 2))
        n1factor = 'Tamanho do Download (MB)'
        n2factor = 'Tamanho (MB)'
        n3factor = 'Total Armazenado (MB):'
    elif units_w == 'GB':
        factor = float(1 / (1024 ** 3))
        n1factor = 'Tamanho do Download (GB)'
        n2factor = 'Tamanho (GB)'
        n3factor = 'Total Armazenado (GB):'
    elif units_w == 'TB':
        factor = float(1 / (1024 ** 4))
        n1factor = 'Tamanho do Download (TB)'
        n2factor = 'Tamanho (TB)'
        n3factor = 'Total Armazenado (TB):'
    elif units_w == 'PB':
        factor = float(1 / (1024 ** 5))
        n1factor = 'Tamanho do Download (PB)'            
        n2factor = 'Tamanho (PB)'
        n3factor = 'Total Armazenado (PB):'
    
    return factor, n1factor, n2factor, n3factor

@pn.depends(otype_w, ftype_w, synoptic_time, date_range_slider.param.value, units_w)
def getTotDown(otype_w, ftype_w, synoptic_time, date_range, units_w):
    start_date, end_date = date_range
    dfs_tmp = dfs.copy()
    dfs2 = subDataframe(dfs_tmp, start_date, end_date)    
   
    factor, n1factor, n2factor, n3factor = unitConvert(units_w)

    dfs2[n1factor] = dfs2['Tamanho do Download (KB)'].multiply(factor)   
    
    time_fmt0, time_fmt1 = subTimeDataFrame(synoptic_time)
    
    if time_fmt0 == time_fmt1:
        dfsp = dfs2.loc[dfs2['Tipo de Observação'].isin(otype_w)].loc[dfs2['Tipo de Arquivo'].isin(ftype_w)].set_index('Data da Observação').at_time(str(time_fmt0)).reset_index()
    else:
        dfsp = dfs2.loc[dfs2['Tipo de Observação'].isin(otype_w)].loc[dfs2['Tipo de Arquivo'].isin(ftype_w)].set_index('Data da Observação').between_time(str(time_fmt0), str(time_fmt1), inclusive='both')
            
        if synoptic_time == '00Z e 12Z':
            dfsp = dfsp.drop(dfsp.at_time('06:00:00').index).reset_index()
        elif synoptic_time == '06Z e 18Z':    
            dfsp = dfsp.drop(dfsp.at_time('12:00:00').index).reset_index()
        elif synoptic_time == '00Z, 06Z, 12Z e 18Z':
            dfsp = dfsp.reset_index()    
            
    dfsp_tot_down = dfsp['Tamanho do Download (KB)'].sum(axis=0)
    
    tot_down = pn.indicators.Number(name=n3factor, value=dfsp_tot_down * factor, format='{value:.2f}', font_size='16pt', title_size='12pt')
    
    return pn.Column(tot_down, sizing_mode="stretch_both")

@pn.depends(otype_w, ftype_w, synoptic_time, date_range_slider.param.value, units_w)
def getTable(otype_w, ftype_w, synoptic_time, date_range, units_w):
    start_date, end_date = date_range
    dfs_tmp = dfs.copy()
    dfs2 = subDataframe(dfs_tmp, start_date, end_date)    
   
    factor, n1factor, n2factor, n3factor = unitConvert(units_w)

    dfs2[n1factor] = dfs2['Tamanho do Download (KB)'].multiply(factor)   
    
    time_fmt0, time_fmt1 = subTimeDataFrame(synoptic_time)
    
    if time_fmt0 == time_fmt1:
        dfsp = dfs2.loc[dfs2['Tipo de Observação'].isin(otype_w)].loc[dfs2['Tipo de Arquivo'].isin(ftype_w)].set_index('Data da Observação').at_time(str(time_fmt0)).reset_index()
    else:
        dfsp = dfs2.loc[dfs2['Tipo de Observação'].isin(otype_w)].loc[dfs2['Tipo de Arquivo'].isin(ftype_w)].set_index('Data da Observação').between_time(str(time_fmt0), str(time_fmt1), inclusive='both')
            
        if synoptic_time == '00Z e 12Z':
            dfsp = dfsp.drop(dfsp.at_time('06:00:00').index).reset_index()
        elif synoptic_time == '06Z e 18Z':    
            dfsp = dfsp.drop(dfsp.at_time('12:00:00').index).reset_index()
        elif synoptic_time == '00Z, 06Z, 12Z e 18Z':
            dfsp = dfsp.reset_index()      
    
    bokeh_formatters = {
        'Diferença de Tempo': DateFormatter(format='%H:%M:%S'),
    }

    # Avançado
#    df_tb = pn.pane.DataFrame(dfsp, 
#                              name='DataFrame', 
#                              height=600, 
#                              bold_rows=True,
#                              border=15,
#                              decimal='.',
#                              index=True,
#                              show_dimensions=True,
#                              justify='center',
#                              sparsify=True,
#                              sizing_mode='stretch_both',
#                             )
    
    # Avançado
    df_tb = pn.widgets.DataFrame(dfsp, 
                                 name='DataFrame', 
                                 height=600, 
                                 show_index=True, 
                                 frozen_rows=0, 
                                 frozen_columns=2, 
                                 autosize_mode='force_fit', 
                                 fit_columns=True,
                                 formatters=bokeh_formatters,
                                 auto_edit=False,
                                 reorderable=True,
                                 sortable=True,
                                 text_align='center',
                                )


    # Muito Avançado (e pesado)
#    df_tb = pn.widgets.Tabulator(dfsp, 
#                                 name='DataFrame', 
#                                 frozen_rows=[0,1],
#                                 frozen_columns=[2], 
#                                 pagination=None,
#                                 selectable='toggle',
#                                 show_index=True,
#                                 theme='default',
#                                 formatters=bokeh_formatters,
#                                )
    
    return pn.Column(df_tb, sizing_mode="stretch_both")
       
@pn.depends(otype_w, ftype_w, synoptic_time, date_range_slider.param.value, units_w)
def plotLine(otype_w, ftype_w, synoptic_time, date_range, units_w):
    for count, i in enumerate(otype_w):
        for count2, j in enumerate(ftype_w):
            if count == 0:
                start_date, end_date = date_range
                dfs_tmp = dfs.copy()
                dfs2 = subDataframe(dfs_tmp, start_date, end_date)
            
                time_fmt0, time_fmt1 = subTimeDataFrame(synoptic_time)
            
                notype = otype_w[count]
            
                if time_fmt0 == time_fmt1:
                    dfsp = dfs2.loc[dfs2['Tipo de Observação'] == str(i)].loc[dfs2['Tipo de Arquivo'] == str(j)].set_index('Data da Observação').at_time(str(time_fmt0)).reset_index()
                else:
                    dfsp = dfs2.loc[dfs2['Tipo de Observação'] == str(i)].loc[dfs2['Tipo de Arquivo'] == str(j)].set_index('Data da Observação').between_time(str(time_fmt0), str(time_fmt1), inclusive='both')                
            
                    if synoptic_time == '00Z e 12Z':
                        dfsp = dfsp.drop(dfsp.at_time('06:00:00').index).reset_index()
                    elif synoptic_time == '06Z e 18Z':    
                        dfsp = dfsp.drop(dfsp.at_time('12:00:00').index).reset_index()
                    elif synoptic_time == '00Z, 06Z, 12Z e 18Z':
                        dfsp = dfsp.reset_index()              
            
                factor, n1factor, n2factor, n3factor = unitConvert(units_w)
            
                dfsp[n1factor] = dfsp['Tamanho do Download (KB)'].multiply(factor)               
            
                df_pl = dfsp.hvplot.line(x='Data da Observação', xlabel='Data', y=n1factor, 
                                     ylabel=str(n2factor), label=str(notype), rot=90, grid=True, 
                                     line_width=2, height=550, responsive=True)
            
            else:
                
                start_date, end_date = date_range
                dfs_tmp = dfs.copy()
                dfs2 = subDataframe(dfs_tmp, start_date, end_date)            
            
                time_fmt0, time_fmt1 = subTimeDataFrame(synoptic_time)
            
                notype = otype_w[count]
            
                if time_fmt0 == time_fmt1:
                    dfsp = dfs2.loc[dfs2['Tipo de Observação'] == str(i)].loc[dfs2['Tipo de Arquivo'] == str(j)].set_index('Data da Observação').at_time(str(time_fmt0)).reset_index()
                else:
                    dfsp = dfs2.loc[dfs2['Tipo de Observação'] == str(i)].loc[dfs2['Tipo de Arquivo'] == str(j)].set_index('Data da Observação').between_time(str(time_fmt0), str(time_fmt1), inclusive='both')                
            
                    if synoptic_time == '00Z e 12Z':
                        dfsp = dfsp.drop(dfsp.at_time('06:00:00').index).reset_index()
                    elif synoptic_time == '06Z e 18Z':    
                        dfsp = dfsp.drop(dfsp.at_time('12:00:00').index).reset_index()
                    elif synoptic_time == '00Z, 06Z, 12Z e 18Z':
                        dfsp = dfsp.reset_index()              
                
                factor, n1factor, n2factor, n3factor = unitConvert(units_w)
                
                dfsp[n1factor] = dfsp['Tamanho do Download (KB)'].multiply(factor)                    
                    
                df_pl *= dfsp.hvplot.line(x='Data da Observação', xlabel='Data', y=n1factor, 
                                      ylabel=n2factor, label=str(notype), rot=90, grid=True, 
                                      line_width=2, height=550, responsive=True)
    
    return pn.Column(df_pl, sizing_mode='stretch_width')

@pn.depends(otype_w, ftype_w, synoptic_time, date_range_slider.param.value, units_w)
def plotSelSize(otype_w, ftype_w, synoptic_time, date_range, units_w):
    start_date, end_date = date_range
    dfs_tmp = dfs.copy()
    dfs2 = subDataframe(dfs_tmp, start_date, end_date)    
    
    time_fmt0, time_fmt1 = subTimeDataFrame(synoptic_time)    
        
    if time_fmt0 == time_fmt1:
        dfsp = dfs2.loc[dfs2['Tipo de Observação'].isin(otype_w)].loc[dfs2['Tipo de Arquivo'].isin(ftype_w)].set_index('Data da Observação').at_time(str(time_fmt0)).reset_index()
    else:
        dfsp = dfs2.loc[dfs2['Tipo de Observação'].isin(otype_w)].loc[dfs2['Tipo de Arquivo'].isin(ftype_w)].set_index('Data da Observação').between_time(str(time_fmt0), str(time_fmt1), inclusive='both')
            
        if synoptic_time == '00Z e 12Z':
            dfsp = dfsp.drop(dfsp.at_time('06:00:00').index).reset_index()
        elif synoptic_time == '06Z e 18Z':    
            dfsp = dfsp.drop(dfsp.at_time('12:00:00').index).reset_index()
        elif synoptic_time == '00Z, 06Z, 12Z e 18Z':
            dfsp = dfsp.reset_index()      
    
    factor, n1factor, n2factor, n3factor = unitConvert(units_w)
    
    # Tamanho do download (ou do espaço ocupado), de acordo com a seleção da tabela
    dfsp_tot_down = dfsp['Tamanho do Download (KB)'].sum(axis=0)
    
    dfsp_dic_down = getSizeDic(dfsp, otype_w)
    
    data = pd.Series(dfsp_dic_down).reset_index(name='Tamanho do Download (KB)').rename(columns={'index':'Tipo de Observação'})  
    
    # Acrescenta uma nova coluna 'Tamanho Relativo' à série data
    data['Tamanho Relativo (%)'] = (data['Tamanho do Download (KB)'] / dfsp_tot_down) * 100
    
    data['angle'] = (data['Tamanho do Download (KB)'] / data['Tamanho do Download (KB)'].sum()) * (2 * pi)
    #data['color'] = Category20c[len(dfsp_dic_down)]
    #if len(dfsp_dic_down) < 3:
    #    data['color'] = '#ffffff'
    #else:
    #    data['color'] = Category20c[len(dfsp_dic_down)]
    if len(dfsp_dic_down) == 0:
        data['color'] = ''
    elif len(dfsp_dic_down) == 1:
        #data['color'] = 'red'
        data['color'] = Category20c[3][0]
    elif len(dfsp_dic_down) == 2:
        #data['color'] = 'blue'
        data['color'] = Category20c[3][1]
    elif len(dfsp_dic_down) > 2:   
        data['color'] = Category20c[len(dfsp_dic_down)]
        #data['color'] = Category20c[20][len(dfsp_dic_down)]

    p = figure(height=550, title='Tamanho Relativo (%)', #toolbar_location=None, tools="hover", 
               tooltips="@{Tipo de Observação}: @{Tamanho Relativo (%)}", x_range=(-0.6, 1.15))    
    
    r = p.wedge(x=0, y=1, radius=0.55,
                start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),
                line_color='white', fill_color='color', legend_field='Tipo de Observação', 
                source=data)

    p.axis.axis_label=None
    p.axis.visible=False
    p.grid.grid_line_color=None

    return pn.Column(pn.pane.Bokeh(p))
         
######    
    
card_parameters = pn.Card(date_range_slider, synoptic_time, units_w, pn.Column(ftype_w, height=120), pn.Column(otype_w, height=450), title='Parâmetros', collapsed=False)

tabs_contents = pn.Tabs(('Gráficos', pn.Row(plotLine, pn.Row(plotSelSize, width=600))), ('Tabela', getTable))

#pn.template.FastListTemplate(
#    site="SMNA Dashboard", title="Armazenamento Observações (ArmObs)",
#    sidebar = [card_parameters],
#    main=["Visualização do armazenamento das observações do **SMNA**", tabs_contents, getTotDown]
#).show();
##).servable();


# In[ ]:


def monitor_armobs_sidebar():
    return card_parameters


def monitor_armobs_main():
    return tabs_contents

