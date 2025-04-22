from django.shortcuts import render, redirect, get_object_or_404
from .models import Curriculum, CreditRow, Course
from django.db.models import Sum
import re

headers = ['ปีที่ 1/1', 'ปีที่ 1/2', 'ปีที่ 2/1', 'ปีที่ 2/2',
           'ปีที่ 3/1', 'ปีที่ 3/2', 'ปีที่ 4/1', 'ปีที่ 4/2']

def select_curriculum(request):
    if request.method == 'POST':
        curriculum_id = request.POST.get('curriculum')
        if curriculum_id:
            return redirect('credit_table', curriculum_id=curriculum_id)

    curriculums = Curriculum.objects.all()
    return render(request, 'table/select_curriculum.html', {'curriculums': curriculums})

def credit_table(request, curriculum_id):
    curriculum = get_object_or_404(Curriculum, pk=curriculum_id)

    if request.method == 'POST':
        # ✅ บันทึกชื่อหลักสูตรถ้ามีการแก้ไข
        new_name = request.POST.get('curriculum_name', '').strip()
        if new_name and new_name != curriculum.name:
            curriculum.name = new_name
            curriculum.save()

        def delete_removed_rows(row_type, prefix_list):
            posted_names = set()
            for prefix in prefix_list:
                pattern = re.compile(rf'{prefix}_(\d+)')
                for key in request.POST:
                    match = pattern.match(key)
                    if match:
                        index = match.group(1)
                        name = request.POST.get(f'{prefix}_{index}', '').strip()
                        if name:
                            posted_names.add(name)
            CreditRow.objects.filter(curriculum=curriculum, row_type=row_type).exclude(name__in=posted_names).delete()

        def save_rows(row_type, prefix, credit_prefix):
            pattern = re.compile(rf'{prefix}_(\d+)')
            indices = sorted({match.group(1) for key in request.POST for match in [pattern.match(key)] if match})

            for index in indices:
                name = request.POST.get(f'{prefix}_{index}', '').strip()
                if not name:
                    continue

                credits = [int(request.POST.get(f'{credit_prefix}_{index}_{j}', 0)) for j in range(8)]

                row, created = CreditRow.objects.get_or_create(
                    curriculum=curriculum,
                    name=name,
                    row_type=row_type,
                    defaults={
                        'credits_sem1': credits[0], 'credits_sem2': credits[1],
                        'credits_sem3': credits[2], 'credits_sem4': credits[3],
                        'credits_sem5': credits[4], 'credits_sem6': credits[5],
                        'credits_sem7': credits[6], 'credits_sem8': credits[7],
                    }
                )

                if not created:
                    row.credits_sem1 = credits[0]
                    row.credits_sem2 = credits[1]
                    row.credits_sem3 = credits[2]
                    row.credits_sem4 = credits[3]
                    row.credits_sem5 = credits[4]
                    row.credits_sem6 = credits[5]
                    row.credits_sem7 = credits[6]
                    row.credits_sem8 = credits[7]
                    row.save()

        delete_removed_rows('general', ['general_name', 'general_name_new'])
        delete_removed_rows('core', ['core_name', 'core_name_new'])
        delete_removed_rows('plo', ['plo_name', 'plo_name_new'])

        save_rows('general', 'general_name', 'general_credit')
        save_rows('core', 'core_name', 'core_credit')
        save_rows('plo', 'plo_name', 'plo_credit')
        save_rows('general', 'general_name_new', 'general_credit_new')
        save_rows('core', 'core_name_new', 'core_credit_new')
        save_rows('plo', 'plo_name_new', 'plo_credit_new')

        free_name = 'หมวดวิชาเลือกเสรี'
        free_credits = [int(request.POST.get(f'{free_name}_{i}', 0)) for i in range(8)]
        CreditRow.objects.update_or_create(
            curriculum=curriculum,
            name=free_name,
            row_type='free',
            defaults={
                'credits_sem1': free_credits[0], 'credits_sem2': free_credits[1],
                'credits_sem3': free_credits[2], 'credits_sem4': free_credits[3],
                'credits_sem5': free_credits[4], 'credits_sem6': free_credits[5],
                'credits_sem7': free_credits[6], 'credits_sem8': free_credits[7],
            }
        )

        return redirect('credit_table', curriculum_id=curriculum.id)

    all_rows = CreditRow.objects.filter(curriculum=curriculum)
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
                general_core_sum = Course.objects.filter(
                    curriculum=curriculum,
                    semester=semester,
                    plo=plo_tag,
                    credit_row__row_type__in=['general', 'core']
                ).aggregate(Sum('credits'))['credits__sum'] or 0

                free_sum = Course.objects.filter(
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
        semester = int(semester)
        plo_semester_totals[semester] += value

    # ✅ คำนวณหน่วยกิตรวมของหลักสูตรทั้งหมด
    total_credits_all = sum(row.total_credits() for row in all_rows)

    # ✅ คำนวณเปอร์เซ็นต์ของแต่ละ PLO
    plo_percentages = {}
    for row in all_rows.filter(row_type='plo'):
        plo_percentages[str(row.id)] = (
            round((row.total_credits() / total_credits_all) * 100, 2) if total_credits_all else 0
        )

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
        'plo_percentages': plo_percentages,   # ✅ เพิ่มตรงนี้
    })

