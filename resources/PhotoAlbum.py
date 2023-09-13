


# 사진첩

# 라이브러리 ------------------------------------------------------------------
from multiprocessing import connection
import os
import re
from flask_restful import Resource
from flask import request
import mysql.connector
from mysql.connector import Error
from config import Config
from mysql_connection import get_connection
from utils import check_password, hash_password, save_uploaded_file2
from email_validator import validate_email,EmailNotValidError 
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity, jwt_required

import boto3
import datetime
# ----------------------------------------------------------------------------



### 사진첩 목록 보기 
# 전체. 글 아이디별로 구분 안하고 최신순으로 다 가져옴
# 의문점 ) 주소에 int를 두번이나 써야 하는데 이거 괜찮은걸까? --> 수정중.
# --> 0907 : 데이터 가져와서 목록 보는걸로 수정 중.
class PhotoAlbumListResource(Resource): 

    @jwt_required()
    def get(self):

        # 유저 정보 가져오기
        teacherId = get_jwt_identity()
        print("* teacherId : ", teacherId)
        
        try:
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

            # - 원 아이디
            nursery_id = teacher_result_list[1]
            print("* nursery_id : ", nursery_id)

            # - 반 아이디
            class_id = teacher_result_list[0]
            print("* class_id : ", class_id)


            ### 사진첩 글 아이디 가져오기
            # 사진첩 글 아이디 가져올 필요 없이 선생님 아이디로 구분 후 글목록 아이디로 그룹바이 하면 됨.
            

            # 일단 사진첩 목록 가져오기
            query = '''select id, nurseryId , classId, teacherId, totalAlbumId, date, title, contents, photoUrl
                    from totalPhoto
                    where nurseryId = %s and classId = %s and teacherId = %s
                    group by totalAlbumId
                    order by createdAt desc;'''
            record = (nursery_id, class_id, teacherId)
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)

            totalPhotoList_result = cursor.fetchall()

            cursor.close()
            connection.close()

        except Error as e:
            print(e)
            return{'result':'fail', 'error':str(e)}, 400
        
        i = 0
        for row in totalPhotoList_result :
            totalPhotoList_result[i]['date']= row['date'].isoformat().replace('T', ' ')[0:10]
            i = i + 1

        return {'result':'success', 'items':totalPhotoList_result}
    






### 사진첩 얼굴인식 폴더 리스트 보기 - 원아별
class PhotoAlbumRekogListResource(Resource):
    @jwt_required()
    def get(self):

        # 유저 정보 가져오기
        teacherId = get_jwt_identity()
        print("* teacherId : ", teacherId)
        
        try:
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

            # - 원 아이디
            nursery_id = teacher_result_list[1]
            print("* nursery_id : ", nursery_id)

            # - 반 아이디
            class_id = teacher_result_list[0]
            print("* class_id : ", class_id)
            

            # 사진첩 목록 가져오기
            query = '''select id, nurseryId, classId, childId, totalAlbumId, date, title, contents, photoUrl 
                        from myAlbum
                        where nurseryId = %s and classId = %s
                        group by totalAlbumId
                        order by createdAt desc;'''
            record = (nursery_id, class_id)
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)

            myAlbumList_result = cursor.fetchall()
            print("* myAlbumList_result : ", myAlbumList_result)

            cursor.close()
            connection.close()

        except Error as e:
            print(e)
            return{'result':'fail', 'error':str(e)}, 400
        
        i = 0
        for row in myAlbumList_result :
            myAlbumList_result[i]['date']= row['date'].isoformat().replace('T', ' ')[0:10]
            i = i + 1

        return {'result':'success', 'items':myAlbumList_result}






