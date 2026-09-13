import struct
import os
import datetime

# ============================================================
#  โครงสร้างไฟล์ไบนารีทั้ง 3 ไฟล์ (Fixed-length record, Little-Endian)
# ============================================================

# 1) นักศึกษา (Student)
STUDENT_FORMAT = "<I 15s 50s 20s I I"
# id(I) | student_code(15s) | name(50s) | major(20s) | year(I) | status(I: 1=active,0=deleted)
STUDENT_SIZE = struct.calcsize(STUDENT_FORMAT)
STUDENT_FILE = "students.dat"

# 2) รายวิชา (Course)  -- โครงสร้างเดิม ไม่เปลี่ยน
COURSE_FORMAT = "<I 15s 50s 20s I f I I"
# id(I) | code(15s) | title(50s) | category(20s) | credits(I) | fee(f) | status(I) | full(I)
COURSE_SIZE = struct.calcsize(COURSE_FORMAT)
COURSE_FILE = "courses.dat"

# 3) การลงทะเบียน (Enrollment)  -- ไฟล์ใหม่ที่เพิ่มเข้ามา
ENROLL_FORMAT = "<I I I 20s I"
# enroll_id(I) | student_id(I) | course_id(I) | enroll_date(20s) | status(I: 1=ลงทะเบียนอยู่,0=ยกเลิก)
ENROLL_SIZE = struct.calcsize(ENROLL_FORMAT)
ENROLL_FILE = "enrollments.dat"

LOG_FILE = "operations.log"


# ============================================================
#  ฟังก์ชันช่วยทั่วไป
# ============================================================

def log_action(text):
    """บันทึกประวัติการทำงานลง operations.log (ใช้โชว์ในรายงาน)"""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{now}] {text}\n")


def read_all_records(filename, fmt, size):
    """อ่าน record ทั้งหมดจากไฟล์ไบนารี คืนค่าเป็น list ของ tuple ที่ unpack แล้ว"""
    records = []
    if not os.path.exists(filename):
        return records
    with open(filename, "rb") as f:
        while True:
            data = f.read(size)
            if not data:
                break
            if len(data) != size:
                # กันกรณีไฟล์เสีย/ถูกตัดไม่ครบ record
                print(f"คำเตือน: พบข้อมูลไม่ครบ record ในไฟล์ {filename} (ข้ามส่วนนี้)")
                break
            records.append(struct.unpack(fmt, data))
    return records


def decode_str(b):
    return b.rstrip(b"\x00").decode("utf-8", errors="replace")


def encode_fixed(s, size):
    """เข้ารหัส utf-8 แล้วตัด/เติมให้พอดี size ไบต์ โดยไม่ตัดกลางตัวอักษรหลายไบต์ (กันภาษาไทยเพี้ยน)"""
    b = s.encode("utf-8")
    if len(b) > size:
        # ตัดทีละไบต์จนกว่าจะ decode ได้สมบูรณ์ ไม่ตัดกลางตัวอักษร
        cut = size
        while cut > 0:
            try:
                b[:cut].decode("utf-8")
                break
            except UnicodeDecodeError:
                cut -= 1
        b = b[:cut]
    return b.ljust(size, b"\x00")


def id_exists(filename, fmt, size, target_id, active_only=True):
    """เช็คว่ามี id นี้อยู่แล้วหรือไม่ (สำหรับกันเพิ่มซ้ำ)"""
    for rec in read_all_records(filename, fmt, size):
        if rec[0] == target_id:
            if not active_only:
                return True
            # status อยู่ตำแหน่งสุดท้ายของ student/enrollment, ตำแหน่ง [6] ของ course
            status = rec[-1] if filename != COURSE_FILE else rec[6]
            if status == 1:
                return True
    return False


# ============================================================
#  1) นักศึกษา (Student) : Add / Update / Delete / View
# ============================================================

