# 🎓 Course Registration System (CLI Binary Engine)

> **Private Master Repository** — ระบบจัดการข้อมูลรายวิชา การลงทะเบียนเรียน และนักศึกษา แบบ Command Line Interface (CLI) ที่ประมวลผลผ่านไฟล์ไบนารีชนิด Fixed-length Record 3 ไฟล์ ด้วยภาษา Python (`struct` module)

---

## 👨‍💻 Project Information & Ownership
* **Developer:** Thitiwat Thaicharoen (AIGUS__) & Project Team
* **Course:** Computer Programming Project
* **Architecture:** Multi-Binary Fixed-Length File Storage (`.dat`)
* **Access Level:** Confidential / Internal Team Only

---

## 📌 System Features (ฟีเจอร์หลัก)
1. **👨‍🎓 Student Management:** เพิ่ม แก้ไข ลบ (Soft Delete) และดูข้อมูลนักศึกษา บันทึกลง `students.dat`
2. **📚 Course Management:** เพิ่ม แก้ไข ลบ (Soft Delete) และดูข้อมูลรายวิชา บันทึกลง `courses.dat`
3. **📝 Enrollment System:** ระบบลงทะเบียนเรียน เชื่อมโยง ID นักศึกษากับรายวิชา บันทึกลง `enrollments.dat`
4. **🔍 Advanced View & Analytics:** ระบบดูข้อมูลแบบ 4 โหมด (ดูทั้งหมด, ดูรายการเดียว, กรองคำค้นหา, สถิติสรุป ค่าธรรมเนียม Min/Max/Avg)
5. **✏️ In-Place Binary Update & Soft Delete:** แก้ไขข้อมูลแบบกระโดดทับตำแหน่งเดิมด้วย `seek()` และลบข้อมูลด้วยการเปลี่ยน Flag (`status = 0`) เพื่อคงโครงสร้างไบนารี
6. **📄 Auto Report & Sync:** สรุปสถิติข้อมูล Free Slots และประวัติการทำงานลงไฟล์ `report.txt` และ `operations.log` อัตโนมัติเมื่อปิดโปรแกรม

---

## 🛠️ Data Dictionary (Binary Record Structures)

ระบบใช้การจัดเก็บแบบ Little-Endian (`<`) โดยกำหนดขนาดไบต์คงที่ทุกไฟล์:

### 1. `courses.dat` (105-Byte Structure)
* **Struct Format String:** `"<I 15s 50s 20s I f I I"` (ขนาดรวม 105 ไบต์)

| Field Name | Format | Data Type | Size (Bytes) | Description & Padding |
| :--- | :---: | :--- | :---: | :--- |
| **course_id** | `I` | Unsigned Int | 4 | รหัสไอดีประจำวิชา (e.g. `1001`) |
| **code** | `15s` | String (Bytes) | 15 | รหัสวิชา (UTF-8, Padded with `\x00`) |
| **title** | `50s` | String (Bytes) | 50 | ชื่อรายวิชา (UTF-8, Padded with `\x00`) |
| **category** | `20s` | String (Bytes) | 20 | หมวดหมู่วิชา (UTF-8, Padded with `\x00`) |
| **credits** | `I` | Unsigned Int | 4 | จำนวนหน่วยกิต |
| **fee** | `f` | Single Float | 4 | ค่าธรรมเนียมการเรียน (บาท) |
| **status** | `I` | Unsigned Int | 4 | `1` = Active, `0` = Deleted (Soft Delete) |
| **enrolled** | `I` | Unsigned Int | 4 | `0` = Open/Available, `1` = Full/Closed |

### 2. `students.dat` (97-Byte Structure)
* **Struct Format String:** `"<Q 15s 50s 20s I I"` (ขนาดรวม 97 ไบต์)

| Field Name | Format | Data Type | Size (Bytes) | Description & Padding |
| :--- | :---: | :--- | :---: | :--- |
| **student_id** | `Q` | Unsigned Long Long | 8 | รหัสนักศึกษา 13 หลัก (e.g. `6906022610029`) |
| **code** | `15s` | String (Bytes) | 15 | รหัสอ้างอิงนักศึกษา (UTF-8) |
| **name** | `50s` | String (Bytes) | 50 | ชื่อ-นามสกุล (UTF-8) |
| **major** | `20s` | String (Bytes) | 20 | สาขาวิชา (UTF-8) |
| **year** | `I` | Unsigned Int | 4 | ชั้นปี (1-4) |
| **status** | `I` | Unsigned Int | 4 | `1` = Active, `0` = Deleted (Soft Delete) |

### 3. `enrollments.dat` (36-Byte Structure)
* **Struct Format String:** `"<I Q I 20s I"` (ขนาดรวม 36 ไบต์)

| Field Name | Format | Data Type | Size (Bytes) | Description & Padding |
| :--- | :---: | :--- | :---: | :--- |
| **enroll_id** | `I` | Unsigned Int | 4 | รหัสการลงทะเบียน |
| **student_id** | `Q` | Unsigned Long Long | 8 | รหัสนักศึกษาที่ลงทะเบียน |
| **course_id** | `I` | Unsigned Int | 4 | รหัสวิชาที่ลงทะเบียน |
| **enroll_date**| `20s` | String (Bytes) | 20 | วันเวลาที่ลงทะเบียน (`YYYY-MM-DD HH:MM:SS`) |
| **status** | `I` | Unsigned Int | 4 | `1` = Active, `0` = Cancelled |

---

## 📐 Binary Random Access Concept

เนื่องจากทุก Record มีขนาดคงที่ โปรแกรมคำนวณตำแหน่ง (Offset) ในไฟล์ไบนารีเพื่ออ่านหรือเขียนทับได้ทันที:

$$\text{Offset} = \text{Record Index} \times \text{RECORD\_SIZE}$$

```text
[ Record 0: 0 - 104 Bytes ] -> [ Record 1: 105 - 209 Bytes ] -> [ Record 2: 210 - 314 Bytes ]
                                 ▲
                                 │ file.seek(Record Index * Size) เพื่อเขียนทับข้อมูลทันที

## 🚀 How to Run
1. Clone Repository
Bash
git clone [https://github.com/Aigus25/Project_COMPRO.git](https://github.com/Aigus25/Project_COMPRO.git)
cd Project_COMPRO
2. Generate Mock Data (Optional)
หากต้องการสุ่มข้อมูลทดสอบ 60+ รายการใส่ไฟล์ไบนารี:

Bash
python generate_mock_data.py
3. Execute Application
Bash
python main.py
4. Exit & Report Generation
เลือกเมนู 0 ในโปรแกรม ระบบจะทำการ Flush/Sync ข้อมูล ล็อกประวัติลง operations.log และสร้างรายงานสรุป report.txt ให้อัตโนมัติ


<ElicitationsGroup message="ต้องการดำเนินการต่อในส่วนใดครับ:">
  <Elicitation label="ให้ช่วยจัดทำสไลด์นำเสนอโครงการ (Presentation Outline)" query="ช่วยเขียนโครงร่างสไลด์นำเสนอโครงการ (Presentation Outline) สำหรับพรีเซนต์งานอาจารย์"/>
</ElicitationsGroup>
