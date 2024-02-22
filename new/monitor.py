#! /usr/bin/env python3

import panel as pn

from monitor_jo import monitor_jo_sidebar, monitor_jo_main
from monitor_mass import MonitoringAppMass
#from monitor_armobs import monitor_armobs_sidebar, monitor_armobs_main

monitoring_app_mass = MonitoringAppMass()
monitor_mass_sidebar = monitoring_app_mass.LayoutSidebar()
monitor_mass_main = monitoring_app_mass.LayoutMain()

class MonitoringApp:
    def __init__(self):
        pn.extension()

        self.create_layout()

    def create_layout(self):

        self.tab1 = pn.Column(monitor_jo_main(), sizing_mode="stretch_both")

        self.tab2 = pn.Column(monitor_mass_main, sizing_mode="stretch_both")   

#        self.tab3 = pn.Column(monitor_armobs_main, sizing_mode="stretch_both")   
        
        # Conteúdo da aplicação
        tabs = pn.Tabs(dynamic=True, active=0)
        tabs.append(("Minimization Plots", self.tab1))
        tabs.append(("Constrains", self.tab2))
#        tabs.append(("ArmObs", self.tab3))

        # Layout da barra lateral
        sidebar_jo = pn.Column(monitor_jo_sidebar())
        
        sidebar_mass = pn.Column(monitor_mass_sidebar)

#        sidebar_armobs = pn.Column(monitor_armobs_sidebar)

        col = pn.Column(sidebar_jo)
        
        @pn.depends(tabs.param.active, watch=True)
        def insert_widget(active_tab):
            if active_tab == 0: 
                col[0] = sidebar_jo
            elif active_tab == 1:
                col[0] = sidebar_mass
#            elif active_tab == 2:
#                col[0] = sidebar_armobs
    

        self.app = pn.template.FastListTemplate(
            site="SMNA Dashboard",
            title="MonitoringApp",
        )
    
        self.app.main.append(pn.Column('### Dashboard para o monitoramento operacional do SMNA'))
        self.app.main.append(tabs)
        self.app.sidebar.append(col)
        self.app.sidebar.append('##### CPTEC-INPE, 2024.')

    def run(self):
        self.app.servable()

monitoring_app = MonitoringApp()
monitoring_app.run()
