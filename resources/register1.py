

# 회원가입 - 학부모

# 라이브러리 ------------------------------------------------------------------
from flask_restful import Resource
from flask import request
import mysql.connector
from mysql.connector import Error
from mysql_connection import get_connection
from utils import check_password, hash_password
from email_validator import validate_email,EmailNotValidError 
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity, jwt_required
# ----------------------------------------------------------------------------



class ParentDeleteResource(Resource):

    @jwt_required()
    def delete(self, id):

        try : 
            connection = get_connection()
            query = '''delete from parents
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


class ParentEditResource(Resource):

    @jwt_required()
    def put(self, id):

        data = request.get_json()
        hashed_password = hash_password(data['password'])

        try :
            # 1) 데이터베이스 연결
            connection = get_connection()

            query = '''update parents
                        set phone = %s, email = %s, 
                        parentsName = %s, userId = %s, password = %s, childNameP = %s, birthP = %s 
                        where id = %s;'''
            
            record = (data['phone'], data['email'], data['parentsName'],data['userId'],hashed_password,data['childNameP'],data['birthP'], id)
            
            cursor = connection.cursor()
            cursor.execute(query, record)
            connection.commit()
            cursor.close()
            connection.close()

        except Error as e :  
            print(e)
            return { 'result' : 'fail', 'error' : str(e) }, 500


        return {'result' :'success'}


class ParentViewResource(Resource) :

    @jwt_required()
    def get(self, id):

        parentsId = get_jwt_identity()

        try:
            connection = get_connection()
            query = '''select * from parents 
                    where id = %s;'''
            record = (parentsId, )
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)
            result_list = cursor.fetchall()
            cursor.close()
            connection.close()

        except Error as e:
            print(e)
            return{'result':'fail', 'error':str(e)}, 400
        
        print(result_list)
        i = 0
        for row in result_list :
            result_list[i]['birthP']= row['birthP'].isoformat()
            i = i + 1


        return {'items':result_list}


# 회원가입 - 학부모 - 학부모 정보 : 완
jwt_blocklist = set()
class ParentRegisterpResource(Resource) :

    def post(self) : 
        # {
            # "phone":"01012345678", 
            # "email":"aaa@naver.com", 
            # "nurseryName":"햇님어린이집", 
            # "parentsName":"가부모", 
            # "userId":"닉네임", 
            # "password":"1234",
            # "childNameP":"김철수",
            # "birthP":"2010-07-14"
        # }

        # 클라이언트가 보낸 데이터를 받는다
        data = request.get_json( )


        # 이메일 주소형식이 올바른지 확인하기.
        try :
            validate_email( data['email'] )

        except EmailNotValidError as e :
            print('이메일 오류', e)
            return { 'result':'fail' , 'error': str(e)} , 400
                    # 400 : http 에러코드, 에러코드는 인터넷에사 내가 찾아야함.
            # 저장한 뒤 서버에 올리고 (flask run)
            # 포스트맨가서 send버튼 눌러서 결과 확인하기


        # 비밀번호 길이가 유효한지 체크하기(비밀번호는 4자리 이상 12자리 이하)
        if len(  data['password']  ) < 4   or   len(  data['password']  ) > 12 :
            return { 'result' : 'fail', 'error' : '비번 길이 에러' }, 400
        

        # 비밀번호 암호화
        hashed_password = hash_password( data['password'] )
        print('비번암호화', hashed_password)


        # 회원정보가 이미 있는지 확인하기
        try : 
            connection = get_connection()
            query = '''select *
                        from parents
                        where email = %s;'''
            record = ( data['email'], )

            cursor = connection.cursor(dictionary= True)
            cursor.execute(query, record)

            result_list = cursor.fetchall()
            print('결과리스트', result_list )

            if len(result_list) == 1 :
                return { 'result' : 'fail', 'error' : '이미 회원가입 되었습니다.' }, 400
            


            # 회원이 아니라면 회원가입 시키기
            query = '''insert into parents
                        (phone, email, nurseryName, parentsName, userId, password,childNameP,birthP)
                        values
                        (%s, %s, %s, %s, %s, %s,%s,%s);'''
            # %s에 들어갈 내용이 record
            record = ( data['phone'], data['email'], 
                      data['parentsName'], data['userId'], hashed_password,data['childNameP'],data['birthP'] )
            
            # DB에 집어넣기 위해 커서 가져옴
            cursor = connection.cursor()
            cursor.execute(query, record)

            # 데이터 집어넣기 - 데이터베이스에 적용해라
            connection.commit()

            ### DB에 데이터를 insert 한 후에 
            ### 그 인서트된 행의 아이디를 가져오는 코드!!!
            ### 꼭 commit 뒤에 해야한다!!
            parentsId = cursor.lastrowid
            

            ### 라이브러리 설치
            # Flask-JWT-Extended
            # pip install Flask-JWT-Extended


            # 닫기
            cursor.close()
            connection.close()
            

        except Error as e :
            print('DB에 학부모-학부모정보넣기', e)
            return { 'result': 'fail', 'error' : str(e) }, 500



        # # 암호화 인증토큰 적용하기
        access_token = create_access_token(parentsId)

        # return { 'result' : '회원가입이 완료 되었습니다', 'access_token' : access_token }
        return { 'result' : '정보 저장 성공', 'access_token' : access_token }







# 회원가입 - 학부모 - 원아정보 : 완 --->회원가입할 시 원아정보까지 한꺼번에 넣자고 했기때문에 ParentsRegisterpResource에 원아정보 넣었다
# class ParentsRegistercResource(Resource) :

#     def post(self, parentsId) : 

#         # 클라이언트가 보낸 데이터를 받는다
#         data = request.get_json( )

#         # 원아 정보를 넣는다
#         try : 
#             connection = get_connection()
                    
#             query = '''update parents
#                         set childNameP = %s, birthP= %s
#                         where parentsId = %s;'''
#             # %s에 들어갈 내용이 record
#             record = ( data['childNameP'], data['birthP'], parentsId)
            
