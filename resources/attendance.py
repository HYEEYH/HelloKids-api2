from flask_restful import Resource
from flask import request
import mysql.connector
from mysql.connector import Error
from mysql_connection import get_connection
from utils import check_password, hash_password
from email_validator import validate_email,EmailNotValidError 
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity, jwt_required
from datetime import datetime
import boto3
from config import Config
import json

class AttendanceChildrenListResource(Resource) :

    @jwt_required()
    def get(self):

        teacherId = get_jwt_identity()

        try:
            connection = get_connection()
            query = '''select c.classId,className,c.id,childName from children c
                    join teacher t
                    on t.classId = c.classId
                    left join class cl
                    on c.classId = cl.id
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
        

        return {'result':'success', 'count':len(result_list), 'items':result_list}