def add_student():
    print("\n--- เพิ่มนักศึกษาใหม่ ---")
    try:
        student_id = int(input("ป้อน Student ID (เช่น 1): "))
        code = input("ป้อนรหัสนักศึกษา (เช่น 6501001): ")
        name = input("ป้อนชื่อ-สกุล: ")
        major = input("ป้อนสาขาวิชา: ")
        year = int(input("ป้อนชั้นปี: "))
    except ValueError:
        print("ป้อนข้อมูลผิดประเภท!\n")
        return

    if id_exists(STUDENT_FILE, STUDENT_FORMAT, STUDENT_SIZE, student_id):
        print(f"มี Student ID {student_id} ในระบบอยู่แล้ว (สถานะ Active) ห้ามซ้ำ!\n")
        return

    code_b = encode_fixed(code, 15)
    name_b = encode_fixed(name, 50)
    major_b = encode_fixed(major, 20)

    packed = struct.pack(STUDENT_FORMAT, student_id, code_b, name_b, major_b, year, 1)
    with open(STUDENT_FILE, "ab") as f:
        f.write(packed)
    log_action(f"เพิ่มนักศึกษา ID={student_id} ชื่อ={name}")
    print(f"บันทึกนักศึกษา '{name}' เรียบร้อย!\n")


def update_student():
    print("\n--- แก้ไขข้อมูลนักศึกษา ---")
    if not os.path.exists(STUDENT_FILE) or os.path.getsize(STUDENT_FILE) == 0:
        print("ยังไม่มีข้อมูลในระบบ\n")
        return
    try:
        search_id = int(input("ป้อน Student ID ที่ต้องการแก้ไข: "))
    except ValueError:
        print("ID ต้องเป็นตัวเลขเท่านั้น!\n")
        return

    with open(STUDENT_FILE, "r+b") as f:
        index = 0
        found = False
        while True:
            offset = index * STUDENT_SIZE
            f.seek(offset)
            data = f.read(STUDENT_SIZE)
            if not data:
                break
            u = struct.unpack(STUDENT_FORMAT, data)
            if u[0] == search_id and u[4 + 1] == 1:  # status
                found = True
                curr_name = decode_str(u[2])
                print(f"พบข้อมูลเดิม: {curr_name}")
                new_name = input("ชื่อใหม่ (Enter = ไม่เปลี่ยน): ") or curr_name
                new_year_str = input("ชั้นปีใหม่ (Enter = ไม่เปลี่ยน): ")
                new_year = int(new_year_str) if new_year_str else u[4]

                name_b = encode_fixed(new_name, 50)
                packed_new = struct.pack(STUDENT_FORMAT, u[0], u[1], name_b, u[3], new_year, 1)
                f.seek(offset)
                f.write(packed_new)
                log_action(f"แก้ไขนักศึกษา ID={search_id}")
                print("แก้ไขข้อมูลเรียบร้อยแล้ว!\n")
                break
            index += 1
        if not found:
            print("ไม่พบนักศึกษานี้ หรือถูกลบไปแล้ว\n")


def delete_student():
    print("\n--- ลบนักศึกษา (Soft Delete) ---")
    if not os.path.exists(STUDENT_FILE) or os.path.getsize(STUDENT_FILE) == 0:
        print("ยังไม่มีข้อมูลในระบบ\n")
        return
    try:
        search_id = int(input("ป้อน Student ID ที่ต้องการลบ: "))
    except ValueError:
        print("ID ต้องเป็นตัวเลขเท่านั้น!\n")
        return

    with open(STUDENT_FILE, "r+b") as f:
        index = 0
        found = False
        while True:
            offset = index * STUDENT_SIZE
            f.seek(offset)
            data = f.read(STUDENT_SIZE)
            if not data:
                break
            u = struct.unpack(STUDENT_FORMAT, data)
            if u[0] == search_id and u[5] == 1:
                found = True
                packed_del = struct.pack(STUDENT_FORMAT, u[0], u[1], u[2], u[3], u[4], 0)
                f.seek(offset)
                f.write(packed_del)
                log_action(f"ลบนักศึกษา ID={search_id}")
                print(f"ลบนักศึกษารหัส {search_id} เรียบร้อยแล้ว!\n")
                break
            index += 1
        if not found:
            print("ไม่พบนักศึกษานี้\n")


