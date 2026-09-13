# 🎓 Course Registration System (CLI Binary Engine)

> **Private Master Repository** — ระบบจัดการข้อมูลรายวิชาและการลงทะเบียนเรียนแบบ Command Line Interface (CLI) ที่ประมวลผลข้อมูลผ่านระบบไฟล์ไบนารีชนิด Fixed-length Record ด้วยภาษา Python (`struct` module)

---

## 👨‍💻 Project Information & Ownership
* **Developer:** Thitiwat Thaicharoen (AIGUS__) & Project Team
* **Course:** Computer Programming Project
* **Architecture:** Fixed-Length Binary Storage (105-Byte Structure)
* **Access Level:** Confidential / Internal Team Only

---

## 📌 System Features (ฟีเจอร์หลัก)
1. **➕ Add Course:** เพิ่มรายวิชาใหม่ เข้ารหัสแบบ UTF-8 บันทึกลงไบนารีไฟล์ (`courses.dat`)
2. **✏️ In-Place Update:** แก้ไขข้อมูลรายวิชาแบบกระโดดทับตำแหน่งเดิมด้วย `seek()` โดยไม่ต้องสร้างไฟล์ใหม่
3. **🗑️ Soft Delete:** ลบรายวิชาแบบเปลี่ยน Flag สถานะ (`status = 0`) เพื่อคงความสมบูรณ์ของโครงสร้างไบนารี
4. **📖 View All Courses:** ดึงรายการวิชาที่ใช้งานอยู่ (`status = 1`) มาแสดงผลบน Terminal
5. **📄 Report Generator:** ประมวลผลและสร้างรายงานสรุป (`report.txt`) แสดงสถิติค่าธรรมเนียม (Min/Max/Avg) และจำแนกตามหมวดหมู่รายวิชา

---

## 🛠️ Data Dictionary (105-Byte Structure)

การจัดเก็บข้อมูลใช้โครงสร้างแบบ Little-Endian (`<`) มีขนาดรวม **105 ไบต์ต่อ 1 Record** เท่ากันทุกรายการ

| Field Name | Format | Data Type | Size (Bytes) | Description & Padding |
| :--- | :---: | :--- | :---: | :--- |
| **course_id** | `I` | Unsigned Int | 4 | รหัสไอดีประจำวิชา (e.g. `1001`) |
| **code** | `15s` | String (Bytes) | 15 | รหัสวิชา (UTF-8, Padded with `\x00`) |
| **title** | `50s` | String (Bytes) | 50 | ชื่อรายวิชา (UTF-8, Padded with `\x00`) |
| **category** | `20s` | String (Bytes) | 20 | หมวดหมู่วิชา (UTF-8, Padded with `\x00`) |
| **credits** | `I` | Unsigned Int | 4 | จำนวนหน่วยกิต |
| **fee** | `f` | Single Float | 4 | ค่าธรรมเนียมการเรียน (บาท) |
| **status** | `I` | Unsigned Int | 4 | `1` = Active, `0` = Deleted (Soft Delete) |
| **enrolled** | `I` | Unsigned Int | 4 | `0` = Available, `1` = Full/Closed |

> **Struct Format String:** `"<I 15s 50s 20s I f I I"`  
> **Total Size Formula:** `4 + 15 + 50 + 20 + 4 + 4 + 4 + 4 = 105 Bytes`

---

## 📐 Binary Random Access Concept

เนื่องจากทุก Record มีขนาด 105 ไบต์เท่ากันหมด โปรแกรมสามารถคำนวณตำแหน่ง (Offset) ในไฟล์เพื่ออ่านหรือเขียนทับได้ทันทีโดยใช้สูตร:

$$\text{Offset} = \text{Record Index} \times 105$$

```text
[ Record 0: 0 - 104 Bytes ] -> [ Record 1: 105 - 209 Bytes ] -> [ Record 2: 210 - 314 Bytes ]
                                 ▲
                                 │ file.seek(105) เพื่อเขียนทับ Record 1 ได้ทันที


🚀 How to Run
Clone Private Repository

Bash
git clone [https://github.com/Aigus25/Project_COMPRO.git](https://github.com/Aigus25/Project_COMPRO.git)
cd Project_COMPRO
Execute Application

Bash
python main.py
Generate Report
เลือกเมนู 5 ในโปรแกรม ระบบจะคำนวณข้อมูลใน courses.dat และสร้างไฟล์ report.txt ให้อัตโนมัติ
