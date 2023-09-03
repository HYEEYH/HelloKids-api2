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
        return {'result' : '식단이 삭제되었습니다'}

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

            if 'mealPhotoUrl' not in request.files or 'mealPhotoUrl' == None:
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
    def put(self, id):

        file = request.files['mealPhotoUrl']
        print(file)
        # files = os.path.abspath(file.filename) 

        data = json.loads(request.form['mealJson'])

        teacherId = get_jwt_identity()
        print(data)
       
        try:
            # 3-1. 데이터베이스를 연결한다.
            connection = get_connection()

            if 'mealPhotoUrl' not in request.files or 'mealPhotoUrl' == None:
                try:
                    connection = get_connection()

                    query = '''update mealMenu set mealDate = %s, mealContent = %s, mealType = %s where id = %s;'''
                    record = (data['mealDate'], data['mealContent'], data['mealType'],id)
                    print(record)

                    cursor = connection.cursor(prepared=True)
                    cursor.execute(query,record)
                    connection.commit()

                    cursor.close()
                    connection.close()

                except Error as e :
                    print(e)
                    return {'result':'fail','error': str(e)}, 500

            else:
                query = '''SELECT classId, nurseryId, nurseryName FROM nursery n left join teacher t on n.id = t.nurseryId where t.id = %s;'''
                record = (teacherId, )
                cursor = connection.cursor()
                cursor.execute(query,record)
                teacher_result_list = cursor.fetchall()
    
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

                    query = '''update mealMenu set mealDate = %s, mealPhotoUrl = %s, mealContent = %s, mealType = %s where id = %s;'''
                    record = (data['mealDate'], file_url, data['mealContent'], data['mealType'],id)
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


# 메뉴 전체 목록
class MenuListResource(Resource):
    @jwt_required()
    def get(self, nurseryId):

        try:
            connection = get_connection()
           
            query = '''select nurseryId, mealPhotoUrl, mealContent, mealType from mealMenu where nurseryId = %s;'''
            record = (nurseryId, )
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)
            result_list = cursor.fetchall()
            cursor.close()
            connection.close()

        except Error as e:
            print(e)
            return{'result':'fail', 'error':str(e)}, 400

        return {'result':'success', 'items':result_list}

# 하루 메뉴 목록
class MenuListDayResource(Resource):
    @jwt_required()
    def get(self, nurseryId, mealDate):

        try:
            connection = get_connection()
           
            query = '''select nurseryId, mealPhotoUrl, mealContent, mealType from mealMenu where nurseryId = %s and mealDate = %s;'''
            record = (nurseryId, mealDate)
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)
            result_list = cursor.fetchall()
            cursor.close()
            connection.close()

        except Error as e:
            print(e)
            return{'result':'fail', 'error':str(e)}, 400

        return {'result':'success', 'count': len(result_list), 'items':result_list}

# 메뉴 상세보기    
class MenuViewResource(Resource):
    @jwt_required()
    def get(self, id):

        try:
            connection = get_connection()
            query = '''select nurseryId, mealPhotoUrl, mealContent, mealType from mealMenu 
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

        return {'result':'success',  'items':result_list}