def view_students():
    print("\n--- เมนูย่อย: ดูข้อมูลนักศึกษา ---")
    print("1) ดูทั้งหมด  2) ดูรายการเดียว (ตาม ID)  3) ดูแบบกรอง (ตามสาขา)  4) สถิติโดยสรุป")
    choice = input("เลือก: ").strip()
    records = read_all_records(STUDENT_FILE, STUDENT_FORMAT, STUDENT_SIZE)
    active = [r for r in records if r[5] == 1]

    if choice == "1":
        if not active:
            print("ไม่มีข้อมูลนักศึกษา (Active)\n")
            return
        for i, r in enumerate(active, 1):
            print(f"[{i}] ID:{r[0]} รหัส:{decode_str(r[1])} ชื่อ:{decode_str(r[2])} "
                  f"สาขา:{decode_str(r[3])} ชั้นปี:{r[4]}")
    elif choice == "2":
        try:
            sid = int(input("ป้อน Student ID: "))
        except ValueError:
            print("ID ต้องเป็นตัวเลข!\n")
            return
        found = [r for r in active if r[0] == sid]
        if not found:
            print("ไม่พบนักศึกษานี้\n")
        else:
            r = found[0]
            print(f"ID:{r[0]} รหัส:{decode_str(r[1])} ชื่อ:{decode_str(r[2])} "
                  f"สาขา:{decode_str(r[3])} ชั้นปี:{r[4]}")
    elif choice == "3":
        major_kw = input("ป้อนคำค้นสาขาวิชา: ").strip().lower()
        found = [r for r in active if major_kw in decode_str(r[3]).lower()]
        if not found:
            print("ไม่พบนักศึกษาที่ตรงเงื่อนไข\n")
        for r in found:
            print(f"ID:{r[0]} รหัส:{decode_str(r[1])} ชื่อ:{decode_str(r[2])} สาขา:{decode_str(r[3])}")
    elif choice == "4":
        print(f"จำนวนนักศึกษาทั้งหมด (records) : {len(records)}")
        print(f"จำนวนนักศึกษา Active            : {len(active)}")
        print(f"จำนวนนักศึกษาที่ถูกลบ            : {len(records) - len(active)}")
    else:
        print("เลือกเมนูไม่ถูกต้อง\n")
    print()


# ============================================================
#  2) รายวิชา (Course) : Add / Update / Delete / View  (ของเดิม + เมนูย่อย)
# ============================================================

def add_course():
    print("\n--- เพิ่มรายวิชาใหม่ ---")
    try:
        course_id = int(input("ป้อน Course ID (เช่น 1001): "))
        code = input("ป้อนรหัสวิชา (เช่น CS101): ")
        title = input("ป้อนชื่อรายวิชา: ")
        category = input("ป้อนหมวดวิชา (เช่น Core, Elective, GenEd): ")
        credits = int(input("ป้อนจำนวนหน่วยกิต: "))
        fee = float(input("ป้อนค่าธรรมเนียมวิชา (บาท): "))
    except ValueError:
        print("ป้อนข้อมูลผิดประเภท!\n")
        return

    if id_exists(COURSE_FILE, COURSE_FORMAT, COURSE_SIZE, course_id):
        print(f"มี Course ID {course_id} ในระบบอยู่แล้ว (สถานะ Active) ห้ามซ้ำ!\n")
        return

    code_bytes = encode_fixed(code, 15)
    title_bytes = encode_fixed(title, 50)
    cat_bytes = encode_fixed(category, 20)

    packed_data = struct.pack(COURSE_FORMAT, course_id, code_bytes, title_bytes, cat_bytes, credits, fee, 1, 0)
    with open(COURSE_FILE, "ab") as file:
        file.write(packed_data)
    log_action(f"เพิ่มรายวิชา ID={course_id} ชื่อ={title}")
    print(f"บันทึกวิชา '{title}' เรียบร้อย!\n")


