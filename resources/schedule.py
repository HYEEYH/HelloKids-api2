from flask_restful import Resource
from flask import request
import mysql.connector
from mysql.connector import Error
from mysql_connection import get_connection
from utils import check_password, hash_password
from email_validator import validate_email, EmailNotValidError 
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity, jwt_required
from datetime import datetime
import boto3
from config import Config
import json



class ScheduleAddResource(Resource) :
    
    @jwt_required()
    def post(self):

        data = request.get_json()
        teacherId = get_jwt_identity()
        print(data)

        try:
            connection = get_connection()

            query = '''insert into schedule (classId,teacherId,title,contents,date,selectIcon) values (%s,%s,%s,%s,%s,%s);'''
            record = (data["classId"], teacherId, data["title"], data["contents"], data["date"], data["selectIcon"])
            cursor = connection.cursor()
            cursor.execute(query,record)
            connection.commit()

            cursor.close()
            connection.close()

        except Error as e:
            print(e)
            return {'result':'fail','error': str(e)}, 500

        return {'result' :'success'}

class ScheduleViewResource(Resource) :

    @jwt_required()
    def get(self, id):

        try:
            connection = get_connection()
            query = '''select * from schedule 
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
            result_list[i]['date']= row['date'].isoformat()
            result_list[i]['createdAt']= row['createdAt'].isoformat()
            result_list[i]['updatedAt']= row['updatedAt'].isoformat()
            i = i + 1

        return {'result':'success', 'items':result_list}


class ScheduleChildListResource(Resource) :

    @jwt_required()
    def get(self, id):

        try:
            connection = get_connection()
            query = '''select * from children
                    right join schedule
                    on children.classId = schedule.classId
                    where children.id = %s;'''
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
            result_list[i]['date']= row['date'].isoformat()
            result_list[i]['createdAt']= row['createdAt'].isoformat()
            result_list[i]['updatedAt']= row['updatedAt'].isoformat()
            i = i + 1

        return {'result':'success', 'item count':len(result_list), 'items':result_list}


class ScheduleClassListResource(Resource) :

    @jwt_required()
    def get(self, classId):

        try:
            connection = get_connection()
            query = '''select * from schedule
                        where classId= %s;'''
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
            result_list[i]['date']= row['date'].isoformat()
            result_list[i]['createdAt']= row['createdAt'].isoformat()
            result_list[i]['updatedAt']= row['updatedAt'].isoformat()
            i = i + 1

        return {'result':'success', 'item count':len(result_list), 'items':result_list}

class ScheduleAllListResource(Resource) :

    @jwt_required()
    def get(self):

        teacherId = get_jwt_identity()

        try:
            connection = get_connection()
            query = '''select nurseryId from teacher
                    where id = %s'''
            record = (teacherId, )
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)
            result_one = cursor.fetchone()
            print(result_one)
            nurseryId = result_one['nurseryId']

            query1 = '''select s.id,classId,title,contents,date,selectIcon from schedule s
                        left join class c
                        on s.classId = c.id 
                        where nurseryId = %s;'''
            record1 = (nurseryId, )
            cursor1 = connection.cursor(dictionary=True)
            cursor1.execute(query1, record1)
            result_list = cursor1.fetchall()
            cursor.close()
            cursor1.close()
            connection.close()

        except Error as e:
            print(e)
            return{'result':'fail', 'error':str(e)}, 400
        
        print(result_list)

        i = 0
        for row in result_list :
            result_list[i]['date']= row['date'].isoformat()
            i = i + 1

        return {'result':'success', 'count':len(result_list), 'items':result_list}

class ScheduleEditResource(Resource) :

    @jwt_required()
    def put(self, id):

        data = request.get_json()
        teacherId = get_jwt_identity()

        try :
            connection = get_connection()

            query = '''update schedule
                    set classId = %s, title = %s, contents = %s, date = %s, selectIcon = %s 
                    where id = %s and teacherId = %s'''
            record = (data['classId'],data['title'],data['contents'],data['date'],data['selectIcon'],id,teacherId)
            
            cursor = connection.cursor()
            cursor.execute(query, record)
            connection.commit()
            cursor.close()
            connection.close()

        except Error as e :  
            print(e)
            return { 'result' : 'fail', 'error' : str(e) }, 500


        return {'result' :'success'}

class ScheduleDeleteResource(Resource) :

    @jwt_required()
    def delete(self, id):

        teacherId = get_jwt_identity()

        try : 
            connection = get_connection()
            query = '''delete from schedule
                        where id = %s and teacherId = %s;'''
            record = (id,teacherId)
            cursor = connection.cursor()
            cursor.execute(query, record)
            connection.commit()

            cursor.close()
            connection.close()

        except Error as e:
            print(e)
            return {'result':'fail', 'error':str(e)}

        return {'result' : '등록 정보가 삭제되었습니다'}



