# GSIMonitor

![Under construction](https://upload.wikimedia.org/wikipedia/commons/d/d9/Under_construction_animated.gif)

To update the GSIDashboard (under construction), make the necessary changes to the `monitor.py` script and check the results with the command `panel serve monitor.py --autoreload --show`. This will open the browser with the dashboard.

If everything works as expected, the dashboard can be deployed at GitHub pages:

1. Convert the `monitor.py` to `monitor.[html,js]` with the command:

    **Note:** make sure to have `self.app.servable()` instead of `self.app.show()` in the `monitor.py` script.

    ```
    panel convert monitor.py --to pyodide-worker --out .
    ```

2. Make sure to insert the `sqlite3` module in the `monitor.js` in the line:

    ```
    const env_spec = ['https://cdn.holoviz.org/panel/wheels/bokeh-3.3.4-py3-none-any.whl', 'https://cdn.holoviz.org/panel/1.3.8/dist/wheels/panel-1.3.8-py3-none-any.whl', 'pyodide-http==0.2.1', 'holoviews', 'hvplot', 'numpy', 'pandas', 'requests', 'sqlite3']
    ```

3. Add, commit and push the updated files:

    ```
    git add monitor.py monitor.js monitor.html
    git commit -m "bla bla bla"
    git push
    ```

