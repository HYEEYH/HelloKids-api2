


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
# 전체. 글 아이디별로 구분 안하고 최신순으로 다 가져옴
# 의문점 ) 주소에 int를 두번이나 써야 하는데 이거 괜찮은걸까? --> 수정중.
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






### 사진첩 - 원아별 사진 폴더 생성 및 자동분류
### 1. 컬렉션 생성 : 원 별로 1번씩만 하면 됨.
### 2. 원아 프로필 사진을 컬렉션에 추가 : 나중에 얼굴인식 하기위한 원본 이미지로 사용됨.
### 3. 컬렉션의 사진과 사진첩에 올라온 사진을 비교
### 4. 각 원아별 폴더 생성 및 자동 분류

## !!! -- 컬렉션은 한번만 생성하면 되니까 따로 컬렉션 만드는 API를 빼놓아야 한다 -- !!! ##
# --> 테스트 해야 하는데 아직 컬렉션을 어디서 확인해야 하는지 잘 모름. 찾아봐야 함.
### 1. 컬렉션 생성
# class PhotoAlbumAddCollectionResource(Resource):
#     def post(self):

#         # 1. 데이터 받아오기(유저 정보)
#         teacherId = get_jwt_identity()
#         print("teacherId : ", teacherId)

#         try:

#             # 2. 컬렉션 만들기 
#             collection_id = 'HelloKisRekogTest'
#             리전 = "ap-northeast-2"
#             create_collection(collection_id, region)

#             collectionArn = []

#             def create_collection(collection_id, region):  # - 컬렉션 만드는 함수
#                 client = boto3.client('rekognition', region_name=region)

#                 # Create a collection
#                 print('Creating collection:' + collection_id)
#                 response = client.create_collection(CollectionId=collection_id, 
#                 Tags={"SampleKey1":"SampleValue1"})
#                 collectionArn = response['CollectionArn']
#                 print('Collection ARN: ' + response['CollectionArn'])
#                 print('Status code: ' + str(response['StatusCode']))
#                 print('Done...')

#             # create_collection(collection_id, region)

#             print("컬렉션의 ARN collectionArn ", collectionArn )

            

#             # 3. 컬렉션 만들고 ARN을 데이터베이스에 저장
#             connection = get_connection()
#             query = '''insert into collection
#                         (teacherId, collectionArn)
#                         values
#                         (%s, %s);'''
#             record = (teacherId, collectionArn)

#             cursor = connection.cursor()
#             cursor.execute(query, record)
#             connection.commit()

#             collectionArn_result = cursor.fetchall()
#             print("teacher_result_list : ", collectionArn_result)

#             cursor.close()
#             connection.close()

#         except Error as e:
#             print(e)
#             return{'result':'fail', 'error':str(e)}, 400
        
#         return {'result':'success'}
    





# ### 2. 원아 프로필 사진을 컬렉션에 추가 (인덱싱 하기)
# class PhotoAlbumCollectionResource(Resource):
#     def post(self):

#         return






