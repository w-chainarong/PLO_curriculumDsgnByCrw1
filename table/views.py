from django.shortcuts import render, redirect, get_object_or_404
from .models import Curriculum, CreditRow, Course
from django.db.models import Sum
import re
from django.contrib import messages  # 🔥 เพิ่มไว้ด้านบนด้วยนะครับ (import messages)


headers = [
    'ปีที่ 1/1', 'ปีที่ 1/2', 'ปีที่ 2/1', 'ปีที่ 2/2',
    'ปีที่ 3/1', 'ปีที่ 3/2', 'ปีที่ 4/1', 'ปีที่ 4/2'
]

from django.shortcuts import render, redirect, get_object_or_404
from .models import Curriculum

def select_curriculum(request):
    if request.method == 'POST':
        curriculum_id = request.POST.get('curriculum')
        mode = request.POST.get('mode')
        password = request.POST.get('password', '').strip()

        if not curriculum_id:
            return render(request, 'table/select_curriculum.html', {
                'curriculums': Curriculum.objects.using('default').all(),
                'error_message': 'กรุณาเลือกหลักสูตร',
            })

        curriculum = get_object_or_404(Curriculum.objects.using('default'), pk=curriculum_id)

        if mode == 'edit' and password != curriculum.password:
            return render(request, 'table/select_curriculum.html', {
                'curriculums': Curriculum.objects.using('default').all(),
                'error_message': 'รหัสผ่านไม่ถูกต้อง',
            })

        request.session['access_mode'] = mode  # ✅ บันทึกโหมดใน session
        return redirect('credit_table', curriculum_id=curriculum.id)

    return render(request, 'table/select_curriculum.html', {
        'curriculums': Curriculum.objects.using('default').all()
    })



