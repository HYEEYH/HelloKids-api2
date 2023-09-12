from flask_restful import Resource
from flask import request
import mysql.connector
from mysql.connector import Error
from mysql_connection import get_connection
from utils import check_password, hash_password
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity, jwt_required



class LoginResource(Resource):
    def post(self):

        data = request.get_json()

        # 이메일 주소로 DB select 쿼리문을 수정
        try:
            connection = get_connection()
            query = '''SELECT id, teacherName, password, email
                    FROM teacher
                    where email = %s
                    UNION
                    SELECT id, parentsName, password, email 
                    FROM parents
                    where email = %s;'''
            record = (data['email'], data['email'])

            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)

            result_list = cursor.fetchall()
            
            cursor.close()
            connection.close()

        except Error as e:
            print(e)
            return {'result':'fail', 'error':str(e)}, 500
        
        if len(result_list) == 0:
            return {'result':'fail','error':'회원가입이 되어있지 않습니다'}, 400
        
        print(result_list)

        # 비밀번호 일치여부 확인
        check = check_password(data['password'], result_list[0]['password'])
        if check == False:
            return {'result':'fail', 'error':'비밀번호가 틀렸으니 다시 확인하세요'}
        
        # 클라이언트에게 데이터를 보내준다
        access_token = create_access_token(result_list[0]['id'])

        return {'result':'success', 
                'access_token' : access_token,
                'message':'로그인을 환영합니다' }
    
# 로그아웃
jwt_blocklist = set()

class LogoutResource(Resource):
    
    @jwt_required()
    def delete(self):

        jti = get_jwt()['jti']
        print(jti)
        jwt_blocklist.add(jti)

        return {'result': '로그아웃 되었습니다'}
    


class UserCheckResource(Resource):

    @jwt_required()
    def get(self, email):
       
        try : 
            connection = get_connection()
            query = '''select id from teacher where email = %s;'''
            record = (email, )
            cursor = connection.cursor()
            cursor.execute(query, record)
            result_list = cursor.fetchone()
            connection.commit()

            cursor.close()
            connection.close()

        except Error as e:
            print(e)
            return {'result':'fail', 'error':str(e)}

        return {'isTeacher' : result_list}
