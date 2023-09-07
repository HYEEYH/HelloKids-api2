class Config:
    AWS_ACCESS_KEY_ID = 'AKIAQMYXLF4OKK3GWTUZ'
    AWS_SECRET_ACCESS_KEY = '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'

    # S3 관련 변수
    S3_BUCKET = 'hellokids'
    S3_BASE_URL = 'https://'+S3_BUCKET+'.s3.ap-northeast-2.amazonaws.com/'

    # DB 관련 정보
    HOST = 'yhdb.cnwaypyqm4je.ap-northeast-2.rds.amazonaws.com'
    DATABASE = 'hellokids'
    DB_USER = 'hellokids_db_user'
    DB_PASSWORD = '123456789'
    # 비번 암호화
    SALT = '0417helloqkqh' # 비번에 붙일 문자열
    # JWT 환경 변수 셋팅
    JWT_SECRET_KEY = 'hello!richtoto'
    JWT_ACCESS_TOKEN_EXPIRES = False
    PROPAGATE_EXCEPTIONS = True

     # 네이버 파파고 관련 변수
    X_NAVER_CLIENT_ID='hbsgahvmUQ0PxXoy89WT'
    X_NAVER_CLIENT_SECRET ='hFXTGhxxVe'


