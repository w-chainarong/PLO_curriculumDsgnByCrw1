from django.contrib import admin
from django.urls import path, include
from table import views  # ✅ เพิ่มบรรทัดนี้ เพื่อเรียก views.select_curriculum

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.select_curriculum, name='select_curriculum'),  # ✅ หน้าเลือกหลักสูตร
    path('', include('table.urls')),  # ✅ เส้นทางอื่น ๆ ของแอป table
]
