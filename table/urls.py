from django.urls import path
from . import views
from . import views_course
from . import views_plo
from . import views_ylo
from . import views_ksec
from . import views_ksec_select
from . import admin_views
from . import views_clo
from . import views_plo_summary

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

    # ✅ ตารางแผนการเรียน YLO
    path('curriculum/<int:curriculum_id>/ylo-studyplan/<int:semester>/', views_ylo.ylo_studyplan_view, name='ylo_studyplan_view'),
    path('curriculum/<int:curriculum_id>/ylo-studyplan/<int:semester>/save/', views_ylo.save_ylo_studyplan, name='save_ylo_studyplan'),

    # ✅ แก้ไขรายการ K/S/E/C
    path('curriculum/<int:curriculum_id>/ksec/<int:semester>/<str:type>/', views_ksec.edit_ksec_choices, name='edit_ksec_choices'),

    # ✅ Popup เลือกรายการ K/S/E/C
    path('curriculum/<int:curriculum_id>/select-ksec/', views_ksec_select.select_ksec_items, name='select_ksec_items'),

    # ✅ Sync และ Backup/Restore
    path('sync-db/', admin_views.sync_real_to_example, name='sync_real_to_example'),
    path('curriculum/<int:curriculum_id>/backup/', views.sync_curriculum_real_to_example, name='sync_curriculum_real_to_example'),
    path('curriculum/<int:curriculum_id>/restore/', views.sync_curriculum_example_to_real, name='sync_curriculum_example_to_real'),

    # ✅ ปุ่มดาวน์โหลดฐานของ DB
    path('download-db/all/', views.download_all_databases, name='download_all_databases'),
    path('download-db/<str:db_name>/', views.download_database, name='download_database'),

    # ✅ CLO-KSEC Mapping
    path('curriculum/<int:curriculum_id>/clo-ksec-mapping/<int:course_id>/', views_clo.clo_ksec_mapping, name='clo_ksec_mapping'),
    path('curriculum/<int:curriculum_id>/clo-ksec-mapping/<int:course_id>/save/', views_clo.save_clo_ksec_mapping, name='save_clo_ksec_mapping'),
    path('curriculum/<int:curriculum_id>/clo-ksec-mapping/<int:course_id>/reset/', views_clo.reset_clo_ksec_mapping, name='reset_clo_ksec_mapping'),
    path('curriculum/<int:curriculum_id>/clo-ksec-mapping/<int:course_id>/save-session/', views_clo.save_clo_ksec_to_session, name='save_clo_ksec_to_session'),  # ← ✅ เพิ่มตรงนี้
    
    # ✅ สรุป CLOs ต่อ PLO
    path('curriculum/<int:curriculum_id>/plo-summary/', views_plo_summary.plo_summary_view, name='plo_summary_view'),
    # ✅ กราฟหน่วยกิตหมวด PLOs (Stacked Bar)
    path('curriculum/<int:curriculum_id>/plo-graph/', views.plo_graph_from_creditrow, name='plo_graph_from_creditrow'),

]