### 사진첩 목록보기 - 상세(같은 글 목록 아이디 사진들)
class PhotoAlbumViewResource(Resource):

    @jwt_required()
    def get(self, id):

        # 데이터 받아오기
        # - 유저정보
        teacherId = get_jwt_identity()
        print("teacherId : ", teacherId)

        # id = request.form['id']
        print("* id : ", id )

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
            print("* teacher_result_list : ", teacher_result_list)

            # 원 아이디 
            nursery_id = teacher_result_list[1]
            print("* nursery_id : ", nursery_id)
            # 반 아이디
            class_id = teacher_result_list[0]
            print("* class_id : ", class_id)


            # 해당 글 목록 아이디와 연결된 사진들 전부 가져오기
            # id와 같은 행의 토탈앨범아이디 가져오기
            query2 = '''SELECT id, nurseryId , classId, teacherId, totalAlbumId, date, title, contents, photoUrl
                        FROM totalPhoto
                        where id = %s and nurseryId = %s and classId = %s and teacherId = %s
                        group by totalAlbumId
                        order by createdAt desc;'''
            record2 = ( id, nursery_id, class_id, teacherId )
            
            cursor = connection.cursor()
            cursor.execute(query2, record2)

            totalAlbumId_result = cursor.fetchall()
            print("* totalAlbumId_result : ", totalAlbumId_result)

            # 토탈 앨범 아이디
            totalAlbumId = totalAlbumId_result[0][4]
            print(" * totalAlbumId : ", totalAlbumId)


            # 토탈 앨범 아이디에 해당하는 사진 다 가져오기
            query3 = '''SELECT id, nurseryId , classId, teacherId, totalAlbumId, date, title, contents, photoUrl
                        FROM totalPhoto
                        where totalAlbumId = %s
                        order by createdAt desc;'''
            record3 = ( totalAlbumId, )
            
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query3, record3)

            photoList_result = cursor.fetchall()
            print(" * photoList_result : ", photoList_result)
            
            cursor.close()
            connection.close()

        except Error as e:
            print('오류1', e)
            return {'result':'fail', 'error':str(e) }, 500
        
        i = 0
        for row in photoList_result :
            photoList_result[i]['date']= row['date'].isoformat().replace('T', ' ')[0:10]
            i = i + 1

        return { 'result':'success', 'items': photoList_result }
        
        # totalAlbum_photoCount_list = []
        # i = 0
        # for row in photoCount_result :
        #     totalAlbum_photoCount_list.append(photoCount_result[i]['count'])
        #     i = i + 1

        # return {'result':'success', 'item count':len(photoCount_result), 'items':photoCount_result}






### 사진첩 목록보기 - 상세(얼굴인식 사진들)
class PhotoAlbumRekogViewResource(Resource):

    @jwt_required()
    def get(self, id):

        # 데이터 받아오기
        # - 유저정보
        teacherId = get_jwt_identity()
        print("teacherId : ", teacherId)

        # id = request.form['id'] # myAlbum의 아이디
        print("* id : ", id )

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
            print("* teacher_result_list : ", teacher_result_list)

            # 원 아이디 
            nursery_id = teacher_result_list[1]
            print("* nursery_id : ", nursery_id)
            # 반 아이디
            class_id = teacher_result_list[0]
            print("* class_id : ", class_id)


            # 해당 글 목록 아이디와 연결된 사진들 전부 가져오기
            # id와 같은 행의 토탈앨범아이디 가져오기
            query2 = '''select id, nurseryId, classId, childId, totalAlbumId, date, title, contents, photoUrl 
                        from myAlbum
                        where id = %s and nurseryId = %s and classId = %s
                        group by totalAlbumId
                        order by createdAt desc;'''
            record2 = ( id, nursery_id, class_id)
            
            cursor = connection.cursor()
            cursor.execute(query2, record2)

            totalAlbumId_result = cursor.fetchall()
            print("* totalAlbumId_result : ", totalAlbumId_result)

            # 토탈 앨범 아이디
            totalAlbumId = totalAlbumId_result[0][4]
            print(" * totalAlbumId : ", totalAlbumId)


            # 토탈 앨범 아이디에 해당하는 사진 다 가져오기
            query3 = '''SELECT id, nurseryId , classId, childId, totalAlbumId, date, title, contents, photoUrl
                        FROM myAlbum
                        where totalAlbumId = %s
                        order by createdAt desc;'''
            record3 = ( totalAlbumId, )
            
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query3, record3)

            photoList_result = cursor.fetchall()
            print(" * photoList_result : ", photoList_result)
            
            cursor.close()
            connection.close()

        except Error as e:
            print('오류1', e)
            return {'result':'fail', 'error':str(e) }, 500
        
        i = 0
        for row in photoList_result :
            photoList_result[i]['date']= row['date'].isoformat().replace('T', ' ')[0:10]
            i = i + 1

        return { 'result':'success', 'items': photoList_result }







### 사진첩 글 아이디 생성 : 로컬 테스트 완료
# - 선생님 아이디도 추가하도록 수정
class PhotoAlbumAddIdResource(Resource):

    @jwt_required()
    def post(self):

        # 데이터 받아오기
        # - 유저정보
        teacherId = get_jwt_identity()
        print("teacherId : ", teacherId)
        # - 바디
        data = request.get_json()
        print("data : ", data)

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

            class_id = teacher_result_list[0]
            print("class_id : ", class_id)

            # 글 아이디 생성하기
                # insert into totalAlbum
                # (totalAlbumNum)
                # values
                # (0);
            query2 = '''insert into totalAlbum
                        (teacherId, totalAlbumNum)
                        values
                        (%s, %s);'''
            
            record2 = ( teacherId, data['totalAlbumNum'] )
            
            cursor = connection.cursor()
            cursor.execute(query2, record2)

            connection.commit()

            cursor.close()
            connection.close()

        except Error as e:
            print('오류1', e)
            return {'result':'fail', 'error':str(e) }, 500


        return { 'result': 'success'}








