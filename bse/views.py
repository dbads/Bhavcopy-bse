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

CSV_DIR = 'csv'


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
  csv_path = CSV_DIR + '/' + csv_name + '.CSV'

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
      zfile.extractall(CSV_DIR)


def store_bhav_data_in_redis(csv_data, redis_instance, date, csv_path):
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

  # set date in redis, so that we know that bhav for today are fetched
  redis_instance.set(str(date), 'true', 7 * 24 * 60 * 60)  # set date for 7 days

  # remove csv file
  if os.path.exists(csv_path):
    os.remove(csv_path)


def csv_to_list(csv_path):
  """This function parses the given csv file and returns the list of Bhav objects(each line of csv)"""
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


def get_day(date, redis_instance, dayname):
  """Tells the date of the Bhavs shown on the app"""

  # modify date if todays data is not fetched i.e date is not set in redis
  if not redis_instance.get(str(date)):
    if dayname == 'Sunday':  # for sunday last open day would be date - 2
      date = date - timedelta(days=2)
    else:  # for saturday and other days, if bhave for today is not fethced then showing bhav would be for date - 1
      date = date - timedelta(days=1)

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
  dayname = today.strftime('%A')
  yesterday = today - timedelta(days=1)
  hour = int(((datetime.utcnow().hour) * 60 + (330)) / 60)

  csv_path_today = get_csv_path(today)
  csv_path_yesterday = get_csv_path(yesterday)

  # downlaod bhav copy for today if hour >= 18, else previous bhavs will be shown
  weekends = ['Saturday', 'Sunday']
  if hour >= 1 and dayname not in weekends and not redis_instance.get(str(today)):
    download_bhav_copy(today)
    csv_path = csv_path_today
    csv_data = csv_to_list(csv_path)
    # store new data in redis
    store_bhav_data_in_redis(csv_data, redis_instance, today, csv_path)

  day = get_day(today, redis_instance, dayname)

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
