


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

# 의문점 ) 주소에 int를 두번이나 써야 하는데 이거 괜찮은걸까? --> 수정해야함.

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








### 사진첩 글 아이디 생성 : 로컬 테스트 완료
# - 선생님 아이디도 추가하도록 수정

class PhotoAlbumAddIdResource(Resource):

    @jwt_required()
    def post(self):

        # 데이터 받아오기
        # - 유저정보
        teacherId = get_jwt_identity()
        # - 바디
        data = request.get_json()

        #
        try :
            connection = get_connection()

            # 선생님이 속한 원과 반 아이디 가져오기
            query1 = '''SELECT classId, nurseryId, nurseryName 
                        FROM nursery n 
                        left join teacher t on n.id = t.nurseryId 
                        where t.id = %s;'''
        
            record1 = (teacherId, )

            cursor = connection.cursor()
            cursor.execute(query1, record1)

            teacher_result_list = cursor.fetchone()
            print("teacher_result_list : ", teacher_result_list)

            getTeacherId = teacher_result_list[0]

            # 글 아이디 생성하기
                # insert into totalAlbum
                # (totalAlbumNum)
                # values
                # (0);
            query2 = '''insert into totalAlbum
                        (teacherId, totalAlbumNum)
                        values
                        (%s, %s);'''
            
            record2 = ( getTeacherId, data['totalAlbumNum'] )
            
            cursor = connection.cursor()
            cursor.execute(query2, record2)

            connection.commit()

            cursor.close()
            connection.close()

        except Error as e:
            print('오류1', e)
            return {'result':'fail', 'error':str(e) }, 500

        return { 'result': 'success'}







### 사진첩 사진 추가

# 의문점 ) 주소에 int를 두번이나 써야 하는데 이거 괜찮은걸까? --> int 삭제함.
# 사진 여러장 받아서 AWS 올리고 그 내용 다운받아서 어레이로 데이터베이스에 저장

class PhotoAlbumAddResource(Resource):

    @jwt_required()
    def post(self):  
    

        # 1. 데이터 받아오기(유저 정보)
        teacherId = get_jwt_identity()

        
        # 유저가 입력한 데이터
        date = request.form['date'].replace('T', ' ')[0:10]
        print("date : ", date )
        title = request.form['title']
        print("title : ", title )
        contents = request.form['contents']
        print("contents : ", contents )
        classId = request.form['classId']
        print("classId : ", classId )
        photoUrl = request.files['photoUrl']
        print("photoUrl : ", photoUrl )


        try : 

            #teacher_result_list = []

            # 데이터 가져오기
            connection = get_connection()

            query = '''SELECT classId, nurseryId, nurseryName 
                        FROM nursery n 
                        left join teacher t on n.id = t.nurseryId 
                        where t.id = %s;'''
            
            record = (teacherId, )
            cursor = connection.cursor()
            cursor.execute(query, record)

            # - 선생님이 속한 어린이집 아이디와 클래스 아이디 가져오기
            teacher_result_list = cursor.fetchall()
            print("teacher_result_list : ", teacher_result_list)

            # - 선생님이 속한 반 아이디 가져오기
            classIdList = teacher_result_list[0][0]
            print("classIdList : ", classIdList)


            # 사진 잘 올렸니?
            if 'photoUrl' not in request.files or 'contents' not in request.form :
                return { 'result' : 'fail', 'error' : '필수항목을 확인하세요'}, 400
            
            else :

                # 데이터베이스에서 어린이집 아이디와 반 아이디를 가져오기(파일 정리할때 이름으로 정리되어 들어가도록)
                teacher_result_list_str = str(teacher_result_list[0][1]) + '_' + teacher_result_list[0][2]
                print("어린이집아이디+반아이디 : " ,teacher_result_list_str)

                # 이름 붙일때 유니크하게 붙이기 위해 시간 가져옴
                current_time = datetime.datetime.now()
                print("current_time : ", current_time)

                # 파일 이름 붙이기
                new_filename = teacher_result_list_str + '/photo_album/' + classId + '/' + title + '/' + current_time.isoformat().replace(':','_').replace('.','_')+'.jpg' # 사람이보는형식
                print("파일 이름 : ", new_filename)

                try: 
                    # 사진부터 S3에 저장
                    s3 = boto3.client('s3',
                            aws_access_key_id = Config.AWS_ACCESS_KEY_ID,
                            aws_secret_access_key = Config.AWS_SECRET_ACCESS_KEY) 
                    s3.upload_fileobj(photoUrl,
                                    Config.S3_BUCKET,
                                    new_filename,
                                    ExtraArgs = {'ACL':'public-read', 'ContentType':'image/jpeg'}) 
                    
                    file_url = Config.S3_BASE_URL + new_filename 

                except Exception as e:
                    print(e)
                    return {'result1':'fail','error1': str(e)}, 500 


                # # 반복문을 통해 여러 파일을 s3에 저장 ----> 이런식으로 만들어야 함.
                # for i in range (1, len(request.FILES)+1):
                #     file = request.FILES[f'filename{i}']



                # s3에 올린 사진 파일 데이터베이스에 저장하기
            try:
                connection = get_connection()


                # - 원 아이디를 가져오기 위한 쿼리
                query1 = '''SELECT nurseryId, nurseryName, classId
                            FROM nursery n 
                            left join teacher t on n.id = t.nurseryId 
                            where t.id = %s;'''
            
                record1 = (teacherId, )
                cursor1 = connection.cursor()
                cursor1.execute(query1, record1)

                nursery_id_result = cursor1.fetchall()
                print("nursery_id_result : ", nursery_id_result)

                nursery_id_result_str = str(nursery_id_result[0][0])
                print("nursery_id_result_str : ", nursery_id_result_str)
            
        

                # - 글 아이디를 가져오기 위한 쿼리
                query4 = '''SELECT *
                            FROM totalAlbum
                            where teacherId = %s
                            order by createdAt desc;'''
        
                record4 = (teacherId, )

                cursor4 = connection.cursor()
                cursor4.execute(query4, record4)

                totalAlbumId_result = cursor4.fetchall()
                print("totalAlbumId_result : ", totalAlbumId_result)

                totalAlbumId = str(totalAlbumId_result[0][0])
                print("totalAlbumId : ", totalAlbumId)


                # - 원 아이디를 포함해서 데이터베이스에 입력하기 위한 쿼리
                # - 글 아이디 포함하기 추가
                query2 = '''insert into totalPhoto
                        (nurseryId, classId, teacherId, totalAlbumId, date, title, contents, photoUrl)
                        values
                        (%s,%s,%s,%s,%s,%s,%s, %s);'''

                record2 = ( nursery_id_result_str, classId, teacherId, totalAlbumId, date, title, contents, file_url)
                print("record2 : ", record2)

                cursor = connection.cursor(prepared=True)
                cursor.execute(query2, record2)

                connection.commit()

                cursor.close()
                connection.close()

            except Error as e :
                print(e)
                return {'result2':'fail','error2': str(e)}, 500


        except Exception as e:
            print(e)
            return {'result3':'fail','error3': str(e)}, 500  



        return { 'result' : 'success' }   

        # return { 'result4' : 'success',
        #         'nurseryId' : nursery_id_result_str,
        #         'classId' : classId,
        #         'teacherId' : teacherId,
        #         'date': date,
        #         'title' : title,
        #         'contents' : contents,
        #         'classId' : classId,
        #         'photoUrl' : file_url }