### 1. 사진첩 사진 추가
# 의문점 ) 주소에 int를 두번이나 써야 하는데 이거 괜찮은걸까? ---> int 삭제함.
# 사진 여러장 받아서 AWS 올리고 그 내용 다운받아서 어레이로 데이터베이스에 저장 
#            --> 한개씩 올리고 DB에 한줄씩 저장하는걸로 바꿈
class PhotoAlbumAddResource(Resource):

    @jwt_required()
    def post(self):  
    

        # 1. 데이터 받아오기(유저 정보)
        teacherId = get_jwt_identity()
        print("teacherId : ", teacherId)

        
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
            print("선생님 원 ID, 반ID teacher_result_list : ", teacher_result_list)

            # - 선생님이 속한 반 아이디 가져오기
            class_id = teacher_result_list[0][0]
            print("선생님이 반 ID classIdList : ", class_id)

            # - 원 아이디 가져오기
            nursery_id = teacher_result_list[0][1]
            print("선생님 원 ID nursery_id : ",  nursery_id)


            # 사진 잘 올렸니?
            if 'photoUrl' not in request.files or 'contents' not in request.form :
                return { 'result' : 'fail', 'error' : '필수항목을 확인하세요'}, 400
            
            else :

                # 데이터베이스에서 어린이집 아이디와 반 아이디를 가져오기(파일 정리할때 이름으로 정리되어 들어가도록)
                teacher_result_list_str = str(teacher_result_list[0][1]) + '_' + teacher_result_list[0][2]
                print("원ID+반ID teacher_result_list_str : " ,teacher_result_list_str)

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

                # 위에서 받아온 아이디 정리
                # - 원 아이디 : nursery_id
                # - 반 아이디 : class_id
                # - 선생님 아이디 : teacherId
         
                # - 글 아이디를 가져오기 위한 쿼리
                query = '''SELECT *
                            FROM totalAlbum
                            where teacherId = %s
                            order by createdAt desc;'''

                record = (teacherId, )

                cursor = connection.cursor()
                cursor.execute(query, record)

                totalAlbumId_result = cursor.fetchall()
                print("totalAlbumId_result : ", totalAlbumId_result)

                totalAlbumId = str(totalAlbumId_result[0][0])
                print("totalAlbumId : ", totalAlbumId)



                # - 원 아이디를 포함해서 데이터베이스에 입력하기 위한 쿼리
                # - 글 아이디 포함하기 추가
                query2 = '''insert into totalPhoto
                        (nurseryId, classId, teacherId, totalAlbumId, date, title, contents, photoUrl)
                        values
                        (%s,%s,%s,%s,%s,%s,%s, %s);'''

                record2 = ( nursery_id, class_id, teacherId, totalAlbumId, date, title, contents, file_url)
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







### 2. 원아 프로필 사진을 눌렀을 때 글 목록 아이디 생성
class PhotoAlbumChildProfileListIdResource(Resource):

    @jwt_required()
    def post(self):

        # 데이터 받아오기
        # - 유저정보
        teacherId = get_jwt_identity()
        print("teacherId : ", teacherId)

        # - 바디
        # totalAlbumNum 과 원아 아이디를 받음

        totalAlbumNum = request.form['totalAlbumNum']
        print("* totalAlbumNum : ", totalAlbumNum )

        childId = request.form['childId']
        print("* childId : ", childId )

        # data = request.get_json()
        # print("data : ", data)
        

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

            class_id = teacher_result_list[0]
            print("class_id : ", class_id)

            # 글 아이디 생성하기
                # insert into totalAlbum
                # (totalAlbumNum)
                # values
                # (0);
            query2 = '''insert into totalAlbum
                        (teacherId, childId, totalAlbumNum)
                        values
                        (%s, %s, %s);'''
            
            record2 = ( teacherId, childId, totalAlbumNum )
            
            cursor = connection.cursor()
            cursor.execute(query2, record2)

            connection.commit()

            cursor.close()
            connection.close()

        except Error as e:
            print('오류1', e)
            return {'result':'fail', 'error':str(e) }, 500

        return { 'result': 'success'}

        





