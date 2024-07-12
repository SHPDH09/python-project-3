import tkinter as tk
from tkinter import Scrollbar, Text, Entry, Button, Label
from threading import Thread
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from socketio import Client

# Initialize Flask app and SocketIO
app = Flask(__name__)
app.config['SECRET_KEY'] = '92063bc773b277535cf8e466a8e6d15812b1f5001b216c10c75d915e3bd79e1a'
socketio = SocketIO(app, cors_allowed_origins="*")  # Allow CORS for development

# Initialize SocketIO client for tkinter GUI
sio = Client()

class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Chat Application')

        # Frame to hold sender and receiver sections
        self.frame = tk.Frame(self.root)
        self.frame.pack(fill=tk.BOTH, expand=True)

        # Sender section
        self.sender_frame = tk.Frame(self.frame)
        self.sender_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.sender_msg_listbox = Text(self.sender_frame, width=50, height=10, wrap=tk.WORD)
        self.sender_msg_listbox.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.sender_scrollbar = Scrollbar(self.sender_frame, command=self.sender_msg_listbox.yview)
        self.sender_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.sender_msg_listbox.config(yscrollcommand=self.sender_scrollbar.set)
        self.sender_msg_listbox.tag_configure('sent', justify='left', foreground='blue')
        self.sender_msg_listbox.tag_configure('received', justify='right', foreground='green')

        self.sender_entry_frame = tk.Frame(self.sender_frame)
        self.sender_entry_frame.pack(side=tk.TOP, fill=tk.X, pady=10)

        self.sender_entry_message = Entry(self.sender_entry_frame, width=40)
        self.sender_entry_message.pack(side=tk.LEFT, padx=5)

        self.sender_send_button = Button(self.sender_entry_frame, text='Send', command=self.send_sender_message)
        self.sender_send_button.pack(side=tk.LEFT, padx=5)

        # Receiver section
        self.receiver_frame = tk.Frame(self.frame)
        self.receiver_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.receiver_msg_listbox = Text(self.receiver_frame, width=50, height=10, wrap=tk.WORD)
        self.receiver_msg_listbox.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.receiver_scrollbar = Scrollbar(self.receiver_frame, command=self.receiver_msg_listbox.yview)
        self.receiver_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.receiver_msg_listbox.config(yscrollcommand=self.receiver_scrollbar.set)
        self.receiver_msg_listbox.tag_configure('received', justify='right', foreground='green')
        self.receiver_msg_listbox.tag_configure('sent', justify='left', foreground='blue')

        self.receiver_entry_frame = tk.Frame(self.receiver_frame)
        self.receiver_entry_frame.pack(side=tk.TOP, fill=tk.X, pady=10)

        self.receiver_entry_message = Entry(self.receiver_entry_frame, width=40)
        self.receiver_entry_message.pack(side=tk.LEFT, padx=5)

        self.receiver_send_button = Button(self.receiver_entry_frame, text='Send', command=self.send_receiver_message)
        self.receiver_send_button.pack(side=tk.LEFT, padx=5)

    def send_sender_message(self):
        message_text = self.sender_entry_message.get()
        if sio.connected:
            sio.emit('message', {'message': message_text, 'sender': 'sender'})
            self.sender_entry_message.delete(0, tk.END)
            self.insert_message(f" {message_text}", 'sent', self.sender_msg_listbox)
        else:
            print('SocketIO client is not connected.')

    def send_receiver_message(self):
        message_text = self.receiver_entry_message.get()
        if sio.connected:
            sio.emit('message', {'message': message_text, 'sender': 'receiver'})
            self.receiver_entry_message.delete(0, tk.END)
            self.insert_message(f" {message_text}", 'sent', self.receiver_msg_listbox)
        else:
            print('SocketIO client is not connected.')

    def insert_message(self, message, tag, listbox):
        self.root.after(0, lambda: listbox.insert(tk.END, message + '\n', tag))

def setup_gui():
    root = tk.Tk()
    global chat_app
    chat_app = ChatApp(root)
    root.mainloop()

# Connect to the Flask-SocketIO server
@sio.event
def connect():
    print('Connected to server')
    sio.emit('join', {'username': 'User'})  # Emit a join event upon connection

# Handle incoming messages
@sio.on('message')
def message(data):
    message_text = data['message']
    sender = data['sender']
    
    if chat_app:
        if sender == 'sender':
            chat_app.insert_message(f" {message_text}", 'received', chat_app.receiver_msg_listbox)
        elif sender == 'receiver':
            chat_app.insert_message(f" {message_text}", 'received', chat_app.sender_msg_listbox)

# Flask routes and socket handling
@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('message')
def handle_message(data):
    message_text = data['message']
    sender = data['sender']
    print(f'Received message from {sender}: {message_text}')
    emit('message', data, broadcast=True)

# Global variable for chat app instance
chat_app = None

# Function to start the SocketIO client
def start_client():
    sio.connect('http://localhost:5000')

# Start Flask-SocketIO server and run GUI in separate threads
if __name__ == '__main__':
    # Flask-SocketIO server in a separate thread
    flask_thread = Thread(target=socketio.run, args=(app,), kwargs={'host': 'localhost', 'port': 5000})
    flask_thread.start()

    # SocketIO client connection in another thread
    client_thread = Thread(target=start_client)
    client_thread.start()

    # tkinter GUI in another separate thread
    gui_thread = Thread(target=setup_gui)
    gui_thread.start()

    flask_thread.join()
    client_thread.join()
    gui_thread.join()