### 3. 원아 얼굴 컬렉션에서 찾아서 비교하기 + 4. 원아별 사진폴더 생성 및 자동분류
class PhotoAlbumRekogResource(Resource):

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
        # photoUrl = request.files['photoUrl']
        # print("photoUrl : ", photoUrl )


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

            # --- 선생님이 속한 반 아이디
            # class_id = teacher_result_list[0][0]
            # print("선생님이 반 ID classIdList : ", class_id)

            # --- 원 아이디
            nursery_id = teacher_result_list[0][1]
            print("선생님 원 ID nursery_id : ",  nursery_id)

            # --- 원 아이디 + 원 이름
            nurseryIdName = str(teacher_result_list[0][1]) + '_' + teacher_result_list[0][2]


            # 반 아이들 프로필 주소 가져오기
            query = '''SELECT id, nurseryId, classId, childName, birth, profileUrl
                    FROM children
                    where nurseryId = %s and classId = %s;'''
            record = (nursery_id, classId)
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)

            
            # 프로필 주소만 가져오기
            profileUrl_result = cursor.fetchall()
            # print("profileUrl_result : ", profileUrl_result)
            print("len(profileUrl_result) : ", len(profileUrl_result))
            print("profileUrl_result[1]['profileUrl']", profileUrl_result[0]['profileUrl'] )

            profileUrl_list = []  # ---> 프로필 사진 담아논 리스트
            i = 0
            for i in range( len(profileUrl_result) ) :
                #profileUrl_list = profileUrl_result[i]['profileUrl']
                profileUrl_list.append(profileUrl_result[i]['profileUrl'])
                i = i + 1
            print("프로필 URL profileUrl_list : ", profileUrl_list)

            
            childName_list = []  # ---> 원아이름 순서대로 담아논 리스트
            i = 0
            for i in range ( len( profileUrl_result ) ) :
                 childName_list.append(profileUrl_result[i]['childName'])
                 i = i + 1
            print("원아 이름 childName_list : ", childName_list)


