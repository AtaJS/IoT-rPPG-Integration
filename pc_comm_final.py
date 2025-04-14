import socket
import csv
import time
import matplotlib.pyplot as plt
from datetime import datetime

# Function to send start signal to Raspberry Pi
def send_start_signal():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(('xxx.xxx.xxx.xxx', xxxxx))  # Replace with Raspberry Pi's IP address
        print("Connected to Raspberry Pi, sending START signal")
        s.sendall(b'START')
        print("START signal sent")
        s.close()
    except socket.error as e:
        print(f"Failed to connect to Raspberry Pi: {e}")
        return False
    return True

# Function to receive heart rate data from Raspberry Pi
def receive_heart_rate_data():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow reuse of address
    
    try:
        s.bind(('xxx.xxx.xxx.xxx', xxxx))  # Bind to all interfaces on port xxxxx(write your PC's IP and port number)
        s.listen(1)
        s.settimeout(60)  # 60 second timeout to wait for initial connection
        print("Waiting for heart rate data...")
        conn, addr = s.accept()
        print("Connection established with", addr)
        conn.settimeout(30)  # 30 second timeout for receiving data

        heart_rate_data = []
        start_time = time.time()
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            while time.time() - start_time < 35:  # Allow slightly longer than 30s for data collection
                try:
                    data = conn.recv(1024).decode('utf-8').strip()
                    if data:
                        elapsed_time = time.time() - start_time
                        print(f"Time: {elapsed_time:.2f}s, Heart Rate: {data}")
                        
                        # Extract numeric value from the data (remove " bpm")
                        value = data.split()[0]
                        heart_rate_data.append((elapsed_time, value))
                except socket.timeout:
                    # This allows us to break out of recv if no data is available
                    continue
                except Exception as e:
                    print(f"Error receiving data: {e}")
                    break
        finally:
            conn.close()
            s.close()
            
        return heart_rate_data, current_time
        
    except socket.error as e:
        print(f"Socket error: {e}")
        return [], datetime.now().strftime("%Y%m%d_%H%M%S")

# Function to save heart rate data to CSV
def save_to_csv(data, timestamp):
    filename = f'heart_rate_data_{timestamp}.csv'
    with open(filename, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['Time (s)', 'Heart Rate (bpm)'])
        for row in data:
            csvwriter.writerow([f"{row[0]:.2f}", row[1]])
    
    print(f"Data saved to {filename}")
    return filename

# Function to plot heart rate data
def plot_heart_rate(data, timestamp):
    if not data:
        print("No data to plot")
        return
        
    # Convert string heart rates to float
    times = [row[0] for row in data]
    try:
        heart_rates = [float(row[1]) for row in data]
    except ValueError as e:
        print(f"Error converting heart rate values: {e}")
        return
        
    plt.figure(figsize=(10, 6))
    plt.plot(times, heart_rates, 'b-o', linewidth=2, markersize=6)
    plt.xlabel('Time (s)')
    plt.ylabel('Heart Rate (bpm)')
    plt.title('Heart Rate Over Time')
    plt.grid(True)
    
    # Add statistical information
    if heart_rates:
        avg_hr = sum(heart_rates) / len(heart_rates)
        min_hr = min(heart_rates)
        max_hr = max(heart_rates)
        plt.axhline(y=avg_hr, color='r', linestyle='--', label=f'Avg: {avg_hr:.1f} bpm')
        plt.legend()
        
        # Add text annotation
        plt.annotate(f'Min: {min_hr:.1f} bpm\nMax: {max_hr:.1f} bpm\nAvg: {avg_hr:.1f} bpm',
                    xy=(0.02, 0.95), xycoords='axes fraction',
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8))
    
    # Save the plot
    plt_filename = f'heart_rate_plot_{timestamp}.png'
    plt.savefig(plt_filename)
    print(f"Plot saved as {plt_filename}")
    
    # Show the plot
    plt.tight_layout()
    plt.show()

# Main function
def main():
    print("=== Heart Rate Monitoring System ===")
    print("Sending start signal to Raspberry Pi...")
    
    if send_start_signal():
        print("Waiting for heart rate measurements...")
        heart_rate_data, timestamp = receive_heart_rate_data()
        
        if heart_rate_data:
            print(f"Received {len(heart_rate_data)} heart rate measurements")
            csv_file = save_to_csv(heart_rate_data, timestamp)
            plot_heart_rate(heart_rate_data, timestamp)
            print("\nProcess completed successfully!")
        else:
            print("No heart rate data received.")
    else:
        print("Failed to start the process.")

if __name__ == '__main__':
    main()
