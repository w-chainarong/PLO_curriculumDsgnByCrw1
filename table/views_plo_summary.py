from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Curriculum, Course, CreditRow, CLO, KSECItem, CLOSummary  # ✅ เพิ่ม CLOSummary

def plo_summary_view(request, curriculum_id):
    # ✅ ตรวจสอบโหมดฐานข้อมูล
    mode = request.session.get('access_mode', 'view')
    db = 'real' if mode == 'edit' else 'default'

    # ✅ ดึงหลักสูตร
    curriculum = get_object_or_404(Curriculum.objects.using(db), id=curriculum_id)

    # ✅ ดึงรายการ PLO ทั้งหมด
    plo_rows = CreditRow.objects.using(db).filter(
        curriculum=curriculum, row_type='plo'
    ).order_by('id')

    # ✅ ดึง KSECItem ทั้งหมดของหลักสูตร
    ksec_items = list(KSECItem.objects.using(db).filter(curriculum=curriculum))

    # ✅ สร้าง lookup: CE(K)6 → รายละเอียด
    ksec_lookup = {
        f"{item.category_type.strip()}({item.type.strip()}){item.sort_order + 1}".replace(" ", ""): item.description.strip()
        for item in ksec_items
    }

    summary = {}

    # ✅ วนลูปแต่ละ PLO
    for row in plo_rows:
        if not row.name:
            continue

        plo_tag = row.name.split(':')[0].strip()
        description = row.name.strip()

        # ✅ ดึงรายวิชาที่โยงกับ PLO นี้
        related_courses = Course.objects.using(db).filter(
            curriculum=curriculum
        ).filter(
            Q(plo__iexact=plo_tag) | Q(plo__iexact=f"{plo_tag}:")
        ).distinct()

        course_data = []

        for course in related_courses:
            # ✅ ดึง CLO ของวิชานั้น
            clo_objs = CLO.objects.using(db).filter(course=course)
            clos = []

            # ✅ ดึงข้อมูลเปอร์เซ็นต์จาก CLOSummary (ถ้ามี)
            clo_summary = CLOSummary.objects.using(db).filter(course=course).first()
            max_bloom = clo_summary.bloom_score if clo_summary else None

            for i, clo in enumerate(clo_objs):
                line = clo.clo.strip()
                if i == len(clo_objs) - 1 and max_bloom is not None:
                    line += f'<br><span class="text-blue">(Bloom สูงสุด: {max_bloom})</span>'
                clos.append(line)

            # ✅ เตรียม K/S/E/C
            ksec_grouped = {'K': [], 'S': [], 'E': [], 'C': []}

            for clo in clo_objs:
                for typ, attr in [('K', clo.k), ('S', clo.s), ('E', clo.e), ('C', clo.c)]:
                    if attr:
                        tokens = [t.strip() for t in attr.split(',') if t.strip()]
                        for token in tokens:
                            token_clean = token.replace(" ", "")
                            desc = ksec_lookup.get(token_clean, token)
                            label = f"{token.strip()}: {desc}"
                            if label not in ksec_grouped[typ]:
                                ksec_grouped[typ].append(label)

            # ✅ รวมชื่อวิชาและคำอธิบายขึ้นบรรทัดใหม่ในวงเล็บ
            course_name_display = course.course_name.strip()
            if course.description:
                course_name_display += f"<br>({course.description.strip()})"

            course_data.append({
                'course_code': course.course_code,
                'course_name': course_name_display,
                'clos': clos,
                'ksec_grouped': ksec_grouped,
                'credits': course.credits or 0,
                'clo_summary': clo_summary,  # ✅ ใส่ไว้ให้ใช้ใน template
            })

        # ✅ สรุปผลเข้า dictionary
        summary[plo_tag] = {
            'description': description,
            'courses': course_data,
            'course_count': len(course_data),
            'total_credits': sum(c['credits'] for c in course_data),
        }

    # ✅ ส่งไปยัง template
    return render(request, 'table/plo_summary.html', {
        'curriculum': curriculum,
        'summary': summary,
    })
