from flask_restful import Resource
from flask import request
import mysql.connector
from mysql.connector import Error
from mysql_connection import get_connection
from utils import check_password, hash_password
from email_validator import validate_email,EmailNotValidError 
from flask_jwt_extended import create_access_token, get_jwt, jwt_required, get_jwt_identity
from datetime import datetime
from config import Config
import boto3






class DailyNoteDeleteResource(Resource):

    @jwt_required()
    def delete(self, id):

        print(id)

        # 1. 헤더에 담긴 JWT 토큰을 받아온다.
        # teacherId = get_jwt_identity()
        # print('토큰확인', teacherId)

        # 2. DB에서 삭제한다
        try : 
            connection = get_connection()
            query = '''delete from dailyNote
                        where id = %s;'''
            record = (id, )
            cursor = connection.cursor()
            cursor.execute(query, record)
            connection.commit()

            cursor.close()
            connection.close()

        except Error as e:
            print(e)
            return {'result':'fail', 'error':str(e)}



        ### 3. 결과를 응답한다
        
        return {'result' : '알림장 기록이 삭제되었습니다'}


class DailyNoteAddResource(Resource) : #선생님이 알림장 등록

    @jwt_required()
    def post(self,childId):

        teacherId = get_jwt_identity()
        data = request.get_json()
         # 사진이 필수인 경우의 코드
        # if 'photoUrl' not in request.files or 'title' not in request.form or 'contents' not in request.form or 'dailyTemperCheck' not in request.form or 'dailyMealCheck' not in request.form or 'dailyNapCheck' not in request.form or 'dailyPooCheck' not in request.form: # 두 줄로 하고싶으면 \ (역슬래시) 이용해라
        #     return{'result':'fail','error':'필수항목 확인'},400
        # # 유저가 올린 파일을 변수로 만든다
        # file = request.files['photoUrl']
        # title = request.form['title']
        # contents = request.form['contents']
        # dailyTemperCheck = request.form['dailyTemperCheck']
        # dailyMealCheck = request.form['dailyMealCheck']
        # dailyNapCheck = request.form['dailyNapCheck']
        # dailyPooCheck = request.form['dailyPooCheck']

        # # 2. 사진부터 s3에 저장
        # # 파일명을 유니크하게 만들어준다
        # current_time = datetime.now()

        # new_filename = current_time.isoformat().replace(':','_').replace('.','_')+'.jpg'

        # # 새로운 파일명으로, s3에 파일 업로드
        # try:
        #     s3 = boto3.client('s3', #s3에 올릴거다
        #              aws_access_key_id =  Config.AWS_ACCESS_KEY_ID,
        #              aws_secret_access_key = Config.AWS_SECRET_ACCESS_KEY) # 올릴려면 권한이 필요하다 
        # # 그냥 액세스키를 넣어주면 짜면 회사에서 짤린다! 보안때문에!
        #     s3.upload_fileobj(file,
        #                     Config.S3_BUCKET,
        #                     new_filename,
        #                     ExtraArgs = {'ACL':'public-read', 'ContentType':'image/jpeg'}) # 퍼블릭으로해야 웹페이지에서도 볼 수 있다? / 우리는 사진을 jpeg 타입으로 할거에요
        # except Exception as e:
        #     print(str(e))
        #     return{'result':'fail','error':str(e)},500
        
        # # 3. 위에서 저장한 사진의 URL 주소와 내용을 DB에 저장해야 한다!
        # # URL 주소는 = 버킷명.S3주소/우리가 만든 파일명
        # file_url = Config.S3_BASE_URL+ new_filename # 이미지 url 부분은 회사마다 다르다
        try:
            # 2-1. 데이터베이스를 연결한다.
            connection = get_connection()

            # 2-2. 쿼리문 만든다
            ###### 중요! 컬럼과 매칭되는 데이터만 %s로 바꿔준다.
            query = '''insert into dailyNote
                    (teacherId,childId,title,contents,dailyTemperCheck,dailyMealCheck,dailyNapCheck,dailyPooCheck)
                    values
                    (%s,%s,%s,%s,%s,%s,%s,%s);'''
            #2-3. 쿼리에 매칭되는 변수 처리! 중요! 튜플로 처리해준다!(튜프은 데이터변경이 안되니까?)
            # 위의 %s부분을 만들어주는거다
            record = (teacherId,childId,data['title'],data['contents'],data['dailyTemperCheck'],data['dailyMealCheck'],data['dailyNapCheck'],data['dailyPooCheck'])
            #2-4 커서를 가져온다
            cursor = connection.cursor(prepared=True)
            #2-5 쿼리문을,커서로 실행한다.
            cursor.execute(query,record)
            #2-6 DB 반영 완료하라는, commit 해줘야한다.
            connection.commit()
            #2-7. 자원해제
            cursor.close()
            connection.close()

        except Error as e :
            print(e)
            return {'result':'fail','error': str(e)}, 500
            # 상태코드 에러에 맞게 내가 설계한다
        return{'result': 'success'} 