def update_course():
    print("\n--- แก้ไขข้อมูลรายวิชา ---")
    if not os.path.exists(COURSE_FILE) or os.path.getsize(COURSE_FILE) == 0:
        print("ยังไม่มีข้อมูลในระบบ\n")
        return
    try:
        search_id = int(input("ป้อน Course ID ที่ต้องการแก้ไข: "))
    except ValueError:
        print("ID ต้องเป็นตัวเลขเท่านั้น!\n")
        return

    with open(COURSE_FILE, "r+b") as file:
        index = 0
        found = False
        while True:
            offset = index * COURSE_SIZE
            file.seek(offset)
            data_read = file.read(COURSE_SIZE)
            if not data_read:
                break
            unpacked = struct.unpack(COURSE_FORMAT, data_read)
            if unpacked[0] == search_id and unpacked[6] == 1:
                found = True
                curr_title = decode_str(unpacked[2])
                print(f"พบข้อมูลเดิม: {curr_title}")
                new_title = input("ชื่อวิชาใหม่ (Enter = ไม่เปลี่ยน): ") or curr_title
                new_fee_str = input("ค่าธรรมเนียมใหม่ (Enter = ไม่เปลี่ยน): ")
                new_fee = float(new_fee_str) if new_fee_str else unpacked[5]
                full_str = input("สถานะเต็ม/ปิดรับ (0=เปิดรับ,1=เต็ม, Enter=ไม่เปลี่ยน): ")
                full_val = int(full_str) if full_str in ["0", "1"] else unpacked[7]

                t_bytes = encode_fixed(new_title, 50)
                packed_new = struct.pack(COURSE_FORMAT, unpacked[0], unpacked[1], t_bytes,
                                          unpacked[3], unpacked[4], new_fee, 1, full_val)
                file.seek(offset)
                file.write(packed_new)
                log_action(f"แก้ไขรายวิชา ID={search_id}")
                print("แก้ไขข้อมูลเรียบร้อยแล้ว!\n")
                break
            index += 1
        if not found:
            print("ไม่พบวิชานี้ หรือถูกลบไปแล้ว\n")


def delete_course():
    print("\n--- ลบรายวิชา (Soft Delete) ---")
    if not os.path.exists(COURSE_FILE) or os.path.getsize(COURSE_FILE) == 0:
        print("ยังไม่มีข้อมูลในระบบ\n")
        return
    try:
        search_id = int(input("ป้อน Course ID ที่ต้องการลบ: "))
    except ValueError:
        print("ID ต้องเป็นตัวเลขเท่านั้น!\n")
        return

    with open(COURSE_FILE, "r+b") as file:
        index = 0
        found = False
        while True:
            offset = index * COURSE_SIZE
            file.seek(offset)
            data_read = file.read(COURSE_SIZE)
            if not data_read:
                break
            unpacked = struct.unpack(COURSE_FORMAT, data_read)
            if unpacked[0] == search_id and unpacked[6] == 1:
                found = True
                packed_del = struct.pack(COURSE_FORMAT, unpacked[0], unpacked[1], unpacked[2],
                                          unpacked[3], unpacked[4], unpacked[5], 0, unpacked[7])
                file.seek(offset)
                file.write(packed_del)
                log_action(f"ลบรายวิชา ID={search_id}")
                print(f"ลบวิชารหัส {search_id} เรียบร้อยแล้ว (Soft Delete)!\n")
                break
            index += 1
        if not found:
            print("ไม่พบวิชานี้\n")


