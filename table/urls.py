from django.urls import path
from . import views
from . import views_course
from . import views_plo
from . import views_ylo           # ✅ สำหรับตาราง YLO
from . import admin_views         # ✅ สำหรับ Backup/Restore/Download

urlpatterns = [
    # ✅ หน้าเลือกหลักสูตร
    path('', views.select_curriculum, name='select_curriculum'),

    # ✅ ตารางหลัก
    path('curriculum/<int:curriculum_id>/credit-table/', views.credit_table, name='credit_table'),
    path('curriculum/<int:curriculum_id>/reset/', views.reset_credit_table, name='reset_credit_table'),

    # ✅ รายวิชาในหมวดทั่วไป / เฉพาะ / เลือกเสรี
    path('curriculum/<int:curriculum_id>/course-list/<str:row_id>/<int:semester>/', views_course.course_list, name='course_list'),
    path('curriculum/<int:curriculum_id>/course-list/<str:row_id>/<int:semester>/save/', views_course.save_course_list, name='save_course_list'),
    path('curriculum/<int:curriculum_id>/course-list/<str:row_id>/<int:semester>/reset/', views_course.reset_course_list, name='reset_course_list'),

    # ✅ รายวิชาในหมวด PLOs
    path('curriculum/<int:curriculum_id>/course-list-plo/<int:row_id>/<int:semester>/', views_plo.course_list_plo, name='course_list_plo'),
    path('curriculum/<int:curriculum_id>/course-list-plo/<int:row_id>/<int:semester>/save/', views_plo.save_course_list_plo, name='save_course_list_plo'),

    # ✅ ตารางแผนการเรียนตาม YLO
    path('curriculum/<int:curriculum_id>/ylo-studyplan/<int:semester>/', views_ylo.ylo_studyplan_view, name='ylo_studyplan_view'),
    path('curriculum/<int:curriculum_id>/ylo-studyplan/<int:semester>/save/', views_ylo.save_ylo_studyplan, name='save_ylo_studyplan'),

    # ✅ ฟังก์ชัน Sync ข้อมูลระหว่างฐาน real ↔ example
    path('sync-db/', admin_views.sync_real_to_example, name='sync_real_to_example'),  # 🔁 ทั้งฐาน real → example
    path('curriculum/<int:curriculum_id>/backup/', views.sync_curriculum_real_to_example, name='sync_curriculum_real_to_example'),  # 🔁 หลักสูตรเดียว real → example (user page)
    path('curriculum/<int:curriculum_id>/restore/', admin_views.sync_curriculum_example_to_real, name='sync_curriculum_example_to_real'),  # ✅ หลักสูตรเดียว example → real (admin page)

    # ✅ ปุ่มดาวน์โหลดฐานข้อมูล
    path('download-db/all/', views.download_all_databases, name='download_all_databases'),
    path('download-db/<str:db_name>/', views.download_database, name='download_database'),
]
