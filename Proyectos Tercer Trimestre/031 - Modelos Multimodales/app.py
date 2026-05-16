import threading
import tkinter as tk
from tkinter import ttk

import cv2
from PIL import Image, ImageTk

from camara import Camara
from vision_ai import analizar_imagen


PREGUNTA_IA = "Describe brevemente qué aparece en esta imagen. Responde en español."


class AplicacionVisual:
    def __init__(self, ventana):
        self.ventana = ventana
        self.ventana.title("Asistente Visual Multimodal")
        self.ventana.geometry("1000x700")

        self.camara = Camara(0)
        self.frame_actual = None
        self.analizando = False

        self.crear_interfaz()
        self.iniciar_camara()
        self.actualizar_video()

    def crear_interfaz(self):
        self.titulo = ttk.Label(
            self.ventana,
            text="Asistente Visual Multimodal",
            font=("Arial", 22, "bold")
        )
        self.titulo.pack(pady=10)

        self.video = ttk.Label(self.ventana)
        self.video.pack(pady=10)

        self.boton = ttk.Button(
            self.ventana,
            text="Analizar imagen actual",
            command=self.lanzar_analisis
        )
        self.boton.pack(pady=10)

        self.resultado = tk.Text(
            self.ventana,
            height=8,
            wrap="word",
            font=("Arial", 12)
        )
        self.resultado.pack(fill="x", padx=20, pady=10)
        self.resultado.insert("1.0", "Pulsa el botón para analizar la imagen de la cámara.")
        self.resultado.config(state="disabled")

        self.estado = ttk.Label(
            self.ventana,
            text="Estado: cámara iniciada",
            font=("Arial", 10)
        )
        self.estado.pack(pady=5)

    def iniciar_camara(self):
        try:
            self.camara.iniciar()
        except Exception as error:
            self.estado.config(text=f"Error: {error}")

    def actualizar_video(self):
        frame = self.camara.leer_frame()

        if frame is not None:
            self.frame_actual = frame.copy()

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            imagen = Image.fromarray(frame_rgb)
            imagen = imagen.resize((800, 450))

            foto = ImageTk.PhotoImage(imagen)
            self.video.configure(image=foto)
            self.video.image = foto

        self.ventana.after(30, self.actualizar_video)

    def lanzar_analisis(self):
        if self.analizando:
            return

        if self.frame_actual is None:
            self.mostrar_resultado("No hay imagen disponible para analizar.")
            return

        self.analizando = True
        self.estado.config(text="Estado: analizando imagen...")
        self.boton.config(state="disabled")

        frame_para_analizar = self.frame_actual.copy()

        hilo = threading.Thread(
            target=self.procesar_analisis,
            args=(frame_para_analizar,),
            daemon=True
        )
        hilo.start()

    def procesar_analisis(self, frame):
        respuesta = analizar_imagen(frame, PREGUNTA_IA)

        self.ventana.after(
            0,
            lambda: self.finalizar_analisis(respuesta)
        )

    def finalizar_analisis(self, texto):
        self.mostrar_resultado(texto)
        self.estado.config(text="Estado: análisis completado")
        self.boton.config(state="normal")
        self.analizando = False

    def mostrar_resultado(self, texto):
        self.resultado.config(state="normal")
        self.resultado.delete("1.0", "end")
        self.resultado.insert("1.0", texto)
        self.resultado.config(state="disabled")

    def cerrar(self):
        self.camara.cerrar()
        self.ventana.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = AplicacionVisual(root)
    root.protocol("WM_DELETE_WINDOW", app.cerrar)
    root.mainloop()
