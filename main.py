import struct
import os
import datetime

# โครงสร้าง 105 Bytes (Fixed-length Record)
# I   = Course ID (4 bytes)
# 15s = Course Code (15 bytes)
# 50s = Title (50 bytes)
# 20s = Category (20 bytes)
# I   = Credits (4 bytes)
# f   = Tuition Fee (4 bytes)
# I   = Status (4 bytes: 1=Active, 0=Deleted)
# I   = Enrolled/Closed (4 bytes: 1=Full/Closed, 0=Available)
FORMAT = "<I 15s 50s 20s I f I I"
RECORD_SIZE = struct.calcsize(FORMAT)
FILENAME = "courses.dat"

def add_course():
    """1) เพิ่มรายวิชาใหม่"""
    print("\n--- ➕ เพิ่มรายวิชาใหม่ ---")
    try:
        course_id = int(input("ป้อน Course ID (เช่น 1001): "))
        code = input("ป้อนรหัสวิชา (เช่น CS101): ")
        title = input("ป้อนชื่อรายวิชา: ")
        category = input("ป้อนหมวดวิชา (เช่น Core, Elective, GenEd): ")
        credits = int(input("ป้อนจำนวนหน่วยกิต: "))
        fee = float(input("ป้อนค่าธรรมเนียมวิชา (บาท): "))
    except ValueError:
        print("❌ ป้อนข้อมูลผิดประเภท!\n")
        return

    code_bytes = code.encode('utf-8').ljust(15, b'\x00')
    title_bytes = title.encode('utf-8').ljust(50, b'\x00')
    cat_bytes = category.encode('utf-8').ljust(20, b'\x00')

    packed_data = struct.pack(FORMAT, course_id, code_bytes, title_bytes, cat_bytes, credits, fee, 1, 0)

    with open(FILENAME, "ab") as file:
        file.write(packed_data)
    print(f"✅ บันทึกวิชา '{title}' เรียบร้อย!\n")

def update_course():
    """2) แก้ไขข้อมูลรายวิชา"""
    print("\n--- ✏️ แก้ไขข้อมูลรายวิชา ---")
    if not os.path.exists(FILENAME) or os.path.getsize(FILENAME) == 0:
        print("ยังไม่มีข้อมูลในระบบ\n")
        return

    try:
        search_id = int(input("ป้อน Course ID ที่ต้องการแก้ไข: "))
    except ValueError:
        print("❌ ID ต้องเป็นตัวเลขเท่านั้น!\n")
        return

    with open(FILENAME, "r+b") as file:
        index = 0
        found = False
        while True:
            offset = index * RECORD_SIZE
            file.seek(offset)
            data_read = file.read(RECORD_SIZE)
            if not data_read:
                break

            unpacked = struct.unpack(FORMAT, data_read)
            if unpacked[0] == search_id and unpacked[6] == 1:
                found = True
                curr_title = unpacked[2].rstrip(b'\x00').decode('utf-8')
                print(f"พบข้อมูลเดิม: {curr_title}")
                
                new_title = input("ชื่อวิชาใหม่ (กด Enter ถ้าไม่เปลี่ยน): ") or curr_title
                new_fee_str = input("ค่าธรรมเนียมใหม่ (กด Enter ถ้าไม่เปลี่ยน): ")
                new_fee = float(new_fee_str) if new_fee_str else unpacked[5]
                
                enrolled_str = input("สถานะการลงทะเบียน (0 = เปิดรับ, 1 = เต็ม/ปิดรับ, กด Enter ถ้าไม่เปลี่ยน): ")
                enrolled_val = int(enrolled_str) if enrolled_str in ["0", "1"] else unpacked[7]

                t_bytes = new_title.encode('utf-8').ljust(50, b'\x00')
                packed_new = struct.pack(FORMAT, unpacked[0], unpacked[1], t_bytes, unpacked[3], unpacked[4], new_fee, 1, enrolled_val)

                file.seek(offset)
                file.write(packed_new)
                print("✅ แก้ไขข้อมูลเรียบร้อยแล้ว!\n")
                break
            index += 1

        if not found:
            print("❌ ไม่พบวิชานี้ หรือถูกลบไปแล้ว\n")

