#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  AppAnnie Playground
#  Set your API key and account numbers in settings.py

import io
import csv
import glob
import os.path
import requests
import subprocess
from datetime import date, timedelta

import settings as _s


def main():
	""" Run the whole toolchain for all accounts. """
	_clean()
	
	for account_id, account_name in _accounts().items():
		
		# CSV file for reviews per account
		with io.open('Reviews {}.csv'.format(account_name), 'w', encoding='UTF-8') as comm:
			w_comm = csv.writer(comm)
			w_comm.writerow(["App","version","country","date","title","text","reviewer"])
			
			# loop apps
			for app_id, app_name in _apps(account_id).items():
				if _s.skip_apps and app_id in _s.skip_apps:
					continue
				print()
				print('{} [{}]'.format(app_name, app_id))
				print('==========')
				
				# dump and print reviews
				n = 0
				for rev in _reviews(account_id, app_id):
					w_comm.writerow([app_name, rev['version'], rev['country'], rev['date'], _sf(rev['title']), _sf(rev['text']), _sf(rev['reviewer'])])
					
					# print last 7 reviews
					if n < 7:
						stars = '%s%s' % (''.join([u"★" for i in range(rev['rating'])]), ''.join([u"☆" for i in range(5 - rev['rating'])]))
						print()
						print("%s, %s  %s (%s)" % (rev['version'], stars, rev['title'], rev['country']))
						print(rev['text'])
						print("%s, %s" % (rev['date'], rev['reviewer']))
					n += 1
				
				sales = _sales(account_id, app_id)
				
				# create CSV for sales data per app
				csv_path = 'Numbers {}.csv'.format(app_name)
				csv_exists = os.path.exists(csv_path)
				csv_mode = 'a' if csv_exists else 'w'
				with open(csv_path, csv_mode) as hndl:
					w_csv = csv.writer(hndl)
					if not csv_exists:
						w_csv.writerow(["date","num_downloads","num_updates","num_refunds","sales","refunds"])
					
					for sale in sales:
						s_date = sale.get('date')
						s_num = sale.get('units', {}).get('app')
						s_sale = sale.get('revenue', {}).get('app')
						assert s_num and s_sale
						w_csv.writerow([s_date, s_num.get('downloads'), s_num.get('updates'), s_num.get('refunds'), s_sale.get('downloads'), s_sale.get('refunds')])
	
	# run R script to generate PDFs
	if _s.run_r:
		subprocess.call(['R', '--vanilla', '--slave', '-f', 'appannie.R'])

def _clean():
	""" Cleans old data files.
	"""
	for f in glob.glob('./Numbers *.csv'):
		os.remove(f)

def _get(path):
	""" Sets up a requests object, composes the URL and downloads data from
	AppAnnie's API. """
	assert _s.api_key
	assert _s.base_url
	assert path and len(path) > 0
	
	headers = {
		'Authorization': 'Bearer {}'.format(_s.api_key),
		'content-type': 'application/json'
	}
	
	url = os.path.join(_s.base_url, path)
	r = requests.get(url, headers=headers)
	try:
		r.raise_for_status()
	except Exception as e:
		print("Failed to download:\n%s\n%s" % (url, e))
	
	return r.json()

def _accounts():
	""" Return a dictionary of account-id: account-name entries. """
	raw = _get('accounts')
	d = {}
	for acc in raw['account_list']:
		d[str(acc['account_id'])] = acc['account_name']
	return d

def _apps(account_id):
	raw = _get('accounts/{}/apps'.format(account_id))
	d = {}
	for app in raw['app_list']:
		d[str(app['app_id'])] = app['app_name']
	return d

def _sales(account_id, app_id, start=None, end=None):
	sales = []
	raw = _get('accounts/{}/apps/{}/sales?break_down=date'.format(account_id, app_id))
	sales.extend(raw['sales_list'])
	
	# more pages?
	next = raw.get('next_page')
	if next is not None:
		print("MUST GET NEXT PAGE", next)
	
	return sales

def _reviews(account_id, app_id, start=None, end=None):
	""" Downloads app reviews. """
	if end is None:
		end = date.today().isoformat()
	if start is None:
		d_start = date.today() - timedelta(days=31)
		start = d_start.isoformat()
	
	raw = _get('accounts/{}/apps/{}/reviews?break_down=date'.format(account_id, app_id))
	return raw['review_list']

def _sf(string):
	""" Make a string CSV-safe. """
	if not string:
		return ''
	return string.replace('"', '""').encode('utf-8')

	
if '__main__' == __name__:
	main()
