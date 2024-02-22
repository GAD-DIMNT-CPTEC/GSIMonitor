importScripts("https://cdn.jsdelivr.net/pyodide/v0.24.1/full/pyodide.js");

function sendPatch(patch, buffers, msg_id) {
  self.postMessage({
    type: 'patch',
    patch: patch,
    buffers: buffers
  })
}

async function startApplication() {
  console.log("Loading pyodide!");
  self.postMessage({type: 'status', msg: 'Loading pyodide'})
  self.pyodide = await loadPyodide();
  self.pyodide.globals.set("sendPatch", sendPatch);
  console.log("Loaded!");
  await self.pyodide.loadPackage("micropip");
  const env_spec = ['https://cdn.holoviz.org/panel/wheels/bokeh-3.3.4-py3-none-any.whl', 'https://cdn.holoviz.org/panel/1.3.8/dist/wheels/panel-1.3.8-py3-none-any.whl', 'pyodide-http==0.2.1', 'monitor_armobs', 'monitor_jo', 'monitor_mass', 'holoviews', 'hvplot', 'numpy', 'pandas', 'requests' 'sqlite3']
  for (const pkg of env_spec) {
    let pkg_name;
    if (pkg.endsWith('.whl')) {
      pkg_name = pkg.split('/').slice(-1)[0].split('-')[0]
    } else {
      pkg_name = pkg
    }
    self.postMessage({type: 'status', msg: `Installing ${pkg_name}`})
    try {
      await self.pyodide.runPythonAsync(`
        import micropip
        await micropip.install('${pkg}');
      `);
    } catch(e) {
      console.log(e)
      self.postMessage({
	type: 'status',
	msg: `Error while installing ${pkg_name}`
      });
    }
  }
  console.log("Packages loaded!");
  self.postMessage({type: 'status', msg: 'Executing code'})
  const code = `
  
import asyncio

from panel.io.pyodide import init_doc, write_doc

init_doc()

#! /usr/bin/env python3

import panel as pn

from monitor_jo import monitor_jo_sidebar, monitor_jo_main
from monitor_mass import MonitoringAppMass
from monitor_armobs import monitor_armobs_sidebar, monitor_armobs_main

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

        self.tab3 = pn.Column(monitor_armobs_main, sizing_mode="stretch_both")   
        
        # Conteúdo da aplicação
        tabs = pn.Tabs(dynamic=True, active=0)
        tabs.append(("Minimization Plots", self.tab1))
        tabs.append(("Constrains", self.tab2))
        tabs.append(("ArmObs", self.tab3))

        # Layout da barra lateral
        sidebar_jo = pn.Column(monitor_jo_sidebar())
        
        sidebar_mass = pn.Column(monitor_mass_sidebar)

        sidebar_armobs = pn.Column(monitor_armobs_sidebar)

        col = pn.Column(sidebar_jo)
        
        @pn.depends(tabs.param.active, watch=True)
        def insert_widget(active_tab):
            if active_tab == 0: 
                col[0] = sidebar_jo
            elif active_tab == 1:
                col[0] = sidebar_mass
            elif active_tab == 2:
                col[0] = sidebar_armobs
    

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


await write_doc()
  `

  try {
    const [docs_json, render_items, root_ids] = await self.pyodide.runPythonAsync(code)
    self.postMessage({
      type: 'render',
      docs_json: docs_json,
      render_items: render_items,
      root_ids: root_ids
    })
  } catch(e) {
    const traceback = `${e}`
    const tblines = traceback.split('\n')
    self.postMessage({
      type: 'status',
      msg: tblines[tblines.length-2]
    });
    throw e
  }
}

self.onmessage = async (event) => {
  const msg = event.data
  if (msg.type === 'rendered') {
    self.pyodide.runPythonAsync(`
    from panel.io.state import state
    from panel.io.pyodide import _link_docs_worker

    _link_docs_worker(state.curdoc, sendPatch, setter='js')
    `)
  } else if (msg.type === 'patch') {
    self.pyodide.globals.set('patch', msg.patch)
    self.pyodide.runPythonAsync(`
    state.curdoc.apply_json_patch(patch.to_py(), setter='js')
    `)
    self.postMessage({type: 'idle'})
  } else if (msg.type === 'location') {
    self.pyodide.globals.set('location', msg.location)
    self.pyodide.runPythonAsync(`
    import json
    from panel.io.state import state
    from panel.util import edit_readonly
    if state.location:
        loc_data = json.loads(location)
        with edit_readonly(state.location):
            state.location.param.update({
                k: v for k, v in loc_data.items() if k in state.location.param
            })
    `)
  }
}

startApplication()
