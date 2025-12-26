from kivy.app import App
from kivy.uix.button import Button
from Merry_Xmas import show_menu  # importiere die Funktion

class MyApp(App):
    def build(self):
        # Button klickt → Funktion ausführen
        show_menu()  # Funktion aufrufen, wenn die App gebaut wird
        

if __name__ == "__main__":
    MyApp().run()
