from flask import Flask
from flask_restful import Api
from config import Config
from flask_jwt_extended import JWTManager

from resources.PhotoAlbum import PhotoAlbumAddResource, PhotoAlbumListResource

from resources.dailynote import DailyNoteEditResource, DailyNoteAddResource, DailyNoteDeleteResource, DailyNoteListResource, DailyNoteViewResource
from resources.login import LoginResource, LogoutResource
from resources.menu import MenuAddResource, MenuDeleteResource, MenuEditResource, MenuListDayResource, MenuListResource, MenuViewResource
from resources.notice import NoticeDeleteResource, NoticeEditResource, NoticeResource, NoticeWillResource, NoticeViewResource, NoticeListResource
from resources.register1 import ParentRegisterpResource, ParentEditResource, ParentViewResource, ParentDeleteResource
from resources.register import TeacherRegisterResource, TeacherViewResource, TeacherEditResource, TeacherDeleteResource
from resources.schedule import ScheduleAddResource, ScheduleViewResource, ScheduleAllListResource, ScheduleClassListResource, ScheduleEditResource, ScheduleDeleteResource, ScheduleChildListResource

from resources.schoolbus import SchoolBusBoardingAddResource, SchoolBusBoardingDeleteResource, SchoolBusBoardingListResource, SchoolBusBoardingTimeResource, SchoolBusDriveEditResource, SchoolBusDriveListResource, SchoolBusDriveResource, SchoolBusDriveViewResource, SchoolBusLocationAddResource, SchoolBusLocationViewResource, SchoolBusResource, SchoolBusEditResource, SchoolBusSearchResource, SchoolBusSearchListResource, SchoolBusTeacherAddResource, SchoolBusTeacherListResource
from resources.schoolbus import SchoolBusResource, SchoolBusEditResource, SchoolBusSearchResource, SchoolBusDeleteResource

from resources.teacher import TeacherChildrenResource, TeacherNurseryResource
from resources.setting import SettingChildrenResource, SettingChildEditResource, SettingChildViewResource, SettingChildDeleteResource, SettingChildrenListResource, SettingAllChildrenListResource
from resources.setting import SettingNurseryResource, SettingNurseryViewResource, SettingNurseryEditResource, SettingNurseryDeleteResource
from resources.setting import SettingClassResource, SettingClassViewResource, SettingClassListResource, SettingClassEditResource, SettingClassDeleteResource, SettingApproveResource, SettingApproveList


app = Flask(__name__)


# 환경변수 셋팅
app.config.from_object(Config)

# JWT 매니저 초기화
jwt = JWTManager(app)
api = Api(app)


# 회원가입 - 선생님
api.add_resource(TeacherRegisterResource,'/user/register/teacher')
api.add_resource(TeacherEditResource,'/user/teacher/<int:id>') # update
api.add_resource(TeacherViewResource,'/user/teacher/<int:id>') # read
api.add_resource(TeacherDeleteResource,'/user/teacher/<int:id>') # delete

# 회원가입 - 학부모
api.add_resource(ParentRegisterpResource,'/user/register/parent') # 회원가입-학부모-학부모정보
api.add_resource(ParentEditResource,'/user/parent/<int:id>') # update
api.add_resource(ParentViewResource,'/user/parent/<int:id>') # read
api.add_resource(ParentDeleteResource,'/user/parent/<int:id>') # delete


# setting
api.add_resource(SettingChildrenResource,'/setting/child') # JSON 버전 아이 입력 
api.add_resource(SettingAllChildrenListResource,'/setting/children/<int:nurseryId>/all') # read 
api.add_resource(SettingChildrenListResource,'/setting/children/<int:classId>') # read 
api.add_resource(SettingChildViewResource,'/setting/child/<int:id>') # read
api.add_resource(SettingChildEditResource,'/setting/child/<int:id>') # update
api.add_resource(SettingChildDeleteResource,'/setting/child/<int:id>') # delete


