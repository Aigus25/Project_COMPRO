# 🎓 Course Registration System (CLI Binary Engine)

> **Private Master Repository** — ระบบจัดการข้อมูลนักศึกษา, รายวิชา และการลงทะเบียนเรียนแบบ Command Line Interface (CLI) ที่ประมวลผลข้อมูลผ่านระบบไฟล์ไบนารีชนิด Fixed-length Record จำนวน 3 ไฟล์ ด้วยภาษา Python (`struct` module)

---

## 👨‍💻 Project Information & Ownership
* **Developer:** Thitiwat Thaicharoen (AIGUS__) & Project Team
* **Course:** Computer Programming Project
* **Architecture:** Fixed-Length Binary Storage (3 Files, Little-Endian)
* **Access Level:** Confidential / Internal Team Only

---

## 📌 System Features (ฟีเจอร์หลัก)

ระบบแบ่งการทำงานออกเป็น 3 module หลัก ตามไฟล์ข้อมูล:

### 1) 📚 Course Management (`courses.dat`)
- **➕ Add:** เพิ่มรายวิชาใหม่ เข้ารหัสแบบ UTF-8 บันทึกลงไบนารี
- **✏️ Update (In-Place):** แก้ไขข้อมูลรายวิชาแบบกระโดดทับตำแหน่งเดิมด้วย `seek()` โดยไม่ต้องสร้างไฟล์ใหม่
- **🗑️ Soft Delete:** ลบรายวิชาแบบเปลี่ยน Flag สถานะ (`status = 0`) เพื่อคงความสมบูรณ์ของโครงสร้างไบนารี
- **📖 View:** ดูทั้งหมด / ดูรายการเดียว (ตาม ID) / ดูแบบกรอง (ตามหมวดวิชา) / สถิติโดยสรุป (Min/Max/Avg Fee)

### 2) 🧑‍🎓 Student Management (`students.dat`)
- Add / Update / Soft Delete / View (ทั้งหมด, รายการเดียว, กรองตามสาขา, สถิติ)
- กันการเพิ่ม Student ID ซ้ำกับรายการที่ยัง Active อยู่

### 3) 📝 Enrollment Management (`enrollments.dat`)
- **ลงทะเบียน:** ผูกนักศึกษาเข้ากับรายวิชา พร้อมตรวจสอบว่านักศึกษา/วิชามีอยู่จริง วิชายังไม่เต็ม และไม่ได้ลงทะเบียนซ้ำวิชาเดิม
- **ยกเลิกการลงทะเบียน:** Soft Delete (`status = 0`)
- **View:** ดูทั้งหมด / ดูตาม Student ID / ดูตาม Course ID / สถิติโดยสรุป

### 4) 📄 Report Generator (`report.txt`)
สร้างรายงานสรุปที่รวมข้อมูลจากทั้ง 3 ไฟล์ ประกอบด้วย:
- ตารางรายวิชา / นักศึกษา / การลงทะเบียนทั้งหมด (รวม Active และ Deleted)
- สรุปจำนวน Active/Deleted ของแต่ละไฟล์
- **Free Slots** — จำนวน record ที่ถูก soft-delete แล้ว (พื้นที่ที่เหลือ)
- สถิติค่าธรรมเนียม (Min/Max/Avg) และจำนวนวิชาแยกตามหมวดหมู่
- **ประวัติการทำงานล่าสุด** (อ่านจาก `operations.log`)

### 5) 🔒 Safe Exit
เมื่อเลือกออกจากโปรแกรม ระบบจะ `fsync()` ไฟล์ไบนารีทั้ง 3 ไฟล์ และสร้างรายงานสรุปให้อัตโนมัติก่อนปิดโปรแกรมทุกครั้ง

---

## 🛠️ Data Dictionary

การจัดเก็บข้อมูลทุกไฟล์ใช้โครงสร้างแบบ Little-Endian (`<`) และ Fixed-length Record

### `students.dat` — 107 ไบต์/record

| Field | Format | Size (Bytes) | Description |
| :--- | :---: | :---: | :--- |
| **student_id** | `I` | 4 | รหัสไอดีนักศึกษา |
| **student_code** | `15s` | 15 | รหัสนักศึกษา (UTF-8, Padded) |
| **name** | `50s` | 50 | ชื่อ-สกุล (UTF-8, Padded) |
| **major** | `20s` | 20 | สาขาวิชา (UTF-8, Padded) |
| **year** | `I` | 4 | ชั้นปี |
| **status** | `I` | 4 | `1` = Active, `0` = Deleted |