def view_courses():
    print("\n--- เมนูย่อย: ดูข้อมูลรายวิชา ---")
    print("1) ดูทั้งหมด  2) ดูรายการเดียว (ตาม ID)  3) ดูแบบกรอง (ตามหมวดวิชา)  4) สถิติโดยสรุป")
    choice = input("เลือก: ").strip()
    records = read_all_records(COURSE_FILE, COURSE_FORMAT, COURSE_SIZE)
    active = [r for r in records if r[6] == 1]

    def fmt_line(r):
        full = "เต็ม/ปิดรับ" if r[7] == 1 else "เปิดรับ"
        return (f"ID:{r[0]} รหัส:{decode_str(r[1])} วิชา:{decode_str(r[2])} "
                f"หมวด:{decode_str(r[3])} {r[4]} หน่วยกิต ค่าวิชา:{r[5]:.2f} สถานะ:{full}")

    if choice == "1":
        if not active:
            print("ไม่มีรายวิชา (Active)\n")
            return
        for i, r in enumerate(active, 1):
            print(f"[{i}] {fmt_line(r)}")
    elif choice == "2":
        try:
            cid = int(input("ป้อน Course ID: "))
        except ValueError:
            print("ID ต้องเป็นตัวเลข!\n")
            return
        found = [r for r in active if r[0] == cid]
        print(fmt_line(found[0]) if found else "ไม่พบรายวิชานี้")
    elif choice == "3":
        kw = input("ป้อนคำค้นหมวดวิชา: ").strip().lower()
        found = [r for r in active if kw in decode_str(r[3]).lower()]
        if not found:
            print("ไม่พบรายวิชาที่ตรงเงื่อนไข")
        for r in found:
            print(fmt_line(r))
    elif choice == "4":
        fees = [r[5] for r in active] or [0.0]
        print(f"จำนวนรายวิชาทั้งหมด (records) : {len(records)}")
        print(f"จำนวนรายวิชา Active            : {len(active)}")
        print(f"จำนวนรายวิชาที่ถูกลบ            : {len(records) - len(active)}")
        print(f"ค่าธรรมเนียม ต่ำสุด/สูงสุด/เฉลี่ย : {min(fees):.2f} / {max(fees):.2f} / {sum(fees)/len(fees):.2f}")
    else:
        print("เลือกเมนูไม่ถูกต้อง")
    print()


# ============================================================
#  3) การลงทะเบียน (Enrollment) : Add / Delete / View
# ============================================================

def _next_enroll_id():
    records = read_all_records(ENROLL_FILE, ENROLL_FORMAT, ENROLL_SIZE)
    return (max((r[0] for r in records), default=0)) + 1


def enroll_student():
    """ลงทะเบียนนักศึกษาเข้าเรียนในรายวิชา"""
    print("\n--- ลงทะเบียนเรียน ---")
    try:
        student_id = int(input("ป้อน Student ID: "))
        course_id = int(input("ป้อน Course ID: "))
    except ValueError:
        print("ID ต้องเป็นตัวเลขเท่านั้น!\n")
        return

    if not id_exists(STUDENT_FILE, STUDENT_FORMAT, STUDENT_SIZE, student_id):
        print("ไม่พบนักศึกษารหัสนี้ในระบบ (หรือถูกลบไปแล้ว)\n")
        return

    course_rec = None
    for r in read_all_records(COURSE_FILE, COURSE_FORMAT, COURSE_SIZE):
        if r[0] == course_id and r[6] == 1:
            course_rec = r
            break
    if course_rec is None:
        print("ไม่พบรายวิชานี้ในระบบ (หรือถูกลบไปแล้ว)\n")
        return
    if course_rec[7] == 1:
        print("วิชานี้เต็ม/ปิดรับลงทะเบียนแล้ว\n")
        return

    # กันลงทะเบียนซ้ำวิชาเดิมทั้งที่ยังลงอยู่
    for r in read_all_records(ENROLL_FILE, ENROLL_FORMAT, ENROLL_SIZE):
        if r[1] == student_id and r[2] == course_id and r[4] == 1:
            print("นักศึกษาคนนี้ลงทะเบียนวิชานี้อยู่แล้ว\n")
            return

    enroll_id = _next_enroll_id()
    date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    date_bytes = encode_fixed(date_str, 20)
    packed = struct.pack(ENROLL_FORMAT, enroll_id, student_id, course_id, date_bytes, 1)
    with open(ENROLL_FILE, "ab") as f:
        f.write(packed)
    log_action(f"ลงทะเบียน Student={student_id} -> Course={course_id} (EnrollID={enroll_id})")
    print(f"ลงทะเบียนเรียบร้อย! (Enrollment ID: {enroll_id})\n")


