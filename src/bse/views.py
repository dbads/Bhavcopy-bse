from io import BytesIO, StringIO
from urllib.request import urlopen
from zipfile import ZipFile
from django.shortcuts import render
import requests


def bhav_bse(request):
  template_name = 'bhav_bse.html'
  headers = {
      'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3'
  }
  bhav_url = 'https://www.bseindia.com/download/BhavCopy/Equity/EQ060421_CSV.ZIP'

  # download zipfile and extract it into /tmp/bse/
  with requests.get(bhav_url, headers=headers) as zipresp:
    with ZipFile(BytesIO(zipresp.content)) as zfile:
      zfile.extractall('/tmp/bse/')
      print('done!')

  # read downloaded csv file and store bhav data in redis
  
  return render(request, template_name, {'bhav_data': 'bhav', 'data': 'z'})
