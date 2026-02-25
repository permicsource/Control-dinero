#Conecta interfaz, base de datos y funciones de análisis.
from datetime import datetime
from models import Gasto
from database import crear_tabla, insertar_gasto
from analysis import resumen_por_categoria, resumen_mensual
from analysis import exportar_a_excel

def menu():
    print("\n=== CONTROL DE FINANZAS ===")
    print("1. Agregar gasto")
    print("2. Ver resumen por categoría")
    print("3. Ver resumen mensual")
    print("4. Exportar a Excel")
    print("5. Salir")


def agregar_gasto():
    fecha_str = input("Fecha (YYYY-MM-DD) [Enter para hoy]: ")

    if fecha_str == "":
        fecha = datetime.today().date()
    else:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()

    categoria = input("Categoría: ").upper()  #Convierte a mayúsculas para estandarizar.
    descripcion = input("Descripción: ")
    monto = float(input("Monto: "))

    gasto = Gasto(fecha, categoria, descripcion, monto)
    insertar_gasto(gasto)

    print(" Gasto guardado correctamente")


def main():
    crear_tabla()

    while True:
        menu()
        opcion = input("Seleccione una opción: ")

        if opcion == "1":
            agregar_gasto()

        elif opcion == "2":
            print(resumen_por_categoria())

        elif opcion == "3":
            print(resumen_mensual())

        elif opcion == "4":
            exportar_a_excel()    

        elif opcion == "5":
            print("Saliendo...")
            break

        else:
            print("Opción inválida")

#Solo ejecuta la función main() si este archivo se abre directamente.
if __name__ == "__main__":
    main()