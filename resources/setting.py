from flask_restful import Resource
from flask import request
import mysql.connector
from mysql.connector import Error
from mysql_connection import get_connection
from utils import check_password, hash_password, save_uploaded_file2
from email_validator import validate_email,EmailNotValidError 
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity, jwt_required
from datetime import datetime
import boto3
from config import Config
import json


# 권한 설정 목록
class SettingApproveList(Resource) :
    
    @jwt_required()
    def get(self):
        teacherId = get_jwt_identity()

        try:
            connection = get_connection()
            query = '''select nurseryId, nurseryName, nurseryAddress from nursery n left join teacher t on n.id = t.nurseryId where t.id = %s;'''
            record = (teacherId, )
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query,record)
            teachers_nursery = cursor.fetchall()
            nursery_id = teachers_nursery[0]["nurseryId"]
            nursery_name = teachers_nursery[0]["nurseryName"]
            nursery_address = teachers_nursery[0]["nurseryAddress"]
            print(nursery_id, nursery_name, nursery_address)


            query = '''select id, parentsName, email, phone, childNameP, birthP, childId from parents where nurseryName = %s and childId is null;'''
            record = (nursery_name, )
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query,record)

            result_list = cursor.fetchall()
            print(result_list)

            if len(result_list) == 0:
                return {'result':'fail','error':'미승인된 학부모님이 없습니다'}, 400


            connection.commit()
            cursor.close()
            connection.close()

        except Error as e:
            print(e)
            return {'result':'fail','error':'선생님의 원 정보가 등록되지 않았습니다.'}, 500
        
        i = 0
        for row in result_list :
            result_list[i]['birthP']= row['birthP'].isoformat()
            i = i + 1

        return {'items':result_list}



# 권한 설정 
class SettingApproveResource(Resource) :
    
    @jwt_required()
    def put(self,parentsId):

        # {
        #  "parentId":1   
        # }

        data = request.get_json()
        teacherId = get_jwt_identity()

        try:
            connection = get_connection()
            query = '''select c.id
                    from parents p 
                    left outer join children c 
                    on p.childNameP = c.childName
                    where p.id = %s;'''
            record = (parentsId, )
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query,record)

            result_list = cursor.fetchall()
            child_id = result_list[0]["id"]


            if len(result_list) == 0:
                return {'result':'fail','error':'매칭되는 원아가 없습니다'}, 400

            # 매칭되는 원아가 있으므로 앱 사용권한 설정 코드 작성 
            # parents table의 childId 값이 null인지 아닌지 확인하여 사용 권한을 부여한다. 
            query =  '''update parents set childId = %s where id = %s;'''  
            record = (child_id, parentsId)
            cursor = connection.cursor()
            cursor.execute(query,record)

            connection.commit()


            cursor.close()
            connection.close()

        except Error as e:
            print(e)
            return {'result':'fail','error': str(e)}, 500
        return {'result' :'success', 'msg':"학부모와 원아가 매칭되었습니다."}


# 반 생성

class SettingClassResource(Resource) :
    
    @jwt_required()
    def post(self,nurseryId):

        # 1. 클라이언트로부터 데이터를 받는다.
        data = request.get_json()
        # print(data)

        # json_array = data["className"]
        # class_list = []

        # for item in json_array:
        #     class_info = {"nurseryId":data["nurseryId"], "className":item}
        #     print(class_info)

        #     "nurseryId": 1,
        #    "className": [
        #        "개미반",
        #        "베짱이반",
        #        "참새반"
        #   ]
            
            #2. DB에 이미 반 정보가 있는지 확인한다.
        try:
            connection = get_connection()
            query = '''select * from class 
                    where nurseryId = %s and className = %s;'''
            record = (nurseryId, data["className"])
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query,record)

            result_list = cursor.fetchall()

            print(result_list)

            if len(result_list) == 1:
                return {'result':'fail','error':'이미 등록한 원'}, 400

            
            # 등록 원이 아니므로 등록 코드 작성
            # DB에 저장
            query = '''insert into class (nurseryId, className)
                    values (%s, %s);'''
            record = (nurseryId, data["className"])
            cursor = connection.cursor()
            cursor.execute(query,record)

            connection.commit()

            user_id = cursor.lastrowid

            cursor.close()
            connection.close()

        except Error as e:
            print(e)
            return {'result':'fail','error': str(e)}, 500

        return {'result' :'success'}