### 3. 원아별 얼굴 비교 후 DB와 버킷에 저장
# -> 사진을 한장씩 받아서 얼굴비교하는 코드
class PhotoAlbumRekogResource(Resource):

    @jwt_required()
    def post(self):

        # 1. 데이터 받아오기(유저 정보)
        teacherId = get_jwt_identity()
        print("* teacherId : ", teacherId)

        # 유저가 입력한 데이터
        date = request.form['date'].replace('T', ' ')[0:10]
        print("* date : ", date )
        title = request.form['title']
        print("* title : ", title )
        contents = request.form['contents']
        print("* contents : ", contents )
        classId = request.form['classId']
        print("* classId : ", classId )
        childId = request.form['childId']
        print("* childId : ", childId )
        photoUrl_1 = request.files['photoUrl_1']
        print("* photoUrl_1 : ", photoUrl_1 )

        # photoUrl_2 = request.files['photoUrl_2']
        # print("* photoUrl_2 : ", photoUrl_2 )
        # photoUrl_3 = request.files['photoUrl_3']
        # print("* photoUrl_3 : ", photoUrl_3 )
        # photoUrl_4 = request.files['photoUrl_4']
        # print("* photoUrl_4 : ", photoUrl_4 )
        # photoUrl_5 = request.files['photoUrl_5']
        # print("* photoUrl_5 : ", photoUrl_5 )


        # 1. 데이터베이스에서 원 아이디 + 반 아이디 + 원아 이름 가져오기

        try : 
            # 데이터베이스 연결
            connection = get_connection()


            # 로컬에 저장 되어있는지 확인
            print("* os.path.abspath('./photoUrl_image')", os.path.abspath('./photoUrl_image'))
            print("* os.listdir()" , os.listdir())


            # 선생님이 속한 원, 반의 아이디 가져오기
            query = '''SELECT classId, nurseryId, nurseryName 
                        FROM nursery n 
                        left join teacher t on n.id = t.nurseryId 
                        where t.id = %s;'''
            record = (teacherId, )

            cursor = connection.cursor()
            cursor.execute(query, record)

            teacher_result_list = cursor.fetchall()
            print("* 선생님 원 ID, 반ID teacher_result_list : ", teacher_result_list)

            # --- 원 아이디
            nursery_id = teacher_result_list[0][1]
            print("* 선생님 원 ID nursery_id : ",  nursery_id)

            # --- 반 아이디 : 유저가 입력하는 반 아이디 가져와서 쓰면 됨 : classId

            # --- 원 아이디 + 원 이름
            nurseryIdName = str(teacher_result_list[0][1]) + '_' + teacher_result_list[0][2]


            # 원아 아이디 가져오기 : childId

            
            # 사진첩 글 아이디 가져오기 
            query4 = '''SELECT *
                        FROM totalAlbum
                        where teacherId = %s and childId = %s
                        order by createdAt desc;'''
            record4 = (teacherId, childId)

            cursor = connection.cursor()
            cursor.execute(query4, record4)

            totalAlbumId_result = cursor.fetchall()
            print("* totalAlbumId_result : ", totalAlbumId_result)

            # --- 사진첩 글 아이디
            totalAlbumId = str(totalAlbumId_result[0][0])
            print("* totalAlbumId : ", totalAlbumId)


            # 로컬사진첩의 원아 프로필 이미지 리스트 가져오기
            print('* os.getswd() : ', os.getcwd()) # - 현재 경로 확인
            os.chdir('./profileUrl_image')       # - 프로필이미지 폴더로 이동
            print('* os.chdir : ', os.getcwd())   # - 이동 후 현재 경로 확인

            profile_image_list = os.listdir()         # - 폴더에 있는 파일을 리스트 형식으로 가져오기
            print('* profile_image_list : ', profile_image_list)


            # - 원과 반 아이디 
            nursery_class = str( nursery_id ) + '_' + str(classId)
            print("* nursery_class : ", nursery_class)

            profile_image1 = []      # ---- 원+반 과 원아아이디, 원아 이름 나눈 리스트
            i = 0
            for i in range( len(profile_image_list) ) :
                profile_image1.append( profile_image_list[i].split('.') )
                i = i+1
            print('* 프로필 사진 이름 나누기 profile_image1 : ', profile_image1)
            print('* 프로필 사진 이름 나누기 원+반 profile_image1[0][0] : ', profile_image1[13][0])
            print('* 프로필 사진 이름 나누기 원아아이디 profile_image1[0][1] : ', profile_image1[13][1])
            print('* 프로필 사진 이름 나누기 원아 이름 profile_image1[0][2] : ', profile_image1[13][2])




            today = datetime.date.today()
            print("* today : ", today)

            os.chdir('../') # 상위 폴더로 이동
            print('*  현재 경로 표시 : ', os.getcwd())

            # 선생님이 선택한 원아의 프로필 사진을 가져온다.
            profile_image_get = []
            i=0
            for i in range( len(profile_image1) ):
                if profile_image1[i][1] == childId :
                    profile_image_get.append( profile_image1[i] )
                i = i+1
            print("* profile_image_get : ", profile_image_get)
            
            if profile_image_get[0][0] == nursery_class :

                # 현재시간을 파일 이름에 넣기
                current_time1 = datetime.datetime.now()
                print("* current_time1 : ", current_time1)

                # 원+반 이 같을 때 선생님이 선택한 원아 프로필 사진 원아 아이디와
                # 프로필 이미지 폴더에 있는 원아 아이디가 같은 아이의 사진을 가져오기.
                child_photo_get = []
                h = 0
                for h in range( len(profile_image1) ):
                    if profile_image1[h][1] == childId :    # --> 원+반과 원아아이디 분리된 리스트의 원아 아이디==입력받은원아 아이디
                        child_photo_get.append( profile_image1[h][1])
                        img_file1 = profile_image_list[h]   # --> 프로필 이미지 담아논 리스트에서 해당 사진 가져오기
                        childindex = h                      # --> 몇번째 인덱스인지 저장
                        h = h+1
                print('* 선택된 원아 프로필 사진 : ', child_photo_get)


                print('*  img_file1 : ', img_file1)

                filename1 = current_time1.isoformat().replace(':', '_') + '_source.jpg'
                print("*  프로필 이름 수정 filename1 : ", filename1)

       

                # 유저가 입력한 사진 가져오기
                img_file2 = photoUrl_1

                # 유저가 입력한 사진 이름 바꾸기
                filename2 = current_time1.isoformat().replace(':', '_') + '_target.jpg'
                filename2 = re.sub("[\/:*?\"<>|]","", filename2)
                print("* 유저가 올린 사진 이름 수정 filename2 : ", filename2)

                # 유저에게 받은 사진 저장
                save_uploaded_file2('photoUrl_image', img_file2, filename2)

                
                # - 저장되어있는 폴더의 절대 경로를 반환
                # abspath_profile =  os.path.abspath('./profileUrl_image')
                # print('-- 절대경로 반환 abspath_profile : ' , abspath_profile)
                # abspath_photo =  os.path.abspath('./photoUrl_image')
                # print('-- 절대경로 반환 abspath_photo : ' , abspath_photo)



                # 얼굴 비교 함수 실행        
                num_face_matches = compare_faces1( 'profileUrl_image/'+ str(img_file1), 'photoUrl_image/'+ filename2)
                print('* 얼굴매칭Num num_face_matches : ', num_face_matches)
            

                # 얼굴 유사도가 존재하면(다른얼굴이라면 유사도가 아예 안나옴) 넘는다면 버킷에 저장하고 데이터베이스에도 저장
                if num_face_matches > 0:
                    # 경로는 원 아이디+원 이름/ 포토앨범 / 
                    # 파일이름 : 클래스 아이디 + 원아 아이디 + (원아이름) + 날짜 + r + .jpg
                    new_filename = nurseryIdName + '/photo_album/' + classId + '_' + childId + '_' + profile_image1[childindex][2] +'_'+ str(today) + '_' + 'r' + '.jpg'
                    print('* 새 파일 이름 new_filename : ' , new_filename)


                    # 일치하는 얼굴이면 파일을 버킷에 저장.
                    try: 
                        # 사진부터 S3에 저장
                        s3 = boto3.client('s3',
                                aws_access_key_id = Config.AWS_ACCESS_KEY_ID,
                                aws_secret_access_key = Config.AWS_SECRET_ACCESS_KEY)
                        s3.upload_fileobj(photoUrl_1, # --? 사진파일 
                                        Config.S3_BUCKET,
                                        new_filename,
                                        ExtraArgs = {'ACL':'public-read', 'ContentType':'image/jpeg'}) 
                        
                        file_url = Config.S3_BASE_URL + new_filename 
                        print("* 저장한 파일 주소 file_url : ", file_url)

                    except Exception as e:
                        print(e)
                        return {'result1':'fail','error1': str(e)}, 500
                    
                    
                    # 버킷에 사진 저장한걸 다시 데이터 베이스에 저장 해야 함.
                    # - 사진첩 글 아이디 가져오기 --> 위에서 가져옴
                    try :
                        
                        # - 원 아이디를 포함해서 데이터베이스에 입력하기 위한 쿼리
                        # - 글 아이디 포함하기 추가
                        # - 차일드 아이디가 같은 토탈앨범 아이디를 가져와서 입력
                        query6 = '''insert into myAlbum
                                    (nurseryId, classId, childId, totalAlbumId, date, title, contents, photoUrl)
                                    values
                                    (%s,%s,%s,%s,%s,%s,%s,%s);'''

                        record6 = ( nursery_id, classId, childId, totalAlbumId, date, title, contents, file_url)
                        print("record6 : ", record6)

                        cursor = connection.cursor(prepared=True)
                        cursor.execute(query6, record6)

                        connection.commit()

                        # 이미지 파일 삭제 (필요한 경우)
                        # os.remove('profileUrl_image/' + profileUrl_list[i])
                        # os.remove('photoUrl_image/' + photoUrl_list[j])


                    except Error as e :
                        print(e)
                        return {'result2':'fail','error2': str(e)}, 500

                    # else : continue

                    #j = j+1

            cursor.close()
            connection.close()

        except Error as e :
            print(e)
            return {'result2':'fail','error2': str(e)}, 500


        return {'result' : 'success'}
        # return { 'result' : 'success',
        #         'profileUrl_result_list Count' : len(profileUrl_result_list),
        #         'profileUrl_result_list' : profileUrl_result_list
        #         }
    


