from flask_restful import Resource
from flask import request
import mysql.connector
from mysql.connector import Error
from mysql_connection import get_connection
from utils import check_password, hash_password
from email_validator import validate_email,EmailNotValidError 
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity, jwt_required



class TeacherDeleteResource(Resource):

    @jwt_required()
    def delete(self, id):

        try : 
            connection = get_connection()
            query = '''delete from teacher
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

        return {'result' : '회원정보가 삭제되었습니다'}


class TeacherEditResource(Resource):

    @jwt_required()
    def put(self, id):

        data = request.get_json()
        hashed_password = hash_password(data['password'])

        try :
            # 1) 데이터베이스 연결
            connection = get_connection()

            query = '''update teacher
                        set classId = %s, nurseryId = %s, 
                        teacherName = %s, teacherUserId = %s, password = %s, email = %s, phone = %s 
                        where id = %s;'''
            
            record = (data['classId'], data['nurseryId'], data['teacherName'],data['teacherUserId'],hashed_password,data['email'],data['phone'], id)
            
            cursor = connection.cursor()
            cursor.execute(query, record)
            connection.commit()
            cursor.close()
            connection.close()

        except Error as e :  
            print(e)
            return { 'result' : 'fail', 'error' : str(e) }, 500


        return {'result' :'success'}


class TeacherViewResource(Resource) :

    @jwt_required()
    def get(self, id):

        try:
            connection = get_connection()
            query = '''select * from teacher 
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
        
        print(result_list)

        return {'result':'success', 'items':result_list}


jwt_blocklist = set()
class TeacherRegisterResource(Resource) :

    def post(self):
        # 1. 클라이언트로부터 데이터를 받는다.
        data = request.get_json()

        #2. 이메일 주소형식이 올바른지 확인한다.
        try:
            validate_email(data['email'])
        # 에러가 안나면 무사통과 아니면 에러 발생
        except EmailNotValidError as e:
            print(e) # 디버깅 할 때 필요하다
            return {'result':'fail','error':str(e)},400

        #3. 비밀번호 길이가 유용한지 체크한다.
        # 만약, 비번이 4자리 이상, 12자리 이하라고 한다면,
        if len(data['password'])< 4 or len(data['password']) > 12:
            return{'result':'fail','error':'비번 길이 에러'},400
        
        # 4. 비밀번호를 암호화 한다.
        hashed_password = hash_password(data['password'])
        print(hashed_password)

        #5. DB에 이미 회원 정보가 있는지 확인한다.
        try:
            connection = get_connection()
            query = '''select * from teacher
                    where teacherUserId = %s;'''
            record = (data['teacherUserId'],)
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query,record)

            result_list = cursor.fetchall()

            print(result_list)

            if len(result_list) == 1:
                return {'result':'fail','error':'이미 회원가입 한 사람'},400
            # 회원이 아니므로 회원가입 코드 작성
            # DB에 저장
            query =  '''insert into teacher
                    (teacherName,teacherUserId,password,phone,email)
                    values
                    (%s,%s,%s,%s,%s);'''
            record = (data['teacherName'],data['teacherUserId'],hashed_password,data['phone'],data['email'])
            cursor = connection.cursor()
            cursor.execute(query,record)

            connection.commit()

            user_id = cursor.lastrowid

            cursor.close()
            connection.close()

        except Error as e:
            print(e)
            return {'result':'fail','error': str(e)}, 500
        access_token = create_access_token(user_id)
        return {'result' :'success','access_token': access_token}