class SettingClassViewResource(Resource) :

    @jwt_required()
    def get(self, id):

        try:
            connection = get_connection()
            query = '''select * from class 
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
         # 가공이 필요하면 가공한다. 
        i = 0
        for row in result_list :
            result_list[i]['createdAt']= row['createdAt'].isoformat()
            result_list[i]['updatedAt']= row['updatedAt'].isoformat()
            i = i + 1

        return {'result':'success', 'items':result_list}

class SettingClassListResource(Resource) :

    @jwt_required()
    def get(self):

        teacherId = get_jwt_identity()

        try:
            connection = get_connection()
            query = '''select c.id,className
                    from class c
                    left join teacher t
                    on t.nurseryId = c.nurseryId
                    where t.id = %s;'''
            record = (teacherId, )
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)
            result_list = cursor.fetchall()
            cursor.close()
            connection.close()

        except Error as e:
            print(e)
            return{'result':'fail', 'error':str(e)}, 400
        
        print(result_list)
         # 가공이 필요하면 가공한다. 

        return {'items':result_list}
    
class SettingNurseryClassListResource(Resource):
    @jwt_required()
    def get(self,nurseryId):

        try:
            connection = get_connection()
            query = '''select id,className
                    from class 
                    where nurseryId = %s;'''
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
         # 가공이 필요하면 가공한다. 

        return {'items':result_list}


class SettingClassEditResource(Resource) :

    @jwt_required()
    def put(self, id):

        data = request.get_json()

        try :
            # 1) 데이터베이스 연결
            connection = get_connection()

            query = '''update class
                        set nurseryId = %s, className = %s
                        where id = %s;'''
            
            record = (data['nurseryId'],data['className'], id)
            
            cursor = connection.cursor()
            cursor.execute(query, record)
            connection.commit()
            cursor.close()
            connection.close()

        except Error as e :  
            print(e)
            return { 'result' : 'fail', 'error' : str(e) }, 500


        return {'result' :'success'}

class SettingClassDeleteResource(Resource) :

    @jwt_required()
    def delete(self, id):

        try : 
            connection = get_connection()
            query = '''delete from class
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

        return {'result' : '등록 정보가 삭제되었습니다'}




# 원 생성

class SettingNurseryResource(Resource) :

    @jwt_required() 
    def post(self):

        data = request.get_json()

        try:
            connection = get_connection()
            query = '''select * from nursery 
                        where nurseryName = %s and nurseryAddress = %s;'''
            record = (data['nurseryName'], data['nurseryAddress'])
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query,record)
            result_list = cursor.fetchall()
            print(result_list)

            if len(result_list) > 0:
                return {'result':'fail','error':'이미 등록한 원'}, 400

            
            # 등록 원이 아니므로 등록 코드 작성, DB에 저장
            query =  '''insert into nursery (nurseryName, nurseryAddress)
                    values (%s, %s);'''
            record = (data['nurseryName'],data['nurseryAddress'])
            cursor = connection.cursor()
            cursor.execute(query,record)
            connection.commit()

            nursery_id = cursor.lastrowid

            try:
                s3 = boto3.client('s3', 
                                    aws_access_key_id =  Config.AWS_ACCESS_KEY_ID,
                                    aws_secret_access_key = Config.AWS_SECRET_ACCESS_KEY)
                nursery_id_str = str(nursery_id)
                folder_name = nursery_id_str+'_'+data['nurseryName']
                bucket_name = Config.S3_BUCKET

                s3.put_object(Bucket=bucket_name, Key=(folder_name + '/'))
                s3.put_object(Bucket=bucket_name, Key=(folder_name + '/photo_album/'))
                s3.put_object(Bucket=bucket_name, Key=(folder_name + '/profile/'))
                s3.put_object(Bucket=bucket_name, Key=(folder_name + '/menu/'))


            except Exception as e:
                print(str(e))
                return{'Result':'Setting','Error':str(e)}, 500

            cursor.close()
            connection.close()
          


        except Error as e:
            print(e)
            return {'result':'fail','error': str(e)}, 500
        return {'result' :'success'}