def credit_table(request, curriculum_id):
    mode = request.session.get('access_mode', 'view')  # 'view' หรือ 'edit'
    db = 'real' if mode == 'edit' else 'default'

    curriculum = get_object_or_404(Curriculum.objects.using(db), pk=curriculum_id)

    if request.method == 'POST' and mode == 'edit':
        new_name = request.POST.get('curriculum_name', '').strip()
        if new_name and new_name != curriculum.name:
            curriculum.name = new_name
            curriculum.save(using='real')  # ต้องบันทึกลงฐาน real เสมอ

        def delete_removed_rows(row_type, id_prefixes):
            posted_ids = set()
            for prefix in id_prefixes:
                pattern = re.compile(rf'{prefix}_(\d+)')
                for key in request.POST:
                    match = pattern.match(key)
                    if match:
                        try:
                            val = request.POST.get(key)
                            if val:
                                posted_ids.add(int(val))
                        except (TypeError, ValueError):
                            continue
            if posted_ids:
                CreditRow.objects.using('real').filter(
                    curriculum=curriculum,
                    row_type=row_type
                ).exclude(id__in=posted_ids).delete()

        def save_rows(row_type, prefix, credit_prefix):
            pattern = re.compile(rf'{prefix}_(\d+)')
            indices = sorted({match.group(1) for key in request.POST for match in [pattern.match(key)] if match})

            for index in indices:
                name = request.POST.get(f'{prefix}_{index}', '').strip()
                if not name:
                    continue

                credits = [int(request.POST.get(f'{credit_prefix}_{index}_{j}', 0)) for j in range(8)]
                row_id_key = f'{row_type}_id_{index}'
                row_id = request.POST.get(row_id_key)

                if row_id:
                    try:
                        row = CreditRow.objects.using('real').get(pk=row_id, curriculum=curriculum, row_type=row_type)
                        row.name = name
                        for i in range(8):
                            setattr(row, f'credits_sem{i+1}', credits[i])
                        row.save(using='real')
                    except CreditRow.DoesNotExist:
                        continue
                else:
                    CreditRow.objects.using('real').create(
                        curriculum=curriculum,
                        name=name,
                        row_type=row_type,
                        **{f'credits_sem{i+1}': credits[i] for i in range(8)}
                    )

        delete_removed_rows('plo', ['plo_id'])
        delete_removed_rows('core', ['core_id'])
        delete_removed_rows('general', ['general_id'])

        save_rows('general', 'general_name', 'general_credit')
        save_rows('core', 'core_name', 'core_credit')
        save_rows('plo', 'plo_name', 'plo_credit')
        save_rows('general', 'general_name_new', 'general_credit_new')
        save_rows('core', 'core_name_new', 'core_credit_new')
        save_rows('plo', 'plo_name_new', 'plo_credit_new')

        free_name = 'หมวดวิชาเลือกเสรี'
        free_credits = [int(request.POST.get(f'{free_name}_{i}', 0)) for i in range(8)]
        CreditRow.objects.using('real').update_or_create(
            curriculum=curriculum,
            name=free_name,
            row_type='free',
            defaults={f'credits_sem{i+1}': free_credits[i] for i in range(8)}
        )

        return redirect('credit_table', curriculum_id=curriculum.id)

    all_rows = CreditRow.objects.using(db).filter(curriculum=curriculum)
    general_rows = [(row.id, row.name, row.credit_list(), row.total_credits()) for row in all_rows.filter(row_type='general')]
    core_rows = [(row.id, row.name, row.credit_list(), row.total_credits()) for row in all_rows.filter(row_type='core')]
    plo_rows = [(row.id, row.name, row.credit_list(), row.total_credits()) for row in all_rows.filter(row_type='plo').order_by('id')]
    free_elective = all_rows.filter(row_type='free').first()
    free_elective_tuple = (free_elective.name, free_elective.credit_list(), free_elective.total_credits()) if free_elective else None
    has_saved = request.method == 'POST'

    plo_course_totals = {}
    for row in all_rows.filter(row_type='plo'):
        if row.name:
            plo_tag = row.name.split()[0]
            for semester in range(1, 9):
                general_core_sum = Course.objects.using(db).filter(
                    curriculum=curriculum,
                    semester=semester,
                    plo=plo_tag,
                    credit_row__row_type__in=['general', 'core']
                ).aggregate(Sum('credits'))['credits__sum'] or 0
                free_sum = Course.objects.using(db).filter(
                    curriculum=curriculum,
                    semester=semester,
                    plo=plo_tag,
                    category='free_elective'
                ).aggregate(Sum('credits'))['credits__sum'] or 0
                key = f"{row.id}_{semester}"
                plo_course_totals[key] = general_core_sum + free_sum

    plo_semester_totals = {i: 0 for i in range(1, 9)}
    for key, value in plo_course_totals.items():
        _, semester = key.split('_')
        plo_semester_totals[int(semester)] += value

    total_credits_all = sum(row.total_credits() for row in all_rows)
    plo_percentages = {
        str(row.id): round((row.total_credits() / total_credits_all) * 100, 2) if total_credits_all else 0
        for row in all_rows.filter(row_type='plo')
    }

    return render(request, 'table/credit_table.html', {
        'curriculum': curriculum,
        'headers': headers,
        'general_rows': general_rows,
        'core_rows': core_rows,
        'plo_rows': plo_rows,
        'free_elective': free_elective_tuple,
        'has_saved': has_saved,
        'plo_course_totals': plo_course_totals,
        'plo_semester_totals': plo_semester_totals,
        'plo_percentages': plo_percentages,
        'access_mode': mode,    # ✅ เพิ่มบรรทัดนี้
    })