# 원 입력
api.add_resource(SettingNurseryResource,'/setting/nursery') # 원 입력 
api.add_resource(SettingNurseryViewResource,'/setting/nursery/<int:id>/view') # 원 정보 보기
api.add_resource(SettingNurseryEditResource,'/setting/nursery/<int:id>/edit') # 원 정보 수정
api.add_resource(SettingNurseryDeleteResource,'/setting/nursery/<int:id>') # 원 정보 삭제


# 반 입력
api.add_resource(SettingClassResource,'/setting/class') # 반 입력
api.add_resource(SettingClassViewResource,'/setting/class/<int:id>/view') # 반 정보 보기
api.add_resource(SettingClassListResource,'/setting/class/list') # 반 목록 보기 id: nurseryId
api.add_resource(SettingClassEditResource,'/setting/class/<int:id>/edit') # 반 정보 수정
api.add_resource(SettingClassDeleteResource,'/setting/class/<int:id>') # 반 정보 삭제


# 학부모 승인
api.add_resource(SettingApproveList,'/setting/approve') # 학부모 테이블에서 childId가 없는 사람들의 목록 원 별로 불러오기 # get
api.add_resource(SettingApproveResource,'/setting/approve') # 학부모 테이블에서 childId가 없는 사람들은 미승인, 넣을 때 승인 # update
# api.add_resource(ApproveDeleteResource,'/setting/approve') # 미승인 항목 삭제 # 이 부분은 parents 가 회원탈퇴하면서 자동 삭제됨  


# 로그인,로그아웃
api.add_resource(LoginResource, '/user/login')
api.add_resource(LogoutResource, '/user/logout')

# 공지사항
api.add_resource(NoticeWillResource,'/notice/<int:classId>/publish') # 공지사항-임시저장
api.add_resource(NoticeResource,'/notice/<int:id>/publish') # 공지사항 발행 #noticeId
api.add_resource(NoticeEditResource,'/notice/<int:id>') # 공지사항 - 수정
api.add_resource(NoticeDeleteResource,'/notice/<int:id>') # 공지사항 - 삭제
api.add_resource(NoticeViewResource,'/notice/<int:id>') # 공지사항 - 보기
api.add_resource(NoticeListResource,'/notice/<int:nurseryId>/list') # 공지사항 - 목록


# 안심등하원
api.add_resource(SchoolBusResource,'/schoolbus')  # 차량 추가 
api.add_resource(SchoolBusEditResource,'/schoolbus/<int:id>') # 차량 수정
api.add_resource(SchoolBusSearchResource,'/schoolbus/<int:nurseryId>')  # 차량 조회 
api.add_resource(SchoolBusSearchListResource,'/schoolbus') # 차량 목록 조회 
api.add_resource(SchoolBusDeleteResource,'/schoolbus/<int:id>') # 차량 삭제

api.add_resource(SchoolBusTeacherListResource,'/schoolbus/teacher/<int:nurseryId>') # 인솔교사 리스트 
api.add_resource(SchoolBusTeacherAddResource,'/schoolbus/drive/<int:id>/teacher') # 인솔교사 등록 
api.add_resource(SchoolBusBoardingListResource,'/schoolbus/drive/<int:id>/boarding') # 탑승자 리스트  
api.add_resource(SchoolBusBoardingTimeResource,'/schoolbus/drive/<int:id>/boarding') # 승하차 시간 체크  

api.add_resource(SchoolBusBoardingAddResource,'/schoolbus/drive/<int:id>/boarding') # 탑승신청 - 학부모화면  
api.add_resource(SchoolBusBoardingDeleteResource,'/schoolbus/boarding/<int:id>') # 탑승취소 - 학부모화면 

api.add_resource(SchoolBusDriveResource,'/schoolbus/drive/<int:id>') # 차량 운행 기록 생성 - 운행시작,운행종료 시간 입력 
api.add_resource(SchoolBusDriveEditResource,'/schoolbus/drive/<int:id>') # 차량 운행 기록 수정 
api.add_resource(SchoolBusDriveViewResource,'/schoolbus/drive/<int:id>') # 차량 운행 기록 보기 
api.add_resource(SchoolBusDriveListResource,'/schoolbus/drive') # 차량 운행 기록 목록 조회