class DailyNoteParentsAddResource(Resource):
    
    @jwt_required()
    def post(self):

        parentsId = get_jwt_identity()
        data = request.get_json()

        try:
            connection = get_connection()
            query = '''select childId from parents
                    where id = %s;'''
            record = (parentsId, )
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)
            result_one = cursor.fetchone()
            print(result_one)
            childId = result_one['childId']

            # 2-2. 쿼리문 만든다
            ###### 중요! 컬럼과 매칭되는 데이터만 %s로 바꿔준다.
            query1 = '''insert into dailyNote
                    (parentsId,childId,title,contents,dailyTemperCheck,dailyMealCheck,dailyNapCheck,dailyPooCheck)
                    values
                    (%s,%s,%s,%s,%s,%s,%s,%s);'''
            #2-3. 쿼리에 매칭되는 변수 처리! 중요! 튜플로 처리해준다!(튜프은 데이터변경이 안되니까?)
            # 위의 %s부분을 만들어주는거다
            record1 = (parentsId,childId,data['title'],data['contents'],data['dailyTemperCheck'],data['dailyMealCheck'],data['dailyNapCheck'],data['dailyPooCheck'])
            #2-4 커서를 가져온다
            cursor1 = connection.cursor(prepared=True)
            #2-5 쿼리문을,커서로 실행한다.
            cursor1.execute(query1,record1)
            #2-6 DB 반영 완료하라는, commit 해줘야한다.
            connection.commit()
            #2-7. 자원해제
            cursor.close()
            cursor1.close()
            connection.close()

        except Error as e :
            print(e)
            return {'result':'fail','error': str(e)}, 500
            # 상태코드 에러에 맞게 내가 설계한다
        return{'result': 'success'} 

