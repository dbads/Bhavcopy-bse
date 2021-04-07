from io import BytesIO, StringIO
from urllib.request import urlopen
from zipfile import ZipFile
from django.shortcuts import render
import requests
import redis
from bhavcopy import settings
import json
# from django.utils import simplejson


def bhav_bse(request):
  template_name = 'bhav_bse.html'
  # headers = {
  #     'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3'
  # }
  # bhav_url = 'https://www.bseindia.com/download/BhavCopy/Equity/EQ060421_CSV.ZIP'

  # # download zipfile and extract it into /tmp/bse/
  # with requests.get(bhav_url, headers=headers) as zipresp:
  #   with ZipFile(BytesIO(zipresp.content)) as zfile:
  #     zfile.extractall('/tmp/bse/')
  #     print('done!')

  # read downloaded csv file and store bhav data in redis
  # Connect to our Redis instance
  redis_instance = redis.StrictRedis(host=settings.REDIS_HOST,
                                     port=settings.REDIS_PORT, db=0)

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

  rows = [
      {'department': 'Accounting', 'employees': ['Bradley', 'Jones', 'Alvarado']},
      {
          'department': 'Human Resources',
          'employees': ['Juarez', 'Banks', 'Smith'],
      },
      {
          'department': 'Production',
          'employees': ['Sweeney', 'Bartlett', 'Singh'],
      },
      {
          'department': 'Research and Development',
          'employees': ['Lambert', 'Williamson', 'Smith'],
      },
      {
          'department': 'Sales and Marketing',
          'employees': ['Prince', 'Townsend', 'Jones'],
      },
  ]
  return render(request, template_name, {'bhav_data': 'bhav', 'data': 'keys', 'rows': rows})
