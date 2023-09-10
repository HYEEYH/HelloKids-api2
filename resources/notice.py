

# 공지사항

# 라이브러리 ------------------------------------------------------------------
from flask_restful import Resource
from flask import request
import mysql.connector
from mysql.connector import Error
from config import Config
from mysql_connection import get_connection
from utils import check_password, hash_password
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity, jwt_required
import boto3
from datetime import datetime
import os
import passlib

# ----------------------------------------------------------------------------



### 공지사항 - 원별목록
class NoticeListResource(Resource) :

    @jwt_required()
    def get(self, nurseryId):

        try:
            connection = get_connection()
            query = '''SELECT * FROM teacher t
                    left join notice n
                    on t.id = n.teacherId
                    where t.nurseryId = %s;'''
            record = (nurseryId, )
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
            result_list[i]['createdAt']= row['createdAt'].isoformat()
            result_list[i]['updatedAt']= row['updatedAt'].isoformat()
            i = i + 1

        return {'result':'success', 'items':result_list}

### 공지사항 - 상세보기
class NoticeViewResource(Resource) :

    @jwt_required()
    def get(self, id):

        try:
            connection = get_connection()
            query = '''select * from notice 
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
        i = 0
        for row in result_list :
            result_list[i]['createdAt']= row['createdAt'].isoformat()
            result_list[i]['updatedAt']= row['updatedAt'].isoformat()
            i = i + 1

        return {'result':'success', 'item count':len(result_list), 'items':result_list}


### 공지사항 - 임시저장
class NoticeAddResource(Resource):

    @jwt_required()
    def post(self):    

        if 'noticePhotoUrl' not in request.files :
            return {  'result' : 'fail', 'error' : '파일없음'  }, 400              

        teacherId = get_jwt_identity()
        notice_date = request.form['noticeDate'].replace('T', ' ')[0:10]
        file = request.files['noticePhotoUrl']
        notice_contents = request.form['noticeContents']
        notice_title = request.form['noticeTitle']
        notice_ispublish = request.form['isPublish']
               
        try:
            # 3-1. 데이터베이스를 연결한다.
            connection = get_connection()
            query = '''SELECT classId, nurseryId, nurseryName FROM nursery n left join teacher t on n.id = t.nurseryId where t.id = %s;'''
            record = (teacherId, )
            cursor = connection.cursor()
            cursor.execute(query,record)
            teacher_result_list = cursor.fetchall()
            
            teacher_result_list_str = str(teacher_result_list[0][1]) + '_' + teacher_result_list[0][2]
            current_time = datetime.now()
            new_filename = teacher_result_list_str + '/notice/' + current_time.isoformat().replace(':','_').replace('.','_')+'.jpg'
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
                query = '''insert into notice
                                (nurseryId, teacherId, noticeDate, noticeTitle, noticeContent, noticePhotoUrl, isPublish)
                                values
                                (%s, %s, %s, %s, %s, %s, %s);'''
                    
                record = (teacher_result_list[0][1], teacherId, notice_date, notice_contents, notice_title, file_url, notice_ispublish)
                print(record)

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

        # # 데이터베이스 연결
        # try :
        #     connection = get_connection()
        #     query = '''SELECT classId, nurseryId, nurseryName FROM nursery n left join teacher t on n.id = t.nurseryId where t.id = %s;'''
        #     record = (teacherId, )
        #     cursor = connection.cursor()
        #     cursor.execute(query,record)
        #     teacher_result_list = cursor.fetchall()
        #     urlNurseryId = str(teacher_result_list[0][1])         
        #     urlNurseryName = teacher_result_list[0][2]
        #     print(teacher_result_list[0][0], teacher_result_list[0][1], teacher_result_list[0][2])
        #     print(data["noticePhotoUrl"])

            

        #     noticePhotoList = data["noticePhotoUrl"]
        #     for noticePhoto in noticePhotoList: 
        #         print(noticePhoto)
        #         noticePhotoPath = str(noticePhoto).replace('"', '').replace("'","").replace(",", "")

        #         noticePhotoImage = noticePhotoPath

        #         # print("noticePhotoPath os.path.isdir(noticePhotoPath) 해당 경로의 파일 있는지 확인 : ") 
        #         # print(os.path.isdir(noticePhotoPath))
        #         # print("noticePhotoPath os.path.exists(noticePhotoPath) 해당 경로의 파일 있는지 확인 : ") 
        #         # print(os.path.exists(noticePhotoPath))
        #         # print("noticePhotoPath Path(noticePhotoPath).resolve() 해당 경로의 파일 있는지 확인 : ") 
        #         # print(Path(noticePhotoPath).resolve())
        #         # noticePhotoPathData = open(noticePhotoPath, 'rb')
        #         # print("noticePhotoPathData = open(noticePhotoPath, 'rb') 해당 경로의 파일 객체 불러오기 : ") 
        #         # print(noticePhotoPathData )
                


        #         # 사진 파일명 변경
        #         current_time = datetime.now()
        #         current_time.isoformat()

        #         new_filename = urlNurseryId +'_'+ urlNurseryName + '/notice/' + current_time.isoformat().replace(':', '').replace('.', '')+'.jpg'
        #         print('new_filename', new_filename)

        #         # 새로운 파일명으로 s3에 파일 업로드
        #         try :
        #             # 권한 설정
        #             s3 = boto3.client('s3', aws_access_key_id = Config.AWS_ACCESS_KEY_ID, aws_secret_access_key = Config.AWS_SECRET_ACCESS_KEY)
        #             # 파일 업로드하기
        #             s3.upload_file(noticePhotoImage, Config.S3_BUCKET, new_filename, ExtraArgs = {'ACL' : 'public-read', 'ContentType':'image/jpeg'} )  
                    
        #         except Exception as e :
        #             print('오류', str(e))
        #             return { 'result' : 'fail_s3', 'error' : str(e) }, 500
                
        #         noticePhotoUrl = Config.S3_BASE_URL + new_filename
        #         noticePhotoUrlList.append(str(noticePhotoUrl))
        #         print(noticePhotoUrlList)

        #     query = '''insert into notice
        #                     (nurseryId, teacherId, noticeDate, noticeTitle, noticeContent, noticePhotoUrl, isPublish)
        #                     values
        #                     (%s, %s, %s, %s, %s, %s, %s);'''
                
        #     record = (teacher_result_list[0][1], teacherId, data["noticeDate"], data["noticeTitle"], data["noticeContent"], str(noticePhotoUrlList), data["isPublish"])
            
        #     cursor = connection.cursor()
        #     cursor.execute(query, record)
        #     connection.commit()

        #     cursor.close()
        #     connection.close()

        # except Error as e : 
        #     print(e)
        #     return { 'result' : 'fail', 'error' : str(e) }, 500
        #     # 500 은 http 상태코드 - 내가 찾아서 넣은 에러 코드

        # return {'result' : 'success'}
    



