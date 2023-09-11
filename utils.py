# -------------------------------------------------------------
import os
from passlib.hash import pbkdf2_sha256

from config import Config

import boto3
# import logging
# from botocore.exceptions import ClientError
# --------------------------------------------------------------


# 1. 원문 비밀번호를, 단방향 암호화 하는 함수
def hash_password(original_password):
    # original_password는 사용자가 넣은 1234
    password = pbkdf2_sha256.hash(original_password + Config.SALT)# 서버에서 보낸 비번 앞 뒤에 문자열 붙인다 그리고 그상태로 암호화한다
    return password
    
# 2. 유저가 입력한 비번이 맞는지 체크하는 함수
def check_password(original_password, hashed_password) :
    check = pbkdf2_sha256.verify(original_password + Config.SALT,hashed_password)
    return check # true냐 false냐 알아서 해결


# # 3. 얼굴비교 함수
# def compare_faces1(sourceFile, targetFile):
#     client = boto3.client('rekognition', region_name='ap-northeast-2', aws_access_key_id=Config.AWS_ACCESS_KEY_ID, aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY)
#     imageSource = open(sourceFile, 'rb')
#     imageTarget = open(targetFile, 'rb')
#     response = client.compare_faces(
#         SimilarityThreshold=99,
#         SourceImage={'Bytes': imageSource.read()},
#         TargetImage={'Bytes': imageTarget.read()}
#     )
#     face_matches = response.get('FaceMatches', [])
#     imageSource.close()
#     imageTarget.close()
#     return len(face_matches)



# # 4. 컬렉션 생성 함수 --> 유틸에 안쓰고 코드 자체에 써 놓음. --> 삭제


# # 5. 얼굴비교할 이미지 파일 로컬에 저장하는 함수
# def save_uploaded_file(directory, file, filename):
#     if not os.path.exists(directory):
#         os.makedirs(directory)
#     with open(os.path.join(directory, filename), 'wb') as f:
#         f.write(file.getbuffer()) 


# # 5. 이미지 파일 로컬에 저장 함수 2
# def save_uploaded_file2(directory, file, filename):
#     if not os.path.exists(directory):
#         os.makedirs(directory)
#     else :
#         file_1 = open(os.path.join(directory, filename), 'wb')
#         file_1.write(file.getbuffer())
#         file_1.close()



