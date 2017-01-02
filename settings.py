#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#  AppAnnie Settings


# your AppAnnie API key
api_key = ''

# set to False to not run the R script that generates the graph
run_r = True

# set to True to add time delay to avoid AppAnnie Maximum calls per minute limit
add_delay = False

# set App IDs that you want to skip (as strings!)
skip_apps = []

# manually mess with the data, format: {'app_id': {'iso-date': {'type': (from, to)}}}
alter_data = {
}

# API Base URL
base_url = 'https://api.appannie.com/v1.2'
