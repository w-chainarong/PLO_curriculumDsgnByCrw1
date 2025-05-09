from django.shortcuts import render, get_object_or_404
from .models import Curriculum, KSECItem

TYPE_MAP = {
    'K': 'Knowledge',
    'S': 'Skills',
    'E': 'Ethics',
    'C': 'Character'
}

def select_ksec_items(request, curriculum_id):
    semester = request.GET.get('semester')
    ksec_type = request.GET.get('type')
    course_id = request.GET.get('course_id')

    if not semester or not ksec_type:
        return render(request, 'table/error.html', {
            'message': 'กรุณาระบุ semester และประเภทให้ครบถ้วน'
        })

    mode = request.GET.get('mode') or request.session.get('access_mode', 'view')
    db = 'real' if mode == 'edit' else 'default'

    curriculum = get_object_or_404(Curriculum.objects.using(db), id=curriculum_id)

    # ✅ โหลดรายการและสร้างรหัส
    raw_items = list(KSECItem.objects.using(db).filter(
        curriculum=curriculum,
        semester=0,
        type=ksec_type
    ).order_by('sort_order', 'id'))

    for idx, item in enumerate(raw_items):
        item.code = f"{item.category_type}({ksec_type}){idx + 1}"

    # ✅ สร้างชื่อภาค เช่น ปีที่ 1/1
    year = (int(semester) - 1) // 2 + 1
    term = 1 if int(semester) % 2 == 1 else 2
    semester_str = f"ปีที่ {year}/{term}"

    return render(request, 'table/select_ksec_items.html', {
        'curriculum': curriculum,
        'semester': semester,
        'semester_str': semester_str,
        'type': ksec_type,
        'type_name': TYPE_MAP.get(ksec_type, ksec_type),
        'course_id': course_id,
        'items': raw_items,
        'access_mode': mode,
    })
