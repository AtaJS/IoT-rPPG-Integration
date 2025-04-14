import socket
import serial
import cv2
import time
import datetime
import numpy as np
from scipy import signal
from scipy.fftpack import fft, fftfreq, fftshift
from sklearn.decomposition import PCA, FastICA
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt

client_ip   = None
client_port = xxxx # write your PC's port number


def receive_signal():
    global client_ip, client_port
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('xxx.xxx.xxx.xxx', xxxxx))  # Bind to IP address and port(write your raspberry pi's IP and port number)
    s.listen(1)
    print("Waiting for connection...")
    while True:
        conn, addr = s.accept()
        client_ip   = addr[0]  # store the IP address
        print("Connection established with", addr)
        data = conn.recv(1024)
        if data == b'START':
            print("Start signal received")
            conn.close()  # Close connection before proceeding
            send_command_to_arduino('START_MEASUREMENT')
            receive_arduino_signal()
            break  # Exit after processing one START command
        conn.close()

def send_command_to_arduino(command):
    ser = serial.Serial('/dev/ttyACM0', 9600, timeout=5)  # Added timeout
    time.sleep(1)  # Allow time for serial connection to establish
    ser.write(command.encode())
    ser.close()

def receive_arduino_signal():
    ser = serial.Serial('/dev/ttyACM0', 9600, timeout=10)  # Added longer timeout
    print("Waiting for Arduino signal...")
    start_time = time.time()
    timeout = 600  # 10 minutes timeout for Arduino response
    
    while time.time() - start_time < timeout:
        if ser.in_waiting > 0:
            data = ser.readline().decode('utf-8').strip()
            print("Received from Arduino:", data)
            if data == 'END_MEASUREMENT':
                print("End signal received from Arduino")
                ser.close()
                run_rppg()
                return
        time.sleep(0.1)  # Short sleep to prevent CPU hogging
    
    print("Timed out waiting for Arduino signal")
    ser.close()



def run_rppg():
    global client_port
    global client_ip
    
    # Establish connection to PC for data streaming
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Add debug information
    print(f"Attempting to connect to PC at {client_ip}: {client_port}") 
    
    # Add retry logic
    max_retries = 5
    retry_count = 0
    connected = False
    
    while retry_count < max_retries and not connected:
        try:
            s.connect((client_ip, client_port))  # Connect to PC port 
            print(f"Successfully connected to PC at {client_ip}:{client_port} for data streaming")
            connected = True
        except socket.error as e:
            retry_count += 1
            print(f"Connection attempt {retry_count} failed: {e}")
            time.sleep(2)  # Wait before retrying
    
    if not connected:
        print(f"Failed to connect to PC after {max_retries} attempts")
        return
    

    
    face_cascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
    firstFrame = None
    time_list = []
    R = []
    G = []
    B = []
    pca = FastICA(n_components=3)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Failed to open webcam")
        s.close()
        return
    
    frame_num = 0
    plt.ion()
    start_time = time.time()
    max_duration = 30  # Run for 30 seconds maximum
    
    while cap.isOpened() and time.time() - start_time < max_duration:
        ret, frame = cap.read()
        if ret:
            frame_num += 1
            if firstFrame is None:
                start = datetime.datetime.now()
                time_list.append(0)
                firstFrame = frame
                old_gray = cv2.cvtColor(firstFrame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(old_gray, 1.3, 5)
                if len(faces) == 0:
                    firstFrame = None
                    continue  # Skip this frame and try again
                else:
                    for (x, y, w, h) in faces:
                        x2 = x + w
                        y2 = y + h
                        cv2.rectangle(firstFrame, (x, y), (x2, y2), (255, 0, 0), 2)
                        VJ_mask = np.zeros_like(firstFrame)
                        VJ_mask = cv2.rectangle(VJ_mask, (x, y), (x2, y2), (255, 0, 0), -1)
                        VJ_mask = cv2.cvtColor(VJ_mask, cv2.COLOR_BGR2GRAY)
                        ROI_color = cv2.bitwise_and(firstFrame, firstFrame, mask=VJ_mask)
                        R_new, G_new, B_new, _ = cv2.mean(ROI_color, mask=VJ_mask)
                        R.append(R_new)
                        G.append(G_new)
                        B.append(B_new)
            else:
                current = datetime.datetime.now() - start
                current = current.total_seconds()
                time_list.append(current)
                frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # Try to detect faces in each frame
                faces = face_cascade.detectMultiScale(frame_gray, 1.3, 5)
                if len(faces) > 0:
                    for (x, y, w, h) in faces:
                        x2 = x + w
                        y2 = y + h
                        VJ_mask = np.zeros_like(frame)
                        VJ_mask = cv2.rectangle(VJ_mask, (x, y), (x2, y2), (255, 0, 0), -1)
                        VJ_mask = cv2.cvtColor(VJ_mask, cv2.COLOR_BGR2GRAY)
                        ROI_color = cv2.bitwise_and(frame, frame, mask=VJ_mask)
                        R_new, G_new, B_new, _ = cv2.mean(ROI_color, mask=VJ_mask)
                else:
                    # If no face detected, use whole image
                    ROI_color = frame
                    R_new, G_new, B_new, _ = cv2.mean(ROI_color)
                
                R.append(R_new)
                G.append(G_new)
                B.append(B_new)
                
                # Process every 30 frames or so for smoother updates
                if len(R) > 90 and frame_num % 10 == 0:  # Start analysis after collecting some data
                    N = min(900, len(R))  # Use up to 900 frames or all available
                    
                    G_std = StandardScaler().fit_transform(np.array(G[-N:]).reshape(-1, 1))
                    G_std = G_std.reshape(1, -1)[0]
                    R_std = StandardScaler().fit_transform(np.array(R[-N:]).reshape(-1, 1))
                    R_std = R_std.reshape(1, -1)[0]
                    B_std = StandardScaler().fit_transform(np.array(B[-N:]).reshape(-1, 1))
                    B_std = B_std.reshape(1, -1)[0]
                    
                    T = 1 / (len(time_list[-N:]) / (time_list[-1] - time_list[-N]))
                    X_f = pca.fit_transform(np.array([R_std, G_std, B_std]).transpose()).transpose()
                    
                    N = len(X_f[0])
                    yf = fft(X_f[1])
                    yf = yf / np.sqrt(N)
                    xf = fftfreq(N, T)
                    xf = fftshift(xf)
                    yplot = fftshift(abs(yf))
                    
                    plt.figure(1)
                    plt.gcf().clear()
                    fft_plot = yplot.copy()  # Create a copy to avoid modifying original
                    fft_plot[xf <= 0.75] = 0  # Filter out low frequencies
                    
                    # Safely find the max value in the BPM range
                    mask = (xf <= 4) & (xf > 0.75)
                    if np.any(mask):
                        try:
                            hr_freq = xf[mask][fft_plot[mask].argmax()]
                            heart_rate = hr_freq * 60
                            data = f"{heart_rate:.1f} bpm"
                            print(data)
                            
                            # Send data to PC
                            try:
                                s.sendall(data.encode('utf-8'))
                            except socket.error as e:
                                print(f"Failed to send data: {e}")
                                break
                                
                            plt.plot(xf[(xf >= 0) & (xf <= 4)], fft_plot[(xf >= 0) & (xf <= 4)])
                            plt.pause(0.0001)
                        except Exception as e:
                            print(f"Error in heart rate calculation: {e}")
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    s.close()
    print("rPPG measurement completed")

if __name__ == "__main__":
    receive_signal()


















