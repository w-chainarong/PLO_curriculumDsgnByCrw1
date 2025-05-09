from django.shortcuts import render, redirect, get_object_or_404
from .models import Curriculum, KSECItem
from django.db import transaction

TYPE_MAP = {
    'K': 'Knowledge',
    'S': 'Skills',
    'E': 'Ethics',
    'C': 'Character'
}

def edit_ksec_choices(request, curriculum_id, semester, type):
    if type not in TYPE_MAP:
        return redirect('select_curriculum')

    type_name = TYPE_MAP[type]

    # ✅ ตรวจสอบ access_mode และเลือกฐานข้อมูลที่ถูกต้อง
    mode = request.GET.get('mode') or request.session.get('access_mode', 'view')
    db = 'real' if mode == 'edit' else 'default'

    curriculum = get_object_or_404(Curriculum.objects.using(db), pk=curriculum_id)

    # ✅ โหลดรายการที่ไม่สนใจ semester แล้ว (เรียงตาม sort_order)
    items = KSECItem.objects.using(db).filter(
        curriculum=curriculum,
        type=type
    ).order_by('sort_order', 'id')

    if request.method == 'POST' and mode == 'edit':  # ✅ บันทึกเฉพาะเมื่ออยู่ในโหมด edit
        with transaction.atomic(using=db):
            total = int(request.POST.get('total_items', 0))
            keep_ids = set()
            new_items = []

            for i in range(total + 50):
                item_id = request.POST.get(f'item_id_{i}')
                desc = request.POST.get(f'item_{i}')
                category_type = request.POST.get(f'item_type_{i}')

                if desc and category_type in ['GE', 'CE']:
                    desc = desc.strip()
                    if item_id and item_id.isdigit():
                        obj = KSECItem.objects.using(db).filter(id=int(item_id), curriculum=curriculum).first()
                        if obj:
                            obj.description = desc
                            obj.category_type = category_type
                            obj.sort_order = i  # ✅ อัปเดต sort_order
                            obj.save(using=db)
                            keep_ids.add(obj.id)
                    else:
                        new_items.append(KSECItem(
                            curriculum=curriculum,
                            semester=0,  # ✅ ใช้ค่าเดียวกันทุกภาคการศึกษา
                            type=type,
                            category_type=category_type,
                            description=desc,
                            sort_order=i  # ✅ ใส่ลำดับใหม่
                        ))

            if new_items:
                created = KSECItem.objects.using(db).bulk_create(new_items)
                keep_ids.update(obj.id for obj in created)

            KSECItem.objects.using(db).filter(
                curriculum=curriculum,
                type=type
            ).exclude(id__in=keep_ids).delete()

        return redirect('edit_ksec_choices', curriculum_id=curriculum_id, semester=semester, type=type)

    semester_str = f"ปีที่ {(semester - 1) // 2 + 1} ภาค {1 if semester % 2 == 1 else 2}"

    return render(request, 'table/edit_ksec.html', {
        'curriculum': curriculum,
        'semester': semester,
        'semester_str': semester_str,
        'type': type,
        'type_name': type_name,
        'items': items,
        'access_mode': mode,  # ✅ ส่ง access_mode ไปให้ template เพื่อจัดการ readonly
    })