# 5. 얼굴비교할 이미지 파일 로컬에 저장하는 함수
def save_uploaded_file(directory, file, filename):
    if not os.path.exists(directory):
        os.makedirs(directory)
    with open(os.path.join(directory, filename), 'wb') as f:
        f.write(file.getbuffer()) 


# 5. 이미지 파일 로컬에 저장 함수 2
def save_uploaded_file2(directory, file, filename):
    if not os.path.exists(directory):
        os.makedirs(directory)
    else : 
        file_1 = open(os.path.join(directory, filename), 'wb')
        file_1.write(file.getbuffer())
        file_1.close()


# 얼굴인식 실행 함수 
def compare_faces1(sourceFile, targetFile):
    client = boto3.client('rekognition', region_name='ap-northeast-2', 
                            aws_access_key_id=Config.AWS_ACCESS_KEY_ID, 
                            aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY)
    imageSource = open(sourceFile, 'rb')  # 오류 (해결): OSError: [Errno 22] Invalid argument: "profileUrl_image/<FileStorage: '1_1_김담연.png' ('image/png')>"
    imageTarget = open(targetFile, 'rb')
    
    response = client.compare_faces(
        SimilarityThreshold=80,
        SourceImage={'Bytes': imageSource.read()},
        TargetImage={'Bytes': imageTarget.read()}
    )

    print("* 얼굴 비교 응답 response" , response)

    # responseGet = response.get('FaceMatches')
    print("* 얼굴일치 응답만 보기 response.get('FaceMatches')", response.get('FaceMatches'))                   

    face_matches = response.get('FaceMatches', [])
    print("* 얼굴일치 - 유사성 response.get('FaceMatches', []) : ", response.get('FaceMatches', []))

    print("* 얼굴 매칭 face_matches : ", face_matches)

    imageSource.close()
    imageTarget.close()

    return len(face_matches)







