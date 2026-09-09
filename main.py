import struct
import os
import datetime

FORMAT = "<I 50s 30s 20s I f I I"
RECORD_SIZE = struct.calcsize(FORMAT)
FILENAME = "books.dat"

def add_book():
    """1) เพิ่มหนังสือใหม่"""
    print("\n--- ➕ เพิ่มหนังสือใหม่ ---")
    try:
        book_id = int(input("ป้อนรหัสหนังสือ (เช่น 1005): "))
        title = input("ป้อนชื่อหนังสือ: ")
        author = input("ป้อนชื่อผู้แต่ง: ")
        category = input("ป้อนหมวดหมู่: ")
        year = int(input("ป้อนปีที่พิมพ์: "))
        fine_rate = float(input("ป้อนค่าปรับต่อวัน (บาท): "))
    except ValueError:
        print("❌ ป้อนข้อมูลผิดประเภท!\n")
        return

    title_bytes = title.encode('utf-8').ljust(50, b'\x00')
    author_bytes = author.encode('utf-8').ljust(30, b'\x00')
    cat_bytes = category.encode('utf-8').ljust(20, b'\x00')

    packed_data = struct.pack(FORMAT, book_id, title_bytes, author_bytes, cat_bytes, year, fine_rate, 1, 0)

    with open(FILENAME, "ab") as file:
        file.write(packed_data)
    print(f"✅ บันทึกหนังสือ '{title}' เรียบร้อย!\n")

def update_book():
    """2) แก้ไขข้อมูลหนังสือ (กระโดดไปเขียนทับตำแหน่งเดิม)"""
    print("\n--- ✏️ แก้ไขข้อมูลหนังสือ ---")
    if not os.path.exists(FILENAME) or os.path.getsize(FILENAME) == 0:
        print("ยังไม่มีข้อมูลในระบบ\n")
        return

    try:
        search_id = int(input("ป้อนรหัสหนังสือที่ต้องการแก้ไข: "))
    except ValueError:
        print("❌ รหัสหนังสือต้องเป็นตัวเลขเท่านั้น!\n")
        return

    with open(FILENAME, "r+b") as file: # เปิดโหมด r+b เพื่ออ่านและเขียนทับได้
        index = 0
        found = False
        while True:
            offset = index * RECORD_SIZE
            file.seek(offset)
            data_read = file.read(RECORD_SIZE)
            if not data_read:
                break

            unpacked = struct.unpack(FORMAT, data_read)
            r_id, r_status = unpacked[0], unpacked[6]

            if r_id == search_id and r_status == 1:
                found = True
                print(f"พบข้อมูลเดิม: {unpacked[1].rstrip(b'\\x00').decode('utf-8')}")
                
                new_title = input("ชื่อหนังสือใหม่ (กด Enter ถ้าไม่เปลี่ยน): ") or unpacked[1].rstrip(b'\x00').decode('utf-8')
                new_fine = input("ค่าปรับใหม่ (กด Enter ถ้าไม่เปลี่ยน): ")
                fine_val = float(new_fine) if new_fine else unpacked[5]
                
                # ถามสถานะการยืม
                borrow_input = input("สถานะการยืม (0 = ว่าง, 1 = ยืมอยู่, กด Enter ถ้าไม่เปลี่ยน): ")
                borrow_val = int(borrow_input) if borrow_input in ["0", "1"] else unpacked[7]

                # แพ็กข้อมูลใหม่
                t_bytes = new_title.encode('utf-8').ljust(50, b'\x00')
                packed_new = struct.pack(FORMAT, r_id, t_bytes, unpacked[2], unpacked[3], unpacked[4], fine_val, 1, borrow_val)

                # กระโดดกลับไปตำแหน่งเดิมแล้วเขียนทับ
                file.seek(offset)
                file.write(packed_new)
                print("✅ แก้ไขข้อมูลเรียบร้อยแล้ว!\n")
                break
            index += 1

        if not found:
            print("❌ ไม่พบรหัสหนังสือนี้ หรือหนังสือถูกลบไปแล้ว\n")

def delete_book():
    """3) ลบหนังสือ (Soft Delete)"""
    print("\n--- 🗑️ ลบหนังสือ ---")
    if not os.path.exists(FILENAME) or os.path.getsize(FILENAME) == 0:
        print("ยังไม่มีข้อมูลในระบบ\n")
        return

    try:
        search_id = int(input("ป้อนรหัสหนังสือที่ต้องการลบ: "))
    except ValueError:
        print("❌ รหัสหนังสือต้องเป็นตัวเลขเท่านั้น!\n")
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
                # เปลี่ยน status เป็น 0 (Deleted)
                packed_del = struct.pack(FORMAT, unpacked[0], unpacked[1], unpacked[2], unpacked[3], unpacked[4], unpacked[5], 0, unpacked[7])
                file.seek(offset)
                file.write(packed_del)
                print(f"✅ ลบหนังสือรหัส {search_id} เรียบร้อยแล้ว (Soft Delete)!\n")
                break
            index += 1

        if not found:
            print("❌ ไม่พบรหัสหนังสือนี้\n")

