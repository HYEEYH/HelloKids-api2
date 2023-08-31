from flask_restful import Resource
from flask import request
import mysql.connector
from mysql.connector import Error
from mysql_connection import get_connection
from utils import check_password, hash_password
from email_validator import validate_email,EmailNotValidError 
from flask_jwt_extended import create_access_token, get_jwt, jwt_required
from datetime import datetime
from config import Config
import boto3


class TeacherNurseryResource(Resource) :

    def post(self):
#     {
#     "email" : "abc@naver.com",
#     "password" : "1234" 
#   }  
        # 1. 클라이언트로부터 데이터를 받는다.
        data = request.get_json()
        
        try:
            connection = get_connection()
            
            # DB에 저장
            query = '''insert into nursery
                    (nurseryName,nurseryAddress)
                    values
                    (%s,%s);'''
            query1 = '''insert into class
                    (className)
                    values
                    (%s);'''
           
            record = (data['nurseryName'],data['nurseryAddress'])
            record1 = (data['className'],)
            
            cursor = connection.cursor()
            cursor.execute(query,record)
            cursor.execute(query1,record1)
           
            connection.commit()

            cursor.close()
            connection.close()

        except Error as e:
            print(e)
            return {'result':'fail','error': str(e)}, 500
       
        return {'result' :'success'}
    


    
class TeacherChildrenResource(Resource) :
    def post(self):

        # 사진이 필수인 경우의 코드

        if 'profileUrl' not in request.files or 'childName' not in request.form or 'birth' not in request.form or 'sex' not in request.form: # 두 줄로 하고싶으면 \ (역슬래시) 이용해라
            return{'result':'fail','error':'필수항목 확인'},400
        # 유저가 올린 파일을 변수로 만든다
        file = request.files['profileUrl']
        childName = request.form['childName']
        birth = request.form['birth']
        sex = request.form['sex']

        # 2. 사진부터 s3에 저장
        # 파일명을 유니크하게 만들어준다
        current_time = datetime.now()

        new_filename = current_time.isoformat().replace(':','_').replace('.','_')+'_'+childName+'.jpg'

        # 새로운 파일명으로, s3에 파일 업로드
        try:
            s3 = boto3.client('s3', #s3에 올릴거다
                     aws_access_key_id =  Config.AWS_ACCESS_KEY_ID,
                     aws_secret_access_key = Config.AWS_SECRET_ACCESS_KEY) # 올릴려면 권한이 필요하다 
        # 그냥 액세스키를 넣어주면 짜면 회사에서 짤린다! 보안때문에!
            s3.upload_fileobj(file,
                            Config.S3_BUCKET,
                            new_filename,
                            ExtraArgs = {'ACL':'public-read', 'ContentType':'image/jpeg'}) # 퍼블릭으로해야 웹페이지에서도 볼 수 있다? / 우리는 사진을 jpeg 타입으로 할거에요
        except Exception as e:
            print(str(e))
            return{'result':'fail','error':str(e)},500
        
        # 3. 위에서 저장한 사진의 URL 주소와 내용을 DB에 저장해야 한다!
        # URL 주소는 = 버킷명.S3주소/우리가 만든 파일명
        file_url = Config.S3_BASE_URL+ new_filename # 이미지 url 부분은 회사마다 다르다
        try:
            # 3-1. 데이터베이스를 연결한다.
            connection = get_connection()

            # 3-2. 쿼리문 만든다
            ###### 중요! 컬럼과 매칭되는 데이터만 %s로 바꿔준다.
            query = '''insert into children
                    (childName,birth,sex,profileUrl)
                    values
                    (%s,%s,%s,%s);'''
            #3-3. 쿼리에 매칭되는 변수 처리! 중요! 튜플로 처리해준다!(튜프은 데이터변경이 안되니까?)
            # 위의 %s부분을 만들어주는거다
            record = (childName,birth,sex,file_url)
            #3-4 커서를 가져온다
            cursor = connection.cursor()
            #3-5 쿼리문을,커서로 실행한다.
            cursor.execute(query,record)
            #3-6 DB 반영 완료하라는, commit 해줘야한다.
            connection.commit()
            #3-7. 자원해제
            cursor.close()
            connection.close()

        except Error as e :
            print(e)
            return {'result':'fail','error': str(e)}, 500

        # 4. 잘 되었으면 또는 필요하면 데이터 가공해서 클라이언트에 데이터를 응답한다
        return {'result':'success','file_url':file_url}