class SettingNurseryViewResource(Resource) :

    @jwt_required()
    def get(self, id):

        try:
            connection = get_connection()
            query = '''select * from nursery 
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

        return {'result':'success', 'items':result_list}

class SettingNurseryEditResource(Resource) :

    @jwt_required()
    def put(self, id):

        data = request.get_json()

        try :
            # 1) 데이터베이스 연결
            connection = get_connection()

            query = '''update nursery
                        set nurseryName = %s, nurseryAddress = %s
                        where id = %s;'''
            
            record = (data['nurseryName'],data['nurseryAddress'], id)
            
            cursor = connection.cursor()
            cursor.execute(query, record)
            connection.commit()
            cursor.close()
            connection.close()

        except Error as e :  
            print(e)
            return { 'result' : 'fail', 'error' : str(e) }, 500


        return {'result' :'success'}

class SettingNurseryDeleteResource(Resource) :

    @jwt_required()
    def delete(self, id):

        try : 
            connection = get_connection()
            query = '''delete from nursery
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

        return {'result' : '등록 정보가 삭제되었습니다'}




# 원아 관리

class SettingChildViewResource(Resource) :

    @jwt_required()
    def get(self, id):

        try:
            connection = get_connection()
            query = '''select * from children
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
            result_list[i]['birth']= row['birth'].isoformat()
            i = i + 1

        return {'result':'success', 'items':result_list}

class SettingChildrenListResource(Resource) :

    @jwt_required()
    def get(self, classId):

        try:
            connection = get_connection()
            query = '''select * from children 
                    where classId = %s;'''
            record = (classId, )
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
            result_list[i]['birth']= row['birth'].isoformat()
            i = i + 1

        return {'result':'success','items':result_list}
    
class SettingTeachersChildrenListResource(Resource):
    @jwt_required()
    def get(self):

        teacherId = get_jwt_identity()

        try:
            connection = get_connection()
            query = '''select c.id,childName
                    from children c
                    left join teacher t
                    on t.classId = c.classId
                    where t.id = %s;'''
            record = (teacherId, )
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)
            result_list = cursor.fetchall()
            cursor.close()
            connection.close()

        except Error as e:
            print(e)
            return{'result':'fail', 'error':str(e)}, 400
        
        print(result_list)
         # 가공이 필요하면 가공한다. 

        return {'items':result_list}


class SettingAllChildrenListResource(Resource) :

    @jwt_required()
    def get(self, nurseryId):

        try:
            connection = get_connection()
            query = '''select * from children
                    where nurseryId = %s;'''
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
            result_list[i]['birth']= row['birth'].isoformat()
            i = i + 1

        return {'result':'success', 'item count':len(result_list), 'items':result_list}

class SettingChildDeleteResource(Resource) :

    @jwt_required()
    def delete(self, id):

        try : 
            connection = get_connection()
            query = '''delete from children
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

        return {'result' : '원아 정보가 삭제되었습니다'}

