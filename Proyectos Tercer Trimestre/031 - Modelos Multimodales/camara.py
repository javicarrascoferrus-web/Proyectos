import cv2


class Camara:
    def __init__(self, indice=0):
        self.indice = indice
        self.captura = None

    def iniciar(self):
        self.captura = cv2.VideoCapture(self.indice)

        if not self.captura.isOpened():
            raise RuntimeError("No se pudo abrir la cámara.")

    def leer_frame(self):
        if self.captura is None:
            return None

        correcto, frame = self.captura.read()

        if not correcto:
            return None

        return frame

    def cerrar(self):
        if self.captura is not None:
            self.captura.release()
            self.captura = None
