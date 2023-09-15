from tkinter import *
import os
import sys

from tkinter.messagebox import showerror, showwarning, showinfo, askyesno
import sqlite3
import datetime

from tkinter import filedialog
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle
from reportlab.lib.pagesizes import A4

from tkinter import ttk
from tkcalendar import DateEntry
from babel import numbers


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS2
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def sort(tv, col, reverse, key=str):
    try:
        l = [(tv.set(k, col), k) for k in tv.get_children()]
        l.sort(reverse=reverse, key=lambda t: key(t[0]))

        for index, (val, k) in enumerate(l):
            tv.move(k, '', index)

        tv.heading(col, command=lambda: sort(tv, col, not reverse, key=key))
    except Exception as e:
        pass


class PrintPage(Frame):
    def __init__(self, root):

        super().__init__()

        def clean_product_table():
            data = product_table.get_children()
            for elements in data:
                product_table.delete(elements)

        def show_products():
            clean_product_table()
            search_entry.delete(0, END)
            conn = None
            try:
                conn = sqlite3.connect(resource_path("data/my_data.db"))
                cursor = conn.cursor()
                cursor.execute('SELECT code, title, unit, price, count FROM product')
                data = cursor.fetchall()

                for row in data:
                    product_table.insert('', END, values=row)
                conn.close()
            except Exception as e:
                showinfo('', str(e))
            finally:
                if conn is not None:
                    conn.close()

        def search_product():
            clean_product_table()
            conn = None
            try:
                if search_label.cget('text') == '1':
                    conn = sqlite3.connect(resource_path("data/my_data.db"))
                    cursor = conn.cursor()
                    title = search_entry.get()
                    if len(title) < 1:
                        show_products()
                    else:
                        cursor.execute(
                            '''SELECT code, title, unit, price, count FROM product WHERE title LIKE ?''',
                            ("%" + title + "%",)
                        )
                        data = cursor.fetchall()
                        if data:
                            for row in data:
                                product_table.insert("", END, values=row)
                        else:
                            showinfo('Предупреждение', 'Результаты поиска не найдены')
                elif search_label.cget('text') == '2':
                    conn = sqlite3.connect(resource_path("data/my_data.db"))
                    cursor = conn.cursor()
                    title = search_entry.get()
                    if len(title) < 1:
                        show_products()
                    else:
                        cursor.execute(
                            '''SELECT code, title, unit, price, count FROM product WHERE code LIKE ?''',
                            ("%" + title + "%",)
                        )
                        data = cursor.fetchall()
                        if data:
                            for row in data:
                                product_table.insert("", END, values=row)
                        else:
                            showinfo('Предупреждение', 'Результаты поиска не найдены')
            except Exception as e:
                showwarning("Ошибка", str(e))
            finally:
                if conn is not None:
                    conn.close()

        def select_product(event):
            item = product_table.focus()
            tp = product_table.item(item, "values")

            for k in cart_table.get_children(''):
                cart_title = cart_table.item(k).get('values')[1]
                if str(tp[1]) == str(cart_title):
                    showinfo('', 'Товар уже в корзине')
                    return

            cart_code_entry.configure(state='normal')
            cart_title_entry.configure(state='normal')

            cart_code_entry.delete(0, END)
            cart_title_entry.delete(0, END)
            cart_count_entry.delete(0, END)

            try:
                cart_code_entry.insert(index=0, string=tp[0])
                cart_title_entry.insert(index=0, string=tp[1])
                cart_count_entry.insert(index=0, string='0')
            except Exception as e:
                pass

            cart_code_entry.configure(state='readonly')
            cart_title_entry.configure(state='readonly')

        def clean_cart_detail():
            cart_code_entry.configure(state='normal')
            cart_title_entry.configure(state='normal')

            cart_code_entry.delete(0, END)
            cart_title_entry.delete(0, END)
            cart_count_entry.delete(0, END)

            cart_code_entry.configure(state='readonly')
            cart_title_entry.configure(state='readonly')

        def add_to_cart():
            if cart_code_entry.get():
                value = (cart_code_entry.get(), cart_title_entry.get(), cart_count_entry.get())
                cart_table.insert("", END, values=value)
                clean_cart_detail()
            else:
                showwarning('', 'Товар не выбран')

        def delete_from_cart(event):
            try:
                item = cart_table.focus()
                if item:
                    cart_table.delete(item)
            except Exception as e:
                pass

        def post_order():
            fetch_data = cart_table.get_children()
            for f in fetch_data:
                cart_table.delete(f)

        def save_report_as_pdf():
            file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Файлы", "*.pdf")])

            if file_path:
                styles = getSampleStyleSheet()

                styles['Normal'].fontName = 'DejaVuSerif'
                styles['Heading3'].fontName = 'DejaVuSerif'

                pdfmetrics.registerFont(TTFont('DejaVuSerif', resource_path('fonts/DejaVuSerif.ttf'), 'UTF-8'))

                doc = SimpleDocTemplate(file_path,
                                        pagesize=A4,
                                        title='Basic thing',
                                        author='Gogol', rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)

                story = []

                headers = Table(
                    [
                        [Paragraph('Артикул', styles["Heading3"]), Paragraph('Товар', styles["Heading3"]),
                         Paragraph('Количество', styles["Heading3"])]
                    ]
                )
                headers.setStyle(TableStyle([('ALIGN', (1, 1), (-2, -2), 'RIGHT'),
                                             ('BACKGROUND', (0, 0), (-1, -1), colors.tan),
                                             ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                                             ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
                                             ]))
                story.append(headers)

                for k in cart_table.get_children(''):
                    product = cart_table.item(k).get('values')

                    try:
                        column = Table([
                            [Paragraph(product[0], styles["Normal"]), Paragraph(product[1], styles["Normal"]),
                             product[2]]
                        ])
                        column.setStyle(TableStyle([('ALIGN', (1, 1), (-2, -2), 'RIGHT'),
                                                    ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                                                    ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
                                                    ]))
                        story.append(column)
                    except Exception as e:

                        column = Table([
                            [product[0], Paragraph(product[1], styles["Normal"]),
                             product[2]]
                        ])
                        column.setStyle(TableStyle([('ALIGN', (1, 1), (-2, -2), 'RIGHT'),
                                                    ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                                                    ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
                                                    ]))
                        story.append(column)

                doc.build(story)
                post_order()

        self.root = root

        style = ttk.Style()
        style.theme_use("clam")
        style.map("Treeview")
        style.configure("Treeview", font=('None', 13))
        style.configure("Treeview.Heading", font=('None', 13, 'bold'))

        # TODO LEFT FRAME
        left_frame = Frame(self.root)
        left_frame.pack(side=LEFT, fill=Y)
        left_frame.pack_propagate(False)
        left_frame.configure(width=800)

        search_frame = LabelFrame(left_frame, bd=1, padx=5, pady=5, relief=RIDGE)
        search_frame.pack(side=TOP, fill=X)
        search_frame.pack_propagate(False)
        search_frame.configure(height=50)

        search_entry = Entry(search_frame, width=25, font=('None', 15))
        search_entry.grid(row=0, column=0)

        def selection():
            slc = str(radio.get())
            search_label.config(text=slc)

        radio = IntVar()

        name_btn = Radiobutton(search_frame, text="Товар", variable=radio, value=1, command=selection,
                               font=('None', 12))
        name_btn.grid(row=0, column=1)

        code_btn = Radiobutton(search_frame, text="Артикул", variable=radio, value=2, command=selection,
                               font=('None', 12))
        code_btn.grid(row=0, column=2)

        search_label = Label()

        search_btn = Button(search_frame, text='Поиск', width=8, command=search_product,
                            font=('None', 13), bd=3, fg='black')
        search_btn.grid(row=0, column=3)
        table_rst_btn = Button(search_frame, text='Обновить', width=8, command=show_products,
                               font=('None', 13), bd=3, fg='black')
        table_rst_btn.grid(row=0, column=4)

        for widget in search_frame.winfo_children():
            widget.grid_configure(padx=5, pady=5)
        name_btn.invoke()

        # TODO PRODUCT TABLE FRAME
        product_table_frame = Frame(left_frame, relief=RIDGE, bd=1, padx=5, pady=5)
        product_table_frame.pack(side=TOP, fill=X)
        product_table_frame.pack_propagate(False)
        product_table_frame.configure(width=800, height=800)

        product_table_sc_x = Scrollbar(product_table_frame, orient=HORIZONTAL)
        product_table_sc_x.pack(side=BOTTOM, fill=X)
        product_table_sc_y = Scrollbar(product_table_frame, orient=VERTICAL)
        product_table_sc_y.pack(side=RIGHT, fill=Y)
        product_table = ttk.Treeview(product_table_frame,
                                     column=('code', 'title', 'unit', 'price', 'quantity'),
                                     xscrollcommand=product_table_sc_x.set,
                                     yscrollcommand=product_table_sc_y.set)
        product_table_sc_x.config(command=product_table.xview)
        product_table_sc_y.config(command=product_table.yview)
        product_table.heading('code', text='Артикул')
        product_table.heading('title', text='Товар', command=lambda: sort(product_table, 'title', False))
        product_table.heading('unit', text='Единица')
        product_table.heading('price', text='Цена')
        product_table.heading('quantity', text='Количество',
                              command=lambda: sort(product_table, 'quantity', False, key=float))
        product_table['show'] = 'headings'
        product_table.pack(fill=BOTH, expand=1)
        product_table.column('code', width=50)
        product_table.column('title', width=220)
        product_table.column('unit', width=50, anchor='e')
        product_table.column('price', width=100, anchor='e')
        product_table.column('quantity', width=100, anchor='e')

        product_table.bind("<Double-1>", select_product)

        show_products()

        # TODO RIGHT FRAME
        right_frame = Frame(self.root)
        right_frame.pack(side=RIGHT, fill=Y)
        right_frame.pack_propagate(False)
        right_frame.configure(width=800)

        cart_frame = Frame(right_frame, bd=1, padx=3, pady=3, relief=RIDGE)
        cart_frame.pack(side=TOP, fill=X)
        cart_frame.pack_propagate(False)
        cart_frame.configure(height=150)

        cart_label = LabelFrame(cart_frame, text='Добавление в корзину', font=('None', 13), fg='red')
        cart_label.pack(side=TOP, fill=X)

        cart_code_label = Label(cart_label, font=('None', 13, 'bold'), text='Артикул', width=15)
        cart_code_label.grid(row=0, column=0)
        cart_code_entry = Entry(cart_label, font=('None', 13), state='readonly', width=15)
        cart_code_entry.grid(row=1, column=0)

        cart_title_label = Label(cart_label, font=('None', 13, 'bold'), text='Товар')
        cart_title_label.grid(row=0, column=1)
        cart_title_entry = Entry(cart_label, font=('None', 13), state='readonly', width=30)
        cart_title_entry.grid(row=1, column=1)

        cart_price_label = Label(cart_label, font=('None', 13, 'bold'), text='Количество', width=15)
        cart_price_label.grid(row=0, column=2)
        cart_count_entry = Entry(cart_label, font=('None', 13), width=15)
        cart_count_entry.grid(row=1, column=2)

        cart_adding_btn = Button(cart_label, text='Добавить корзину', font=('None', 13), command=add_to_cart,
                                 fg='black')
        cart_adding_btn.grid(row=2, column=2)

        for widget in cart_label.winfo_children():
            widget.grid_configure(padx=5, pady=5)

        # CART_TABLE_FRAME
        cart_table_frame = Frame(right_frame, relief=RIDGE, bd=1, padx=5, pady=5)
        cart_table_frame.pack(side=TOP, fill='y')
        cart_table_frame.pack_propagate(False)
        cart_table_frame.configure(width=800, height=450)

        cart_table_sc_x = Scrollbar(cart_table_frame, orient=HORIZONTAL)
        cart_table_sc_x.pack(side=BOTTOM, fill=X)
        cart_table_sc_y = Scrollbar(cart_table_frame, orient=VERTICAL)
        cart_table_sc_y.pack(side=RIGHT, fill=Y)
        cart_table = ttk.Treeview(cart_table_frame,
                                  column=('code', 'title', 'quantity'),
                                  xscrollcommand=cart_table_sc_x.set,
                                  yscrollcommand=cart_table_sc_y.set)
        cart_table_sc_x.config(command=cart_table.xview)
        cart_table_sc_y.config(command=cart_table.yview)
        cart_table.heading('code', text='Артикул')
        cart_table.heading('title', text='Товар')
        cart_table.heading('quantity', text='Количество')
        cart_table['show'] = 'headings'
        cart_table.pack(fill=BOTH, expand=1)
        cart_table.column('code', width=40)
        cart_table.column('title', width=200)
        cart_table.column('quantity', width=50, anchor='e')

        cart_table.bind("<Double-1>", delete_from_cart)

        # ORDER FRAME
        order_frame = Frame(right_frame, bd=1, padx=5, pady=5, relief=RIDGE)
        order_frame.pack(side=TOP, fill=X)
        order_frame.pack_propagate(False)
        order_frame.configure(height=300)

        order_frame_label = LabelFrame(order_frame, text='', font=('None', 13), fg='red')
        order_frame_label.pack(side=TOP, fill=X)

        order_button = Button(order_frame_label, text="Распечатать", command=save_report_as_pdf, width=12,
                              font=('None', 13), bd=3, fg='black')
        order_button.grid(row=1, column=3)

        for widget in order_frame_label.winfo_children():
            widget.grid_configure(padx=10, pady=5)