def cancel_enrollment():
    print("\n--- ยกเลิกการลงทะเบียน (Soft Delete) ---")
    if not os.path.exists(ENROLL_FILE) or os.path.getsize(ENROLL_FILE) == 0:
        print("ยังไม่มีข้อมูลการลงทะเบียนในระบบ\n")
        return
    try:
        search_id = int(input("ป้อน Enrollment ID ที่ต้องการยกเลิก: "))
    except ValueError:
        print("ID ต้องเป็นตัวเลขเท่านั้น!\n")
        return

    with open(ENROLL_FILE, "r+b") as f:
        index = 0
        found = False
        while True:
            offset = index * ENROLL_SIZE
            f.seek(offset)
            data = f.read(ENROLL_SIZE)
            if not data:
                break
            u = struct.unpack(ENROLL_FORMAT, data)
            if u[0] == search_id and u[4] == 1:
                found = True
                packed_del = struct.pack(ENROLL_FORMAT, u[0], u[1], u[2], u[3], 0)
                f.seek(offset)
                f.write(packed_del)
                log_action(f"ยกเลิกการลงทะเบียน EnrollID={search_id}")
                print("ยกเลิกการลงทะเบียนเรียบร้อยแล้ว!\n")
                break
            index += 1
        if not found:
            print("ไม่พบรายการลงทะเบียนนี้\n")


def view_enrollments():
    print("\n--- เมนูย่อย: ดูข้อมูลการลงทะเบียน ---")
    print("1) ดูทั้งหมด  2) ดูตาม Student ID  3) ดูตาม Course ID  4) สถิติโดยสรุป")
    choice = input("เลือก: ").strip()

    records = read_all_records(ENROLL_FILE, ENROLL_FORMAT, ENROLL_SIZE)
    active = [r for r in records if r[4] == 1]
    students = {r[0]: decode_str(r[2]) for r in read_all_records(STUDENT_FILE, STUDENT_FORMAT, STUDENT_SIZE)}
    courses = {r[0]: decode_str(r[2]) for r in read_all_records(COURSE_FILE, COURSE_FORMAT, COURSE_SIZE)}

    def fmt_line(r):
        sname = students.get(r[1], "(ไม่พบนักศึกษา)")
        cname = courses.get(r[2], "(ไม่พบวิชา)")
        return f"EnrollID:{r[0]} Student:{r[1]}-{sname} Course:{r[2]}-{cname} วันที่:{decode_str(r[3])}"

    if choice == "1":
        if not active:
            print("ไม่มีข้อมูลการลงทะเบียน (Active)\n")
            return
        for i, r in enumerate(active, 1):
            print(f"[{i}] {fmt_line(r)}")
    elif choice == "2":
        try:
            sid = int(input("ป้อน Student ID: "))
        except ValueError:
            print("ID ต้องเป็นตัวเลข!\n")
            return
        found = [r for r in active if r[1] == sid]
        if not found:
            print("ไม่พบข้อมูลการลงทะเบียนของนักศึกษานี้")
        for r in found:
            print(fmt_line(r))
    elif choice == "3":
        try:
            cid = int(input("ป้อน Course ID: "))
        except ValueError:
            print("ID ต้องเป็นตัวเลข!\n")
            return
        found = [r for r in active if r[2] == cid]
        if not found:
            print("ไม่พบข้อมูลการลงทะเบียนของวิชานี้")
        for r in found:
            print(fmt_line(r))
    elif choice == "4":
        print(f"จำนวนการลงทะเบียนทั้งหมด (records) : {len(records)}")
        print(f"จำนวนที่ยังลงทะเบียนอยู่ (Active)    : {len(active)}")
        print(f"จำนวนที่ถูกยกเลิก                    : {len(records) - len(active)}")
    else:
        print("เลือกเมนูไม่ถูกต้อง")
    print()


# ============================================================
#  4) สร้างรายงานสรุป (report.txt)
# ============================================================