class SettingChildEditResource(Resource) :

    @jwt_required()
    def put(self, id):

        file = request.files['profileUrl']
        data = json.loads(request.form['childData'])
        teacherId = get_jwt_identity()

        try:
            # 3-1. 데이터베이스를 연결한다.
            connection = get_connection()

            print(teacherId)

            query = '''SELECT classId, nurseryId, nurseryName FROM nursery n left join teacher t on n.id = t.nurseryId where t.id = %s;'''
            record = (teacherId, )
            cursor = connection.cursor()
            cursor.execute(query,record)
            teacher_result_list = cursor.fetchall()
            urlNurseryId = str(teacher_result_list[0][1])
            urlNurseryName = teacher_result_list[0][2]
            print(urlNurseryId, urlNurseryName, teacher_result_list)

            # 3-2. 쿼리문 만든다
            query = '''select * from children
                    where id = %s;'''
            record = (id, )
            #3-4 커서를 가져온다
            cursor = connection.cursor()
            #3-5 쿼리문을,커서로 실행한다.
            cursor.execute(query,record)
            result_list = cursor.fetchall()

            data = json.loads(request.form['childData'])
            print(data['childName'])
            print(result_list[0][6])

            if result_list[0][6] == "" or 'profileUrl' in request.files :
                file = request.files['profileUrl']

                try:
                    current_time = datetime.now().isoformat().replace(':','').replace('.','').replace('-','')[:14]
                    new_filename = current_time+'_'+data['childName']+'.jpg'

                    s3 = boto3.client('s3',
                            aws_access_key_id =  Config.AWS_ACCESS_KEY_ID,
                            aws_secret_access_key = Config.AWS_SECRET_ACCESS_KEY)  
                    s3.upload_fileobj(file,
                                    Config.S3_BUCKET,
                                    new_filename,
                                    ExtraArgs = {'ACL':'public-read', 'ContentType':'image/jpeg'})
                except Exception as e:
                    print(str(e))
                    return{'result':'fail','error':str(e)},500
                file_url = Config.S3_BASE_URL+urlNurseryId+'/profile/'+new_filename 
            
            else: 
                file_url = result_list[0][6]


            # 3-2. 쿼리문 만든다
            query = '''update children
                    set childName = %s, birth = %s, sex = %s, profileUrl = %s
                    where id = %s;'''
            record = (data['childName'],data['birth'],data['sex'], file_url, id)
            #3-4 커서를 가져온다
            cursor = connection.cursor()
            #3-5 쿼리문을,커서로 실행한다.
            cursor.execute(query,record)
            #3-6 DB 반영 완료하라는, commit 해줘야한다.
            connection.commit()
            #3-7. 자원해제
            cursor.close()
            connection.close()

        except Error as e :
            print(e)
            return {'result':'fail','error': str(e)}, 500

        return {'result':'success'}

class SettingChildrenResource(Resource) :

    @jwt_required()
    def post(self):

        # # 사진이 필수인 경우의 코드
        # if 'profileUrl' not in request.files or 'childName' not in request.form or 'birth' not in request.form or 'sex' not in request.form: # 두 줄로 하고싶으면 \ (역슬래시) 이용해라
        #     return{'result':'fail','error':'필수항목 확인'},400
        # 유저가 올린 파일을 변수로 만든다
        file = request.files['profileUrl']
        data = json.loads(request.form['childData'])
        teacherId = get_jwt_identity()
        print(data['childName'])
        try:
            # 3-1. 데이터베이스를 연결한다.
            connection = get_connection()

            query = '''SELECT classId, nurseryId, nurseryName FROM nursery n left join teacher t on n.id = t.nurseryId where t.id = %s;'''
            record = (teacherId, )
            cursor = connection.cursor()
            cursor.execute(query,record)
            teacher_result_list = cursor.fetchall()

            # {
            #     "childName": "김철수",
            #     "birth": "2010-07-14",
            #     "sex": 1
            # }
            # + profileUrl
       
            try:
                current_time = datetime.now().isoformat().replace(':','').replace('.','').replace('-','')[:7]
                urlNurseryId = str(teacher_result_list[0][1])               
                urlNurseryName = teacher_result_list[0][2]

                new_filename = urlNurseryId +'_'+ urlNurseryName + '/profile/' + data['birth'] + '_' + data['childName'] + '_' + current_time + '.jpg'

                s3 = boto3.client('s3',
                        aws_access_key_id =  Config.AWS_ACCESS_KEY_ID,
                        aws_secret_access_key = Config.AWS_SECRET_ACCESS_KEY)  
                s3.upload_fileobj(file,
                                Config.S3_BUCKET,
                                new_filename,
                                ExtraArgs = {'ACL':'public-read', 'ContentType':'image/jpeg'})
            except Exception as e:
                print(str(e))
                return{'result':'fail','error':str(e)},500
            
            file_url = Config.S3_BASE_URL + new_filename

            query = '''insert into children
                    (classId, nurseryId, childName, birth, sex, profileUrl)
                    values
                    (%s, %s, %s, %s, %s, %s);'''
            record = (teacher_result_list[0][0], teacher_result_list[0][1], data['childName'], data['birth'], data['sex'], file_url)
            print(record)
            cursor = connection.cursor()
            cursor.execute(query,record)
            connection.commit()
            cursor.close()
            connection.close()

        except Error as e :
            print(e)
            return {'result':'fail','error': str(e)}, 500


        return {'result':'success'}