# 실시간 위치 
api.add_resource(SchoolBusLocationAddResource,'/schoolbus/drive/<int:id>/location') # 인솔교사의 현재 위치 테이블에 저장
api.add_resource(SchoolBusLocationViewResource,'/schoolbus/drive/<int:id>/location') # 가장 최근 위치 가져오기

# 실시간 위치 가져오기(구글 API이용)(안쓸꺼지만 아까워서 남겨놓았다!)
# api.add_resource(LocationNow,'/schoolbus/drive/now')


# 사진첩 
api.add_resource(PhotoAlbumAddResource,'/photoAlbum/add') # 사진첩 생성하기
# api.add_resource(PhotoAlbumAddResource,'/photoAlbum/autoAdd') # 사진첩 자동 생성
api.add_resource(PhotoAlbumListResource,'/photoAlbum/list/<int:nurseryId>/<int:classId>') # 사진첩 목록 보기
# api.add_resource(PhotoAlbumListResource,'/photoAlbum/<int:childId>/list') # 사진첩 원아별 목록 보기
# api.add_resource(PhotoAlbumViewResource,'/photoAlbum/<int:id>') # 사진첩 상세 보기
# api.add_resource(PhotoAlbumEditResource,'/photoAlbum/<int:id>') # 사진첩 수정
# api.add_resource(PhotoAlbumSelectResource,'/photoAlbum/<int:id>') # 개별 사진첩의 사진 선택 수정(사진첩 안에 있다.)
# api.add_resource(PhotoAlbumDeleteResource,'/photoAlbum/<int:id>') # 사진첩 삭제

# 사진첩 보기 권한 설정을 해 줘야 한다. 원별사진첩:1 반별 사진첩:2 개인사진첩:3


# 알림장
api.add_resource(DailyNoteAddResource,'/dailynote/write/<int:childId>') # 알림장 등록
api.add_resource(DailyNoteViewResource,'/dailynote/<int:id>') # 알림장 상세보기
api.add_resource(DailyNoteListResource,'/dailynote/list/<int:childId>') # 알림장 목록(원아별) 
api.add_resource(DailyNoteEditResource,'/dailynote/<int:id>') # 알림장 수정
api.add_resource(DailyNoteDeleteResource,'/dailynote/<int:id>') # 알림장 삭제


# # 일정표
api.add_resource(ScheduleAddResource,'/schedule/write') # 일정 등록 <완료>
api.add_resource(ScheduleViewResource,'/schedule/<int:id>') # 일정 상세보기 - 안드로이드에서 구현할 때 이 API 없어도 구현이 가능했다 <완료>
api.add_resource(ScheduleEditResource,'/schedule/<int:id>') # 일정 수정 <완료>
api.add_resource(ScheduleDeleteResource,'/schedule/<int:id>') # 일정 삭제 <완료>
api.add_resource(ScheduleChildListResource,'/schedule/child/list') # 원아별 일정 리스트(학부모) <완료>
api.add_resource(ScheduleClassListResource,'/schedule/<int:classId>/class')
api.add_resource(ScheduleAllListResource,'/schedule/all') # 선생님이 속한 어린이집 전체 일정 리스트 <완료>

# mealMenu
api.add_resource(MenuAddResource,'/menu/add') # 개별 메뉴 입력 
api.add_resource(MenuListResource,'/menu/<int:nurseryId>/list') # 원 별 메뉴 목록 
api.add_resource(MenuListDayResource,'/menu/<int:nurseryId>/<string:mealDate>') # 하루 메뉴 목록 /menu/1/2023-09-01
api.add_resource(MenuViewResource,'/menu/<int:id>') # 개별 메뉴 정보 보기
api.add_resource(MenuEditResource,'/menu/<int:id>') # 개별 메뉴 정보 수정
api.add_resource(MenuDeleteResource,'/menu/<int:id>') # 개별 메뉴 삭제 



if __name__ == '__main__':
    app.run()