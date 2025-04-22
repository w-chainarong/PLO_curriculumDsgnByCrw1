from django.shortcuts import render, get_object_or_404
from .models import CreditRow, Course

def convert_semester(sem):
    year = (sem - 1) // 2 + 1
    term = 1 if sem % 2 == 1 else 2
    return f"{year}/{term}"

def course_list_plo(request, curriculum_id, row_id, semester):
    # ✅ ดึงแถว PLO ที่เกี่ยวข้องกับ curriculum
    plo_row = get_object_or_404(CreditRow, id=row_id, curriculum_id=curriculum_id)

    # ✅ ตัดชื่อ PLO เช่น "PLO1: ด้านการคิด" → "PLO1"
    plo_label = plo_row.name.split()[0] if plo_row.name else ''

    # ✅ ดึงเฉพาะรายวิชาที่อยู่ใน curriculum นี้
    matching_courses = Course.objects.filter(
        curriculum_id=curriculum_id,
        semester=semester,
        plo=plo_label,
        credit_row__row_type__in=['general', 'core']
    ) | Course.objects.filter(
        curriculum_id=curriculum_id,
        semester=semester,
        plo=plo_label,
        category='free_elective'
    )

    matching_courses = matching_courses.order_by('course_code')
    total_credits = sum(course.credits for course in matching_courses)

    semester_str = convert_semester(semester)

    return render(request, 'table/course_list_plo.html', {
        'row': plo_row,
        'semester': semester,
        'semester_str': semester_str,
        'courses': matching_courses,
        'total_credits': total_credits,
    })
