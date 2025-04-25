from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
import shutil
import os

@staff_member_required
def sync_real_to_example(request):
    status = ""
    if request.method == "POST":
        try:
            source = os.path.join(os.path.dirname(__file__), '..', 'real.sqlite3')
            dest = os.path.join(os.path.dirname(__file__), '..', 'example.sqlite3')
            shutil.copyfile(source, dest)
            status = "✅ Sync สำเร็จ! ข้อมูลถูกคัดลอกจาก real → example แล้ว"
        except Exception as e:
            status = f"❌ เกิดข้อผิดพลาด: {str(e)}"
    
    return render(request, 'admin/sync_real_to_example.html', {'status': status})
