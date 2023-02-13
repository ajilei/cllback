import re

from rest_framework.views import APIView
from ORG.models import UrlModel
from django.http.response import HttpResponse
import json
# coding=utf-8

class GetUrlAPIView(APIView):
    def get(self, request):
        a = UrlModel.objects.using('cgl').filter()
        b = []
        for i in a:
            if i.params:
                d = {'fun':i.status,'name': i.name, 'url': i.url, 'text': i.text, 'params': json.loads(i.params)['b']}
            else:
                d = {'fun':i.status,'name': i.name, 'url': i.url, 'text': i.text, 'params': None}
            b.append(d)
        data = {
            'code': 200,
            'data': b,
            # 'msg': '获取成功'
        }

        return HttpResponse(json.dumps(data), content_type='application/json')
        # res =HttpResponse
        # res ['date']=a
        # return res