class SellingPage(Frame):
    def __init__(self, root):

        super().__init__()

        def clean_product_table():
            data = product_table.get_children()
            for elements in data:
                product_table.delete(elements)

        def show_products():
            clean_product_table()
            search_entry.delete(0, END)
            conn = None
            try:
                conn = sqlite3.connect(resource_path("data/my_data.db"))
                cursor = conn.cursor()
                cursor.execute('SELECT code, title, unit, price, count FROM product')
                data = cursor.fetchall()

                for row in data:
                    product_table.insert('', END, values=row)
                conn.close()
            except Exception as e:
                showinfo('', str(e))

        def search_product():
            clean_product_table()
            conn = None
            try:
                if search_label.cget('text') == '1':
                    conn = sqlite3.connect(resource_path("data/my_data.db"))
                    cursor = conn.cursor()
                    title = search_entry.get()
                    if len(title) < 1:
                        show_products()
                    else:
                        cursor.execute(
                            '''SELECT code, title, unit, price, count FROM product WHERE title LIKE ?''',
                            ("%" + title + "%",)
                        )
                        data = cursor.fetchall()
                        if data:
                            for row in data:
                                product_table.insert("", END, values=row)
                        else:
                            showwarning('Предупреждение', 'Результаты поиска не найдены')
                elif search_label.cget('text') == '2':
                    conn = sqlite3.connect(resource_path("data/my_data.db"))
                    cursor = conn.cursor()
                    title = search_entry.get()
                    if len(title) < 1:
                        show_products()
                    else:
                        cursor.execute(
                            '''SELECT code, title, unit, price, count FROM product WHERE code LIKE ?''',
                            ("%" + title + "%",)
                        )
                        data = cursor.fetchall()
                        if data:
                            for row in data:
                                product_table.insert("", END, values=row)
                        else:
                            showwarning('Предупреждение', 'Результаты поиска не найдены')
            except Exception as e:
                showerror("Ошибка", str(e))
            finally:
                if conn is not None:
                    conn.close()

        def select_product(event):
            item = product_table.focus()
            tp = product_table.item(item, "values")

            for k in cart_table.get_children(''):
                cart_title = cart_table.item(k).get('values')[1]
                if str(tp[1]) == str(cart_title):
                    showwarning('', 'Товар уже в корзине')
                    return

            cart_code_entry.configure(state='normal')
            cart_title_entry.configure(state='normal')

            cart_code_entry.delete(0, END)
            cart_title_entry.delete(0, END)
            cart_price_entry.delete(0, END)
            cart_count_entry.delete(0, END)

            try:
                cart_code_entry.insert(index=0, string=tp[0])
                cart_title_entry.insert(index=0, string=tp[1])
                cart_price_entry.insert(index=0, string=tp[3])
                cart_count_entry.insert(index=0, string='1')
            except Exception as e:
                pass

            cart_code_entry.configure(state='readonly')
            cart_title_entry.configure(state='readonly')

        def restart():
            search_entry.delete(0, END)
            cart_code_entry.configure(state='normal')
            cart_title_entry.configure(state='normal')

            cart_code_entry.delete(0, END)
            cart_title_entry.delete(0, END)
            cart_price_entry.delete(0, END)
            cart_count_entry.delete(0, END)

            cart_code_entry.configure(state='readonly')
            cart_title_entry.configure(state='readonly')

            conn = None
            try:
                conn = sqlite3.connect(resource_path("data/my_data.db"))
                cursor = conn.cursor()
                db = "SELECT code, title, unit, price, count FROM product"
                cursor.execute(db)

                fetch_data = product_table.get_children()
                for elements in fetch_data:
                    product_table.delete(elements)

                data = cursor.fetchall()
                for d in data:
                    product_table.insert("", END, values=d)

                conn.commit()
            except Exception as e:
                showerror("Fail", str(e))
                conn.rollback()
            finally:
                if conn is not None:
                    conn.close()

        def clean_cart_detail():
            cart_code_entry.configure(state='normal')
            cart_title_entry.configure(state='normal')

            cart_code_entry.delete(0, END)
            cart_title_entry.delete(0, END)
            cart_price_entry.delete(0, END)
            cart_count_entry.delete(0, END)

            cart_code_entry.configure(state='readonly')
            cart_title_entry.configure(state='readonly')

        def add_to_cart():
            if cart_code_entry.get():
                conn = None
                try:
                    conn = sqlite3.connect(resource_path("data/my_data.db"))
                    cursor = conn.cursor()
                    cursor.execute('SELECT title, count FROM product WHERE title=?', (cart_title_entry.get(),))
                    data = cursor.fetchone()
                    conn.close()
                    if float(cart_count_entry.get()) > float(data[1]):
                        showwarning('Предупреждение', f'Товара осталось всего {float(data[1])}')
                        return
                except Exception as e:
                    showwarning('', str(e))

                order_total_entry.delete(0, END)
                total = float(cart_price_entry.get()) * float(cart_count_entry.get())

                value = (cart_code_entry.get(), cart_title_entry.get(), cart_price_entry.get(), cart_count_entry.get(),
                         total)
                cart_table.insert("", END, values=value)
                total_orders = 0
                for k in cart_table.get_children(""):
                    a = cart_table.item(k).get('values')[4]
                    total_orders += float(a)
                order_total_entry.insert(0, string=str(total_orders))
                clean_cart_detail()
            else:
                showwarning('Предупреждение', 'Товар не выбран')

        def delete_from_cart(event):
            try:
                item = cart_table.focus()
                if item:
                    total = float(order_total_entry.get())
                    order_total_entry.delete(0, END)
                    cur = cart_table.item(item).get('values')[4]
                    cart_table.delete(item)
                    new_data = total - float(cur)
                    order_total_entry.insert(0, string=str(new_data))
            except Exception as e:
                pass

        def post_order():
            order_total_entry.delete(0, END)
            consumer_entry.delete(0, END)

            fetch_data = cart_table.get_children()
            for f in fetch_data:
                cart_table.delete(f)
            order_total_entry.insert(0, '0')
            consumer_entry.insert(0, '-')

        def order():
            try:
                if float(order_total_entry.get()) == 0:
                    showerror('Предупреждение', 'Корзина пуста')
                else:
                    answer = askyesno(title="Вопрос", message="Вы уверены?")
                    if answer:
                        conn = sqlite3.connect(resource_path("data/my_data.db"))
                        cursor = conn.cursor()
                        consumer = consumer_entry.get()
                        date = order_date_entry.get()
                        total = order_total_entry.get()

                        cursor = conn.cursor()
                        data_insert_query = '''INSERT INTO "order" (consumer, date, total) VALUES (?, ?, ?)'''
                        data_insert_tuple = (consumer, date, total)
                        cursor.execute(data_insert_query, data_insert_tuple)
                        conn.commit()

                        cursor = conn.cursor()
                        cursor.execute('SELECT MAX(id) FROM "order"')
                        order_id = cursor.fetchone()[0]

                        order_detail_insert_query = '''INSERT INTO order_detail (order_id, product_id, price, count, total) 
                        VALUES (?, ?, ?, ?, ?)'''

                        for k in cart_table.get_children(""):
                            cursor = conn.cursor()
                            product_title = cart_table.item(k).get('values')[1]
                            cursor.execute("SELECT * FROM product WHERE title=?", (product_title,))
                            product_id = cursor.fetchone()[0]

                            cursor = conn.cursor()
                            price = cart_table.item(k).get('values')[2]
                            count = cart_table.item(k).get('values')[3]
                            total_ord = cart_table.item(k).get('values')[4]
                            order_detail_insert_tuple = (order_id, product_id, price, count, total_ord)
                            cursor.execute(order_detail_insert_query, order_detail_insert_tuple)
                            conn.commit()

                            cursor = conn.cursor()
                            cursor.execute("SELECT * FROM product WHERE id=?", (product_id,))
                            old_product_count = cursor.fetchone()[5]
                            current_product_count = float(old_product_count) - float(count)
                            cursor.execute("UPDATE product SET count=? WHERE id=?",
                                           (current_product_count, product_id))
                            conn.cursor()
                        conn.commit()
                        conn.close()
                        restart()
                        post_order()
            except Exception as e:
                showwarning('', str(e))

        self.root = root

        style = ttk.Style()
        style.theme_use("clam")
        style.map("Treeview")
        style.configure("Treeview", font=('None', 13))
        style.configure("Treeview.Heading", font=('None', 13, 'bold'))

        # TODO LEFT FRAME
        left_frame = Frame(self.root)
        left_frame.pack(side=LEFT, fill=Y)
        left_frame.pack_propagate(False)
        left_frame.configure(width=800)

        search_frame = LabelFrame(left_frame, bd=1, padx=5, pady=5, relief=RIDGE)
        search_frame.pack(side=TOP, fill=X)
        search_frame.pack_propagate(False)
        search_frame.configure(height=50)

        search_entry = Entry(search_frame, width=25, font=('None', 15))
        search_entry.grid(row=0, column=0)

        def selection():
            slc = str(radio.get())
            search_label.config(text=slc)

        radio = IntVar()

        name_btn = Radiobutton(search_frame, text="Товар", variable=radio, value=1, command=selection,
                               font=('None', 12))
        name_btn.grid(row=0, column=1)

        code_btn = Radiobutton(search_frame, text="Артикул", variable=radio, value=2, command=selection,
                               font=('None', 12))
        code_btn.grid(row=0, column=2)

        search_label = Label()

        search_btn = Button(search_frame, text='Поиск', width=8, command=search_product,
                            font=('None', 13), bd=3, fg='black')
        search_btn.grid(row=0, column=3)
        table_rst_btn = Button(search_frame, text='Обновить', width=8, command=show_products,
                               font=('None', 13), bd=3, fg='black')
        table_rst_btn.grid(row=0, column=4)

        for widget in search_frame.winfo_children():
            widget.grid_configure(padx=5, pady=5)
        name_btn.invoke()

        # TODO PRODUCT TABLE FRAME
        product_table_frame = Frame(left_frame, relief=RIDGE, bd=1, padx=5, pady=5)
        product_table_frame.pack(side=TOP, fill=X)
        product_table_frame.pack_propagate(False)
        product_table_frame.configure(width=800, height=800)

        product_table_sc_x = Scrollbar(product_table_frame, orient=HORIZONTAL)
        product_table_sc_x.pack(side=BOTTOM, fill=X)
        product_table_sc_y = Scrollbar(product_table_frame, orient=VERTICAL)
        product_table_sc_y.pack(side=RIGHT, fill=Y)
        product_table = ttk.Treeview(product_table_frame,
                                     column=('code', 'title', 'unit', 'price', 'quantity'),
                                     xscrollcommand=product_table_sc_x.set,
                                     yscrollcommand=product_table_sc_y.set)
        product_table_sc_x.config(command=product_table.xview)
        product_table_sc_y.config(command=product_table.yview)
        product_table.heading('code', text='Артикул')
        product_table.heading('title', text='Товар', command=lambda: sort(product_table, 'title', False))
        product_table.heading('unit', text='Единица')
        product_table.heading('price', text='Цена')
        product_table.heading('quantity', text='Количество',
                              command=lambda: sort(product_table, 'quantity', False, key=float))
        product_table['show'] = 'headings'
        product_table.pack(fill=BOTH, expand=1)
        product_table.column('code', width=50)
        product_table.column('title', width=220)
        product_table.column('unit', width=50, anchor='e')
        product_table.column('price', width=100, anchor='e')
        product_table.column('quantity', width=100, anchor='e')

        product_table.bind("<Double-1>", select_product)

        show_products()

        # TODO RIGHT FRAME
        right_frame = Frame(self.root)
        right_frame.pack(side=RIGHT, fill=Y)
        right_frame.pack_propagate(False)
        right_frame.configure(width=800)

        cart_frame = Frame(right_frame, bd=1, padx=3, pady=3, relief=RIDGE)
        cart_frame.pack(side=TOP, fill=X)
        cart_frame.pack_propagate(False)
        cart_frame.configure(height=150)

        cart_label = LabelFrame(cart_frame, text='Добавление в корзину', font=('None', 13), fg='red')
        cart_label.pack(side=TOP, fill=X)

        cart_code_label = Label(cart_label, font=('None', 13, 'bold'), text='Артикул', width=15)
        cart_code_label.grid(row=0, column=0)
        cart_code_entry = Entry(cart_label, font=('None', 13), state='readonly', width=15)
        cart_code_entry.grid(row=1, column=0)

        cart_title_label = Label(cart_label, font=('None', 13, 'bold'), text='Товар')
        cart_title_label.grid(row=0, column=1)
        cart_title_entry = Entry(cart_label, font=('None', 13), state='readonly')
        cart_title_entry.grid(row=1, column=1)

        cart_price_label = Label(cart_label, font=('None', 13, 'bold'), text='Цена', width=15)
        cart_price_label.grid(row=0, column=2)
        cart_price_entry = Entry(cart_label, font=('None', 13), width=15)
        cart_price_entry.grid(row=1, column=2)

        cart_count_label = Label(cart_label, font=('None', 13, 'bold'), text='Количество', width=15)
        cart_count_label.grid(row=0, column=3)
        cart_count_entry = Entry(cart_label, font=('None', 13), width=15)
        cart_count_entry.grid(row=1, column=3)

        cart_adding_btn = Button(cart_label, text='Добавить корзину', font=('None', 13), command=add_to_cart,
                                 fg='black')
        cart_adding_btn.grid(row=2, column=3)

        for widget in cart_label.winfo_children():
            widget.grid_configure(padx=5, pady=5)

        # CART_TABLE_FRAME
        cart_table_frame = Frame(right_frame, relief=RIDGE, bd=1, padx=5, pady=5)
        cart_table_frame.pack(side=TOP, fill='y')
        cart_table_frame.pack_propagate(False)
        cart_table_frame.configure(width=800, height=450)

        cart_table_sc_x = Scrollbar(cart_table_frame, orient=HORIZONTAL)
        cart_table_sc_x.pack(side=BOTTOM, fill=X)
        cart_table_sc_y = Scrollbar(cart_table_frame, orient=VERTICAL)
        cart_table_sc_y.pack(side=RIGHT, fill=Y)
        cart_table = ttk.Treeview(cart_table_frame,
                                  column=('code', 'title', 'price', 'quantity', 'total'),
                                  xscrollcommand=cart_table_sc_x.set,
                                  yscrollcommand=cart_table_sc_y.set)
        cart_table_sc_x.config(command=cart_table.xview)
        cart_table_sc_y.config(command=cart_table.yview)
        cart_table.heading('code', text='Артикул')
        cart_table.heading('title', text='Товар')
        cart_table.heading('price', text='Цена')
        cart_table.heading('quantity', text='Количество')
        cart_table.heading('total', text='Сумма')
        cart_table['show'] = 'headings'
        cart_table.pack(fill=BOTH, expand=1)
        cart_table.column('code', width=40)
        cart_table.column('title', width=200)
        cart_table.column('price', width=50, anchor='e')
        cart_table.column('quantity', width=50, anchor='e')
        cart_table.column('total', width=50, anchor='e')

        cart_table.bind("<Double-1>", delete_from_cart)

        # ORDER FRAME
        order_frame = Frame(right_frame, bd=1, padx=5, pady=5, relief=RIDGE)
        order_frame.pack(side=TOP, fill=X)
        order_frame.pack_propagate(False)
        order_frame.configure(height=300)

        order_frame_label = LabelFrame(order_frame, text='Детали заказа', font=('None', 13), fg='red')
        order_frame_label.pack(side=TOP, fill=X)

        consumer_label = Label(order_frame_label, text="Покупатель", font=('None', 13, 'bold'))
        consumer_label.grid(row=0, column=0)
        order_date_label = Label(order_frame_label, text="Дата", font=('None', 13, 'bold'))
        order_date_label.grid(row=0, column=1)

        consumer_entry = Entry(order_frame_label, width=20, font=('None', 13))
        order_date_entry = DateEntry(order_frame_label, selectmode='day', locale='ru_RU', date_pattern='dd.MM.yyyy',
                                     font=('None', 13))

        consumer_entry.grid(row=1, column=0)
        consumer_entry.insert(0, '-')
        order_date_entry.grid(row=1, column=1)

        order_total_label = Label(order_frame_label, text="Сумма", font=('None', 13, 'bold'))
        order_total_label.grid(row=0, column=2)
        order_total_entry = Entry(order_frame_label, font=('None', 13))
        order_total_entry.grid(row=1, column=2)
        order_total_entry.insert(0, '0')

        order_button = Button(order_frame_label, text="Продать", command=order, width=12,
                              font=('None', 13, 'bold'), bd=3, fg='black')
        order_button.grid(row=1, column=3)

        for widget in order_frame_label.winfo_children():
            widget.grid_configure(padx=10, pady=5)


