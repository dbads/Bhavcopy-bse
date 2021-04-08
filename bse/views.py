# python builtin modules
import csv
import json
import os.path
from io import BytesIO
from zipfile import ZipFile
from datetime import date, timedelta, datetime

# third party module
import requests
import redis

from django.shortcuts import render
from django.http import JsonResponse

# app modules
from bhavcopy import settings


def get_day_month_year(date):
  """Return a tuple of day,month,year in required format, adds leading 0 for single digit day and month"""
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
  csv_path = 'csv/' + csv_name + '.CSV'

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
      zfile.extractall('csv')


def store_bhav_data_in_redis(csv_data, redis_instance):
  """Store the bhav data in provided csv to redis"""
  print('**** storing bhavs in redis ****')
  for bhav in csv_data:
    data = {
        'SC_CODE': bhav["SC_CODE"],
        'OPEN': bhav["OPEN"],
        'LOW': bhav["LOW"],
        'CLOSE': bhav["CLOSE"],
    }
    value = json.dumps(data)
    key = bhav['SC_NAME']
    redis_instance.set(key.strip(), value)


def csv_to_list(csv_path):
  csv_data = []
  with open(csv_path, mode='r') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    line_count = 0
    for row in csv_reader:
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


def get_day(date):
  day_detail = get_day_month_year(date)
  return day_detail[0] + '-' + day_detail[1] + '-' + day_detail[2]


def bhav_bse(request):
  """
    This view has following tasks
    1. download and fetch the zip for today if time >= 6pm and zip is not already fetched
    2. update the fetched bhav data to redis
    3. if a Get request contains a searchKey, then search all the matching bhavs from redis and return
  """
  template_name = 'bhav_bse.html'
  # Connect to redis
  redis_url = os.environ.get('REDIS_URL')
  if redis_url:
    redis_instance = redis.from_url(redis_url)
  else:
    redis_instance = redis.StrictRedis(host=settings.REDIS_HOST,
                                       port=settings.REDIS_PORT, db=0)

  today = date.today()
  yesterday = today - timedelta(days=1)
  hour = int(((datetime.utcnow().hour) * 60 + (330)) / 60)

  csv_path_today = get_csv_path(today)
  csv_path_yesterday = get_csv_path(yesterday)

  # downlaod bhav copy for today if hour >= 18, else previous bhavs will be shown
  if hour >= 18 and not os.path.exists(csv_path_today):
    download_bhav_copy(today)
    csv_path = csv_path_today
    csv_data = csv_to_list(csv_path)
    # store new data in redis
    store_bhav_data_in_redis(csv_data, redis_instance)

  if os.path.exists(csv_path_today):
    day = get_day(today)
  else:
    day = get_day(yesterday)

  # when search input is changed
  searchKey = request.GET.get('searchKey', '')
  if len(searchKey) >= 2:  # query redis only if there are atleast 2 chars in searchKey
    bhav_keys = redis_instance.keys('*' + searchKey.upper() + '*')
    bhav_data = []
    for key in bhav_keys:
      data = redis_instance.get(key.decode('utf-8'))
      data = json.loads(data.decode('utf-8'))
      single_data = {
          'SC_CODE': data['SC_CODE'],
          'SC_NAME': key.decode('utf-8'),
          'OPEN': data['OPEN'],
          'LOW': data['LOW'],
          'CLOSE': data['CLOSE'],
      }
      bhav_data.append(single_data)
    return JsonResponse(json.dumps(bhav_data), status=200, safe=False)

  return render(request, template_name, {'bhav_data': [], 'day': day})
