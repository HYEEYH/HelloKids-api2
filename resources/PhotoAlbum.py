


# 사진첩

# 라이브러리 ------------------------------------------------------------------
from multiprocessing import connection
from flask_restful import Resource
from flask import request
import mysql.connector
from mysql.connector import Error
from config import Config
from mysql_connection import get_connection
from utils import check_password, hash_password
from email_validator import validate_email,EmailNotValidError 
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity, jwt_required

import boto3
import datetime
# ----------------------------------------------------------------------------


### 사진첩 목록 보기
# 의문점 ) 주소에 int를 두번이나 써야 하는데 이거 괜찮은걸까?
class PhotoAlbumListResource(Resource):

    @jwt_required()
    def get(self, nurseryId, classId):

        try:
            connection = get_connection()
            query = '''select nurseryId, classId, teacherId, date, title, contents, photoUrl from totalAlbum 
                    where nurseryId = %s and classId = %s;'''
            record = (nurseryId, classId)
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)
            result_list = cursor.fetchall()
            cursor.close()
            connection.close()

        except Error as e:
            print(e)
            return{'result':'fail', 'error':str(e)}, 400
        
        i = 0
        for row in result_list :
            result_list[i]['date']= row['date'].isoformat().replace('T', ' ')[0:10]
            i = i + 1

        return {'result':'success', 'items':result_list}




### 사진첩 생성
# 의문점 ) 주소에 int를 두번이나 써야 하는데 이거 괜찮은걸까?
# 사진 여러장 받아서 AWS 올리고 그 내용 다운받아서 어레이로 데이터베이스에 저장
class PhotoAlbumAddResource(Resource):

    @jwt_required()
    def post(self, nurseryId, classId):

        # 1. 데이터 받아오기(유저 정보)
        teacherId = get_jwt_identity()

        # 사진 잘 올렸니?
        if 'photo' not in request.files or 'content' not in request.form :
            return { 'result' : 'fail', 'error' : '필수항목을 확인하세요'}, 400
        
        # 2. 데이터 가져오기
        date = request.files['date'].isoformat().replace('T', ' ')[0:10]
        title = request.form['title']
        contents = request.form['contents']
        photoUrl = request.form['photoUrl']

        # 데이터베이스에서 어린이집 아이디와 반 아이디를 가져오기(파일 정리할때 이름으로 정리되어 들어가도록)
        query = '''SELECT classId, nurseryId, nurseryName 
                    FROM nursery n 
                    left join teacher t on n.id = t.nurseryId 
                    where t.id = %s;'''
        record = (teacherId, )
        cursor = connection.cursor()
        cursor.execute(query, record)
        teacher_result_list = cursor.fetchall()

        teacher_result_list_str = str(teacher_result_list[0][1]) + '_' + teacher_result_list[0][2]
        print(teacher_result_list_str)

        # 사진부터 S3에 저장
        current_time = datetime.now()
        new_filename = teacher_result_list_str + '/menu/' + current_time.isoformat().replace(':','_').replace('.','_')+'.jpg' # 사람이보는형식
        print(new_filename)


        # 반복문을 통해 여러 파일을 s3에 저장 -> 만들어야 함.
        for i in range (1, len(request.FILES)+1):
            file = request.FILES[f'filename{i}']





        return