class StockPage(Frame):
    def __init__(self, root):

        super().__init__()

        def clean_product_table():
            data = product_table.get_children()
            for elements in data:
                product_table.delete(elements)

        def show_products():
            button.configure(text='Создать товар', command=add_product)
            clean_product_table()
            title_entry.delete(0, END)
            search_entry.delete(0, END)
            unit_combobox.delete(0, END)
            code_entry.delete(0, END)
            price_entry.delete(0, END)
            unit_combobox.current(0)
            conn = None
            try:
                conn = sqlite3.connect(resource_path("data/my_data.db"))
                cursor = conn.cursor()
                cursor.execute('SELECT code, title, unit, price, count FROM product')
                data = cursor.fetchall()

                for row in data:
                    product_table.insert('', END, values=row)
                conn.close()
            except Exception as e:
                showinfo('', str(e))

        def clean_cart_table():
            data = cart_table.get_children()
            for elements in data:
                cart_table.delete(elements)
            order_total_entry.delete(0, END)
            order_date_entry.delete(0, END)
            supplier_entry.delete(0, END)
            today = datetime.date.today()
            dt = datetime.date.strftime(today, '%d.%m.%Y')
            order_date_entry.insert(0, str(dt))

        def add_product():
            title = title_entry.get()
            unit = unit_combobox.get()
            code = code_entry.get()
            price = price_entry.get()
            if not code:
                code = '-'
            if title:
                conn = None
                try:
                    conn = sqlite3.connect(resource_path("data/my_data.db"))
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM product WHERE title=?", (title,))
                    data = cursor.fetchall()

                    if data:
                        showwarning(title="Ошибка", message="Этот товар уже есть!")
                    else:
                        data_insert_query = '''INSERT INTO product (title, code, unit, price) VALUES (?, ?, ?, ?)'''
                        data_insert_tuple = (title, code, unit, price)
                        cursor.execute(data_insert_query, data_insert_tuple)
                        conn.commit()
                        conn.close()
                        showinfo(title='', message='Товар добавлен')
                        title_entry.delete(0, END)
                        unit_combobox.delete(0, END)
                        unit_combobox.current(0)
                        show_products()
                except Exception as e:
                    showinfo('', str(e))
            else:
                showwarning(title='Ошибка', message='Требуется название товара')

        def search_product():
            button.configure(text='Создать товар', command=add_product)
            clean_product_table()
            conn = None
            try:
                if search_label.cget('text') == '1':
                    conn = sqlite3.connect(resource_path("data/my_data.db"))
                    cursor = conn.cursor()
                    title = search_entry.get()
                    if len(title) < 1:
                        show_products()
                    else:
                        cursor.execute(
                            '''SELECT code, title, unit, price, count FROM product WHERE title LIKE ?''',
                            ("%" + title + "%",)
                        )
                        data = cursor.fetchall()
                        if data:
                            for row in data:
                                product_table.insert("", END, values=row)
                        else:
                            showwarning('Предупреждение', 'Результаты поиска не найдены')
                elif search_label.cget('text') == '2':
                    conn = sqlite3.connect(resource_path("data/my_data.db"))
                    table_create_query = '''CREATE TABLE IF NOT EXISTS product 
                                                                                (id INTEGER PRIMARY KEY, title TEXT UNIQUE, code TEXT, unit TEXT, price REAL DEFAULT 0, count REAL DEFAULT 0)
                                                                        '''
                    conn.execute(table_create_query)
                    cursor = conn.cursor()
                    title = search_entry.get()
                    if len(title) < 1:
                        show_products()
                    else:
                        cursor.execute(
                            '''SELECT code, title, unit, price, count FROM product WHERE code LIKE ?''',
                            ("%" + title + "%",)
                        )
                        data = cursor.fetchall()
                        if data:
                            for row in data:
                                product_table.insert("", END, values=row)
                        else:
                            showwarning('Предупреждение', 'Результаты поиска не найдены')
            except Exception as e:
                showinfo("", str(e))
            finally:
                if conn is not None:
                    conn.close()

        def select_product(event):
            product_entry.delete(0, END)

            cart_code_entry.configure(state='normal')
            cart_title_entry.configure(state='normal')
            cart_unit_entry.configure(state='normal')

            unit_combobox.configure(state='normal')

            cart_code_entry.delete(0, END)
            cart_title_entry.delete(0, END)
            cart_unit_entry.delete(0, END)

            title_entry.delete(0, END)
            code_entry.delete(0, END)
            unit_combobox.delete(0, END)
            price_entry.delete(0, END)

            item = product_table.focus()
            tp = product_table.item(item, "values")

            product_entry.insert(index=0, string=tp[1])

            cart_code_entry.insert(index=0, string=tp[0])
            cart_title_entry.insert(index=0, string=tp[1])
            cart_unit_entry.insert(index=0, string=tp[2])

            cart_code_entry.configure(state='readonly')
            cart_title_entry.configure(state='readonly')
            cart_unit_entry.configure(state='readonly')

            code_entry.insert(index=0, string=tp[0])
            title_entry.insert(index=0, string=tp[1])
            unit_combobox.insert(index=0, string=tp[2])
            price_entry.insert(index=0, string=tp[3])

            unit_combobox.configure(state='readonly')
            button.configure(text='Обновить товар', command=update_product)

        def update_product():
            print(product_entry.get())

            title = title_entry.get()
            unit = unit_combobox.get()
            code = code_entry.get()
            price = price_entry.get()
            connection = None
            try:
                connection = sqlite3.connect(resource_path("data/my_data.db"))
                cursor = connection.cursor()
                cursor.execute("SELECT * FROM product WHERE title=?", (product_entry.get(),))
                product_id = cursor.fetchall()[0][0]
                cursor = connection.cursor()
                cursor.execute("UPDATE product SET title=?, code=?, unit=?, price=? WHERE id=?",
                               (title, code, unit, price, product_id))
                connection.commit()
                showinfo('', 'Товар обновлен')
                clean_cart_table()
                show_products()

                cart_code_entry.configure(state='normal')
                cart_title_entry.configure(state='normal')
                cart_unit_entry.configure(state='normal')

                cart_code_entry.delete(0, END)
                cart_title_entry.delete(0, END)
                cart_unit_entry.delete(0, END)
                cart_price_entry.delete(0, END)
                cart_count_entry.delete(0, END)
                cart_total_entry.delete(0, END)

                cart_code_entry.configure(state='readonly')
                cart_title_entry.configure(state='readonly')
                cart_unit_entry.configure(state='readonly')

                button.configure(text='Создать товар', command=add_product)

            except Exception as e:
                showwarning('', str(e))
            finally:
                if connection is not None:
                    connection.close()

        def add_to_cart():
            cart_code = cart_code_entry.get()
            cart_price = cart_price_entry.get()
            cart_count = cart_count_entry.get()
            cart_total = cart_total_entry.get()
            if cart_code and cart_price and cart_count and cart_total:
                value = (cart_code_entry.get(), cart_title_entry.get(), cart_unit_entry.get(), cart_price_entry.get(),
                         cart_count_entry.get(), cart_total_entry.get())
                cart_table.insert("", END, values=value)

                cart_code_entry.configure(state='normal')
                cart_title_entry.configure(state='normal')
                cart_unit_entry.configure(state='normal')

                cart_code_entry.delete(0, END)
                cart_title_entry.delete(0, END)
                cart_unit_entry.delete(0, END)
                cart_price_entry.delete(0, END)
                cart_count_entry.delete(0, END)
                cart_total_entry.delete(0, END)

                cart_code_entry.configure(state='readonly')
                cart_title_entry.configure(state='readonly')
                cart_unit_entry.configure(state='readonly')

                button.configure(text='Создать товар', command=add_product)
                title_entry.delete(0, END)
                search_entry.delete(0, END)
                unit_combobox.delete(0, END)
                code_entry.delete(0, END)
                price_entry.delete(0, END)
                unit_combobox.current(0)

        def delete_from_cart(event):
            item = cart_table.focus()
            if item:
                cart_table.delete(item)

        def import_order():
            conn = None
            total = order_total_entry.get()
            data = cart_table.get_children('')
            if data:
                if total:
                    try:
                        conn = sqlite3.connect(resource_path("data/my_data.db"))
                        cursor = conn.cursor()

                        data_insert_query = '''INSERT INTO import_order (supplier, date, total) VALUES (?, ?, ?)'''
                        supplier = supplier_entry.get()
                        date = order_date_entry.get()
                        total = order_total_entry.get()
                        data_insert_tuple = (supplier, date, total)

                        cursor.execute(data_insert_query, data_insert_tuple)
                        conn.commit()

                        cursor.execute("SELECT MAX(id) FROM import_order")
                        order_id = cursor.fetchone()[0]
                        cursor = conn.cursor()
                        conn.commit()

                        order_insert_query = '''INSERT INTO import_order_detail (import_order_id, product_id, price, count, total) VALUES (?, ?, ?, ?, ?)'''

                        for i in cart_table.get_children(""):
                            product_title = cart_table.item(i).get('values')[1]
                            cursor.execute("SELECT * FROM product WHERE title=?", (product_title,))
                            product_id = cursor.fetchone()[0]

                            price = cart_table.item(i).get('values')[3]
                            count = cart_table.item(i).get('values')[4]
                            total = cart_table.item(i).get('values')[5]
                            order_insert_tuple = (order_id, product_id, price, count, total)
                            cursor.execute(order_insert_query, order_insert_tuple)
                            conn.commit()

                            cursor = conn.cursor()
                            cursor.execute("SELECT * FROM product WHERE title=?", (product_title,))
                            old_product_count = cursor.fetchone()[5]
                            current_product_count = float(old_product_count) + float(count)
                            cursor.execute("UPDATE product SET count=? WHERE title=?",
                                           (current_product_count, product_title))
                            conn.cursor()

                        conn.commit()

                        conn.close()
                        clean_cart_table()
                        show_products()
                        button.configure(text='Создать товар', command=add_product)
                    except Exception as e:
                        showinfo('', str(e))
                else:
                    showwarning('', 'Введите сумму')
            else:
                showwarning('', 'Корзина пуста')

        self.root = root

        style = ttk.Style()
        style.theme_use("clam")
        style.map("Treeview")
        style.configure("Treeview", font=('None', 13))
        style.configure("Treeview.Heading", font=('None', 13, 'bold'))

        # TODO LEFT FRAME
        left_frame = Frame(self.root)
        left_frame.pack(side=LEFT, fill=Y)
        left_frame.pack_propagate(False)
        left_frame.configure(width=800)

        search_frame = LabelFrame(left_frame, bd=1, padx=5, pady=5, relief=RIDGE)
        search_frame.pack(side=TOP, fill=X)
        search_frame.pack_propagate(False)
        search_frame.configure(height=50)

        search_entry = Entry(search_frame, width=25, font=('None', 15))
        search_entry.grid(row=0, column=0)

        def selection():
            slc = str(radio.get())
            search_label.config(text=slc)

        radio = IntVar()

        name_btn = Radiobutton(search_frame, text="Товар", variable=radio, value=1, command=selection,
                               font=('None', 12))
        name_btn.grid(row=0, column=1)

        code_btn = Radiobutton(search_frame, text="Артикул", variable=radio, value=2, command=selection,
                               font=('None', 12))
        code_btn.grid(row=0, column=2)

        search_label = Label()

        search_btn = Button(search_frame, text='Поиск', width=8, command=search_product,
                            font=('None', 13), bd=3, fg='black')
        search_btn.grid(row=0, column=3)
        table_rst_btn = Button(search_frame, text='Обновить', width=8, command=show_products,
                               font=('None', 13), bd=3, fg='black')
        table_rst_btn.grid(row=0, column=4)
        product_entry = Entry()

        for widget in search_frame.winfo_children():
            widget.grid_configure(padx=5, pady=5)
        name_btn.invoke()

        # TODO PRODUCT FRAME
        product_frame = Frame(left_frame, bd=1, padx=5, pady=5, relief=RIDGE)
        product_frame.pack(side=TOP, fill=X)
        product_frame.pack_propagate(False)
        product_frame.configure(height=120)

        product_label = LabelFrame(product_frame, text='Добавление продукта', font=('None', 13), fg='red')
        product_label.pack(side=TOP, fill=X)

        title_label = Label(product_label, text="Имя продукта", font=('None', 13, 'bold'))
        title_label.grid(row=0, column=0)
        title_entry = Entry(product_label, width=20, font=('None', 15))
        title_entry.grid(row=1, column=0)

        code_label = Label(product_label, text="Артикул", font=('None', 13, 'bold'))
        code_label.grid(row=0, column=1)
        code_entry = Entry(product_label, width=11, font=('None', 15))
        code_entry.grid(row=1, column=1)

        unit_label = Label(product_label, text="Единица", font=('None', 13, 'bold'))
        unit_combobox = ttk.Combobox(product_label, values=['-', 'шт', 'к-т'], width=10, font=('None', 13),
                                     state='readonly')
        unit_combobox.current(0)
        unit_label.grid(row=0, column=3)
        unit_combobox.grid(row=1, column=3)

        price_label = Label(product_label, text="Цена продажи", font=('None', 13, 'bold'))
        price_label.grid(row=0, column=4)
        price_entry = Entry(product_label, width=12, font=('None', 15))
        price_entry.grid(row=1, column=4)

        button = Button(product_label, text="Создать товар", command=add_product, font=('None', 13), bd=3, fg='black')
        button.grid(row=1, column=5, sticky="news", padx=5, pady=5)

        for widget in product_label.winfo_children():
            widget.grid_configure(padx=5, pady=5)

        # TODO PRODUCT TABLE FRAME
        product_table_frame = Frame(left_frame, relief=RIDGE, bd=1, padx=5, pady=5)
        product_table_frame.pack(side=TOP, fill=X)
        product_table_frame.pack_propagate(False)
        product_table_frame.configure(height=600)

        product_table_sc_x = Scrollbar(product_table_frame, orient=HORIZONTAL)
        product_table_sc_x.pack(side=BOTTOM, fill=X)
        product_table_sc_y = Scrollbar(product_table_frame, orient=VERTICAL)
        product_table_sc_y.pack(side=RIGHT, fill=Y)
        product_table = ttk.Treeview(product_table_frame,
                                     column=('code', 'title', 'unit', 'price', 'count'),
                                     xscrollcommand=product_table_sc_x.set,
                                     yscrollcommand=product_table_sc_y.set)
        product_table_sc_x.config(command=product_table.xview)
        product_table_sc_y.config(command=product_table.yview)
        product_table.heading('code', text='Артикул')
        product_table.heading('title', text='Товар', command=lambda: sort(product_table, 'title', False))
        product_table.heading('unit', text='Ед.')
        product_table.heading('price', text='Цена продажи')
        product_table.heading('count', text='К-во')
        product_table['show'] = 'headings'
        product_table.pack(fill=BOTH, expand=1)
        product_table.column('code', width=50)
        product_table.column('title', width=150)
        product_table.column('unit', width=30, anchor='e')
        product_table.column('price', width=50, anchor='e')
        product_table.column('count', width=40, anchor='e')
        product_table.bind("<Double-1>", select_product)
        show_products()

        # TODO RIGHT FRAME
        right_frame = Frame(self.root)
        right_frame.pack(side=LEFT, fill=Y)
        right_frame.pack_propagate(False)
        right_frame.configure(width=900)

        # CART FRAME
        cart_frame = Frame(right_frame, bd=1, padx=5, pady=5, relief=RIDGE)
        cart_frame.pack(side=TOP, fill=X)
        cart_frame.pack_propagate(False)
        cart_frame.configure(height=200)

        cart_label = LabelFrame(cart_frame, text='Добавление в корзину', font=('None', 13), fg='red')
        cart_label.pack(side=TOP, fill=X)

        cart_code_label = Label(cart_label, font=('None', 13, 'bold'), text='Артикул')
        cart_code_label.grid(row=0, column=0)
        cart_code_entry = Entry(cart_label, font=('None', 13), state='readonly')
        cart_code_entry.grid(row=1, column=0)

        cart_title_label = Label(cart_label, font=('None', 13, 'bold'), text='Товар')
        cart_title_label.grid(row=0, column=1)
        cart_title_entry = Entry(cart_label, font=('None', 13), state='readonly')
        cart_title_entry.grid(row=1, column=1)

        cart_unit_label = Label(cart_label, font=('None', 13, 'bold'), text='Единица')
        cart_unit_label.grid(row=0, column=2)
        cart_unit_entry = Entry(cart_label, font=('None', 13), state='readonly')
        cart_unit_entry.grid(row=1, column=2)

        cart_price_label = Label(cart_label, font=('None', 13, 'bold'), text='Цена Покупка')
        cart_price_label.grid(row=2, column=0)
        cart_price_entry = Entry(cart_label, font=('None', 13))
        cart_price_entry.grid(row=3, column=0)

        cart_count_label = Label(cart_label, font=('None', 13, 'bold'), text='Количество')
        cart_count_label.grid(row=2, column=1)
        cart_count_entry = Entry(cart_label, font=('None', 13))
        cart_count_entry.grid(row=3, column=1)

        cart_total_label = Label(cart_label, font=('None', 13, 'bold'), text='Сумма')
        cart_total_label.grid(row=2, column=2)
        cart_total_entry = Entry(cart_label, font=('None', 13))
        cart_total_entry.grid(row=3, column=2)

        cart_adding_btn = Button(cart_label, text='Добавить', font=('None', 13), command=add_to_cart,
                                 fg='black')
        cart_adding_btn.grid(row=3, column=3)

        for widget in cart_label.winfo_children():
            widget.grid_configure(padx=5, pady=5)

        # CART TABLE LABEL
        cart_table_frame = Frame(right_frame, relief=RIDGE, bd=1, padx=5, pady=5)
        cart_table_frame.pack(side=TOP, fill=X)
        cart_table_frame.pack_propagate(False)
        cart_table_frame.configure(height=400)

        cart_table_sc_x = Scrollbar(cart_table_frame, orient=HORIZONTAL)
        cart_table_sc_x.pack(side=BOTTOM, fill=X)
        cart_table_sc_y = Scrollbar(cart_table_frame, orient=VERTICAL)
        cart_table_sc_y.pack(side=RIGHT, fill=Y)
        cart_table = ttk.Treeview(cart_table_frame,
                                  column=('code', 'title', 'unit', 'price', 'count', 'total'),
                                  xscrollcommand=cart_table_sc_x.set,
                                  yscrollcommand=cart_table_sc_y.set)
        cart_table_sc_x.config(command=cart_table.xview)
        cart_table_sc_y.config(command=cart_table.yview)
        cart_table.heading('code', text='Артикул')
        cart_table.heading('title', text='Товар')
        cart_table.heading('unit', text='Ед.')
        cart_table.heading('price', text='Цена покупки')
        cart_table.heading('count', text='К-во')
        cart_table.heading('total', text='Сумма')
        cart_table['show'] = 'headings'
        cart_table.pack(fill=BOTH, expand=1)
        cart_table.column('code', width=50)
        cart_table.column('title', width=150)
        cart_table.column('unit', width=30)
        cart_table.column('price', width=60, anchor=E)
        cart_table.column('count', width=40, anchor=E)
        cart_table.column('total', width=40, anchor=E)
        cart_table.bind("<Double-1>", delete_from_cart)

        # ORDER FRAME
        order_frame = Frame(right_frame, bd=1, padx=5, pady=5, relief=RIDGE)
        order_frame.pack(side=TOP, fill=X)
        order_frame.pack_propagate(False)
        order_frame.configure(height=300)

        order_frame_label = LabelFrame(order_frame, text='Детали заказа', font=('None', 13), fg='red')
        order_frame_label.pack(side=TOP, fill=X)

        supplier_label = Label(order_frame_label, text="Поставшик", font=('None', 13, 'bold'))
        supplier_label.grid(row=0, column=0)
        order_date_label = Label(order_frame_label, text="Дата", font=('None', 13, 'bold'))
        order_date_label.grid(row=0, column=1)

        supplier_entry = Entry(order_frame_label, width=20, font=('None', 13))
        order_date_entry = DateEntry(order_frame_label, selectmode='day', locale='ru_RU', date_pattern='dd.MM.yyyy',
                                     font=('None', 13))

        supplier_entry.grid(row=1, column=0)
        order_date_entry.grid(row=1, column=1)

        order_total_label = Label(order_frame_label, text="Сумма", font=('None', 13, 'bold'))
        order_total_label.grid(row=0, column=2)
        order_total_entry = Entry(order_frame_label, font=('None', 13))
        order_total_entry.grid(row=1, column=2)

        order_button = Button(order_frame_label, text="Покупка", command=import_order, width=12,
                              font=('None', 13), bd=3, fg='black')
        order_button.grid(row=1, column=3)

        for widget in order_frame_label.winfo_children():
            widget.grid_configure(padx=10, pady=5)