### 사진첩 수정(전체 사진첩)
class PhotoAlbumEditResource(Resource):

    @jwt_required()
    def put(self, id): # 아이디는 사진첩 아이디

        # 데이터 받아오기
        # - 유저정보
        teacherId = get_jwt_identity()
        print("teacherId : ", teacherId)
            
        # body에 있는 json 데이터를 받아온다.
        data = request.get_json()

        print("* data['title'] : ", data['title'])
        print("* data['contents'] : ", data['contents'])
        print("* id : ", id )

        #
        try :
            connection = get_connection()

            # 선생님이 속한 원과 반 아이디 가져오기
            query = '''SELECT classId, nurseryId, nurseryName 
                        FROM nursery n 
                        left join teacher t on n.id = t.nurseryId 
                        where t.id = %s;'''
            record = (teacherId, )

            cursor = connection.cursor()
            cursor.execute(query, record)

            teacher_result_list = cursor.fetchone()
            print("* teacher_result_list : ", teacher_result_list)

            # 원 아이디 
            nursery_id = teacher_result_list[1]
            print("* nursery_id : ", nursery_id)
            # 반 아이디
            class_id = teacher_result_list[0]
            print("* class_id : ", class_id)
       

            # 해당 글 목록 아이디와 연결된 사진들 전부 가져오기
            # id와 같은 행의 토탈앨범아이디 가져오기
            query1 = '''select id, nurseryId, classId, teacherId, totalAlbumId, date, title, contents, photoUrl 
                        from totalPhoto
                        where id = %s and nurseryId = %s and classId = %s
                        group by totalAlbumId
                        order by createdAt desc;'''
            record1 = ( id, nursery_id, class_id)
            
            cursor = connection.cursor()
            cursor.execute(query1, record1)

            totalAlbumId_result = cursor.fetchall()
            print("* totalAlbumId_result : ", totalAlbumId_result)

            # 토탈 앨범 아이디
            totalAlbumId = totalAlbumId_result[0][4]
            print(" * totalAlbumId : ", totalAlbumId)


            # 토탈 앨범 아이디에 해당하는 글들 수정하기
            query3 = '''update totalPhoto
                        set title = %s , contents = %s
                        where totalAlbumId = %s;'''
            record3 = ( data['title'], data['contents'], totalAlbumId )
            
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query3, record3)

            photoEdit_result = cursor.fetchall()
            print("* photoEdit_result : " , photoEdit_result)

            connection.commit()
            cursor.close()
            connection.close()

        except Error as e:
            print(e)
            return {'result': 'fail','error': str(e)},500
        
        return {'result': 'success'}
    






