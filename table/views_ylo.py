from django.shortcuts import render, redirect, get_object_or_404
from .models import Curriculum, Course, YLOPerPLOSemester

# 🔁 แปลง semester เป็นรูปแบบ ปี/เทอม เช่น 1/1, 2/2
def convert_semester(sem):
    year = (sem - 1) // 2 + 1
    term = 1 if sem % 2 == 1 else 2
    return f"{year}/{term}"

# ✅ แสดงตาราง YLO Study Plan
def ylo_studyplan_view(request, curriculum_id, semester):
    mode = request.GET.get('mode') or request.session.get('access_mode', 'view')
    db = 'real' if mode == 'edit' else 'default'

    curriculum = get_object_or_404(Curriculum.objects.using(db), id=curriculum_id)

    # 🔎 ดึงรายวิชาในภาคการศึกษานั้น
    courses = Course.objects.using(db).filter(
        curriculum_id=curriculum_id,
        semester=semester
    ).order_by('course_code')

    # 🔎 ดึง YLO ทั้งหมดของเทอมนั้น
    ylo_entries = YLOPerPLOSemester.objects.using(db).filter(
        curriculum_id=curriculum_id,
        semester=semester
    ).order_by('plo')

    # 🧾 แปลง YLO เป็น list ที่มีรหัส + ข้อความ
    ylo_list = []
    semester_str = convert_semester(semester)
    for idx, ylo in enumerate(ylo_entries, start=1):
        ylo_code = f"YLO {semester_str}-{idx}"
        ylo_list.append({
            'code': ylo_code,
            'summary_text': ylo.summary_text,
        })

    return render(request, 'table/course_list_ylo.html', {
        'curriculum_id': curriculum_id,
        'semester': semester,
        'semester_str': semester_str,
        'courses': courses,
        'ylo_list': ylo_list,
        'access_mode': mode,
    })

# ✅ บันทึกข้อมูล Knowledge / Skills / Ethics / Character
def save_ylo_studyplan(request, curriculum_id, semester):
    if request.method == 'POST':
        mode = request.GET.get('mode') or request.session.get('access_mode', 'view')
        db = 'real' if mode == 'edit' else 'default'

        curriculum = get_object_or_404(Curriculum.objects.using(db), id=curriculum_id)
        courses = Course.objects.using(db).filter(curriculum=curriculum, semester=semester)

        for course in courses:
            course.knowledge = request.POST.get(f'knowledge_{course.id}', '').strip()
            course.skills = request.POST.get(f'skills_{course.id}', '').strip()
            course.ethics = request.POST.get(f'ethics_{course.id}', '').strip()
            course.character = request.POST.get(f'character_{course.id}', '').strip()
            course.save(using=db)

        return redirect('ylo_studyplan_view', curriculum_id=curriculum_id, semester=semester)

    # fallback: redirect กลับ ถ้าไม่ใช่ POST
    return redirect('ylo_studyplan_view', curriculum_id=curriculum_id, semester=semester)