def generate_report():
    print("\n--- กำลังสร้างไฟล์รายงาน report.txt ---")

    students = read_all_records(STUDENT_FILE, STUDENT_FORMAT, STUDENT_SIZE)
    courses = read_all_records(COURSE_FILE, COURSE_FORMAT, COURSE_SIZE)
    enrolls = read_all_records(ENROLL_FILE, ENROLL_FORMAT, ENROLL_SIZE)

    active_students = [s for s in students if s[5] == 1]
    active_courses = [c for c in courses if c[6] == 1]
    active_enrolls = [e for e in enrolls if e[4] == 1]

    fees = [c[5] for c in active_courses] or [0.0]
    min_fee, max_fee = min(fees), max(fees)
    avg_fee = sum(fees) / len(fees)

    cat_counts = {}
    for c in active_courses:
        cat = decode_str(c[3])
        cat_counts[cat] = cat_counts.get(cat, 0) + 1

    # จำนวนช่องว่าง (record ที่ถูก soft-delete แล้ว สามารถนำ slot กลับมาใช้ได้ในอนาคต)
    free_students = len(students) - len(active_students)
    free_courses = len(courses) - len(active_courses)
    free_enrolls = len(enrolls) - len(active_enrolls)

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # อ่าน log ล่าสุด 10 รายการ
    recent_logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            recent_logs = f.readlines()[-10:]

    with open("report.txt", "w", encoding="utf-8") as f:
        f.write("Course Registration System - Summary Report\n")
        f.write(f"Generated At : {now}\n")
        f.write("App Version  : 2.0\n")
        f.write("Endianness   : Little-Endian\n")
        f.write("Encoding     : UTF-8 (fixed-length)\n")
        f.write(f"Files        : {STUDENT_FILE}, {COURSE_FILE}, {ENROLL_FILE}\n\n")

        f.write("=== รายวิชา (Courses) ===\n")
        sep = "-" * 85 + "\n"
        f.write(sep)
        f.write(f"| {'ID':<6} | {'Code':<10} | {'Title':<20} | {'Category':<12} | {'Credits':<7} | {'Fee':<9} | {'Status':<7} | {'Full':<5} |\n")
        f.write(sep)
        for c in courses:
            st = "Active" if c[6] == 1 else "Deleted"
            full = "Yes" if c[7] == 1 else "No"
            f.write(f"| {c[0]:<6} | {decode_str(c[1])[:10]:<10} | {decode_str(c[2])[:20]:<20} | "
                     f"{decode_str(c[3])[:12]:<12} | {c[4]:<7} | {c[5]:<9.2f} | {st:<7} | {full:<5} |\n")
        f.write(sep + "\n")

        f.write("=== นักศึกษา (Students) ===\n")
        sep2 = "-" * 70 + "\n"
        f.write(sep2)
        f.write(f"| {'ID':<6} | {'Code':<12} | {'Name':<25} | {'Major':<15} | {'Status':<7} |\n")
        f.write(sep2)
        for s in students:
            st = "Active" if s[5] == 1 else "Deleted"
            f.write(f"| {s[0]:<6} | {decode_str(s[1])[:12]:<12} | {decode_str(s[2])[:25]:<25} | "
                     f"{decode_str(s[3])[:15]:<15} | {st:<7} |\n")
        f.write(sep2 + "\n")

        f.write("=== การลงทะเบียน (Enrollments) ===\n")
        sep3 = "-" * 70 + "\n"
        f.write(sep3)
        f.write(f"| {'EnrollID':<9} | {'StudentID':<10} | {'CourseID':<9} | {'Date':<20} | {'Status':<9} |\n")
        f.write(sep3)
        for e in enrolls:
            st = "Active" if e[4] == 1 else "Cancelled"
            f.write(f"| {e[0]:<9} | {e[1]:<10} | {e[2]:<9} | {decode_str(e[3]):<20} | {st:<9} |\n")
        f.write(sep3 + "\n")

        f.write("Summary\n")
        f.write(f"- Courses  : Total={len(courses)}, Active={len(active_courses)}, Deleted={free_courses}\n")
        f.write(f"- Students : Total={len(students)}, Active={len(active_students)}, Deleted={free_students}\n")
        f.write(f"- Enrolls  : Total={len(enrolls)}, Active={len(active_enrolls)}, Cancelled={free_enrolls}\n\n")

        f.write("Free Slots (record ที่ถูกลบ สามารถใช้ซ้ำได้)\n")
        f.write(f"- {STUDENT_FILE} : {free_students} slot(s)\n")
        f.write(f"- {COURSE_FILE}  : {free_courses} slot(s)\n")
        f.write(f"- {ENROLL_FILE}  : {free_enrolls} slot(s)\n\n")

        f.write("Fee Statistics (THB, Active courses only)\n")
        f.write(f"- Min : {min_fee:.2f}\n")
        f.write(f"- Max : {max_fee:.2f}\n")
        f.write(f"- Avg : {avg_fee:.2f}\n\n")

        f.write("Courses by Category (Active only)\n")
        for cat_name, count in cat_counts.items():
            f.write(f"- {cat_name} : {count}\n")
        f.write("\n")

        f.write("ประวัติการทำงานล่าสุด (Recent Operation History)\n")
        if recent_logs:
            for line in recent_logs:
                f.write(f"- {line.strip()}\n")
        else:
            f.write("- ไม่มีประวัติการทำงาน\n")

    log_action("สร้างรายงาน report.txt")
    print("สร้างไฟล์ report.txt เรียบร้อยแล้ว!\n")


