from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
import shutil
import os
from table.models import Curriculum
from django.contrib import messages

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

@staff_member_required
def sync_curriculum_example_to_real(request, curriculum_id):
    status = ""
    try:
        # ดึง curriculum ที่ต้องการจากฐาน example (default)
        example_curriculum = Curriculum.objects.using('default').get(pk=curriculum_id)

        # เขียนหรืออัปเดตลงฐาน real
        Curriculum.objects.using('real').update_or_create(
            pk=example_curriculum.pk,
            defaults={
                'name': example_curriculum.name,
                # ใส่ field อื่น ๆ ถ้ามี เช่น:
                # 'description': example_curriculum.description,
            }
        )

        status = f"✅ Successfully synced Curriculum ID {curriculum_id} to real DB."

    except Curriculum.DoesNotExist:
        status = f"❌ Curriculum ID {curriculum_id} not found in example DB."
    except Exception as e:
        status = f"❌ Error during sync: {str(e)}"

    return render(request, 'admin/sync_result.html', {'status': status})

