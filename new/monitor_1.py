#! /usr/bin/env python3

import panel as pn

class MonitoringApp1:
    def __init__(self):
        pn.extension()

    def HelloWorld(self):
        return pn.Column("# Hello from MonitoringApp1")