def reset_credit_table(request, curriculum_id):
    mode = request.session.get('access_mode', 'view')
    db = 'real' if mode == 'edit' else 'default'

    if mode != 'edit':
        # ✅ กรณีโหมดอ่านอย่างเดียว: แสดงข้อมูล + แจ้งเตือน
        curriculum = get_object_or_404(Curriculum.objects.using(db), pk=curriculum_id)
        all_rows = CreditRow.objects.using(db).filter(curriculum=curriculum)
        general_rows = [(row.id, row.name, row.credit_list(), row.total_credits()) for row in all_rows.filter(row_type='general')]
        core_rows = [(row.id, row.name, row.credit_list(), row.total_credits()) for row in all_rows.filter(row_type='core')]
        plo_rows = [(row.id, row.name, row.credit_list(), row.total_credits()) for row in all_rows.filter(row_type='plo')]
        free_elective = all_rows.filter(row_type='free').first()
        free_elective_tuple = (free_elective.name, free_elective.credit_list(), free_elective.total_credits()) if free_elective else None
        total_credits_all = sum(row.total_credits() for row in all_rows)
        plo_percentages = {
            str(row.id): round((row.total_credits() / total_credits_all) * 100, 2) if total_credits_all else 0
            for row in all_rows.filter(row_type='plo')
        }

        return render(request, 'table/credit_table.html', {
            'curriculum': curriculum,
            'headers': headers,
            'general_rows': general_rows,
            'core_rows': core_rows,
            'plo_rows': plo_rows,
            'free_elective': free_elective_tuple,
            'has_saved': False,
            'plo_course_totals': {},
            'plo_semester_totals': {},
            'plo_percentages': plo_percentages,
            'error_message': '🚫 ไม่สามารถรีเซตข้อมูลได้ในโหมดอ่านอย่างเดียว'
        })

    # ✅ โหมด edit: ล้างและสร้างข้อมูลใหม่
    curriculum = get_object_or_404(Curriculum.objects.using(db), pk=curriculum_id)

    if request.method == 'POST':
        CreditRow.objects.using(db).filter(
            curriculum=curriculum,
            row_type__in=['general', 'core', 'plo', 'free']
        ).delete()

        general_data = [
            ('กลุ่มวิชาภาษา', [0]*8),
            ('กลุ่มวิชาสังคมศาสตร์', [0]*8),
            ('กลุ่มวิชามนุษยศาสตร์', [0]*8),
            ('กลุ่มวิชาพลศึกษาและนันทนาการ', [0]*8),
            ('กลุ่มวิชาวิทยาศาสตร์', [0]*8),
            ('กลุ่มวิชาคณิตศาสตร์และคอมพิวเตอร์', [0]*8),
            ('กลุ่มวิชาบูรณาการ', [0]*8)
        ]
        core_data = [
            ('กลุ่มวิชาพื้นฐานทางวิทยาศาสตร์และคณิตศาสตร์', [0]*8),
            ('กลุ่มวิชาพื้นฐานทางวิศวกรรม', [0]*8),
            ('กลุ่มวิชาชีพบังคับ', [0]*8),
            ('กลุ่มวิชาชีพเลือก', [0]*8),
            ('กลุ่มวิชาสร้างเสริมประสบการณ์ในวิชาชีพ', [0]*8)
        ]
        plo_data = [('PLO1:', [0]*8)]

        def create_rows(row_type, data):
            for name, credits in data:
                CreditRow.objects.using(db).create(
                    curriculum=curriculum,
                    name=name,
                    row_type=row_type,
                    **{f'credits_sem{i+1}': credits[i] for i in range(8)}
                )

        create_rows('general', general_data)
        create_rows('core', core_data)
        create_rows('plo', plo_data)

        CreditRow.objects.using(db).create(
            curriculum=curriculum,
            name='หมวดวิชาเลือกเสรี',
            row_type='free',
            **{f'credits_sem{i+1}': 0 for i in range(8)}
        )

        return redirect('credit_table', curriculum_id=curriculum.id)
    
