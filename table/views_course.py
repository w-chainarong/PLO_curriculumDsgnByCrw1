from django.shortcuts import render, redirect, get_object_or_404
from .models import CreditRow, Course, Curriculum
from django.contrib import messages

def course_list(request, curriculum_id, row_id, semester):
    # ✅ ตรวจสอบ access mode
    mode = request.session.get('access_mode', 'view')
    db = 'real' if mode == 'edit' else 'default'
    readonly = (mode != 'edit')

    curriculum = get_object_or_404(Curriculum.objects.using(db), id=curriculum_id)

    # ✅ ดึง PLO ทั้งหมด (เลือกแค่ที่ขึ้นต้นด้วย PLO) และจัดเก็บรายละเอียด
    plo_rows = CreditRow.objects.using(db).filter(curriculum=curriculum, row_type='plo')
    plo_choices = []
    plo_descriptions = {}
    for r in plo_rows:
        if r.name:
            parts = r.name.split()
            if parts[0].startswith("PLO"):
                label = parts[0]
                desc = " ".join(parts[1:]) if len(parts) > 1 else ""
                if label not in plo_choices:
                    plo_choices.append(label)
                    plo_descriptions[label] = desc

    # ✅ วิชาเลือกเสรี
    if row_id == 'free_elective':
        courses = Course.objects.using(db).filter(
            curriculum=curriculum,
            category='free_elective',
            semester=semester
        ).order_by('course_code')
        return render(request, 'table/course_list.html', {
            'curriculum_id': curriculum_id,
            'row': {'id': 'free_elective', 'name': 'หมวดวิชาเลือกเสรี'},
            'semester': semester,
            'courses': courses,
            'plo_choices': plo_choices,
            'plo_descriptions': plo_descriptions,
            'readonly': readonly,
        })

    # ✅ แถวปกติ
    row = get_object_or_404(CreditRow.objects.using(db), curriculum=curriculum, id=row_id)
    courses = Course.objects.using(db).filter(
        curriculum=curriculum,
        credit_row=row,
        semester=semester
    ).order_by('course_code')

    return render(request, 'table/course_list.html', {
        'curriculum_id': curriculum_id,
        'row': row,
        'semester': semester,
        'courses': courses,
        'plo_choices': plo_choices,
        'plo_descriptions': plo_descriptions,
        'readonly': readonly,
    })


def save_course_list(request, curriculum_id, row_id, semester):
    mode = request.session.get('access_mode', 'view')
    if mode != 'edit':
        messages.error(request, "🚫 ไม่สามารถบันทึกได้ในโหมดอ่านอย่างเดียว")
        return redirect('course_list', curriculum_id=curriculum_id, row_id=row_id, semester=semester)

    db = 'real'

    if request.method == 'POST':
        curriculum = get_object_or_404(Curriculum.objects.using(db), id=curriculum_id)

        codes = request.POST.getlist('course_code[]')
        names = request.POST.getlist('course_name[]')
        credits = request.POST.getlist('credits[]')
        plos = request.POST.getlist('plo[]')

        if not any(code.strip() for code in codes):
            messages.warning(request, "⚠️ ไม่มีรหัสวิชาที่กรอกไว้")
            return redirect('course_list', curriculum_id=curriculum_id, row_id=row_id, semester=semester)

        if row_id == 'free_elective':
            Course.objects.using(db).filter(
                curriculum=curriculum,
                category='free_elective',
                semester=semester
            ).delete()
            for code, name, credit, plo in zip(codes, names, credits, plos):
                Course.objects.using(db).create(
                    curriculum=curriculum,
                    category='free_elective',
                    semester=semester,
                    course_code=code.strip(),
                    course_name=name.strip(),
                    credits=int(credit or 0),
                    plo=plo.strip()
                )
            messages.success(request, "✅ บันทึกหมวดวิชาเลือกเสรีเรียบร้อยแล้ว")
            return redirect('course_list', curriculum_id=curriculum_id, row_id='free_elective', semester=semester)

        row = get_object_or_404(CreditRow.objects.using(db), curriculum=curriculum, id=row_id)
        Course.objects.using(db).filter(
            curriculum=curriculum,
            credit_row=row,
            semester=semester
        ).delete()

        for code, name, credit, plo in zip(codes, names, credits, plos):
            Course.objects.using(db).create(
                curriculum=curriculum,
                credit_row=row,
                semester=semester,
                course_code=code.strip(),
                course_name=name.strip(),
                credits=int(credit or 0),
                plo=plo.strip()
            )

        # อัปเดตชื่อแถว PLO ถ้ามีการเปลี่ยน
        plo_name_key = f'plo_name_{row_id}'
        if plo_name_key in request.POST:
            row.name = request.POST[plo_name_key].strip()
            row.save(using=db)

        messages.success(request, "✅ บันทึกรายวิชาหมวดนี้เรียบร้อยแล้ว")
        return redirect('course_list', curriculum_id=curriculum_id, row_id=row_id, semester=semester)


def reset_course_list(request, curriculum_id, row_id, semester):
    mode = request.session.get('access_mode', 'view')
    if mode != 'edit':
        return redirect('course_list', curriculum_id=curriculum_id, row_id=row_id, semester=semester)

    db = 'real'

    if request.method == 'POST':
        curriculum = get_object_or_404(Curriculum.objects.using(db), id=curriculum_id)

        if row_id == 'free_elective':
            Course.objects.using(db).filter(
                curriculum=curriculum,
                category='free_elective',
                semester=semester
            ).delete()
            return redirect('course_list', curriculum_id=curriculum_id, row_id='free_elective', semester=semester)

        row = get_object_or_404(CreditRow.objects.using(db), curriculum=curriculum, id=row_id)
        Course.objects.using(db).filter(
            curriculum=curriculum,
            credit_row=row,
            semester=semester
        ).delete()

        return redirect('course_list', curriculum_id=curriculum_id, row_id=row_id, semester=semester)