class DailyNoteEditResource(Resource):

    @jwt_required()
    def put(self,id):

        data = request.get_json()
          # 사진이 필수인 경우의 코드
        # if 'photoUrl' not in request.files or 'title' not in request.form or 'contents' not in request.form or 'dailyTemperCheck' not in request.form or 'dailyMealCheck' not in request.form or 'dailyNapCheck' not in request.form or 'dailyPooCheck' not in request.form: # 두 줄로 하고싶으면 \ (역슬래시) 이용해라
        #     return{'result':'fail','error':'필수항목 확인'},400
        # # 유저가 올린 파일을 변수로 만든다
        # file = request.files['photoUrl']
        # title = request.form['title']
        # contents = request.form['contents']
        # dailyTemperCheck = request.form['dailyTemperCheck']
        # dailyMealCheck = request.form['dailyMealCheck']
        # dailyNapCheck = request.form['dailyNapCheck']
        # dailyPooCheck = request.form['dailyPooCheck']

        # # 2. 사진부터 s3에 저장
        # # 파일명을 유니크하게 만들어준다
        # current_time = datetime.now()

        # new_filename = current_time.isoformat().replace(':','_').replace('.','_')+'.jpg'

        # # 새로운 파일명으로, s3에 파일 업로드
        # try:
        #     s3 = boto3.client('s3', #s3에 올릴거다
        #              aws_access_key_id =  Config.AWS_ACCESS_KEY_ID,
        #              aws_secret_access_key = Config.AWS_SECRET_ACCESS_KEY) # 올릴려면 권한이 필요하다 
        # # 그냥 액세스키를 넣어주면 짜면 회사에서 짤린다! 보안때문에!
        #     s3.upload_fileobj(file,
        #                     Config.S3_BUCKET,
        #                     new_filename,
        #                     ExtraArgs = {'ACL':'public-read', 'ContentType':'image/jpeg'}) # 퍼블릭으로해야 웹페이지에서도 볼 수 있다? / 우리는 사진을 jpeg 타입으로 할거에요
        # except Exception as e:
        #     print(str(e))
        #     return{'result':'fail','error':str(e)},500
        
        # # 3. 위에서 저장한 사진의 URL 주소와 내용을 DB에 저장해야 한다!
        # # URL 주소는 = 버킷명.S3주소/우리가 만든 파일명
        # file_url = Config.S3_BASE_URL+ new_filename # 이미지 url 부분은 회사마다 다르다
       
        #2. 데이터베이스에 update한다.
        try :
            connection = get_connection()
            query = '''update dailyNote
                    set title = %s, contents = %s, dailyTemperCheck = %s, dailyMealCheck = %s, dailyNapCheck = %s, dailyPooCheck = %s
                    where id = %s;''' 
            record = (data['title'],data['contents'],data['dailyTemperCheck'],data['dailyMealCheck'],data['dailyNapCheck'],data['dailyPooCheck'],id) 
            cursor= connection.cursor()
            cursor.execute(query,record)
            connection.commit()

            cursor.close()
            connection.close()

        except Error as e:
            print(e)
            return {'result': 'fail','error': str(e)},500
        
        return {'result': 'success'} 

# 알림장 목록(원아별)   
class DailyNoteListResource(Resource):
    @jwt_required()
    def get(self, childId):

        try:
            connection = get_connection()
            query = '''select id,createdAt,title,contents,dailyTemperCheck,dailyMealCheck,dailyNapCheck,dailyPooCheck
                    from dailyNote
                    where childId = %s;'''
            record = (childId, )
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
            result_list[i]['createdAt']= row['createdAt'].isoformat()
            i = i + 1

        return {'result':'success', 'items':result_list}
# 학부모의 원아 알림장 목록   
class DailyNoteChildListResource(Resource):
    @jwt_required()
    def get(self):

        parentsId = get_jwt_identity()

        try:
            connection = get_connection()
            query = '''select childId from parents
                    where id = %s'''
            record = (parentsId, )
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)
            result_one = cursor.fetchone()
            print(result_one)
            childId = result_one['childId']

            query1 = '''select id,createdAt,title,contents,dailyTemperCheck,dailyMealCheck,dailyNapCheck,dailyPooCheck
                    from dailyNote
                    where childId = %s;'''
            record1 = (childId, )
            cursor1 = connection.cursor(dictionary=True)
            cursor1.execute(query1, record1)
            result_list = cursor1.fetchall()
            cursor.close()
            cursor1.close()
            connection.close()

        except Error as e:
            print(e)
            return{'result':'fail', 'error':str(e)}, 400
        
        i = 0
        for row in result_list :
            result_list[i]['createdAt']= row['createdAt'].isoformat()
            i = i + 1

        return {'result':'success', 'items':result_list}


# 알림장 상세보기    
class DailyNoteViewResource(Resource):
    @jwt_required()
    def get(self, id):

        try:
            connection = get_connection()
            query = '''select createdAt,title,contents,dailyTemperCheck,dailyMealCheck,dailyNapCheck,dailyPooCheck from dailyNote
                    where id = %s;'''
            record = (id, )
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
            result_list[i]['createdAt']= row['createdAt'].isoformat()
            i = i + 1

        return {'result':'success', 'items':result_list}


