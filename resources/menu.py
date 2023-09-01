import json
from flask_restful import Resource
from flask import request
import mysql.connector
from mysql.connector import Error
from mysql_connection import get_connection
from utils import check_password, hash_password
from email_validator import validate_email,EmailNotValidError 
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity, jwt_required
from datetime import datetime
from config import Config
import boto3




class MenuDeleteResource(Resource):

    @jwt_required()
    def delete(self, id):

        print(id)

        # 1. 헤더에 담긴 JWT 토큰을 받아온다.
        # teacherId = get_jwt_identity()
        # print('토큰확인', teacherId)

        # 2. DB에서 삭제한다
        try : 
            connection = get_connection()
            query = '''delete from mealMenu
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


class MenuAddResource(Resource) :

    @jwt_required()
    def post(self):

        file = request.files['mealPhotoUrl']
        print(file)
        # files = os.path.abspath(file.filename) 

        data = json.loads(request.form['mealJson'])

        teacherId = get_jwt_identity()
        print(data)

       
        try:
            # 3-1. 데이터베이스를 연결한다.
            connection = get_connection()
            query = '''SELECT classId, nurseryId, nurseryName FROM nursery n left join teacher t on n.id = t.nurseryId where t.id = %s;'''
            record = (teacherId, )
            cursor = connection.cursor()
            cursor.execute(query,record)
            teacher_result_list = cursor.fetchall()

            if 'mealPhotoUrl' not in request.files:
                file_url = 'https://hellokids.s3.ap-northeast-2.amazonaws.com/img_setting/meal_image.png'
            
            else : 
                teacher_result_list_str = str(teacher_result_list[0][1]) + '_' + teacher_result_list[0][2]
                current_time = datetime.now()
                new_filename = teacher_result_list_str + '/menu/' + current_time.isoformat().replace(':','_').replace('.','_')+'.jpg'
                print(new_filename)
                try:
                    s3 = boto3.client('s3',
                            aws_access_key_id = Config.AWS_ACCESS_KEY_ID,
                            aws_secret_access_key = Config.AWS_SECRET_ACCESS_KEY) 
                    s3.upload_fileobj(file,
                                    Config.S3_BUCKET,
                                    new_filename,
                                    ExtraArgs = {'ACL':'public-read', 'ContentType':'image/jpeg'}) 
                    
                    file_url = Config.S3_BASE_URL + new_filename 

                except Exception as e:
                    print(e)
                    return {'result':'fail','error': str(e)}, 500                                  

            try:
                connection = get_connection()

                query = '''insert into mealMenu
                        (nurseryId,classId,mealDate,mealPhotoUrl,mealContent,mealType)
                        values
                        (%s,%s,%s,%s,%s,%s);'''

                record = (teacher_result_list[0][1],teacher_result_list[0][0], data['mealDate'], file_url, data['mealContent'], data['mealType'])
                print(record)
                # {
                #     "mealDate":"2023-08-30",
                #     "mealContent":"사과와 어묵",
                #     "mealType":"오전 간식",
                #     "mealPhotoUrl":""
                # }
                cursor = connection.cursor(prepared=True)
                cursor.execute(query,record)
                connection.commit()

                cursor.close()
                connection.close()

            except Error as e :
                print(e)
                return {'result':'fail','error': str(e)}, 500
            
        except Error as e :
            print(e)
            return {'result':'fail','error': str(e)}, 500
        return{'result': 'success'} 

class MenuEditResource(Resource):

    @jwt_required()
    def put(self,noteId):
          # 사진이 필수인 경우의 코드
        if 'photoUrl' not in request.files or 'title' not in request.form or 'contents' not in request.form or 'dailyTemperCheck' not in request.form or 'dailyMealCheck' not in request.form or 'dailyNapCheck' not in request.form or 'dailyPooCheck' not in request.form: # 두 줄로 하고싶으면 \ (역슬래시) 이용해라
            return{'result':'fail','error':'필수항목 확인'},400
        # 유저가 올린 파일을 변수로 만든다
        file = request.files['photoUrl']
        title = request.form['title']
        contents = request.form['contents']
        dailyTemperCheck = request.form['dailyTemperCheck']
        dailyMealCheck = request.form['dailyMealCheck']
        dailyNapCheck = request.form['dailyNapCheck']
        dailyPooCheck = request.form['dailyPooCheck']

        # 2. 사진부터 s3에 저장
        # 파일명을 유니크하게 만들어준다
        current_time = datetime.now()

        new_filename = current_time.isoformat().replace(':','_').replace('.','_')+'.jpg'

        # 새로운 파일명으로, s3에 파일 업로드
        try:
            s3 = boto3.client('s3', #s3에 올릴거다
                     aws_access_key_id =  Config.AWS_ACCESS_KEY_ID,
                     aws_secret_access_key = Config.AWS_SECRET_ACCESS_KEY) # 올릴려면 권한이 필요하다 
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
       
        #2. 데이터베이스에 update한다.
        try :
            connection = get_connection()
            query = '''update mealMenu
                    set classId = %s, mealDate = %s, mealPhotoUrl = %s, mealContent = %s, mealType = %s
                    where id = %s;''' 
            record = (title,contents,file_url,dailyTemperCheck,dailyMealCheck,dailyNapCheck,dailyPooCheck,noteId) 
            cursor= connection.cursor()
            cursor.execute(query,record)
            connection.commit()

            cursor.close()
            connection.close()

        except Error as e:
            print(e)
            return {'result': 'fail','error': str(e)},500
        
        return {'result': 'success'} 

# 메뉴 목록
class MenuListResource(Resource):
    @jwt_required()
    def get(self, childId):

        try:
            connection = get_connection()
            query = '''select createdAt,title,contents,photoUrl
                    from mealMenu
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

# 메뉴 상세보기    
class MenuViewResource(Resource):
    @jwt_required()
    def get(self, id):

        try:
            connection = get_connection()
            query = '''select * from mealMenu
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
            result_list[i]['updatedAt']= row['updatedAt'].isoformat()
            i = i + 1

        return {'result':'success', 'items':result_list}