### 사진첩 수정(얼굴비교 사진첩)
class PhotoAlbumRekogEditResource(Resource):

    @jwt_required()
    def put(self, id): # 아이디는 마이앨범 사진첩 아이디

        # 데이터 받아오기
        # - 유저정보
        teacherId = get_jwt_identity()
        print("teacherId : ", teacherId)
            
        # body에 있는 json 데이터를 받아온다.
        data = request.get_json()

        print("* data['title'] : ", data['title'])
        print("* data['contents'] : ", data['contents'])
        print("* id : ", id )

        #
        try :
            connection = get_connection()

            # 선생님이 속한 원과 반 아이디 가져오기
            query = '''SELECT classId, nurseryId, nurseryName 
                        FROM nursery n 
                        left join teacher t on n.id = t.nurseryId 
                        where t.id = %s;'''
            record = (teacherId, )

            cursor = connection.cursor()
            cursor.execute(query, record)

            teacher_result_list = cursor.fetchone()
            print("* teacher_result_list : ", teacher_result_list)

            # 원 아이디 
            nursery_id = teacher_result_list[1]
            print("* nursery_id : ", nursery_id)
            # 반 아이디
            class_id = teacher_result_list[0]
            print("* class_id : ", class_id)
       

            # 해당 글 목록 아이디와 연결된 사진들 전부 가져오기
            # id와 같은 행의 토탈앨범아이디 가져오기
            query1 = '''select * 
                        from myAlbum
                        where id = %s
                        group by totalAlbumId
                        order by createdAt desc;'''
            record1 = ( id, )
            
            cursor = connection.cursor()
            cursor.execute(query1, record1)

            totalAlbumId_result = cursor.fetchall()
            print("* totalAlbumId_result : ", totalAlbumId_result)

            # 마이 아이디
            totalAlbumId = totalAlbumId_result[0][4]
            print(" * myAlbumId : ", totalAlbumId)


            # 마이 앨범 아이디에 해당하는 글들 수정하기
            query3 = '''update myAlbum
                        set title = %s , contents = %s
                        where totalAlbumId = %s;'''
            record3 = ( data['title'], data['contents'], totalAlbumId )
            
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query3, record3)

            photoRekogEdit_result = cursor.fetchall()
            print("* photoRekogEdit_result : " , photoRekogEdit_result)

            connection.commit()
            cursor.close()
            connection.close()

        except Error as e:
            print(e)
            return {'result': 'fail','error': str(e)},500
        
        return {'result': 'success'}
    






### 사진첩 삭제(전체 사진첩)
class PhotoAlbumDeleteResource(Resource):

    @jwt_required()
    def delete(self, id):

        # 데이터 받아오기
        # - 유저정보
        teacherId = get_jwt_identity()
        print("teacherId : ", teacherId)
            
        print("* id : ", id )  # 사진첩 아이디

        #
        try :
            connection = get_connection()

            # 선생님이 속한 원과 반 아이디 가져오기
            query = '''SELECT classId, nurseryId, nurseryName 
                        FROM nursery n 
                        left join teacher t on n.id = t.nurseryId 
                        where t.id = %s;'''
            record = (teacherId, )

            cursor = connection.cursor()
            cursor.execute(query, record)

            teacher_result_list = cursor.fetchone()
            print("* teacher_result_list : ", teacher_result_list)

            # 원 아이디 
            nursery_id = teacher_result_list[1]
            print("* nursery_id : ", nursery_id)
            # 반 아이디
            class_id = teacher_result_list[0]
            print("* class_id : ", class_id)
       

            # 해당 글 목록 아이디와 연결된 사진들 전부 가져오기
            # id와 같은 행의 토탈앨범아이디 가져오기
            query1 = '''select id, nurseryId, classId, teacherId, totalAlbumId, date, title, contents, photoUrl 
                        from totalPhoto
                        where id = %s and nurseryId = %s and classId = %s
                        group by totalAlbumId
                        order by createdAt desc;'''
            record1 = ( id, nursery_id, class_id)
            
            cursor = connection.cursor()
            cursor.execute(query1, record1)

            totalAlbumId_result = cursor.fetchall()
            print("* totalAlbumId_result : ", totalAlbumId_result)

            # 토탈 앨범 아이디
            totalAlbumId = totalAlbumId_result[0][4]
            print(" * totalAlbumId : ", totalAlbumId)


            # 토탈 앨범 아이디에 해당하는 사진 전부 삭제
            query = '''delete from totalPhoto
                        where totalAlbumId = %s;'''
            record = (totalAlbumId, )
            cursor = connection.cursor()
            cursor.execute(query, record)

            connection.commit()

            cursor.close()
            connection.close()

        except Error as e:
            print(e)
            return {'result':'fail', 'error':str(e)}
        
        return {'result' : 'success'}
    







