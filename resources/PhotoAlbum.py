


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



### 사진첩 목록 보기 : 전체. 글 아이디별로 구분 안하고 최신순으로 다 가져옴

# 의문점 ) 주소에 int를 두번이나 써야 하는데 이거 괜찮은걸까? --> 수정해야함.
# --> 0907 : 데이터 가져와서 목록 보는걸로 수정 중
class PhotoAlbumListResource(Resource): 

    @jwt_required()
    def get(self):

        # 유저 정보 가져오기
        teacherId = get_jwt_identity()
        print("teacherId : ", teacherId)
        
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

            # - 반 아이디
            class_id = teacher_result_list[0]
            print("class_id : ", class_id)


            # 일단 사진첩 목록 가져오기
            query = '''SELECT classId, teacherId, totalAlbumId, date, title, contents, photoUrl 
                        FROM totalPhoto
                        where classId = %s and teacherId = %s and totalAlbumId is not null
                        order by totalAlbumId desc;'''
            record = (class_id, teacherId)
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)

            totalAlbumList_result = cursor.fetchall()
            cursor.close()
            connection.close()

        except Error as e:
            print(e)
            return{'result':'fail', 'error':str(e)}, 400
        
        i = 0
        for row in totalAlbumList_result :
            totalAlbumList_result[i]['date']= row['date'].isoformat().replace('T', ' ')[0:10]
            i = i + 1

        return {'result':'success', 'items':totalAlbumList_result}
    





### 사진첩 글 아이디별 사진 개수 가져오기
# - api 경로 안 만들어 놨음.
# - 포스트맨 API 안 만들어 놨음.
# - 잠시 정지. 레코그니션 먼저 하러 감.
class PhotoAlbumListCountResource(Resource):

    @jwt_required()
    def get(self):

        # 데이터 받아오기
        # - 유저정보
        teacherId = get_jwt_identity()
        print("teacherId : ", teacherId)

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

            nursery_id = teacher_result_list[1]
            print("nursery_id : ", nursery_id)

            class_id = teacher_result_list[0]
            print("class_id : ", class_id)


            # 글 아이디 별 사진 개수 가져오기
            query2 = '''SELECT totalAlbumId, count(totalAlbumId) as count, photoUrl, teacherId, classId
                        FROM totalPhoto
                        where nurseryId = %s and classId = %s and teacherId = %s
                        group by totalAlbumId
                        order by createdAt desc;'''
            
            record2 = ( nursery_id, class_id, teacherId )
            
            cursor = connection.cursor()
            cursor.execute(query2, record2)

            photoCount_result = cursor.fetchall()
            
            cursor.close()
            connection.close()

        except Error as e:
            print('오류1', e)
            return {'result':'fail', 'error':str(e) }, 500
        
        totalAlbum_photoCount_list = []
        i = 0
        for row in photoCount_result :
            totalAlbum_photoCount_list.append(photoCount_result[i]['count'])
            i = i + 1

        return {'result':'success', 'item count':len(photoCount_result), 'items':photoCount_result}








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







### 사진첩 사진 추가

# 의문점 ) 주소에 int를 두번이나 써야 하는데 이거 괜찮은걸까? ---> int 삭제함.
# 사진 여러장 받아서 AWS 올리고 그 내용 다운받아서 어레이로 데이터베이스에 저장

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






### 사진첩 자동 분류
# 순서 : 원아별 얼굴인식 -> 자동분류 -> 폴더생성 -> 사진이동

# - 원아별 사진 자동분류
class PhotoAlbumRekogResource(Resource):

    @jwt_required()
    def post(self):

        # 1. 데이터 받아오기(유저 정보)
        teacherId = get_jwt_identity()
        print("teacherId : ", teacherId)

        # 2. 데이터베이스에 있는 원아 프로필 사진 불러오기
        try : 
            # 데이터베이스 연결
            connection = get_connection()

            # 선생님이 속한 원, 반의 아이디 가져오기
            query = '''SELECT classId, nurseryId, nurseryName 
                        FROM nursery n 
                        left join teacher t on n.id = t.nurseryId 
                        where t.id = %s;'''
            record = (teacherId, )

            cursor = connection.cursor()
            cursor.execute(query, record)

            teacher_result_list = cursor.fetchall()
            print("선생님 원 ID, 반ID teacher_result_list : ", teacher_result_list)

            # - 선생님이 속한 반 아이디
            class_id = teacher_result_list[0][0]
            print("선생님이 반 ID classIdList : ", class_id)

            # - 원 아이디
            nursery_id = teacher_result_list[0][1]
            print("선생님 원 ID nursery_id : ",  nursery_id)


            # 반 아이들 프로필 주소 가져오기
            query = '''SELECT nurseryId, classId, childName, birth, profileUrl
                    FROM children
                    where nurseryId = %s and classId = %s;'''
            record = (nursery_id, class_id)
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)

            # 프로필 주소만
            profileUrl_result = cursor.fetchall()
            # print("profileUrl_result : ", profileUrl_result)
            print("len(profileUrl_result) : ", len(profileUrl_result))
            print("profileUrl_result[1]['profileUrl']", profileUrl_result[1]['profileUrl'] )

            profileUrl_list = []
            i = 0
            for i in range( len(profileUrl_result) ) :
                #profileUrl_list = profileUrl_result[i]['profileUrl']
                profileUrl_list.append(profileUrl_result[i]['profileUrl'])
                i = i + 1
            print("profileUrl_list : ", profileUrl_list)

            cursor.close()
            connection.close()

        except Error as e :
                print(e)
                return {'result2':'fail','error2': str(e)}, 500




        # 데이터베이스에 있는 사진첩의 사진 불러오기




        # 얼굴비교 실행
        # num_face_matches = compare_faces("소스파일(원본이미지)", "타켓파일(비교할이미지)")

        # if num_face_matches > 0:
        #     return { f'얼굴이 일치합니다. 일치한 얼굴 수: {num_face_matches}' }
        # else:
        #     return { '얼굴이 일치하지 않습니다.' }

        return {'result' : 'success'}
        # return { 'result' : 'success',
        #         'profileUrl_result_list Count' : len(profileUrl_result_list),
        #         'profileUrl_result_list' : profileUrl_result_list
        #         }




# - 원아별 사진 폴더 생성
class PhotoAlbumAutoAddResource(Resource):

    def post(self):

        return