class OrdersPage(Frame):
    def __init__(self, root):

        super().__init__()

        def clean_selling_table():
            data = selling_table.get_children()
            for elements in data:
                selling_table.delete(elements)

        def show_selling_table():
            clean_selling_table()
            selling_search_entry.delete(0, END)
            connection = None
            try:
                connection = sqlite3.connect(resource_path("data/my_data.db"))
                cursor = connection.cursor()
                cursor.execute('''SELECT product.code, product.title, order_detail.price, order_detail.count, order_detail.total, "order".date, "order".consumer
                                FROM order_detail 
                                JOIN product ON product.id = order_detail.product_id
                                JOIN "order" ON "order".id = order_detail.order_id ''')
                data = cursor.fetchall()

                for row in data:
                    selling_table.insert('', END, values=row)
                connection.close()
            except Exception as e:
                pass
            finally:
                if connection is not None:
                    connection.close()

        def search_selling_table():
            clean_selling_table()
            connection = None
            try:
                if selling_search_label.cget('text') == '1':
                    connection = sqlite3.connect(resource_path("data/my_data.db"))
                    cursor = connection.cursor()
                    title = selling_search_entry.get()
                    if len(title) < 1:
                        show_selling_table()
                    else:
                        cursor.execute(
                            '''SELECT product.code, product.title, order_detail.price, order_detail.count, order_detail.total, "order".date, "order".consumer
                                FROM order_detail 
                                JOIN product ON product.id = order_detail.product_id
                                JOIN "order" ON "order".id = order_detail.order_id 
                                WHERE title LIKE ?''', ("%" + title + "%",)
                        )
                        data = cursor.fetchall()
                        if data:
                            for row in data:
                                selling_table.insert("", END, values=row)
                        else:
                            showwarning('Предупреждение', 'Результаты поиска не найдены')
                elif selling_search_label.cget('text') == '2':
                    connection = sqlite3.connect(resource_path("data/my_data.db"))
                    cursor = connection.cursor()
                    title = selling_search_entry.get()
                    if len(title) < 1:
                        show_selling_table()
                    else:
                        cursor.execute(
                            '''SELECT product.code, product.title, order_detail.price, order_detail.count, order_detail.total, "order".date, "order".consumer
                                FROM order_detail 
                                JOIN product ON product.id = order_detail.product_id
                                JOIN "order" ON "order".id = order_detail.order_id 
                                WHERE code LIKE ?''', ("%" + title + "%",)
                        )
                        data = cursor.fetchall()
                        if data:
                            for row in data:
                                selling_table.insert("", END, values=row)
                        else:
                            showwarning('Предупреждение', 'Результаты поиска не найдены')
            except Exception as e:
                showerror("Ошибка", str(e))
            finally:
                if connection is not None:
                    connection.close()

        def clean_buying_table():
            data = buying_table.get_children()
            for elements in data:
                buying_table.delete(elements)

        def show_buying_table():
            clean_buying_table()
            buying_search_entry.delete(0, END)
            connection = None
            try:
                connection = sqlite3.connect(resource_path("data/my_data.db"))
                cursor = connection.cursor()
                cursor.execute('''SELECT product.code, product.title, import_order_detail.price, import_order_detail.count, import_order_detail.total, "import_order".date, "import_order".supplier
                                FROM import_order_detail 
                                JOIN product ON product.id = import_order_detail.product_id
                                JOIN "import_order" ON "import_order".id = import_order_detail.import_order_id ''')
                data = cursor.fetchall()

                for row in data:
                    buying_table.insert('', END, values=row)
                connection.close()
            except Exception as e:
                showwarning('', str(e))
            finally:
                if connection is not None:
                    connection.close()

        def search_buying_table():
            clean_buying_table()
            connection = None
            try:
                if buying_search_label.cget('text') == '1':
                    connection = sqlite3.connect(resource_path("data/my_data.db"))
                    cursor = connection.cursor()
                    title = buying_search_entry.get()
                    if len(title) < 1:
                        show_buying_table()
                    else:
                        cursor.execute(
                            '''SELECT product.code, product.title, import_order_detail.price, import_order_detail.count, import_order_detail.total, "import_order".date, "import_order".supplier
                                FROM import_order_detail 
                                JOIN product ON product.id = import_order_detail.product_id
                                JOIN "import_order" ON "import_order".id = import_order_detail.import_order_id 
                                WHERE title LIKE ?''', ("%" + title + "%",)
                        )
                        data = cursor.fetchall()
                        if data:
                            for row in data:
                                buying_table.insert("", END, values=row)
                        else:
                            showwarning('Предупреждение', 'Результаты поиска не найдены')
                elif buying_search_label.cget('text') == '2':
                    connection = sqlite3.connect(resource_path("data/my_data.db"))
                    cursor = connection.cursor()
                    title = buying_search_entry.get()
                    if len(title) < 1:
                        show_buying_table()
                    else:
                        cursor.execute(
                            '''SELECT product.code, product.title, import_order_detail.price, import_order_detail.count, import_order_detail.total, "import_order".date, "import_order".supplier
                                FROM import_order_detail 
                                JOIN product ON product.id = import_order_detail.product_id
                                JOIN "import_order" ON "import_order".id = import_order_detail.import_order_id 
                                WHERE code LIKE ?''', ("%" + title + "%",)
                        )
                        data = cursor.fetchall()
                        if data:
                            for row in data:
                                buying_table.insert("", END, values=row)
                        else:
                            showwarning('Предупреждение', 'Результаты поиска не найдены')
            except Exception as e:
                showerror("Ошибка", str(e))
            finally:
                if connection is not None:
                    connection.close()

        self.root = root

        style = ttk.Style()
        style.theme_use("clam")
        style.map("Treeview")
        style.configure("Treeview", font=('None', 13))
        style.configure("Treeview.Heading", font=('None', 13, 'bold'))

        # TODO LEFT FRAME
        left_frame = Frame(self.root, bg='green', bd=2)
        left_frame.pack(side=LEFT, fill=Y)
        left_frame.pack_propagate(False)
        left_frame.configure(width=800)

        selling_search_frame = LabelFrame(left_frame, bd=1, padx=5, pady=5, relief=RIDGE)
        selling_search_frame.pack(side=TOP, fill=X)
        selling_search_frame.pack_propagate(False)
        selling_search_frame.configure(height=50)

        selling_search_entry = Entry(selling_search_frame, width=25, font=('None', 15))
        selling_search_entry.grid(row=0, column=0)

        def selling_selection():
            slc = str(selling_radio.get())
            selling_search_label.config(text=slc)

        selling_radio = IntVar()

        selling_name_btn = Radiobutton(selling_search_frame, text="Товар", variable=selling_radio, value=1,
                                       command=selling_selection,
                                       font=('None', 12))
        selling_name_btn.grid(row=0, column=1)

        selling_code_btn = Radiobutton(selling_search_frame, text="Артикул", variable=selling_radio, value=2,
                                       command=selling_selection,
                                       font=('None', 12))
        selling_code_btn.grid(row=0, column=2)

        selling_search_label = Label()

        selling_search_btn = Button(selling_search_frame, text='Поиск', width=8, command=search_selling_table,
                                    font=('None', 13), bd=3, fg='black')
        selling_search_btn.grid(row=0, column=3)
        selling_table_rst_btn = Button(selling_search_frame, text='Обновить', width=8, command=show_selling_table,
                                       font=('None', 13), bd=3, fg='black')
        selling_table_rst_btn.grid(row=0, column=4)

        for widget in selling_search_frame.winfo_children():
            widget.grid_configure(padx=5, pady=5)
        selling_name_btn.invoke()

        # TODO SELLING TABLE FRAME
        selling_table_frame = Frame(left_frame, relief=RIDGE, bd=1, padx=5, pady=5)
        selling_table_frame.pack(side=TOP, fill=X)
        selling_table_frame.pack_propagate(False)
        selling_table_frame.configure(width=800, height=800)

        selling_table_sc_x = Scrollbar(selling_table_frame, orient=HORIZONTAL)
        selling_table_sc_x.pack(side=BOTTOM, fill=X)
        selling_table_sc_y = Scrollbar(selling_table_frame, orient=VERTICAL)
        selling_table_sc_y.pack(side=RIGHT, fill=Y)
        selling_table = ttk.Treeview(selling_table_frame,
                                     column=('code', 'title', 'price', 'count', 'total', 'date', 'consumer'),
                                     xscrollcommand=selling_table_sc_x.set,
                                     yscrollcommand=selling_table_sc_y.set)
        selling_table_sc_x.config(command=selling_table.xview)
        selling_table_sc_y.config(command=selling_table.yview)
        selling_table.heading('code', text='Артикул')
        selling_table.heading('title', text='Товар', command=lambda: sort(selling_table, 'title', False))
        selling_table.heading('price', text='Цена')
        selling_table.heading('count', text='К-во',
                              command=lambda: sort(selling_table, 'count', False, key=float))
        selling_table.heading('total', text='Сумма')
        selling_table.heading('date', text='Дата')
        selling_table.heading('consumer', text='Покупатель', command=lambda: sort(selling_table, 'consumer', False))
        selling_table['show'] = 'headings'
        selling_table.pack(fill=BOTH, expand=1)
        selling_table.column('code', width=100)
        selling_table.column('title', width=250)
        selling_table.column('price', width=100, anchor='e')
        selling_table.column('count', width=100, anchor='e')
        selling_table.column('total', width=100, anchor='e')
        selling_table.column('date', width=100, anchor='e')
        selling_table.column('consumer', width=100, anchor='e')

        show_selling_table()

        # TODO RIGHT FRAME
        right_frame = Frame(self.root, bg='red', bd=2)
        right_frame.pack(side=LEFT, fill=Y)
        right_frame.pack_propagate(False)
        right_frame.configure(width=800)

        buying_search_frame = LabelFrame(right_frame, bd=1, padx=5, pady=5, relief=RIDGE)
        buying_search_frame.pack(side=TOP, fill=X)
        buying_search_frame.pack_propagate(False)
        buying_search_frame.configure(height=50)

        buying_search_entry = Entry(buying_search_frame, width=25, font=('None', 15))
        buying_search_entry.grid(row=0, column=0)

        def buying_selection():
            slc = str(buying_radio.get())
            buying_search_label.config(text=slc)

        buying_radio = IntVar()

        buying_name_btn = Radiobutton(buying_search_frame, text="Товар", variable=buying_radio, value=1,
                                      command=buying_selection,
                                      font=('None', 12))
        buying_name_btn.grid(row=0, column=1)

        buying_code_btn = Radiobutton(buying_search_frame, text="Артикул", variable=buying_radio, value=2,
                                      command=buying_selection,
                                      font=('None', 12))
        buying_code_btn.grid(row=0, column=2)

        buying_search_label = Label()

        buying_search_btn = Button(buying_search_frame, text='Поиск', width=8, command=search_buying_table,
                                   font=('None', 13), bd=3, fg='black')
        buying_search_btn.grid(row=0, column=3)
        buying_table_rst_btn = Button(buying_search_frame, text='Обновить', width=8, command=show_buying_table,
                                      font=('None', 13), bd=3, fg='black')
        buying_table_rst_btn.grid(row=0, column=4)

        for widget in buying_search_frame.winfo_children():
            widget.grid_configure(padx=5, pady=5)
        buying_name_btn.invoke()

        # TODO BUYING TABLE FRAME
        buying_table_frame = Frame(right_frame, relief=RIDGE, bd=1, padx=5, pady=5)
        buying_table_frame.pack(side=TOP, fill=X)
        buying_table_frame.pack_propagate(False)
        buying_table_frame.configure(width=800, height=800)

        buying_table_sc_x = Scrollbar(buying_table_frame, orient=HORIZONTAL)
        buying_table_sc_x.pack(side=BOTTOM, fill=X)
        buying_table_sc_y = Scrollbar(buying_table_frame, orient=VERTICAL)
        buying_table_sc_y.pack(side=RIGHT, fill=Y)
        buying_table = ttk.Treeview(buying_table_frame,
                                    column=('code', 'title', 'price', 'count', 'total', 'date', 'supplier'),
                                    xscrollcommand=buying_table_sc_x.set,
                                    yscrollcommand=buying_table_sc_y.set)
        buying_table_sc_x.config(command=buying_table.xview)
        buying_table_sc_y.config(command=buying_table.yview)
        buying_table.heading('code', text='Артикул')
        buying_table.heading('title', text='Товар', command=lambda: sort(buying_table, 'title', False))
        buying_table.heading('price', text='Цена')
        buying_table.heading('count', text='К-во',
                             command=lambda: sort(buying_table, 'count', False, key=float))
        buying_table.heading('total', text='Сумма')
        buying_table.heading('date', text='Дата')
        buying_table.heading('supplier', text='Поставшик', command=lambda: sort(buying_table, 'supplier', False))
        buying_table['show'] = 'headings'
        buying_table.pack(fill=BOTH, expand=1)
        buying_table.column('code', width=100)
        buying_table.column('title', width=250)
        buying_table.column('price', width=100, anchor='e')
        buying_table.column('count', width=100, anchor='e')
        buying_table.column('total', width=100, anchor='e')
        buying_table.column('date', width=100, anchor='e')
        buying_table.column('supplier', width=100, anchor='e')

        show_buying_table()


