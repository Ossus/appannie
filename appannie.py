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
import time
from datetime import date, timedelta

import settings as _s


def main():
	""" Run the whole toolchain for all accounts. """
	_clean()
	
	for account in _accounts():
		if 'account_id' not in account:
			raise Exception("There is no 'account_id' in the account dictionary, did the API change?")
		if 'account_name' not in account:
			raise Exception("There is no 'account_name' in the account dictionary, did the API change?")
		
		account_id = account['account_id']
		account_name = account['account_name']
		
		# CSV file for reviews per account
		with io.open('Reviews {}.csv'.format(account_name), 'w', encoding='UTF-8') as comm:
			w_comm = csv.writer(comm)
			w_comm.writerow(["App","version","country","date","title","text","reviewer"])
			
			# loop apps
			for app in _apps(account_id):
				if _s.add_delay:
					time.sleep(5)
				if 'product_id' not in app:
					raise Exception("There is no 'product_id' in the app dictionary, did the API change?")
				app_id = str(app['product_id'])
				app_name = app['product_name']
				if _s.skip_apps and app_id in _s.skip_apps:
					continue
				if 'n/a' == app_name:
					continue
				app_title = '{} ({}) [{}]'.format(app_name, ', '.join(app.get('devices', [])), app_id)
				print()
				print(app_title)
				print(''.join(['=' for i in range(0, len(app_title))]))
				
				# dump and print reviews
				n = 0
				for rev in _reviews(account, app_id):
					w_comm.writerow([app_name, rev['version'], rev['country'], rev['date'], _sf(rev['title']), _sf(rev['text']), _sf(rev['reviewer'])])
					
					# print last 7 reviews
					if n < 7:
						stars = '%s%s' % (''.join([u"★" for i in range(rev['rating'])]), ''.join([u"☆" for i in range(5 - rev['rating'])]))
						print()
						print("%s, %s  %s (%s)" % (rev['version'], stars, rev['title'], rev['country']))
						print(rev['text'])
						print("%s, %s" % (rev['date'], rev['reviewer']))
					n += 1
				
				sales = _sales(account, app_id)
				
				# create CSV for sales data per app; R will create graphs named after the filename
				csv_path = 'Numbers {}.csv'.format(app_title.replace('/', '|'))
				csv_exists = os.path.exists(csv_path)
				csv_mode = 'a' if csv_exists else 'w'
				with open(csv_path, csv_mode) as hndl:
					w_csv = csv.writer(hndl)
					if not csv_exists:
						w_csv.writerow(["date","num_downloads","num_updates","num_refunds","sales","refunds"])
					
					alter = _s.alter_data.get(app_id)
					for sale in sales:
						s_date = sale.get('date')
						s_num = sale.get('units', {}).get('product')
						s_sale = sale.get('revenue', {}).get('product')
						assert s_num and s_sale
						if alter is not None and s_date in alter.keys():
							for a_what, a_chg in alter[s_date].items():
								if s_num.get(a_what) == a_chg[0]:
									s_num[a_what] = a_chg[1]
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
	""" Return a list of account dictionaries. """
	raw = _get('accounts')
	return raw.get('accounts', [])

def _apps(account_id):
	raw = _get('accounts/{}/products'.format(account_id))
	return raw.get('products', [])

def _sales(account, app_id, start=None, end=None):
	sales = []
	raw = _get('accounts/{}/products/{}/sales?break_down=date'.format(account.get('account_id'), app_id))
	if 'sales_list' in raw:
		sales.extend(raw['sales_list'])
	
	# TODO: more pages?
	nxt = raw.get('next_page')
	if nxt is not None:
		print("MUST GET NEXT PAGE - NOT IMPLEMENTED", nxt)
	
	return sales

def _reviews(account, app_id, start=None, end=None):
	""" Downloads app reviews. """
	if end is None:
		end = date.today().isoformat()
	if start is None:
		d_start = date.today() - timedelta(days=31)
		start = d_start.isoformat()
	
	raw = _get('{}/{}/app/{}/reviews?break_down=date'.format(account.get('vertical'), account.get('market'), app_id))
	return raw.get('reviews', [])

def _sf(string):
	""" Make a string CSV-safe. """
	if not string:
		return ''
	return string.replace('"', '""').encode('utf-8')


if '__main__' == __name__:
	main()