# ============================================================
#  เมนูหลักและเมนูย่อยของแต่ละ entity
# ============================================================

def course_menu():
    while True:
        print("\n---- จัดการรายวิชา (Courses) ----")
        print("1) เพิ่มรายวิชา  2) แก้ไขรายวิชา  3) ลบรายวิชา  4) ดูรายวิชา  0) กลับเมนูหลัก")
        c = input("เลือก: ").strip()
        if c == "1":
            add_course()
        elif c == "2":
            update_course()
        elif c == "3":
            delete_course()
        elif c == "4":
            view_courses()
        elif c == "0":
            break
        else:
            print("เลือกเมนูไม่ถูกต้อง\n")


def student_menu():
    while True:
        print("\n---- จัดการนักศึกษา (Students) ----")
        print("1) เพิ่มนักศึกษา  2) แก้ไขนักศึกษา  3) ลบนักศึกษา  4) ดูนักศึกษา  0) กลับเมนูหลัก")
        c = input("เลือก: ").strip()
        if c == "1":
            add_student()
        elif c == "2":
            update_student()
        elif c == "3":
            delete_student()
        elif c == "4":
            view_students()
        elif c == "0":
            break
        else:
            print("เลือกเมนูไม่ถูกต้อง\n")


def enrollment_menu():
    while True:
        print("\n---- การลงทะเบียนเรียน (Enrollments) ----")
        print("1) ลงทะเบียน  2) ยกเลิกการลงทะเบียน  3) ดูข้อมูลการลงทะเบียน  0) กลับเมนูหลัก")
        c = input("เลือก: ").strip()
        if c == "1":
            enroll_student()
        elif c == "2":
            cancel_enrollment()
        elif c == "3":
            view_enrollments()
        elif c == "0":
            break
        else:
            print("เลือกเมนูไม่ถูกต้อง\n")


def main_menu():
    while True:
        print("==========================================")
        print(" ระบบลงทะเบียนเรียน (CLI) ")
        print("==========================================")
        print("1) จัดการรายวิชา (Courses)")
        print("2) จัดการนักศึกษา (Students)")
        print("3) การลงทะเบียนเรียน (Enrollments)")
        print("4) สร้างรายงานสรุป (Generate Report)")
        print("0) ออกจากโปรแกรม (Exit)")
        choice = input("เลือกเมนู (0-4): ").strip()

        if choice == "1":
            course_menu()
        elif choice == "2":
            student_menu()
        elif choice == "3":
            enrollment_menu()
        elif choice == "4":
            generate_report()
        elif choice == "0":
            # ปรับปรุงการ Flush/Sync ไฟล์อย่างปลอดภัยก่อนออก
            for fname in [STUDENT_FILE, COURSE_FILE, ENROLL_FILE]:
                if os.path.exists(fname):
                    try:
                        # เปิดแบบ Read/Write เพื่อส่งให้ os.fsync ได้โดยไม่พัง
                        fd = os.open(fname, os.O_RDWR)
                        os.fsync(fd)
                        os.close(fd)
                    except OSError:
                        pass
            
            generate_report()
            log_action("ปิดโปรแกรม (Exit)")
            print("บันทึกและซิงค์ข้อมูลเรียบร้อย ปิดโปรแกรมเรียบร้อยแล้ว")
            break
        else:
            print("เลือกเมนูไม่ถูกต้อง ลองใหม่อีกครั้ง\n")


if __name__ == "__main__":
    main_menu()