### 공지사항 - 수정
class NoticeEditResource(Resource):

    @jwt_required()
    def put(self, noticeId):

        # 1. 헤더에 담긴 JWT 토큰을 받아온다.
        teacherId = get_jwt_identity()

        # 사진이 필수인 경우의 코드
        if 'noticePhotoUrl' not in request.files :  # 이건 이상한경우니까
            return {  'result' : 'fail', 'error' : '파일없음'  }, 400

        notice_date = request.form['noticeDate'].replace('T', ' ')[0:10]
        file = request.files['noticePhotoUrl']
        notice_contents = request.form['noticeContents']
        notice_title = request.form['noticeTitle']
        notice_ispublish = request.form['isPublish']


        try:
            # 3-1. 데이터베이스를 연결한다.
            connection = get_connection()
            query = '''SELECT classId, nurseryId, nurseryName FROM nursery n left join teacher t on n.id = t.nurseryId where t.id = %s;'''
            record = (teacherId, )
            cursor = connection.cursor()
            cursor.execute(query,record)
            teacher_result_list = cursor.fetchall()
            
            teacher_result_list_str = str(teacher_result_list[0][1]) + '_' + teacher_result_list[0][2]
            current_time = datetime.now()
            new_filename = teacher_result_list_str + '/notice/' + current_time.isoformat().replace(':','_').replace('.','_')+'.jpg'
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
                query = '''update notice 
                            set teacherId, noticeDate = %s, noticeTitle = %s, noticeContent = %s, noticePhotoUrl = %s, isPublish = %s where id = %s;
                                (%s, %s, %s, %s, %s, %s);'''
                    
                record = (teacherId, notice_date, notice_contents, notice_title, file_url, notice_ispublish, noticeId)
                print(record)

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


        

### 공지사항 - 삭제
class NoticeDeleteResource(Resource):
    @jwt_required()
    def delete(self, noticeId):

        print(noticeId)

        # 1. 헤더에 담긴 JWT 토큰을 받아온다.
        teacherId = get_jwt_identity()
        print('토큰확인', teacherId)

        # 2. DB에서 삭제한다
        try : 
            connection = get_connection()
            query = '''delete from notice
                        where id = %s;'''
            record = (noticeId, )
            cursor = connection.cursor()
            cursor.execute(query, record)
            connection.commit()

            cursor.close()
            connection.close()

        except Error as e:
            print(e)
            return {'result':'fail', 'error':str(e)}



        ### 3. 결과를 응답한다
        
        return {'result' : '공지사항이 삭제되었습니다'}



# ### 공지사항 - 임시저장 전 클래스선택
# class NoticeClassChoiceResource(Resource):

#     @jwt_required()
#     def post(self):

#         # 1. 클라이언트가 보낸 데이터를 받아온다.
#         data = request.get_json()
#         print('보내온데이터 확인', data)

#         # 1-1. 헤더에 담긴 JWT 토큰을 받아온다.
#         teacherId = get_jwt_identity()
#         print('확인', teacherId)

#         # 데이터베이스 연결
#         try :
#             # 1) 데이터베이스 연결
#             connection = get_connection()

#             query = '''insert into notice
#                         (classId)
#                         values
#                         (%s);'''
            
#             ### 3) 쿼리에 매칭되는 변수처리 - 중요!! 튜플로 처리해준다!
#             # - 유저가 입력하는 내용은 포스트맨에 있음(post 리퀘스트부분)
#             record = ( data['classId'], )
            
#             # 4) 커서를 가져온다.
#             cursor = connection.cursor()

#             # 5) 쿼리문을 커서로 실행한다
#             cursor.execute(query, record)

#             # 6) DB에 반영완료하라는 commit 해줘야 한다
#             connection.commit()

#             # 7) 자원해제
#             cursor.close()
#             connection.close()

#         except Error as e :   # try 안에서 에러나면 이렇게 처리해
#             print(e)
#             return { 'result' : 'fail', 'error' : str(e) }, 500
#             # 500 은 http 상태코드 - 내가 찾아서 넣은 에러 코드

#         ### 3. 에러났다면 -> 에러 났다고 알려주고
#         ###    그렇지 않으면 -> 잘 저장되었다 알려주기
#         return {'result' : '반 선택 완료'}