### --------- todo : 원아 아이디 가져오는 테이블이 없음. 쿼리 다시 짜기!! -----------------###
            # 원아 아이디 가져오기
            child_id = profileUrl_result[0][0]
            print(" child_id : ",  child_id)


            # 사진첩에 올린 사진 데이터베이스에서 불러오기
            query = '''SELECT id, nurseryId, classId, childName, birth, profileUrl
                    FROM children
                    where nurseryId = %s and classId = %s;'''
            record = (nursery_id, classId)
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)

            
            # 사진첩 글 아이디 가져오기
            query = '''SELECT *
                        FROM totalAlbum
                        where teacher = %s
                        order by createdAt desc;'''
            record = (teacherId, )

            cursor = connection.cursor()
            cursor.execute(query, record)

            totalAlbumId_result = cursor.fetchall()
            print("totalAlbumId_result : ", totalAlbumId_result)

            # --- 사진첩 글 아이디
            totalAlbumId = str(totalAlbumId_result[0][0])
            print("totalAlbumId : ", totalAlbumId)


            # 사진첩의 사진Url 가져오기
            query1 = '''SELECT nurseryId, classId, teacherId, totalAlbumId, date, title, contents, photoUrl
                        FROM totalPhoto
                        where teacher = %s and totalAlbumId = %s
                        order by createdAt desc;'''
            record1 = (teacherId, totalAlbumId)

            cursor = connection.cursor()
            cursor.execute(query1, record1)

            photoUrl_result = cursor.fetchall()
            print("사진첩 사진 주소 photoUrl_result : ", photoUrl_result)


            photoUrl_list = []  # ---> 토탈포토의 phtoUrl만 리스트로 가져옴
            i = 0
            for i in range ( len( profileUrl_result ) ) :
                 childName_list.append(profileUrl_result[i]['childName'])
                 i = i + 1
            print("토탈포토 url 리스트 photoUrl_list : ", photoUrl_list)




            # 3. 컬렉션을 만들어서 원아들의 사진을 저장(대조군으로 쓰기 위해) --> 이 부분 삭제

            
            # -- for 반복문 이중으로 돌리기
            # -- 데이터베이스에 있는 아이의 프로필 사진 하나당, 사진첩에 있는 사진 n장을 비교하기
            # -- 아이 프로필 비교하기 누르는 순간 아이 폴더 하나 만들고 반복문 시작
            # -- 반복문으로 돌려서 매치가 99%이상 나오면 그 사진은 아이 폴더로 들어가게 하기
            # -- 이걸 반 원아 수 만큼 반복.

            # -- 반 원아 리스트에서 1번 원아 가지고 와서 폴더 만들기.
            # -- 원본 이미지에 1번 원아 프로필 이미지 넣기
            # -- 타겟 파일에 사진첩에 올라와있는 이미지 넣기.


            # - 원아별 개인 사진첩 만들기 : 폴더이름 - 원아이름+날짜
            # profileUrl_list   # -> 프로필 사진 담아논 리스트
            # childName_list   # -> 원아이름 순서대로 담아논 리스트

            # --- 폴더 이름 만들기
            today = datetime.date.today()
            print("today : ", today)

            
            if len( profileUrl_list ) == len( childName_list ) :

                h = 0
                for h in range( len(profileUrl_list) ):
                    # 경로는 원 아이디+원 이름/ 포토앨범 / 
                    # 파일이름 : 클래스 아이디 + 원아 아이디 + (원아이름) + 날짜 + r + .jpg
                    new_filename = nurseryIdName + '/photo_album/' + classId + '_' + child_id + '_' +childName_list[i] +'_'+ today + '_' + 'r' + '.jpg'
                    
                    i = 0
                    for i in range( len(profileUrl_list) ) :

                        j = 0
                        for j in range( len(profileUrl_list) ) :

                            num_face_matches = compare_faces1(profileUrl_list[i], photoUrl_list[j])

                            def compare_faces1(sourceFile, targetFile):
                                client = boto3.client('rekognition', region_name='ap-northeast-2', aws_access_key_id=Config.AWS_ACCESS_KEY_ID, aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY)
                                imageSource = open(sourceFile, 'rb')
                                imageTarget = open(targetFile, 'rb')
                                response = client.compare_faces(
                                    SimilarityThreshold=99,
                                    SourceImage={'Bytes': imageSource.read()},
                                    TargetImage={'Bytes': imageTarget.read()}
                                )
                                face_matches = response.get('FaceMatches', [])
                                imageSource.close()
                                imageTarget.close()
                                return len(face_matches)
                            
                            if num_face_matches == 1 :
                                
                                # 일치하는 얼굴이 1 이면 파일을 버킷에 저장.
                                try: 
                                    # 사진부터 S3에 저장
                                    s3 = boto3.client('s3',
                                            aws_access_key_id = Config.AWS_ACCESS_KEY_ID,
                                            aws_secret_access_key = Config.AWS_SECRET_ACCESS_KEY) 
                                    s3.upload_fileobj(profileUrl_list[i], # --? 사진파일 
                                                    Config.S3_BUCKET,
                                                    new_filename,
                                                    ExtraArgs = {'ACL':'public-read', 'ContentType':'image/jpeg'}) 
                                    
                                    file_url = Config.S3_BASE_URL + new_filename 
                                    print("저장한 파일 주소 file_url : ", file_url)

                                except Exception as e:
                                    print(e)
                                    return {'result1':'fail','error1': str(e)}, 500
                                
                                
                                # 버킷에 사진 저장한걸 다시 데이터 베이스에 저장 해야 함.
                                # - 사진첩 글 아이디 가져오기 --> 위에서 가져옴
                                try :
                                    
                                    # - 원 아이디를 포함해서 데이터베이스에 입력하기 위한 쿼리
                                    # - 글 아이디 포함하기 추가
                                    query2 = '''insert into myAlbum
                                                (nurseryId, classId, childId, totalAlbumId, date, title, contents, photoUrl)
                                                values
                                                (%s,%s,%s,%s,%s,%s,%s,%s);'''

                                    record2 = ( nursery_id, classId, child_id, totalAlbumId, date, title, contents, file_url)
                                    print("record2 : ", record2)

                                    cursor = connection.cursor(prepared=True)
                                    cursor.execute(query2, record2)

                                    connection.commit()

                                except Error as e :
                                    print(e)
                                    return {'result2':'fail','error2': str(e)}, 500

                            j = j+1
                        i = i+1
                    h = h+1
                        
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







### 4. 원아별 사진 폴더 생성 및 자동분류
# class PhotoAlbumAutoAddResource(Resource):

#     def post(self):

#         return
    


