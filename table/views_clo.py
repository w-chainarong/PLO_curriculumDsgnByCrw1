from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseNotFound
from django.contrib import messages
from .models import Curriculum, Course, KSECItem, CLO, CLOSummary
import re


# ✅ ตรวจสอบโหมดฐานข้อมูลจาก session
def get_db_alias(request):
    # ✅ รองรับทั้ง query string (?mode=edit) และ session
    mode = request.GET.get('mode') or request.session.get('access_mode', 'view')
    return 'real' if mode == 'edit' else 'default'


# ✅ แปลงข้อความ KSEC เป็นรายการ code
def parse_ksec_list(text):
    return [item.strip().replace(" ", "") for item in text.split(',')] if text else []

# ✅ สร้างรายการ code กับคำอธิบายจาก KSECItem
def get_ksec_map(curriculum, db, ksec_list, ksec_type):
    ksec_items = KSECItem.objects.using(db).filter(
        curriculum=curriculum, type=ksec_type, semester=0
    ).order_by('category_type', 'sort_order')

    ksec_lookup = {
        f"{item.category_type}({item.type}){item.sort_order + 1}".replace(" ", ""): item.description.strip()
        for item in ksec_items
    }

    return [(code, ksec_lookup.get(code.replace(" ", ""), '')) for code in ksec_list]

# ✅ ลบ prefix CLO1:, CLO2:, ... แล้วคืนข้อความที่ไม่มี prefix
def strip_clo_prefix(text):
    return re.sub(r'^CLO\s*\d+\s*:?', '', text or '').strip()

# ✅ ตัวแปร Bloom ทั้ง 3 domains
bloom_domains = {
    'Cognitive': [
        ('Remember', 'list, define, recall, identify, label'),
        ('Understand', 'summarize, describe, interpret, explain, classify'),
        ('Apply', 'use, implement, execute, solve, demonstrate'),
        ('Analyze', 'compare, contrast, differentiate, examine'),
        ('Evaluate', 'judge, critique, defend, argue, support'),
        ('Create', 'design, construct, develop, formulate, invent'),
    ],
    'Affective': [
        ('Receiving', 'ask, follow, give, hold, name, point to, reply'),
        ('Responding', 'answer, comply, help, present, tell, write'),
        ('Valuing', 'complete, demonstrate, express, justify, propose'),
        ('Organization', 'compare, defend, integrate, organize, prepare'),
        ('Characterization', 'display, influence, perform, revise, verify'),
    ],
    'Psychomotor': [
        ('Imitation', 'copy, follow, replicate, repeat, adhere'),
        ('Manipulation', 'execute, implement, operate, perform'),
        ('Precision', 'demonstrate, calibrate, show, perfect'),
        ('Articulation', 'construct, adapt, integrate, refine'),
        ('Naturalization', 'design, initiate, create, compose, master'),
    ],
}

# ✅ คะแนนสูงสุดของแต่ละ level
bloom_scores = {
    'Cognitive': {
        'Remember': 1, 'Understand': 2, 'Apply': 3,
        'Analyze': 4, 'Evaluate': 5, 'Create': 6,
    },
    'Affective': {
        'Receiving': 1, 'Responding': 2, 'Valuing': 3,
        'Organization': 4, 'Characterization': 5,
    },
    'Psychomotor': {
        'Imitation': 1, 'Manipulation': 2, 'Precision': 3,
        'Articulation': 4, 'Naturalization': 5,
    },
}

# ✅ ฟังก์ชันหาคะแนนสูงสุดของ CLO ทั้งหมด
def get_final_bloom_score(clo_list):
    scores = []
    for clo in clo_list:
        bloom = clo.get('bloom', '')
        for domain, levels in bloom_scores.items():
            if bloom in levels:
                scores.append(levels[bloom])
    return max(scores) if scores else 0

# ✅ คำนวณ % ความครอบคลุม KSEC
def compute_ksec_percent(clo_list, ksec_items):
    def get_total_codes(items):
        return set(code for code, _ in items)

    def get_selected_codes(clo_list, key):
        return set(clo[key].strip() for clo in clo_list if clo.get(key, '').strip())

    k_all = get_total_codes(ksec_items['K'])
    s_all = get_total_codes(ksec_items['S'])
    e_all = get_total_codes(ksec_items['E'])
    c_all = get_total_codes(ksec_items['C'])

    k_sel = get_selected_codes(clo_list, 'k')
    s_sel = get_selected_codes(clo_list, 's')
    e_sel = get_selected_codes(clo_list, 'e')
    c_sel = get_selected_codes(clo_list, 'c')

    return {
        'k_percent': round(len(k_sel) / len(k_all) * 100, 2) if k_all else 0,
        's_percent': round(len(s_sel) / len(s_all) * 100, 2) if s_all else 0,
        'e_percent': round(len(e_sel) / len(e_all) * 100, 2) if e_all else 0,
        'c_percent': round(len(c_sel) / len(c_all) * 100, 2) if c_all else 0,
    }