### 사진첩 삭제(얼굴비교 사진첩)
class PhotoAlbumRekogDeleteResource(Resource):

    @jwt_required()
    def delete(self, id):

        # 데이터 받아오기
        # - 유저정보
        teacherId = get_jwt_identity()
        print("teacherId : ", teacherId)
            
        print("* id : ", id )  # 마이앨범 아이디

        #
        try :
            connection = get_connection()

            # 선생님이 속한 원과 반 아이디 가져오기
            query = '''SELECT classId, nurseryId, nurseryName 
                        FROM nursery n 
                        left join teacher t on n.id = t.nurseryId 
                        where t.id = %s;'''
            record = (teacherId, )

            cursor = connection.cursor()
            cursor.execute(query, record)

            teacher_result_list = cursor.fetchone()
            print("* teacher_result_list : ", teacher_result_list)

            # 원 아이디 
            nursery_id = teacher_result_list[1]
            print("* nursery_id : ", nursery_id)
            # 반 아이디
            class_id = teacher_result_list[0]
            print("* class_id : ", class_id)
       

            # 해당 글 목록 아이디와 연결된 사진들 전부 가져오기
            # id와 같은 행의 토탈앨범아이디 가져오기
            query1 = '''select id, nurseryId, classId, childId, totalAlbumId, date, title, contents, photoUrl 
                        from myAlbum
                        where id = %s
                        group by totalAlbumId
                        order by createdAt desc;'''
            record1 = ( id, )
            
            cursor = connection.cursor()
            cursor.execute(query1, record1)

            totalAlbumId_result = cursor.fetchall()
            print("* totalAlbumId_result : ", totalAlbumId_result)

            # 토탈 앨범 아이디
            totalAlbumId = totalAlbumId_result[0][4]
            print(" * totalAlbumId : ", totalAlbumId)


            # 토탈 앨범 아이디에 해당하는 사진 전부 삭제
            query = '''delete from myAlbum
                        where totalAlbumId = %s;'''
            record = (totalAlbumId, )
            cursor = connection.cursor()
            cursor.execute(query, record)

            connection.commit()

            cursor.close()
            connection.close()

        except Error as e:
            print(e)
            return {'result':'fail', 'error':str(e)}
        
        return {'result' : 'success'}




class PhotoAlbumGetProfileUrlResource(Resource):

    @jwt_required()
    def get(self, id):

        # 데이터 받아오기
        # - 유저정보
        teacherId = get_jwt_identity()
        print("teacherId : ", teacherId)
            
        print("* id : ", id )  # 원아 아이디

        #
        try :
            connection = get_connection()

            # 해당 원아의 프로필 사진 Url 가져오기
            query1 = '''select id, classId, nurseryId, childName, birth, profileUrl 
                        from children
                        where id = %s;'''
            record1 = ( id, )
            
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query1, record1)

            profileUrl_result = cursor.fetchall()
            print("* profileUrl_result : ",profileUrl_result)

            # 원아 프로필 결과
            profile = profileUrl_result[0]['profileUrl']
            profile = str(profile)
            print(" * profile : ", profile)

            cursor.close()
            connection.close()

        except Error as e:
            print(e)
            return {'result':'fail', 'error':str(e)}
        
        return {'result' : 'success', 'profile' : profile}



class PhotoAlbumGetProfileListResource(Resource):

    @jwt_required()
    def get(self, classId):

        # 데이터 받아오기
        # - 유저정보
        teacherId = get_jwt_identity()
        print("teacherId : ", teacherId)
            
        print("* id : ", id )  # 원아 아이디

        #
        try :
            connection = get_connection()

            # 해당 원아의 프로필 사진 Url 가져오기
            query1 = '''select id, classId, nurseryId, childName, birth, profileUrl 
                        from children
                        where classId = %s;'''
            record1 = ( classId, )
            
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query1, record1)

            items = cursor.fetchall()
            cursor.close()
            connection.close()

        except Error as e:
            print(e)
            return {'result':'fail', 'error':str(e)}
        
        return {'result' : 'success','count':len(items), 'items' :items}