def reset_credit_table(request, curriculum_id):
    curriculum = get_object_or_404(Curriculum, pk=curriculum_id)

    if request.method == 'POST':
        # ลบข้อมูลเดิมทั้งหมดในตาราง CreditRow สำหรับหลักสูตรนี้
        CreditRow.objects.filter(curriculum=curriculum, row_type__in=['general', 'core', 'plo', 'free']).delete()

        # ข้อมูล default สำหรับหมวดวิชาศึกษาทั่วไป
        general_data = [
            ('กลุ่มวิชาภาษา', [0]*8),
            ('กลุ่มวิชาสังคมศาสตร์', [0]*8),
            ('กลุ่มวิชามนุษยศาสตร์', [0]*8),
            ('กลุ่มวิชาพลศึกษาและนันทนาการ', [0]*8),
            ('กลุ่มวิชาวิทยาศาสตร์', [0]*8),
            ('กลุ่มวิชาคณิตศาสตร์และคอมพิวเตอร์', [0]*8),
            ('กลุ่มวิชาบูรณาการ', [0]*8)
        ]

        # ข้อมูล default สำหรับหมวดวิชาเฉพาะ
        core_data = [
            ('กลุ่มวิชาพื้นฐานทางวิทยาศาสตร์และคณิตศาสตร์', [0]*8),
            ('กลุ่มวิชาพื้นฐานทางวิศวกรรม', [0]*8),
            ('กลุ่มวิชาชีพบังคับ', [0]*8),
            ('กลุ่มวิชาชีพเลือก', [0]*8),
            ('กลุ่มวิชาสร้างเสริมประสบการณ์ในวิชาชีพ', [0]*8)
        ]

        # ข้อมูล default สำหรับหมวด PLOs: มีเพียง 2 แถว
        plo_data = [
            ('PLO1:', [0]*8),
        ]

        # ฟังก์ชันช่วยสำหรับสร้าง CreditRow
        def create_rows(row_type, data):
            for name, credits in data:
                CreditRow.objects.create(
                    curriculum=curriculum,
                    name=name,
                    row_type=row_type,
                    credits_sem1=credits[0], credits_sem2=credits[1],
                    credits_sem3=credits[2], credits_sem4=credits[3],
                    credits_sem5=credits[4], credits_sem6=credits[5],
                    credits_sem7=credits[6], credits_sem8=credits[7],
                )

        create_rows('general', general_data)
        create_rows('core', core_data)
        create_rows('plo', plo_data)

        # เพิ่มหมวดวิชาเลือกเสรี
        CreditRow.objects.create(
            curriculum=curriculum,
            name='หมวดวิชาเลือกเสรี',
            row_type='free',
            credits_sem1=0, credits_sem2=0,
            credits_sem3=0, credits_sem4=0,
            credits_sem5=0, credits_sem6=0,
            credits_sem7=0, credits_sem8=0,
        )

        return redirect('credit_table', curriculum_id=curriculum.id)