def view_all_books():
    """4) ดูหนังสือทั้งหมด"""
    print("\n--- 📖 รายชื่อหนังสือทั้งหมดในระบบ ---")
    if not os.path.exists(FILENAME) or os.path.getsize(FILENAME) == 0:
        print("ยังไม่มีข้อมูลหนังสือในไฟล์\n")
        return

    with open(FILENAME, "rb") as file:
        count = 1
        while True:
            data_read = file.read(RECORD_SIZE)
            if not data_read:
                break
            
            unpacked = struct.unpack(FORMAT, data_read)
            r_id = unpacked[0]
            r_title = unpacked[1].rstrip(b'\x00').decode('utf-8')
            r_author = unpacked[2].rstrip(b'\x00').decode('utf-8')
            r_cat = unpacked[3].rstrip(b'\x00').decode('utf-8')
            r_year = unpacked[4]
            r_fine = unpacked[5]
            r_status = unpacked[6]
            r_borrowed = "ยืมอยู่" if unpacked[7] == 1 else "ว่าง"

            if r_status == 1:
                print(f"[{count}] รหัส: {r_id} | ชื่อ: {r_title} | ผู้แต่ง: {r_author} | หมวด: {r_cat} ({r_year}) | ค่าปรับ: {r_fine:.2f} บาท/วัน | สถานะ: {r_borrowed}")
                count += 1
    print()

def generate_report():
    """5) สร้างไฟล์รายงาน report.txt"""
    print("\n--- 📄 กำลังสร้างไฟล์รายงาน report.txt ---")
    if not os.path.exists(FILENAME):
        print("❌ ไม่พบไฟล์ข้อมูล\n")
        return

    books = []
    with open(FILENAME, "rb") as file:
        while True:
            data = file.read(RECORD_SIZE)
            if not data:
                break
            b = struct.unpack(FORMAT, data)
            books.append({
                "id": b[0],
                "title": b[1].rstrip(b'\x00').decode('utf-8'),
                "author": b[2].rstrip(b'\x00').decode('utf-8'),
                "cat": b[3].rstrip(b'\x00').decode('utf-8'),
                "year": b[4],
                "fine": b[5],
                "status": b[6],
                "borrowed": b[7]
            })

    total = len(books)
    active_books = [b for b in books if b["status"] == 1]
    deleted = total - len(active_books)
    borrowed = len([b for b in active_books if b["borrowed"] == 1])
    available = len(active_books) - borrowed

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S (+07:00)")
    
    with open("report.txt", "w", encoding="utf-8") as f:
        f.write("Library System - Summary Report\n")
        f.write(f"Generated At : {now}\n")
        f.write("App Version  : 1.0\n")
        f.write("Endianness   : Little-Endian\n\n")

        sep = "+" + "-"*8 + "+" + "-"*18 + "+" + "-"*15 + "+" + "-"*12 + "+" + "-"*15 + "+" + "-"*10 + "+" + "-"*10 + "+\n"
        f.write(sep)
        f.write("| BookID   | Title              | Author          | Category     | Fine (THB/day)| Status   | Borrowed |\n")
        f.write(sep)

        for b in books:
            st = "Active" if b["status"] == 1 else "Deleted"
            bw = "Yes" if b["borrowed"] == 1 else "No"
            f.write(f"| {b['id']:<8} | {b['title'][:16]:<16} | {b['author'][:13]:<13} | {b['cat'][:10]:<10} | {b['fine']:<13.2f} | {st:<8} | {bw:<8} |\n")
        f.write(sep + "\n")

        f.write(f"Summary (Active Only)\n")
        f.write(f"- Total Records : {total}\n")
        f.write(f"- Active Books  : {len(active_books)}\n")
        f.write(f"- Deleted Books : {deleted}\n")
        f.write(f"- Borrowed      : {borrowed}\n")
        f.write(f"- Available     : {available}\n")

    print("✅ สร้างไฟล์ report.txt เรียบร้อยแล้ว!\n")

def main_menu():
    while True:
        print("==============================")
        print(" 📚 ระบบยืม-คืนหนังสือ (CLI) ")
        print("==============================")
        print("1) เพิ่มหนังสือ (Add)")
        print("2) แก้ไขหนังสือ (Update)")
        print("3) ลบหนังสือ (Delete)")
        print("4) ดูหนังสือทั้งหมด (View)")
        print("5) สร้างรายงาน (Generate Report)")
        print("0) ออกจากโปรแกรม (Exit)")
        choice = input("เลือกเมนู (0-5): ").strip()

        if choice == "1":
            add_book()
        elif choice == "2":
            update_book()
        elif choice == "3":
            delete_book()
        elif choice == "4":
            view_all_books()
        elif choice == "5":
            generate_report()
        elif choice == "0":
            print("ปิดโปรแกรมเรียบร้อยแล้ว 👋")
            break
        else:
            print("❌ เลือกเมนูไม่ถูกต้อง ลองใหม่อีกครั้ง\n")

if __name__ == "__main__":
    main_menu()