def sync_curriculum_real_to_example(request, curriculum_id):
    if request.session.get('access_mode') != 'edit':
        messages.error(request, "🚫 ต้องอยู่ในโหมดแก้ไขเท่านั้นจึงจะสำรองข้อมูลได้")
        return redirect('credit_table', curriculum_id=curriculum_id)

    curriculum_real = get_object_or_404(Curriculum.objects.using('real'), id=curriculum_id)

    Curriculum.objects.using('default').filter(id=curriculum_id).delete()
    CreditRow.objects.using('default').filter(curriculum_id=curriculum_id).delete()
    Course.objects.using('default').filter(curriculum_id=curriculum_id).delete()

    Curriculum.objects.using('default').create(
        id=curriculum_real.id,
        name=curriculum_real.name,
        password=curriculum_real.password
    )

    real_to_default_creditrow = {}
    for row in CreditRow.objects.using('real').filter(curriculum_id=curriculum_id):
        new_row = CreditRow.objects.using('default').create(
            curriculum_id=row.curriculum_id,
            name=row.name,
            row_type=row.row_type,
            credits_sem1=row.credits_sem1,
            credits_sem2=row.credits_sem2,
            credits_sem3=row.credits_sem3,
            credits_sem4=row.credits_sem4,
            credits_sem5=row.credits_sem5,
            credits_sem6=row.credits_sem6,
            credits_sem7=row.credits_sem7,
            credits_sem8=row.credits_sem8
        )
        real_to_default_creditrow[row.id] = new_row

    for course in Course.objects.using('real').filter(curriculum_id=curriculum_id):
        new_credit_row = real_to_default_creditrow.get(course.credit_row.id) if course.credit_row else None
        Course.objects.using('default').create(
            curriculum_id=course.curriculum_id,
            course_code=course.course_code,
            course_name=course.course_name,
            credits=course.credits,
            semester=course.semester,
            plo=course.plo,
            category=course.category,
            credit_row=new_credit_row
        )

    messages.success(request, "✅ สำรองข้อมูลหลักสูตรไปยังฐานตัวอย่างเรียบร้อยแล้ว")
    return redirect('credit_table', curriculum_id=curriculum_id)


def sync_curriculum_example_to_real(request, curriculum_id):
    if request.session.get('access_mode') != 'edit':
        messages.error(request, "🚫 ต้องอยู่ในโหมดแก้ไขเท่านั้นจึงจะดึงข้อมูลกลับได้")
        return redirect('credit_table', curriculum_id=curriculum_id)

    curriculum_example = get_object_or_404(Curriculum.objects.using('default'), id=curriculum_id)

    # ลบข้อมูลเก่าในฐาน real
    Curriculum.objects.using('real').filter(id=curriculum_id).delete()
    CreditRow.objects.using('real').filter(curriculum_id=curriculum_id).delete()
    Course.objects.using('real').filter(curriculum_id=curriculum_id).delete()

    # ดึง Curriculum
    Curriculum.objects.using('real').create(
        id=curriculum_example.id,
        name=curriculum_example.name,
        password=curriculum_example.password
    )

    # ดึง CreditRow และเก็บ mapping
    example_to_real_creditrow = {}
    for row in CreditRow.objects.using('default').filter(curriculum_id=curriculum_id):
        new_row = CreditRow.objects.using('real').create(
            curriculum_id=row.curriculum_id,
            name=row.name,
            row_type=row.row_type,
            credits_sem1=row.credits_sem1,
            credits_sem2=row.credits_sem2,
            credits_sem3=row.credits_sem3,
            credits_sem4=row.credits_sem4,
            credits_sem5=row.credits_sem5,
            credits_sem6=row.credits_sem6,
            credits_sem7=row.credits_sem7,
            credits_sem8=row.credits_sem8,
        )
        example_to_real_creditrow[row.id] = new_row

    # ดึง Course โดยใช้ CreditRow ใหม่
    for course in Course.objects.using('default').filter(curriculum_id=curriculum_id):
        new_credit_row = example_to_real_creditrow.get(course.credit_row.id) if course.credit_row else None
        Course.objects.using('real').create(
            curriculum_id=course.curriculum_id,
            course_code=course.course_code,
            course_name=course.course_name,
            credits=course.credits,
            semester=course.semester,
            plo=course.plo,
            category=course.category,
            credit_row=new_credit_row
        )

    messages.success(request, "✅ ดึงข้อมูลตัวอย่างกลับไปยังฐานหลักเรียบร้อยแล้ว (เขียนทับข้อมูลเก่า)")
    return redirect('credit_table', curriculum_id=curriculum_id)