class SettingChildrenAddResource(Resource):

    @jwt_required()
    def post(self,classId):

        data = request.get_json()
        id = get_jwt_identity()

        try:
            connection = get_connection()

            query = '''select nurseryId from teacher
                    where id = %s;'''
            record = (id, )
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)
            result_one = cursor.fetchone()
            print(result_one)
            nurseryId = result_one['nurseryId']


            query1 = '''insert into children (classId,nurseryId,childName,birth,sex) values (%s,%s,%s,%s,%s);'''
            record1 = (classId, nurseryId,data["childName"],data["birth"], data["sex"])
            cursor1 = connection.cursor()
            cursor1.execute(query1,record1)
            connection.commit()

            cursor.close()
            cursor1.close()
            connection.close()

        except Error as e:
            print(e)
            return {'result':'fail','error': str(e)}, 500

        return {'result' :'success'}
    

class SettingChildrenPhotoAddResource(Resource):

    @jwt_required()
    def put(self, id):

        # 1. 헤더에 담긴 JWT 토큰을 받아온다.
        teacherId = get_jwt_identity()

        # 원아 아이디 : id

        # 사진이 필수인 경우의 코드
        if 'profileUrl' not in request.files :  # 이건 이상한경우니까
            return {  'result' : 'fail', 'error' : '파일없음'  }, 400

        # 유저에게 프로필 사진을 입력받는다.
        file = request.files['profileUrl']

        try:
            # 3-1. 데이터베이스를 연결한다.
            connection = get_connection()
            query = '''SELECT classId, nurseryId, nurseryName FROM nursery n left join teacher t on n.id = t.nurseryId where t.id = %s;'''
            record = (teacherId, )
            cursor = connection.cursor()
            cursor.execute(query,record)
            teacher_result_list = cursor.fetchall()
            print('* teacher_result_list : ', teacher_result_list)

            query = '''SELECT birth,childName FROM children where id = %s;'''
            record = (id, )
            cursor = connection.cursor()
            cursor.execute(query,record)
            children_result_list = cursor.fetchall()
            
            current_time = datetime.now().isoformat().replace(':','').replace('.','').replace('-','')[:7]

            urlNurseryName = teacher_result_list[0][2]
            birth = children_result_list[0][0].isoformat()
            urlNurseryId = str(teacher_result_list[0][1])
            print('* 원 아이디 urlNurseryId : ', urlNurseryId) 
            class_id = str(teacher_result_list[0][0])
            print('* 반 아이디 cladd_id : ', class_id)
            childName = children_result_list[0][1]
            print('* 원아 이름 childName : ', childName) 


            # 로컬에 사진 먼저 저장
            # 사진 이름 형식 : 원아이디_반아이디.원아아이디.원아이름.jpg (예 : 1_1.14.이채은.jpg)
            img_file = file
            filename = urlNurseryId + '_' + class_id + '.' + str(id) + '.' + childName + '.jpg'
            print('* 업로드 파일 이름 filename : ', filename)
            save_uploaded_file2('profileUrl_image', img_file, filename)


            # 버킷에 저장
            new_filename = urlNurseryId +'_'+ urlNurseryName + '/profile/' + birth + '_' + childName + '_' + current_time + '.jpg'
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
                query = '''update children
                            set profileUrl = %s where id = %s;'''
                    
                record = (file_url,id)
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

    
class SettingNurseryListResource(Resource):

    @jwt_required()
    def get(self):

        try:
            connection = get_connection()
            query = '''select id, nurseryName, nurseryAddress from nursery;'''
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, )
            result_list = cursor.fetchall()
            cursor.close()
            connection.close()

        except Error as e:
            print(e)
            return{'result':'fail', 'error':str(e)}, 400
        
        print(result_list)

        return {'result':'success', 'items':result_list}


