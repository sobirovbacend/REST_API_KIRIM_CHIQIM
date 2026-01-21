


# OOP - obyektga yonaltirilgan dasturlash
# ooyektlarga asoslanib loyiha qilish
# OOP ning 4 ta asosiy ustuni
# OOP 4 ta “ustun”ga tayanadi:
# 1️Encapsulation (Inkapsulyatsiya)
#  2️Inheritance (Meros olish)
#  3️Polymorphism (Polimorfizm)
#  4️Abstraction (Abstraksiya)


# OOP — bu dastur yozish uslubi bo‘lib, dastur real hayotdagi obyektlar kabi quriladi.
# ❓ Nima uchun OOP kerak?
# OOP sizga:
# ·	🔹 Katta loyihalarni tartibli yozish
# ·	🔹 Kod takrorlanishini kamaytirish
# ·	🔹 O‘qilishi va tushunilishi oson kod yozish
# ·	🔹 Kodga oson o‘zgartirish kiritish
# ·	🔹 Django, ORM, REST API kabi texnologiyalarni tushunishni osonlashtiradi


# 1️Encapsulation

# malumot va metodni bita birlikda ishlatish yani malumot obyekt malumot metod bu cllas ichidagi funksiya yani biz incapsuliyatsiyadan
# obyeyt yaratyotgan ham metod ham atributdan foydalanamiz

# misol

# class New:
#     def __init__(self, name, age):
#         self.name = name
#         self.__age = age
#
#
#     def run(self):
#         print("name",self.name,"age",self.__age)
#
#
# p = New('Salohiddin',19)
# p.run()

#
# class User:
#     def login(self):
#         print("User logged in")
#
# class Admin(User):
#     def delete_user(self):
#         print("User deleted")
# admin = Admin()
# admin.login()        # User dan keldi
# admin.delete_user()

def func(*args, **kwargs):
    print(args)
    print(kwargs)

func(1, 2, a=10, b=20)
