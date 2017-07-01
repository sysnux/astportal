# -*- coding: utf-8 -*-

"""Themed JqGrid used in astportal2."""

from tw.uitheme import uilightness_css
from tw.jqgrid import JqGrid, jqgrid_css, jqgrid_search_css

class MyJqGrid(JqGrid):
   css = [uilightness_css, jqgrid_css, jqgrid_search_css]
   caption = u'Données'
   rowNum = -1
   page = 1
   rowList = [25, 50, 100, 500]
   sortorder = 'asc'
   shrinkToFit = True
   viewrecords = True
#   autowidth: true
#   altrows: true
   altRows = True
   gridview = True # Faster but has limitations
   subGridWidth = 20
   navbuttons_options = {'view': False, 'edit': False, 'add': False,
      'del': False, 'search': False, 'refresh': True, 
#'afterRefresh': js_callback('alert("afterRefresh")'),
      }
#beforeRequest = js_callback('alert("XXX")'),
#toolbar = [True,'top'],

