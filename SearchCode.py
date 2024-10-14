import os
import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from threading import Thread
import subprocess

kivy.require('2.0.0')

class FileAnalyzerApp(App):
    def build(self):
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Campo de entrada para la línea a buscar
        self.search_input = TextInput(hint_text='Ingrese la línea a buscar', size_hint=(1, 0.2), multiline=True)
        self.layout.add_widget(self.search_input)

        # Botón para comenzar el análisis
        self.start_button = Button(text='Empezar Análisis', size_hint=(1, 0.1), background_color=(0.1, 0.6, 0.8, 1))
        self.start_button.bind(on_press=self.start_analysis_thread)
        self.layout.add_widget(self.start_button)

        # Barra de progreso
        self.progress_bar = ProgressBar(max=100, size_hint=(1, 0.1))
        self.layout.add_widget(self.progress_bar)

        # Etiqueta para mostrar el progreso del análisis
        self.progress_label = Label(text='Progreso: 0 archivos analizados.', size_hint=(1, 0.1))
        self.layout.add_widget(self.progress_label)

        # Contenedor con scroll para mostrar los resultados
        self.scroll_view = ScrollView(size_hint=(1, 0.5))
        self.result_container = GridLayout(cols=1, size_hint_y=None, padding=10, spacing=10)
        self.result_container.bind(minimum_height=self.result_container.setter('height'))  # Ajustar la altura dinámica

        self.scroll_view.add_widget(self.result_container)
        self.layout.add_widget(self.scroll_view)

        # Verificar acceso root
        if self.check_root():
            self.update_result_label('Acceso root otorgado. Puedes analizar todo el sistema.')
        else:
            self.update_result_label('No se tiene acceso root. Analizará solo el directorio actual.')

        return self.layout

    def check_root(self):
        try:
            output = subprocess.check_output(['su', '-c', 'id'], stderr=subprocess.STDOUT)
            return True  # Si el comando se ejecuta sin excepciones, hay acceso root
        except subprocess.CalledProcessError:
            return False  # No se pudo acceder a root

    def start_analysis_thread(self, instance):
        # Iniciar un hilo separado para evitar bloquear la interfaz de usuario
        search_line = self.search_input.text
        if not search_line:
            self.update_result_label('Por favor, ingrese una línea a buscar.')
            return
        
        self.update_result_label('Analizando archivos...')
        self.file_count = 0  # Contador de archivos analizados
        self.progress_bar.value = 0  # Reiniciar barra de progreso
        Thread(target=self.analyze_files, args=(search_line,)).start()

    def analyze_files(self, search_line):
        directory = '/' if self.check_root() else '.'  # Cambia a '/' si hay acceso root, de lo contrario, usa el directorio actual
        found_files = []
        excluded_files = []  # Para almacenar archivos excluidos y errores

        # Contar el total de archivos
        total_files = sum(len(files) for _, _, files in os.walk(directory))

        # Recorrer archivos y carpetas en el directorio
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            if search_line in line:
                                found_files.append(file_path)
                                break  # Deja de leer este archivo si ya se encontró la línea
                except (IOError, UnicodeDecodeError) as e:
                    excluded_files.append(f"{file_path} - Error: {str(e)}")  # Almacenar archivo y error

                # Incrementar contador y actualizar la barra y etiqueta de progreso
                self.file_count += 1
                progress = (self.file_count / total_files) * 100
                Clock.schedule_once(lambda dt: self.update_progress(self.file_count, total_files, progress))

        # Actualizar la interfaz desde el hilo principal
        Clock.schedule_once(lambda dt: self.update_result(found_files, excluded_files))

    def update_progress(self, count, total, progress):
        self.progress_bar.value = progress
        self.progress_label.text = f'Progreso: {count} de {total} archivos analizados.'

    def update_result(self, found_files, excluded_files):
        # Limpiar el contenedor de resultados
        self.result_container.clear_widgets()

        # Mostrar archivos encontrados
        if found_files:
            for file in found_files:
                label = Label(text=file, size_hint_y=None, height=30, text_size=(self.result_container.width - 20, None), halign='left', valign='middle')
                self.result_container.add_widget(label)
        else:
            no_result_label = Label(text='No se encontraron archivos que contengan la línea buscada.', size_hint_y=None, height=30, halign='left')
            self.result_container.add_widget(no_result_label)

        # Mostrar archivos excluidos
        if excluded_files:
            excluded_label = Label(text='\nArchivos excluidos (errores):', size_hint_y=None, height=30, halign='left', bold=True)
            self.result_container.add_widget(excluded_label)
            for file in excluded_files:
                label = Label(text=file, size_hint_y=None, height=30, text_size=(self.result_container.width - 20, None), halign='left', valign='middle')
                self.result_container.add_widget(label)

    def update_result_label(self, text):
        # Limpiar contenedor de resultados y agregar un nuevo mensaje
        self.result_container.clear_widgets()
        label = Label(text=text, size_hint_y=None, height=30, halign='left')
        self.result_container.add_widget(label)

if __name__ == '__main__':
    FileAnalyzerApp().run()
