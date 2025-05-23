# network.py
import socket
import json

class NetworkHandler:
    def __init__(self, local_ip="127.0.0.1", local_port=5005, rpi_ip="127.0.0.1", rpi_port=5006):
        self.rpi_ip = rpi_ip
        self.rpi_port = rpi_port
        self.local_ip = local_ip
        self.local_port = local_port
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind((self.local_ip, self.local_port))
        self.udp_socket.settimeout(0.1)
        self.image_buffer = {} 

    def send_command(self, thruster_speeds):
        """Відправлення команди з швидкостями двигунів."""
        command = {"thruster_speeds": thruster_speeds}
        print(f"Sending command to {self.rpi_ip}:{self.rpi_port}: {command}")
        try:
            message = json.dumps(command)
            if len(message) > 1024:
                print(f"Warning: Command size {len(message)} exceeds 1024 bytes")
            self.udp_socket.sendto(message.encode(), (self.rpi_ip, self.rpi_port))
        except Exception as e:
            print(f"Send command error: {e}")

    def receive_data(self):
        """Отримання даних: sensor_data або image_chunk."""
        try:
            data, addr = self.udp_socket.recvfrom(16384)
            print(f"Received data size: {len(data)} bytes from {addr}")
            try:
                packet = json.loads(data.decode())
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}, raw data: {data.decode()[:100]}...")
                return {}

            # Обробка image_chunk
            if packet.get("type") == "image_chunk":
                required_fields = ["frame_id", "chunk_index", "total_chunks", "data"]
                if not all(field in packet for field in required_fields):
                    print(f"Error: Missing fields in image_chunk: {packet}")
                    return {}

                frame_id = packet["frame_id"]
                chunk_index = packet["chunk_index"]
                total_chunks = packet["total_chunks"]
                chunk_data = packet["data"]

                print(f"Image chunk: frame_id={frame_id}, chunk={chunk_index+1}/{total_chunks}, size={len(chunk_data)} bytes")

                if frame_id not in self.image_buffer:
                    self.image_buffer[frame_id] = [""] * total_chunks
                    print(f"Started collecting frame {frame_id} with {total_chunks} chunks")
                
                self.image_buffer[frame_id][chunk_index] = chunk_data

                if all(chunk != "" for chunk in self.image_buffer[frame_id]):
                    full_frame = "".join(self.image_buffer[frame_id])
                    print(f"Assembled frame {frame_id} with {len(full_frame)} bytes")
                    del self.image_buffer[frame_id]
                    # Очищення старих фреймів
                    old_frames = [fid for fid in self.image_buffer if fid < frame_id - 10]
                    for fid in old_frames:
                        del self.image_buffer[fid]
                        print(f"Cleared old frame {fid}")
                    return {"type": "camera", "data": full_frame}
                
                return {}

            # Обробка sensor_data
            required_fields = ["timestamp", "imu", "sonar", "thruster_speeds", "frame_id"]
            if not all(field in packet for field in required_fields):
                print(f"Error: Missing fields in sensor_data: {required_fields}, packet: {packet}")
                return {}

            sonar_data = packet.get("sonar", {})
            required_sonar_fields = ["point", "distance", "object_type"]
            if not all(field in sonar_data for field in required_sonar_fields):
                print(f"Error: Missing fields in sonar_data: {required_sonar_fields}, packet: {packet}")
                return {}

            print(f"Sensor data: timestamp={packet['timestamp']}, frame_id={packet['frame_id']}, object_type={sonar_data['object_type']}")
            return {"type": "sensor", "data": packet}

        except socket.timeout:
            raise
        except Exception as e:
            print(f"Receive error: {e}")
            return {}

    def close(self):
        """Закриття сокета."""
        self.udp_socket.close()