# ✅ แสดงหน้า CLO-KSEC Mapping
def clo_ksec_mapping(request, curriculum_id, course_id):
    db = get_db_alias(request)
    curriculum = get_object_or_404(Curriculum.objects.using(db), id=curriculum_id)
    course = get_object_or_404(Course.objects.using(db), id=course_id, curriculum=curriculum)

    readonly = (db != 'real')
    session_saved = request.session.pop('session_saved_flag', False)
    from_link = request.GET.get("from_link") == "1"  # ✅ เช็คการเข้าจากลิงก์

    # ✅ ชื่อตัวแปร session
    session_clo_key = f"clo_list_{curriculum_id}_{course_id}"
    session_desc_key = f"course_desc_{curriculum_id}_{course_id}"

    # ✅ ถ้ามาจากลิงก์โดยตรง → ล้าง session ก่อนโหลด
    if readonly and from_link:
        request.session.pop(session_clo_key, None)
        request.session.pop(session_desc_key, None)
        request.session.pop('session_saved_flag', None)

    # ✅ ดึงรายการ K/S/E/C ที่ตรงกับหลักสูตรและประเภท
    k_items = get_ksec_map(curriculum, db, parse_ksec_list(course.knowledge), 'K')
    s_items = get_ksec_map(curriculum, db, parse_ksec_list(course.skills), 'S')
    e_items = get_ksec_map(curriculum, db, parse_ksec_list(course.ethics), 'E')
    c_items = get_ksec_map(curriculum, db, parse_ksec_list(course.character), 'C')

    # ✅ เงื่อนไขการโหลดข้อมูล
    if readonly and session_saved:
        # ✅ ใช้ session หลังบันทึก และลบทิ้ง
        clo_list = request.session.pop(session_clo_key, [])
        course_description = request.session.pop(session_desc_key, course.description or "")
    elif readonly and (session_clo_key in request.session or session_desc_key in request.session):
        # ✅ รหัสผิดหรือ session ยังค้าง → ใช้ session (ไม่ลบ)
        clo_list = request.session.get(session_clo_key, [])
        course_description = request.session.get(session_desc_key, course.description or "")
    else:
        # ✅ โหลดจากฐานข้อมูล default หรือ real
        clo_objs = CLO.objects.using(db).filter(course_id=course_id).order_by('index')
        clo_list = [
            {
                'index': clo.index,
                'clo': clo.clo,
                'bloom': clo.bloom,
                'k': clo.k,
                's': clo.s,
                'e': clo.e,
                'c': clo.c,
            }
            for clo in clo_objs
        ]
        course_description = course.description or ""

        # ✅ ล้าง session เฉพาะเมื่ออยู่ใน edit mode (กัน session ค้าง)
        if not readonly:
            request.session.pop(session_clo_key, None)
            request.session.pop(session_desc_key, None)

    # ✅ คำนวณคะแนน Bloom และ % การครอบคลุม KSEC
    final_bloom_score = get_final_bloom_score(clo_list)
    percentages = compute_ksec_percent(clo_list, {
        'K': k_items, 'S': s_items, 'E': e_items, 'C': c_items
    })

    return render(request, 'table/clo_ksec_mapping.html', {
        'curriculum': curriculum,
        'course': course,
        'clo_list': clo_list,
        'bloom_domains': bloom_domains,
        'final_bloom_score': final_bloom_score,
        'k_items': k_items,
        's_items': s_items,
        'e_items': e_items,
        'c_items': c_items,
        'course_description': course_description,
        'readonly': readonly,
        'session_saved': session_saved,
        **percentages,
    })