#             # DB에 집어넣기 위해 커서 가져옴
#             cursor = connection.cursor()
#             cursor.execute(query, record)

#             # 데이터 집어넣기 - 데이터베이스에 적용해라
#             connection.commit()

#             ### DB에 데이터를 insert 한 후에 
#             ### 그 인서트된 행의 아이디를 가져오는 코드!!!
#             ### 꼭 commit 뒤에 해야한다!!
#             parentsId = cursor.lastrowid


#             # 닫기
#             cursor.close()
#             connection.close()
            

#         except Error as e :
#             print('DB에 학부모-원아정보 넣기', e)
#             return { 'result': 'fail', 'error' : str(e) }, 500
        

        
        
#         # 회원가입 전체 완료
#         # 암호화 인증토큰 적용하기
#         access_token = create_access_token(parentsId)#

#         return { 'result' : '회원가입이 완료 되었습니다', 'access_token' : access_token }
    






# 회원가입 - 학부모 - 어린이집 정보 : 완 ===>> 알지 말지 일단 보류중. 
# class ParentsRegisternResource(Resource) :

#     def post(self, parentsId) : 

#         # 클라이언트가 보낸 데이터 받기
#         data = request.get_json( )

#         # 어린이집과 반 정보를 넣는다
#         try : 
#             connection = get_connection()
                    
#             query = '''update parents
#                         set nurseryNameP = %s, classNameP= %s
#                         where parentsId = %s;'''
#             # %s에 들어갈 내용이 record
#             record = ( data['nurseryNameP'], data['classNameP'], parentsId)
            
#             # DB에 집어넣기 위해 커서 가져옴
#             cursor = connection.cursor()
#             cursor.execute(query, record)

#             # 데이터 집어넣기 - 데이터베이스에 적용해라
#             connection.commit()

#             ### DB에 데이터를 insert 한 후에 
#             ### 그 인서트된 행의 아이디를 가져오는 코드!!!
#             ### 꼭 commit 뒤에 해야한다!!
#             parentsId = cursor.lastrowid


#             # 닫기
#             cursor.close()
#             connection.close()
            

#         except Error as e :
#             print('DB에 학부모-어린이집정보 넣기', e)
#             return { 'result': 'fail', 'error' : str(e) }, 500



#         return { 'result' : '어린이집정보 등록에 성공하셨습니다' }
