from django.db import models

    
class Curriculum(models.Model):
    name = models.CharField(max_length=255)
    password = models.CharField(max_length=100, blank=True)  # ✅ เพิ่มรหัสผ่าน

    def __str__(self):
        return self.name

class CreditRow(models.Model):
    curriculum = models.ForeignKey(Curriculum, on_delete=models.CASCADE)  # ✅ เพิ่ม
    ROW_TYPES = [
        ('general', 'General Education'),
        ('core', 'Core Education'),
        ('free', 'Free Elective'),
        ('plo', 'PLO Based'),
    ]

    name = models.CharField(max_length=200)
    row_type = models.CharField(max_length=10, choices=ROW_TYPES)
    credits_sem1 = models.IntegerField(default=0)
    credits_sem2 = models.IntegerField(default=0)
    credits_sem3 = models.IntegerField(default=0)
    credits_sem4 = models.IntegerField(default=0)
    credits_sem5 = models.IntegerField(default=0)
    credits_sem6 = models.IntegerField(default=0)
    credits_sem7 = models.IntegerField(default=0)
    credits_sem8 = models.IntegerField(default=0)

    def credit_list(self):
        return [
            self.credits_sem1, self.credits_sem2, self.credits_sem3, self.credits_sem4,
            self.credits_sem5, self.credits_sem6, self.credits_sem7, self.credits_sem8
        ]

    def total_credits(self):
        return sum(self.credit_list())

    def __str__(self):
        return f"{self.name} [{self.row_type}]"

class Course(models.Model):
    curriculum = models.ForeignKey(Curriculum, on_delete=models.CASCADE)  # ✅ เพิ่ม
    credit_row = models.ForeignKey(CreditRow, on_delete=models.CASCADE, related_name='courses', null=True, blank=True)
    category = models.CharField(max_length=50, blank=True, null=True)
    semester = models.PositiveSmallIntegerField(
        choices=[(i + 1, f'ปีที่ {i//2 + 1}/{i%2 + 1}') for i in range(8)]
    )
    course_code = models.CharField(max_length=20)
    course_name = models.CharField(max_length=255)
    credits = models.IntegerField()
    plo = models.CharField(max_length=10)

    def __str__(self):
        return f'{self.course_code} - {self.course_name}'

class YLOPerPLOSemester(models.Model):
    curriculum = models.ForeignKey('Curriculum', on_delete=models.CASCADE)
    plo = models.CharField(max_length=50)  # เช่น "PLO1", "PLO2"
    semester = models.PositiveSmallIntegerField()  # 1–8
    summary_text = models.TextField(blank=True, null=True)  # ✅ Rich Text สำหรับสรุป YLO

    def __str__(self):
        return f"YLO Summary {self.plo} - Sem {self.semester}"