# ✅ บันทึก CLO ทั้งหมดลงฐาน real (รวมถึง course.description)
def save_clo_ksec_mapping(request, curriculum_id, course_id):
    if request.method != 'POST':
        return HttpResponseNotFound("⛔ Method ไม่ถูกต้อง")

    # ✅ ดึงข้อมูลหลักสูตรและวิชาจากฐานทั้ง 2
    curriculum_real = get_object_or_404(Curriculum.objects.using('real'), id=curriculum_id)
    curriculum_default = get_object_or_404(Curriculum.objects.using('default'), id=curriculum_id)
    course_real = get_object_or_404(Course.objects.using('real'), id=course_id, curriculum=curriculum_real)

    # ✅ เตรียมข้อมูลจาก POST
    course_description = request.POST.get('course_description', '').strip()
    total = len(request.POST.getlist('clo[]'))
    clo_list = []

    # ✅ ลบ CLO และ CLOSummary เก่าในทั้ง 2 ฐาน
    for db in ['real', 'default']:
        CLO.objects.using(db).filter(course_id=course_id).delete()
        CLOSummary.objects.using(db).filter(course_id=course_id).delete()

    # ✅ สร้างรายการ CLO ใหม่
    for i in range(total):
        clo_text = strip_clo_prefix(request.POST.getlist('clo[]')[i])
        clo_data = {
            'bloom': request.POST.getlist('bloom[]')[i],
            'k': request.POST.getlist('k[]')[i],
            's': request.POST.getlist('s[]')[i],
            'e': request.POST.getlist('e[]')[i],
            'c': request.POST.getlist('c[]')[i],
        }
        clo_full_text = f"CLO{i+1}: {clo_text}"
        clo_list.append({'index': i+1, 'clo': clo_full_text, **clo_data})

        for db in ['real', 'default']:
            CLO.objects.using(db).create(
                course_id=course_id,
                index=i+1,
                clo=clo_full_text,
                bloom=clo_data['bloom'],
                k=clo_data['k'],
                s=clo_data['s'],
                e=clo_data['e'],
                c=clo_data['c']
            )

    # ✅ สร้าง CLOSummary ใหม่
    k_items = get_ksec_map(curriculum_real, 'real', parse_ksec_list(course_real.knowledge), 'K')
    s_items = get_ksec_map(curriculum_real, 'real', parse_ksec_list(course_real.skills), 'S')
    e_items = get_ksec_map(curriculum_real, 'real', parse_ksec_list(course_real.ethics), 'E')
    c_items = get_ksec_map(curriculum_real, 'real', parse_ksec_list(course_real.character), 'C')

    bloom_score = get_final_bloom_score(clo_list)
    percents = compute_ksec_percent(clo_list, {
        'K': k_items, 'S': s_items, 'E': e_items, 'C': c_items
    })

    for db in ['real', 'default']:
        CLOSummary.objects.using(db).create(
            course_id=course_id,
            bloom_score=bloom_score,
            k_percent=percents['k_percent'],
            s_percent=percents['s_percent'],
            e_percent=percents['e_percent'],
            c_percent=percents['c_percent'],
        )

    # ✅ บันทึก description ลงทั้งฐาน real และ default
    course_real.description = course_description
    course_real.save(using='real')

    course_default = get_object_or_404(Course.objects.using('default'), id=course_id, curriculum=curriculum_default)
    course_default.description = course_description
    course_default.save(using='default')

    messages.success(request, "✅ บันทึก CLO-KSEC สำเร็จ (real + example)")
    return redirect('clo_ksec_mapping', curriculum_id=curriculum_id, course_id=course_id)

# ✅ รีเซ็ต CLO ทั้งหมด
def reset_clo_ksec_mapping(request, curriculum_id, course_id):
    # ✅ ลบ CLO และ CLOSummary ทั้ง 2 ฐาน
    for db in ['real', 'default']:
        CLO.objects.using(db).filter(course_id=course_id).delete()
        CLOSummary.objects.using(db).filter(course_id=course_id).delete()

    # ✅ ลบคำอธิบาย (description) ทั้ง 2 ฐาน
    for db in ['real', 'default']:
        course = get_object_or_404(Course.objects.using(db), id=course_id)
        course.description = ""
        course.save(using=db)

    messages.success(request, "♻️ รีเซ็ต CLO-KSEC สำเร็จแล้ว (ทั้ง real และ default)")
    return redirect('clo_ksec_mapping', curriculum_id=curriculum_id, course_id=course_id)


def save_clo_ksec_to_session(request, curriculum_id, course_id):
    if request.method != 'POST':
        return HttpResponseNotFound("⛔ Method ไม่ถูกต้อง")

    # ✅ เก็บข้อมูลที่กรอกลง session ก่อนตรวจรหัส
    clo_list = build_clo_list_from_post(request)
    course_description = request.POST.get('course_description', '').strip()

    request.session[f"clo_list_{curriculum_id}_{course_id}"] = clo_list
    request.session[f"course_desc_{curriculum_id}_{course_id}"] = course_description
    request.session.modified = True  # ✅ บังคับ Django ให้ save session ทันที

    # ✅ ตรวจสอบรหัสผ่านหลังจากบันทึกข้อมูลแล้ว
    password = request.POST.get('session_password', '').strip()
    curriculum = get_object_or_404(Curriculum.objects.using('default'), id=curriculum_id)
    expected_password = (curriculum.clo_edit_password or '').strip()

    if password != expected_password:
        messages.error(request, "❌ รหัสผ่านไม่ถูกต้อง กรุณาลองใหม่")
        return redirect('clo_ksec_mapping', curriculum_id=curriculum_id, course_id=course_id)

    # ✅ รหัสถูกต้อง → ตั้ง flag เพื่อให้ clo_ksec_mapping เปิดปุ่ม 📂
    request.session['session_saved_flag'] = True
    messages.success(request, "💾 บันทึก CLO-KSEC ลง session เรียบร้อยแล้ว")
    return redirect('clo_ksec_mapping', curriculum_id=curriculum_id, course_id=course_id)


def build_clo_list_from_post(request):
    total = len(request.POST.getlist('clo[]'))
    clo_list = []

    for i in range(total):
        clo_text = strip_clo_prefix(request.POST.getlist('clo[]')[i])
        clo_data = {
            'bloom': request.POST.getlist('bloom[]')[i],
            'k': request.POST.getlist('k[]')[i],
            's': request.POST.getlist('s[]')[i],
            'e': request.POST.getlist('e[]')[i],
            'c': request.POST.getlist('c[]')[i],
        }
        clo_full_text = f"CLO{i+1}: {clo_text}"
        clo_list.append({'index': i+1, 'clo': clo_full_text, **clo_data})

    return clo_list