def delete_course():
    """3) ลบรายวิชา (Soft Delete)"""
    print("\n--- 🗑️ ลบรายวิชา ---")
    if not os.path.exists(FILENAME) or os.path.getsize(FILENAME) == 0:
        print("ยังไม่มีข้อมูลในระบบ\n")
        return

    try:
        search_id = int(input("ป้อน Course ID ที่ต้องการลบ: "))
    except ValueError:
        print("❌ ID ต้องเป็นตัวเลขเท่านั้น!\n")
        return

    with open(FILENAME, "r+b") as file:
        index = 0
        found = False
        while True:
            offset = index * RECORD_SIZE
            file.seek(offset)
            data_read = file.read(RECORD_SIZE)
            if not data_read:
                break

            unpacked = struct.unpack(FORMAT, data_read)
            if unpacked[0] == search_id and unpacked[6] == 1:
                found = True
                packed_del = struct.pack(FORMAT, unpacked[0], unpacked[1], unpacked[2], unpacked[3], unpacked[4], unpacked[5], 0, unpacked[7])
                file.seek(offset)
                file.write(packed_del)
                print(f"✅ ลบวิชารหัส {search_id} เรียบร้อยแล้ว (Soft Delete)!\n")
                break
            index += 1

        if not found:
            print("❌ ไม่พบวิชานี้\n")

def view_all_courses():
    """4) ดูรายวิชาทั้งหมด"""
    print("\n--- 📖 รายชื่อรายวิชาทั้งหมด ---")
    if not os.path.exists(FILENAME) or os.path.getsize(FILENAME) == 0:
        print("ยังไม่มีข้อมูลในระบบ\n")
        return

    with open(FILENAME, "rb") as file:
        count = 1
        while True:
            data_read = file.read(RECORD_SIZE)
            if not data_read:
                break
            
            unpacked = struct.unpack(FORMAT, data_read)
            if unpacked[6] == 1: # แสดงเฉพาะ Active
                r_id = unpacked[0]
                r_code = unpacked[1].rstrip(b'\x00').decode('utf-8')
                r_title = unpacked[2].rstrip(b'\x00').decode('utf-8')
                r_cat = unpacked[3].rstrip(b'\x00').decode('utf-8')
                r_credits = unpacked[4]
                r_fee = unpacked[5]
                r_enrolled = "เต็ม/ปิดรับ" if unpacked[7] == 1 else "เปิดรับ"

                print(f"[{count}] ID: {r_id} | รหัส: {r_code} | วิชา: {r_title} | หมวด: {r_cat} | {r_credits} หน่วยกิต | ค่าวิชา: {r_fee:.2f} บาท | สถานะ: {r_enrolled}")
                count += 1
    print()