class MainApp:
    def __init__(self, root):
        def selling_page():
            sl = SellingPage(container)
            sl.pack()
            root.title('Продажа')
            sel_btn.configure(bg='PaleGreen4')
            stc_btn.configure(bg='tan2')
            ord_btn.configure(bg='tan2')
            prn_btn.configure(bg='tan2')

        def stock_page():
            st = StockPage(container)
            st.pack()
            root.title('Склад')
            stc_btn.configure(bg='PaleGreen4')
            sel_btn.configure(bg='tan2')
            ord_btn.configure(bg='tan2')
            prn_btn.configure(bg='tan2')

        def orders_page():
            ords = OrdersPage(container)
            ords.pack()
            root.title('История Покупки-Продажи')
            ord_btn.configure(bg='PaleGreen4')
            stc_btn.configure(bg='tan2')
            sel_btn.configure(bg='tan2')
            prn_btn.configure(bg='tan2')

        def print_page():
            pr = PrintPage(container)
            pr.pack()
            root.title('Распечать')
            prn_btn.configure(bg='PaleGreen4')
            ord_btn.configure(bg='tan2')
            stc_btn.configure(bg='tan2')
            sel_btn.configure(bg='tan2')

        def delete_pages():
            for frame in container.winfo_children():
                frame.destroy()

        def indicate(page):
            delete_pages()
            page()

        self.root = root
        root.geometry('800x600')
        root.state('zoomed')
        root.iconbitmap(resource_path('assets/icon.ico'))

        button_frame = Frame(self.root, bd=3, relief=RIDGE)
        button_frame.pack(side="top", fill="x", expand=False, padx=1, pady=1)

        container = Frame(self.root, bd=3, relief=RIDGE)
        container.pack(side="left", fill="both", expand=True)

        sel_btn = Button(button_frame, text="Продажа", command=lambda: indicate(selling_page), width=25,
                         font=('None', 13, 'bold'), relief='raised', bg='tan2')

        stc_btn = Button(button_frame, text="Склад", command=lambda: indicate(stock_page), width=25,
                         font=('None', 13, 'bold'), relief='raised', bg='tan2')
        prn_btn = Button(button_frame, text="Распечатать Заказа", command=lambda: indicate(print_page), width=25,
                         font=('None', 13, 'bold'), relief='raised', bg='tan2')
        ord_btn = Button(button_frame, text="История Покупки-Продажи", command=lambda: indicate(orders_page), width=25,
                         font=('None', 13, 'bold'), relief='raised', bg='tan2')

        sel_btn.pack(side="left", padx=5, pady=3)
        stc_btn.pack(side="left", padx=5, pady=3)
        prn_btn.pack(side="left", padx=5, pady=3)
        ord_btn.pack(side="left", padx=5, pady=3)

        selling_page()


if __name__ == '__main__':
    root = Tk()
    obj = MainApp(root)
    root.mainloop()
