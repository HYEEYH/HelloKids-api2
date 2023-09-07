
# --------------------------------------------------------------
from flask_restful import Resource
from flask import request

## restful api 를 코드에서 사용할때 필요한 라이브러리 ##
import requests

from config import Config
# ---------------------------------------------------------------


class TranslateResource(Resource) :

    def post(self) :

        data = request.get_json()

        headers = { 'Content-Type' : 'application/x-www-form-urlencoded; charset=UTF-8' ,
                   'X-Naver-Client-Id' : Config.X_NAVER_CLIENT_ID,
                    'X-Naver-Client-Secret' : Config.X_NAVER_CLIENT_SECRET }
        data = {'source' : 'ko' , 
                'target' : data['lang'],
                'text' : data['text']  }

        response = requests.post("https://openapi.naver.com/v1/papago/n2mt",
                      headers= headers,
                      data= data )
        
        print(response.json() )

        print()
        
        print( response.json()['message']['result']['translatedText'] )

        text = response.json()['message']['result']['translatedText']

        return {'result' : 'success' , 'text' : text}