def generate_report():
    """5) สร้างไฟล์รายงาน report.txt ตามรูปแบบของรุ่นพี่"""
    print("\n--- 📄 กำลังสร้างไฟล์รายงาน report.txt ---")
    if not os.path.exists(FILENAME):
        print("❌ ไม่พบไฟล์ข้อมูล\n")
        return

    courses = []
    with open(FILENAME, "rb") as file:
        while True:
            data = file.read(RECORD_SIZE)
            if not data:
                break
            c = struct.unpack(FORMAT, data)
            courses.append({
                "id": c[0],
                "code": c[1].rstrip(b'\x00').decode('utf-8'),
                "title": c[2].rstrip(b'\x00').decode('utf-8'),
                "cat": c[3].rstrip(b'\x00').decode('utf-8'),
                "credits": c[4],
                "fee": c[5],
                "status": c[6],
                "enrolled": c[7]
            })

    total_records = len(courses)
    active_courses = [c for c in courses if c["status"] == 1]
    deleted_count = total_records - len(active_courses)
    enrolled_count = len([c for c in active_courses if c["enrolled"] == 1])
    available_count = len(active_courses) - enrolled_count

    # คำนวณ Statistics สำหรับ Active courses
    fees = [c["fee"] for c in active_courses] if active_courses else [0.0]
    min_fee = min(fees)
    max_fee = max(fees)
    avg_fee = sum(fees) / len(fees) if fees else 0.0

    # จัดกลุ่มตาม หมวดวิชา (Category)
    cat_counts = {}
    for c in active_courses:
        cat_counts[c["cat"]] = cat_counts.get(c["cat"], 0) + 1

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open("report.txt", "w", encoding="utf-8") as f:
        f.write("Course Registration System - Summary Report (Sample)\n")
        f.write(f"Generated At : {now}\n")
        f.write("App Version  : 1.0\n")
        f.write("Endianness   : Little-Endian\n")
        f.write("Encoding     : UTF-8 (fixed-length)\n\n")

        sep = "-" * 85 + "\n"
        f.write(sep)
        f.write(f"| {'CourseID':<8} | {'Code':<10} | {'Title':<20} | {'Category':<12} | {'Credits':<7} | {'Fee (THB)':<10} | {'Status':<8} | {'Enrolled':<8} |\n")
        f.write(sep)

        for c in courses:
            st = "Active" if c["status"] == 1 else "Deleted"
            en = "Yes" if c["enrolled"] == 1 else "No"
            f.write(f"| {c['id']:<8} | {c['code'][:10]:<10} | {c['title'][:20]:<20} | {c['cat'][:12]:<12} | {c['credits']:<7} | {c['fee']:<10.2f} | {st:<8} | {en:<8} |\n")
        f.write(sep + "\n")

        f.write("Summary (เฉพาะสถานะ Active)\n")
        f.write(f"- Total Courses (records) : {total_records}\n")
        f.write(f"- Active Courses          : {len(active_courses)}\n")
        f.write(f"- Deleted Courses         : {deleted_count}\n")
        f.write(f"- Currently Enrolled/Full : {enrolled_count}\n")
        f.write(f"- Available Now           : {available_count}\n\n")

        f.write("Fee Statistics (THB, Active only)\n")
        f.write(f"- Min : {min_fee:.2f}\n")
        f.write(f"- Max : {max_fee:.2f}\n")
        f.write(f"- Avg : {avg_fee:.2f}\n\n")

        f.write("Courses by Category (Active only)\n")
        for cat_name, count in cat_counts.items():
            f.write(f"- {cat_name} : {count}\n")

    print("✅ สร้างไฟล์ report.txt ตามรูปแบบตัวอย่างเรียบร้อยแล้ว!\n")

def main_menu():
    while True:
        print("==========================================")
        print(" 🎓 ระบบลงทะเบียนเรียน/รายวิชา (CLI) ")
        print("==========================================")
        print("1) เพิ่มรายวิชา (Add Course)")
        print("2) แก้ไขรายวิชา (Update Course)")
        print("3) ลบรายวิชา (Delete Course)")
        print("4) ดูรายวิชาทั้งหมด (View All)")
        print("5) สร้างรายงาน (Generate Report)")
        print("0) ออกจากโปรแกรม (Exit)")
        choice = input("เลือกเมนู (0-5): ").strip()

        if choice == "1":
            add_course()
        elif choice == "2":
            update_course()
        elif choice == "3":
            delete_course()
        elif choice == "4":
            view_all_courses()
        elif choice == "5":
            generate_report()
        elif choice == "0":
            print("ปิดโปรแกรมเรียบร้อยแล้ว 👋")
            break
        else:
            print("❌ เลือกเมนูไม่ถูกต้อง ลองใหม่อีกครั้ง\n")

if __name__ == "__main__":
    main_menu()