from django.urls import path
from . import views
from . import views_course
from . import views_plo
from . import admin_views

urlpatterns = [
    path('', views.select_curriculum, name='select_curriculum'),
    path('curriculum/<int:curriculum_id>/credit-table/', views.credit_table, name='credit_table'),
    path('curriculum/<int:curriculum_id>/reset/', views.reset_credit_table, name='reset_credit_table'),

    # รายวิชาแต่ละหมวด
    path('curriculum/<int:curriculum_id>/course-list/<str:row_id>/<int:semester>/', views_course.course_list, name='course_list'),
    path('curriculum/<int:curriculum_id>/course-list/<str:row_id>/<int:semester>/save/', views_course.save_course_list, name='save_course_list'),
    path('curriculum/<int:curriculum_id>/course-list/<str:row_id>/<int:semester>/reset/', views_course.reset_course_list, name='reset_course_list'),

    # PLO
    path('curriculum/<int:curriculum_id>/course-list-plo/<int:row_id>/<int:semester>/', views_plo.course_list_plo, name='course_list_plo'),

    # Admin
    path('sync-db/', admin_views.sync_real_to_example, name='sync_real_to_example'),

    # ✅ Download ฐานข้อมูล
    path('download-db/<str:db_name>/', views.download_database, name='download_database'),
]