> **Struct Format String:** `"<I 15s 50s 20s I I"`

### `courses.dat` — 105 ไบต์/record

| Field | Format | Size (Bytes) | Description |
| :--- | :---: | :---: | :--- |
| **course_id** | `I` | 4 | รหัสไอดีประจำวิชา (e.g. `1001`) |
| **code** | `15s` | 15 | รหัสวิชา (UTF-8, Padded) |
| **title** | `50s` | 50 | ชื่อรายวิชา (UTF-8, Padded) |
| **category** | `20s` | 20 | หมวดหมู่วิชา (UTF-8, Padded) |
| **credits** | `I` | 4 | จำนวนหน่วยกิต |
| **fee** | `f` | 4 | ค่าธรรมเนียมการเรียน (บาท) |
| **status** | `I` | 4 | `1` = Active, `0` = Deleted (Soft Delete) |
| **enrolled** | `I` | 4 | `0` = Available, `1` = Full/Closed |

> **Struct Format String:** `"<I 15s 50s 20s I f I I"`
> **Total Size Formula:** `4 + 15 + 50 + 20 + 4 + 4 + 4 + 4 = 105 Bytes`

### `enrollments.dat` — 36 ไบต์/record

| Field | Format | Size (Bytes) | Description |
| :--- | :---: | :---: | :--- |
| **enroll_id** | `I` | 4 | รหัสไอดีการลงทะเบียน |
| **student_id** | `I` | 4 | อ้างอิงไปยัง `students.dat` |
| **course_id** | `I` | 4 | อ้างอิงไปยัง `courses.dat` |
| **enroll_date** | `20s` | 20 | วันที่ลงทะเบียน (UTF-8, `YYYY-MM-DD HH:MM:SS`) |
| **status** | `I` | 4 | `1` = ลงทะเบียนอยู่, `0` = ยกเลิก |

> **Struct Format String:** `"<I I I 20s I"`

---

## 📐 Binary Random Access Concept

เนื่องจากทุก Record ในแต่ละไฟล์มีขนาดคงที่เท่ากันหมด โปรแกรมสามารถคำนวณตำแหน่ง (Offset) ในไฟล์เพื่ออ่านหรือเขียนทับได้ทันทีโดยใช้สูตร:

$$\text{Offset} = \text{Record Index} \times \text{Record Size}$$

```text
[ Record 0: 0 - (N-1) Bytes ] -> [ Record 1: N - (2N-1) Bytes ] -> [ Record 2: 2N - (3N-1) Bytes ]
                                    ▲
                                    │ file.seek(N) เพื่อเขียนทับ Record 1 ได้ทันที
```

โดย N = ขนาด record ของไฟล์นั้นๆ (105 สำหรับ courses.dat, 107 สำหรับ students.dat, 36 สำหรับ enrollments.dat)

---

## 🗂️ ไฟล์ที่เกี่ยวข้อง

| ไฟล์ | ประเภท | หน้าที่ |
| :--- | :--- | :--- |
| `main.py` | Source Code | โปรแกรมหลัก (CRUD + Report) |
| `students.dat` | Binary Data | ข้อมูลนักศึกษา |
| `courses.dat` | Binary Data | ข้อมูลรายวิชา |
| `enrollments.dat` | Binary Data | ข้อมูลการลงทะเบียน |
| `operations.log` | Text Log | ประวัติการทำงานทุกครั้ง (ใช้แสดงในรายงาน) |
| `report.txt` | Text Report | รายงานสรุปที่สร้างจากทั้ง 3 ไฟล์ข้างต้น |

---

## 🚀 How to Run

**Clone Private Repository**
```bash
git clone https://github.com/Aigus25/Project_COMPRO.git
cd Project_COMPRO
```

**Execute Application**
```bash
python main.py
```

**เมนูหลัก**
```
1) จัดการรายวิชา (Courses)
2) จัดการนักศึกษา (Students)
3) การลงทะเบียนเรียน (Enrollments)
4) สร้างรายงานสรุป (Generate Report)
0) ออกจากโปรแกรม (Exit)
```

**Generate Report**
เลือกเมนู `4` ในโปรแกรม ระบบจะประมวลผลข้อมูลจาก `students.dat`, `courses.dat`, `enrollments.dat` และสร้างไฟล์ `report.txt` ให้อัตโนมัติ (หรือจะเลือกเมนู `0` เพื่อออกจากโปรแกรม ระบบก็จะสร้างรายงานให้อัตโนมัติก่อนปิดเช่นกัน)
