from django.shortcuts import render, redirect, get_object_or_404
from .models import Curriculum, Course, YLOPerPLOSemester
from django.contrib import messages

# 🗁 • แปลง semester เป็น "ปี/ภาค" (1/1, 2/2, ...)
def convert_semester(sem):
    year = (sem - 1) // 2 + 1
    term = 1 if sem % 2 == 1 else 2
    return f"{year}/{term}"

# ✅ หน้าแสดง YLO Study Plan
def ylo_studyplan_view(request, curriculum_id, semester):
    mode = request.GET.get('mode') or request.session.get('access_mode', 'view')
    db = 'real' if mode == 'edit' else 'default'

    curriculum = get_object_or_404(Curriculum.objects.using(db), id=curriculum_id)

    # 🔎 ดึง course ในภาคสึกษึน
    courses = Course.objects.using(db).filter(
        curriculum_id=curriculum_id,
        semester=semester
    ).order_by('course_code')

    # 🔎 ดึง YLO summary ในภาคนี้
    ylo_entries = YLOPerPLOSemester.objects.using(db).filter(
        curriculum_id=curriculum_id,
        semester=semester
    ).order_by('plo')

    # 📏 เตียง ylo_list บรรทัท summary
    ylo_list = []
    semester_str = convert_semester(semester)
    for idx, ylo in enumerate(ylo_entries, start=1):
        if ylo.summary_text and str(ylo.summary_text).strip():  # <-- เพิ่ม if แค่ตรงนี้!
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
        'access_mode': mode,  # ✅ เพ่มโหมดให้ html ราร์บระสบ read-only
    })

# ✅ บันทึกผล K/S/E/C ลงใน Course
def save_ylo_studyplan(request, curriculum_id, semester):
    mode = request.GET.get('mode') or request.session.get('access_mode', 'view')
    db = 'real' if mode == 'edit' else 'default'

    if request.method == 'POST' and mode == 'edit':
        curriculum = get_object_or_404(Curriculum.objects.using(db), id=curriculum_id)
        courses = Course.objects.using(db).filter(curriculum=curriculum, semester=semester)

        for course in courses:
            course.knowledge = request.POST.get(f'k_{course.id}', '').strip()
            course.skills = request.POST.get(f's_{course.id}', '').strip()
            course.ethics = request.POST.get(f'e_{course.id}', '').strip()
            course.character = request.POST.get(f'c_{course.id}', '').strip()
            course.save(using=db)

        #update_ylo_for_curriculum(curriculum)
        messages.success(request, "✅ บันทึกข้อมูล YLO Study Plan สำเร็จ")

    return redirect('ylo_studyplan_view', curriculum_id=curriculum_id, semester=semester)


def update_ylo_for_curriculum(curriculum):
    from .models import Course, YLOPerPLOSemester

    for sem in range(1, 9):
        print(f"\n=== เทอม {sem} ===")
        plo_with_credits = set()
        courses = Course.objects.using('real').filter(curriculum=curriculum, semester=sem)

        for course in courses:
            print(f" - {course.course_code} | credits={course.credits} | PLO={course.plo}")
            if not course.plo:
                continue
            plo_tag = course.plo.split(':')[0].strip()
            if plo_tag and course.credits and course.credits > 0:
                plo_with_credits.add(plo_tag)

        print(f">> PLO ที่มีหน่วยกิต: {plo_with_credits}")

        # ลบ YLO ที่ไม่มีหน่วยกิต
        for ylo in YLOPerPLOSemester.objects.using('real').filter(curriculum=curriculum, semester=sem):
            ylo_plo_tag = ylo.plo.strip().split(":")[0].strip() if ylo.plo else ''
            if ylo_plo_tag not in plo_with_credits:
                print(f"[ลบ] YLO เทอม {sem}, PLO={ylo.plo} เนื่องจากไม่มีวิชาโยง")
                ylo.delete()
            else:
                print(f"[เก็บ] YLO เทอม {sem}, PLO={ylo.plo}")
