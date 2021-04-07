from io import BytesIO, StringIO
from urllib.request import urlopen
from zipfile import ZipFile
from django.shortcuts import render
import requests
import redis
from bhavcopy import settings
import json
# from django.utils import simplejson
from datetime import date, timedelta
import csv
import os.path


def get_day_month_year(date):
  day, month, year = date.day, date.month, date.year
  # add leading zero in single digit day and month
  if len(str(day)) == 1:
    day = '0' + str(day)
  else:
    day = str(day)

  if len(str(month)) == 1:
    month = '0' + str(month)
  else:
    month = str(month)

  year = str(year)[2:]
  return (day, month, year)


def get_csv_path(date):
  """get csv path for bhav data of date provided"""
  (day, month, year) = get_day_month_year(date)
  csv_name = 'EQ' + day + month + str(year)
  csv_path = '/tmp/bse/' + csv_name + '.csv'

  return csv_path


def download_bhav_copy(date):
  """Download the bhav zip, extract and save csv to /tmp/bse"""
  headers = {
      'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3'
  }

  (day, month, year) = get_day_month_year(date)
  bhav_url = 'https://www.bseindia.com/download/BhavCopy/Equity/EQ' + day + month + year + '_CSV.ZIP'

  # download zipfile and extract it into /tmp/bse/
  with requests.get(bhav_url, headers=headers) as zipresp:
    with ZipFile(BytesIO(zipresp.content)) as zfile:
      zfile.extractall('/tmp/bse/')


def store_bhav_data_in_redis(csv, redis_instance):
  """Store the bhav data in provided csv to redis"""

  pass


def read_csv_in_dict(csv_path):
  csv_data = []
  with open(csv_path, mode='r') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    line_count = 0
    for row in csv_reader:
      if line_count == 0:
        print(f'Column names are {", ".join(row)}')
        line_count += 1
      # print(
      #     f'\t{row["SC_NAME"]}  {row["OPEN"]}  {row["CLOSE"]}.')
      # code, name, open, high, low, close
      data = {
          'SC_CODE': row["SC_CODE"],
          'SC_NAME': row["SC_NAME"],
          'OPEN': row["OPEN"],
          'LOW': row["LOW"],
          'CLOSE': row["CLOSE"],
      }
      csv_data.append(data)
      line_count += 1

    print(f'Processed {line_count} lines.')

  return csv_data


def bhav_bse(request):
  template_name = 'bhav_bse.html'

  # downlaod bhav copy
  today = date.today()
  download_bhav_copy(today)

  # read downloaded csv file and store bhav data in redis
  # Connect to our Redis instance
  redis_instance = redis.StrictRedis(host=settings.REDIS_HOST,
                                     port=settings.REDIS_PORT, db=0)

  yesterday = today - timedelta(days=1)
  csv_path = get_csv_path(today)
  csv_path_yesterday = get_csv_path(yesterday)

  # if todays data is not downloaded then send yesterday data
  if not os.path.exists(csv_path):
    csv_path = csv_path_yesterday

  csv_data = read_csv_in_dict(csv_path)

  # keys = redis_instance.keys('*')
  # data = {}
  # for key in keys:
  #   print(key, type(key))
  # value = redis_instance.get(key)
  # data[key] = value
  # dic = {'msg': 'I am cool'}
  # value = json.dumps(dic)
  # redis_instance.set('deepak', value, '120')
  # v = redis_instance.get('deepak')
  # print(v)
  # print(json.loads(v))
  return render(request, template_name, {'bhav_data': csv_data})
