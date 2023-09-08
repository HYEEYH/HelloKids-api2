from flask_restful import Resource
from flask import request
import mysql.connector
from mysql.connector import Error
from mysql_connection import get_connection
from utils import check_password, hash_password
from email_validator import validate_email,EmailNotValidError 
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity, jwt_required

# import requests
# import googlemaps
# import json



# 안심 등하원 - 차량 삭제
class SchoolBusDeleteResource(Resource):

    # @jwt_required()
    def delete(self, id):

        print(id)

        # 1. 헤더에 담긴 JWT 토큰을 받아온다.


        # 2. DB에서 삭제한다
        try : 
            connection = get_connection()
            query = '''delete from schoolBus
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
        
        return {'result' : '차량 정보가 삭제되었습니다'}

# 안심 등하원 - 차량 추가
class SchoolBusResource(Resource) :

    #### 안심등하원 - 차량 추가
    @jwt_required()
    def post(self):
        # 포스트로 요청한 것을 처리하는 코드 작성을 우리가!
        # 1. 클라이언트가 보낸 데이터를 받아온다.
        teacherId = get_jwt_identity()
        data = request.get_json()
        # 2. DB에 저장한다.
        try:
            # 2-1. 데이터베이스를 연결한다.
            connection = get_connection()

            # 2-2. 쿼리문 만든다
            ###### 중요! 컬럼과 매칭되는 데이터만 %s로 바꿔준다.
            query = '''insert into schoolBus
                    (teacherId,shuttleName,shuttleNum,shuttleTime,shuttleDriver,shuttleDriverNum)
                    values
                    (%s,%s,%s,%s,%s,%s);'''
            #2-3. 쿼리에 매칭되는 변수 처리! 중요! 튜플로 처리해준다!(튜프은 데이터변경이 안되니까?)
            # 위의 %s부분을 만들어주는거다
            record = (teacherId,data['shuttleName'],data['shuttleNum'], data['shuttleTime'],data['shuttleDriver'],data['shuttleDriverNum'])
            #2-4 커서를 가져온다
            cursor = connection.cursor()
            #2-5 쿼리문을,커서로 실행한다.
            cursor.execute(query,record)
            #2-6 DB 반영 완료하라는, commit 해줘야한다.
            connection.commit()
            #2-7. 자원해제
            cursor.close()
            connection.close()

        except Error as e :
            print(e)
            return {'result':'fail','error': str(e)}, 500
            # 상태코드 에러에 맞게 내가 설계한다
        return{'result': 'success'} 

# 안심 등하원 - 차량 수정    
class SchoolBusEditResource(Resource):

    @jwt_required()
    def put(self,id):

        #body에 있는 json 데이터를 받아온다.
        data = request.get_json()
       
        #2. 데이터베이스에 update한다.
        try :
            connection = get_connection()
            query = '''update schoolBus
                    set shuttleName = %s, shuttleNum = %s, shuttleTime = %s, shuttleDriver = %s, shuttleDriverNum = %s
                    where id = %s;''' 
            record = (data['shuttleName'],data['shuttleNum'], data['shuttleTime'],data['shuttleDriver'],data['shuttleDriverNum'],id) 
            cursor= connection.cursor()
            cursor.execute(query,record)
            connection.commit()

            cursor.close()
            connection.close()

        except Error as e:
            print(e)
            return {'result': 'fail','error': str(e)},500
        
        return {'result': 'success'} 

# 안심등하원 - 인솔교사 지정을 위한 교사 리스트(어린이집 별 선생님 목록)
class SchoolBusTeacherListResource(Resource):
    @jwt_required()
    def get(self):

        id = get_jwt_identity()

        try : 

            connection = get_connection()

            query = '''select nurseryId from teacher
                    where id = %s;'''
            record = (id, )
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)
            result_one = cursor.fetchone()
            print(result_one)
            nurseryId = result_one['nurseryId']

            query1 ='''select id,teacherName
                    from teacher
                    where nurseryId = %s;'''
            
            record1 = (nurseryId,)

        # 커서 가져온다
            cursor1 = connection.cursor(dictionary= True)

        # 쿼리문을 커서로 실행한다.
            cursor1.execute(query1,record1)

        # 실행 결과를 가져온다.
            result_list = cursor1.fetchall()

            cursor.close()
            cursor1.close()
            connection.close()

        except Error as e :
            print(e)
            return { 'result' : 'fail', 'error' : str(e)}, 500

        # # - 에러 안났을때 코드
        return { 'result' : 'success',
                'count': len(result_list),
                'items': result_list }, 200  # 200은 안써도 됨.

# 안심등하원 - 인솔교사 등록
class SchoolBusTeacherAddResource(Resource):
    @jwt_required()
    def put(self, id):
        #body에 있는 json 데이터를 받아온다.
        data = request.get_json()
       
        #2. 데이터베이스에 update한다.
        try :
            connection = get_connection()

            query = '''update schoolBusDriveRecord
                    set shuttleTeacherId = %s
                    where id = %s;''' 
            record = (data['shuttleTeacherId'],id) 
            cursor= connection.cursor()
            cursor.execute(query,record)
            connection.commit()

            cursor.close()
            connection.close()

        except Error as e:
            print(e)
            return {'result': 'fail','error': str(e)},500
        
        return {'result': 'success'} 
    
# 안심등하원 - 어린이집별 차량 조회
class SchoolBusNurseryListResource(Resource):

    @jwt_required()
    def get(self):
        
        id = get_jwt_identity()
    
        try : 
            connection = get_connection()
            query = '''select nurseryId from teacher
                    where id = %s;'''
            record = (id, )
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)
            result_one = cursor.fetchone()
            print(result_one)
            nurseryId = result_one['nurseryId']

            query1 ='''select s.id, shuttleName,shuttleNum,shuttleTime,shuttleDriver,shuttleDriverNum from schoolBus s
                    join teacher t
                    on s.teacherId = t.id
                    where t.nurseryId = %s;'''
            
            record1 = (nurseryId, )

        # 커서 가져온다
            cursor1 = connection.cursor(dictionary= True)

        # 쿼리문을 커서로 실행한다.
            cursor1.execute(query1, record1)

        # 실행 결과를 가져온다.
            result_list = cursor1.fetchall()

            print(result_list) 
          
            cursor.close()
            cursor1.close()
            connection.close()

        except Error as e :
            print(e)
            return { 'result' : 'fail', 'error' : str(e)}, 500


        ### 3. 데이터 가공이 필요하면 가공한 후 
        ###     클라이이언트에 응답한다.
        # - 데이터 가공하기 
        # - JSON 으로 변환할때 daytime 형식때문에 자꾸 오류가 남.
        # - created_at, updated_at의 형식을 문자열 형식으로 바꿔줘야함.

        i = 0
        for row in result_list :
            # print(row) # 서버 내렸다가 다시 돌리고 포스트맨에서 send눌러봄 -> row는 딕셔너리
            result_list[i]['shuttleTime'] = row['shuttleTime'].isoformat()
            i = i + 1


        # # - 에러 안났을때 코드
        return { 'result' : 'success',
                'count': len(result_list),
                 'items': result_list }, 200  # 200은 안써도 됨.
# 안심등하원 - 차량 정보 상세 보기
class SchoolBusViewResource(Resource):
    @jwt_required()
    def get(self, id):

        try : 
            connection = get_connection()

            query ='''select shuttleName,shuttleNum,shuttleTime,shuttleDriver,shuttleDriverNum from schoolBus
                    where id = %s;'''
            
            record = (id, )

        # 커서 가져온다
            cursor = connection.cursor(dictionary= True)

        # 쿼리문을 커서로 실행한다.
            cursor.execute(query, record)

        # 실행 결과를 가져온다.
            result_list = cursor.fetchall()

            cursor.close()
            connection.close()

        except Error as e :
            print(e)
            return { 'result' : 'fail', 'error' : str(e)}, 500
        
        i = 0
        for row in result_list :
            # print(row) # 서버 내렸다가 다시 돌리고 포스트맨에서 send눌러봄 -> row는 딕셔너리
            result_list[i]['shuttleTime'] = row['shuttleTime'].isoformat()
            i = i + 1


        return { 'result' : 'success',
                'count': len(result_list),
                 'items': result_list }, 200  # 200은 안써도 됨.

# 차량 운행 기록 등록
class SchoolBusDriveAddResource(Resource):
     @jwt_required()
     def post(self):
         # 포스트로 요청한 것을 처리하는 코드 작성을 우리가!
        # 1. 클라이언트가 보낸 데이터를 받아온다.
        data = request.get_json()
        teacherId = get_jwt_identity()

        # 2. DB에 저장한다.
        try:
            # 2-1. 데이터베이스를 연결한다.
            connection = get_connection()
            query = '''select nurseryId from teacher
                    where id = %s;'''
            record = (teacherId, )
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)
            result_one = cursor.fetchone()
            print(result_one)
            nurseryId = result_one['nurseryId']

            query1 = '''insert into schoolBusDailyRecord
                    (shuttleTeacherId,nurseryId,schoolbusId)
                    values
                    (%s,%s,%s);'''
            #2-3. 쿼리에 매칭되는 변수 처리! 중요! 튜플로 처리해준다!(튜프은 데이터변경이 안되니까?)
            # 위의 %s부분을 만들어주는거다
            record1 = (data['shuttleTeacherId'],nurseryId,data['schoolbusId'])
            #2-4 커서를 가져온다
            cursor1 = connection.cursor()
            #2-5 쿼리문을,커서로 실행한다.
            cursor1.execute(query1,record1)
            #2-6 DB 반영 완료하라는, commit 해줘야한다.
            connection.commit()
            #2-7. 자원해제
            cursor.close()
            cursor1.close()
            connection.close()

        except Error as e :
            print(e)
            return {'result':'fail','error': str(e)}, 500
            # 상태코드 에러에 맞게 내가 설계한다
        return{'result': 'success'} 

# 운행시작,운행종료 시간 입력
class SchoolBusDriveTimeResource(Resource):
     @jwt_required()
     def post(self,id):
         # 포스트로 요청한 것을 처리하는 코드 작성을 우리가!
        # 1. 클라이언트가 보낸 데이터를 받아온다.
        data = request.get_json()
        # 2. DB에 저장한다.
        try:
            # 2-1. 데이터베이스를 연결한다.
            connection = get_connection()

            # 2-2. 쿼리문 만든다
            ###### 중요! 컬럼과 매칭되는 데이터만 %s로 바꿔준다.
            query = '''update schoolBusDailyRecord
                    set shuttleStart = %s, shuttleStop = %s
                    where id = %s;'''
            #2-3. 쿼리에 매칭되는 변수 처리! 중요! 튜플로 처리해준다!(튜프은 데이터변경이 안되니까?)
            # 위의 %s부분을 만들어주는거다
            record = (data['shuttleStart'],data['shuttleStop'],id)
            #2-4 커서를 가져온다
            cursor = connection.cursor()
            #2-5 쿼리문을,커서로 실행한다.
            cursor.execute(query,record)
            #2-6 DB 반영 완료하라는, commit 해줘야한다.
            connection.commit()
            #2-7. 자원해제
            cursor.close()
            connection.close()

        except Error as e :
            print(e)
            return {'result':'fail','error': str(e)}, 500
            # 상태코드 에러에 맞게 내가 설계한다
        return{'result': 'success'} 
# 차량 운행 기록 수정
class SchoolBusDriveEditResource(Resource):
    @jwt_required()
    def put(self,id):
         # 포스트로 요청한 것을 처리하는 코드 작성을 우리가!
        # 1. 클라이언트가 보낸 데이터를 받아온다.
        data = request.get_json()
        # 2. DB에 저장한다.
        try:
            # 2-1. 데이터베이스를 연결한다.
            connection = get_connection()

            # 2-2. 쿼리문 만든다
            ###### 중요! 컬럼과 매칭되는 데이터만 %s로 바꿔준다.
            query = '''update schoolBusDailyRecord
                    set shuttleStart = %s, shuttleStop = %s
                    where id = %s;'''
            #2-3. 쿼리에 매칭되는 변수 처리! 중요! 튜플로 처리해준다!(튜프은 데이터변경이 안되니까?)
            # 위의 %s부분을 만들어주는거다
            record = (data['shuttleStart'],data['shuttleStop'],id)
            #2-4 커서를 가져온다
            cursor = connection.cursor()
            #2-5 쿼리문을,커서로 실행한다.
            cursor.execute(query,record)
            #2-6 DB 반영 완료하라는, commit 해줘야한다.
            connection.commit()
            #2-7. 자원해제
            cursor.close()
            connection.close()

        except Error as e :
            print(e)
            return {'result':'fail','error': str(e)}, 500
            # 상태코드 에러에 맞게 내가 설계한다
        return{'result': 'success'} 
# 차량 운행 기록 조회
class SchoolBusDriveViewResource(Resource):
    @jwt_required()
    def get(self, id):

        try : 
            connection = get_connection()

            query ='''select * 
                    from schoolBusDailyRecord
                    where id = %s;'''
            
            record = (id, )

        # 커서 가져온다
            cursor = connection.cursor(dictionary= True)

        # 쿼리문을 커서로 실행한다.
            cursor.execute(query, record)

        # 실행 결과를 가져온다.
            result_list = cursor.fetchall()

            cursor.close()
            connection.close()

        except Error as e :
            print(e)
            return { 'result' : 'fail', 'error' : str(e)}, 500
        
        i = 0
        for row in result_list :
            # print(row) # 서버 내렸다가 다시 돌리고 포스트맨에서 send눌러봄 -> row는 딕셔너리
            result_list[i]['shuttleStart'] = row['shuttleStart'].isoformat()
            result_list[i]['shuttleStop'] = row['shuttleStop'].isoformat()
            result_list[i]['createdAt'] = row['createdAt'].isoformat()
            result_list[i]['updatedAt'] = row['updatedAt'].isoformat()
            i = i + 1


        return { 'result' : 'success',
                'count': len(result_list),
                 'items': result_list }, 200  # 200은 안써도 됨.
# 차량 운행 기록 목록 조회
class SchoolBusDriveListResource(Resource):
     # @jwt_required()
    def get(self):

        # 데이터베이스에 저장되어있는 차량운행정보 가져오기
        # 자바 캘린더에서 요일을 숫자로 표현하는법 :
        #    int dayOfWeekNumber = dayOfWeek.getValue();
        #    DayOfWeek의 getValue() 메소드를 이용하면 요일을 숫자로 가져올 수 있습니다. 
        #    일요일부터 토요일까지 1~7의 숫자로 표현됩니다. 
        #    일요일 1, 월요일2,.... 토요일7
        try : 
            connection = get_connection()

            query ='''select sc.id,sc.shuttleTeacherId,sc.schoolbusId,shuttleName,shuttleStart,shuttleStop
                    from schoolBusDailyRecord sc
                    LEFT JOIN
                    schoolBus s
                    ON
                    sc.schoolbusId = s.id;'''

        # 커서 가져온다
            cursor = connection.cursor(dictionary= True)

        # 쿼리문을 커서로 실행한다.
            cursor.execute(query)

        # 실행 결과를 가져온다.
            result_list = cursor.fetchall()

            cursor.close()
            connection.close()

        except Error as e :
            print(e)
            return { 'result' : 'fail', 'error' : str(e)}, 500
        

        i = 0
        for row in result_list :
            # print(row) # 서버 내렸다가 다시 돌리고 포스트맨에서 send눌러봄 -> row는 딕셔너리
            result_list[i]['shuttleStart'] = row['shuttleStart'].isoformat()
            result_list[i]['shuttleStop'] = row['shuttleStop'].isoformat()
            i = i + 1



        # # - 에러 안났을때 코드
        return { 'result' : 'success',
                'count': len(result_list),
                 'items': result_list }, 200  # 200은 안써도 됨.
# 오늘 운행 기록이 있는 차량 정보 조회   
class SchoolBusDriveTodayListResource(Resource):
    @jwt_required()
    def get(self, createdAt):

        parentsId = get_jwt_identity() 

        try : 
            connection = get_connection()
            query = '''select n.id
                    from nursery n
                    join parents p
                    on p.nurseryName = n.nurseryName
                    where p.id = %s;'''
            record = (parentsId, )
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)
            result_one = cursor.fetchone()
            print(result_one)
            nurseryId = result_one['id']

            query1 = '''select sc.id, shuttleName,shuttleNum,shuttleTime,shuttleDriver,shuttleDriverNum 
                    from schoolBus s
                    join schoolBusDailyRecord sc
                    on sc.schoolbusId = s.id
                    where LEFT(sc.createdAt, 10) = %s and nurseryId = %s;'''
            
            record1 = (createdAt,nurseryId)

        # 커서 가져온다
            cursor1 = connection.cursor(dictionary= True)

        # 쿼리문을 커서로 실행한다.
            cursor1.execute(query1, record1)

        # 실행 결과를 가져온다.
            result_list = cursor1.fetchall()

            cursor.close()
            cursor1.close()
            connection.close()

        except Error as e :
            print(e)
            return { 'result' : 'fail', 'error' : str(e)}, 500
        
        i = 0
        for row in result_list :
            # print(row) # 서버 내렸다가 다시 돌리고 포스트맨에서 send눌러봄 -> row는 딕셔너리
            result_list[i]['shuttleTime'] = row['shuttleTime'].isoformat()
            i = i + 1

        return { 'result' : 'success',
                'count': len(result_list),
                 'items': result_list }, 200  # 200은 안써도 됨.

# 탑승자 리스트
class SchoolBusBoardingListResource(Resource):
    @jwt_required()
    def get(self, id):

        try : 
            connection = get_connection()

            query ='''select c.id,childName
                    from boardingRecord b
                    LEFT JOIN
                    children c
                    ON
                    b.childId = c.id
                    where dailyRecordId= %s;'''
            record = (id, )

        # 커서 가져온다
            cursor = connection.cursor(dictionary= True)

        # 쿼리문을 커서로 실행한다.
            cursor.execute(query, record)

        # 실행 결과를 가져온다.
            result_list = cursor.fetchall()

            cursor.close()
            connection.close()

        except Error as e :
            print(e)
            return { 'result' : 'fail', 'error' : str(e)}, 500
        
        return {'items': result_list }, 200  # 200은 안써도 됨.
    
# 탑승신청 - 학부모화면 
class SchoolBusBoardingAddResource(Resource):
    @jwt_required()
    def post(self, id):
         # 포스트로 요청한 것을 처리하는 코드 작성을 우리가!
        # 1. 클라이언트가 보낸 데이터를 받아온다.
        parentId = get_jwt_identity()
        # 2. DB에 저장한다.
        try:
            # 2-1. 데이터베이스를 연결한다.
            connection = get_connection()
            query = '''select childId from parents
                    where id = %s;'''
            record = (parentId, )
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query,record)
            result_one = cursor.fetchone()
            print(result_one)
            childId = result_one['childId']

            
            # 2-2. 쿼리문 만든다
            ###### 중요! 컬럼과 매칭되는 데이터만 %s로 바꿔준다.
            query1 = '''insert into boardingRecord
                    (dailyRecordId,childId)
                    values (%s, %s);'''
            #2-3. 쿼리에 매칭되는 변수 처리! 중요! 튜플로 처리해준다!(튜프은 데이터변경이 안되니까?)
            # 위의 %s부분을 만들어주는거다
            record1 = (id,childId)
            # {
            #     'shuttleInOk':1;
            # }
            #2-4 커서를 가져온다
            cursor1 = connection.cursor()
            #2-5 쿼리문을,커서로 실행한다.
            cursor1.execute(query1,record1)
            #2-6 DB 반영 완료하라는, commit 해줘야한다.
            connection.commit()
            #2-7. 자원해제
            cursor.close()
            cursor1.close()
            connection.close()

        except Error as e :
            print(e)
            return {'result':'fail','error': str(e)}, 500
            # 상태코드 에러에 맞게 내가 설계한다
        return{'result': 'success'} 
    
# 탑승취소 - 학부모화면
class SchoolBusBoardingDeleteResource(Resource):
    @jwt_required()
    def delete(self, id):

        # 2. DB에서 삭제한다
        try : 
            connection = get_connection()
            query = '''delete from boardingRecord
                        where dailyRecordId = %s;'''
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
        
        return {'result' : '탑승이 취소되었습니다.'}

# 승하차 시간 체크 - 선생님 화면
class SchoolBusBoardingTimeResource(Resource):
    @jwt_required()
    def put(self,id):
         # 포스트로 요청한 것을 처리하는 코드 작성을 우리가!
        # 1. 클라이언트가 보낸 데이터를 받아온다.
        data = request.get_json()
        # 2. DB에 저장한다.
        try:
            # 2-1. 데이터베이스를 연결한다.
            connection = get_connection()

            # 2-2. 쿼리문 만든다
            ###### 중요! 컬럼과 매칭되는 데이터만 %s로 바꿔준다.
            query = '''update boardingRecord
                    set shuttleChidIn = %s, shuttleChildOut = %s
                    where dailyRecordId = %s and childId = %s;'''
            #2-3. 쿼리에 매칭되는 변수 처리! 중요! 튜플로 처리해준다!(튜프은 데이터변경이 안되니까?)
            # 위의 %s부분을 만들어주는거다
            record = (data['shuttleChidIn'],data['shuttleChildOut'],id,data['childId'])
            #2-4 커서를 가져온다S
            cursor = connection.cursor()
            #2-5 쿼리문을,커서로 실행한다.
            cursor.execute(query,record)
            #2-6 DB 반영 완료하라는, commit 해줘야한다.
            connection.commit()
            #2-7. 자원해제
            cursor.close()
            connection.close()

        except Error as e :
            print(e)
            return {'result':'fail','error': str(e)}, 500
            # 상태코드 에러에 맞게 내가 설계한다
        return{'result': 'success'} 

# 해당 운행 차량 실시간 위치 등록(인솔교사의 위치를 사용한다)
class SchoolBusLocationAddResource(Resource):
     #@jwt_required()
     def post(self,id):
         # 포스트로 요청한 것을 처리하는 코드 작성을 우리가!
        # 1. 클라이언트가 보낸 데이터를 받아온다.
        data = request.get_json()
        # 2. DB에 저장한다.
        try:
            # 2-1. 데이터베이스를 연결한다.
            connection = get_connection()

            # 2-2. 쿼리문 만든다
            ###### 중요! 컬럼과 매칭되는 데이터만 %s로 바꿔준다.
            query = '''insert into location
                    (dailyRecordId,lat,lng)
                    values
                    (%s,%s,%s);'''
            #2-3. 쿼리에 매칭되는 변수 처리! 중요! 튜플로 처리해준다!(튜프은 데이터변경이 안되니까?)
            # 위의 %s부분을 만들어주는거다
            record = (id,data['lat'],data['lng'])
            #2-4 커서를 가져온다
            cursor = connection.cursor()
            #2-5 쿼리문을,커서로 실행한다.
            cursor.execute(query,record)
            #2-6 DB 반영 완료하라는, commit 해줘야한다.
            connection.commit()
            #2-7. 자원해제
            cursor.close()
            connection.close()

        except Error as e :
            print(e)
            return {'result':'fail','error': str(e)}, 500
            # 상태코드 에러에 맞게 내가 설계한다
        return{'result': 'success'} 
     
class SchoolBusLocationViewResource(Resource):
    #@jwt_required()
    def get(self, id):

        try : 
            connection = get_connection()

            query ='''select lat,lng
                    from location
                    where dailyRecordId= %s and id = (SELECT max(id) FROM location);'''
            
            record = (id, )

        # 커서 가져온다
            cursor = connection.cursor(dictionary= True)

        # 쿼리문을 커서로 실행한다.
            cursor.execute(query, record)

        # 실행 결과를 가져온다.
            result_list = cursor.fetchall()

            cursor.close()
            connection.close()

        except Error as e :
            print(e)
            return { 'result' : 'fail', 'error' : str(e)}, 500

        return { "items": result_list }, 200  # 200은 안써도 됨.    
     
# class LocationNow(Resource):
#     def get(self):

#         url = f'https://www.googleapis.com/geolocation/v1/geolocate?key=AIzaSyAFlVtXMR1k224QEstsniTQOW0vckiuYbA'
#         data = {
#             'considerIp': False,
#             'wifiAccessPoints': {
#                 'macAddress': 'c8:bd:4d:6d:13:10',
#                 'signalStrength': -35,
#                 'signalToNoiseRatio': 0
#             }
#         }

#         result = requests.post(url, data) # 해당 API에 요청을 보내며 데이터를 추출한다.

#         print(result.text)
#         result2 = json.loads(result.text)

#         lat = result2["location"]["lat"] # 현재 위치의 위도 추출
#         lng = result2["location"]["lng"] # 현재 위치의 경도 추출

#         gmaps = googlemaps.Client('AIzaSyAFlVtXMR1k224QEstsniTQOW0vckiuYbA')
#         reverse_geocode_result = gmaps.reverse_geocode((lat, lng),language='ko')
#         # 좌표값을 이용해 목적지를 알아내는 코드

#         print(lat)
#         print(lng)