# -*- coding: utf-8 -*-

def classFactory(iface):
    """Load SmartJoin class from file SmartJoin."""
    from .smart_join import SmartJoin
    return SmartJoin(iface)
