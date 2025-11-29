import network
import socket
import ujson
import machine
import time

# --- Logging to local file on the Pico ----------------
LOG_FILE = 'pico_log.txt'

def _now_str():
    try:
        t = time.localtime()
        return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(t[0], t[1], t[2], t[3], t[4], t[5])
    except Exception:
        return str(time.time())

def log(msg):
    """Write a timestamped message to LOG_FILE (no serial print to avoid interference)."""
    s = "{} - {}".format(_now_str(), msg)
    # append to file only
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(s + '\n')
    except Exception:
        pass


# --- Configuration (edit before use) -----------------
SSID = 'Ozymandias_2'
PASSWORD = 'bruno1972'
# Set this to your Mac's IP address where `server.py` will run
SERVER_IP = '10.0.0.161'
SERVER_PORT = 5005

# If you have a known thermostat/reference Fahrenheit temperature,
# set it here for automatic calibration. Otherwise set to None and
# use `manual_offset_f`.
calibration_target_f = 80.0  # set to your thermostat reading or None
manual_offset_f = 0.0

# ADC for onboard temperature sensor
adc = machine.ADC(4)  # onboard temperature sensor (ADC4)

def read_temp_c():
    raw = adc.read_u16()                     # 0..65535
    voltage = raw * 3.3 / 65535              # convert to volts
    temp_c = 27.0 - (voltage - 0.706) / 0.001721
    return temp_c

def calibrate_offset(target_f, samples=20, delay=0.05):
    if target_f is None:
        return manual_offset_f
    s = 0.0
    for _ in range(samples):
        s += read_temp_c() * 9.0 / 5.0 + 32.0
        time.sleep(delay)
    measured_avg = s / samples
    return target_f - measured_avg

def connect_wifi(ssid, password, timeout=15):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        log('Attempting Wi-Fi connect to {}'.format(ssid))
        wlan.connect(ssid, password)
        t = 0
        while not wlan.isconnected() and t < timeout:
            time.sleep(1)
            t += 1
    return wlan


# --- Startup: connect and calibrate ----------------
log('Starting Pico client')
log('Connecting to Wi-Fi...')
wlan = connect_wifi(SSID, PASSWORD)
if wlan.isconnected():
    ip = wlan.ifconfig()[0]
    log('Connected, IP: {}'.format(ip))
else:
    log('WARNING: Wi-Fi not connected')

calibration_offset_f = calibrate_offset(calibration_target_f)
log('Calibration offset: {:.2f}F'.format(calibration_offset_f))

# --- TCP client setup and main loop ------------------
# We'll open a TCP connection to the server and send newline-delimited JSON.
def make_tcp_socket():
    s = socket.socket()
    s.settimeout(5)
    return s

sock = None
last_connect = 0

while True:
    c_meas = read_temp_c()
    f_meas = c_meas * 9.0 / 5.0 + 32.0

    # Apply Fahrenheit offset and convert back to C
    f_adj = f_meas + calibration_offset_f
    c_adj = (f_adj - 32.0) * 5.0 / 9.0

    # Log measured values (helps diagnose when Pico is headless)
    log('Measured {:.2f}C {:.2f}F'.format(c_adj, f_adj))

    # Build JSON payload
    payload = {
        'celsius': round(c_adj, 2),
        'fahrenheit': round(f_adj, 2)
    }

    # Ensure we have a connected socket
    if sock is None:
        try:
            sock = make_tcp_socket()
            log('Attempting TCP connect to {}:{}'.format(SERVER_IP, SERVER_PORT))
            sock.connect((SERVER_IP, SERVER_PORT))
            sock.settimeout(None)  # use blocking after connect
            log('TCP: connected to {}:{}'.format(SERVER_IP, SERVER_PORT))
        except Exception as e:
            log('TCP connect error: {}'.format(e))
            try:
                sock.close()
            except Exception:
                pass
            sock = None

    # Send payload over TCP (newline-delimited JSON)
    if sock is not None:
        try:
            msg = ujson.dumps(payload) + '\n'
            sock.send(msg.encode('utf-8'))

            # Wait briefly for an ACK from server (non-blocking longer than timeout)
            try:
                sock.settimeout(2.0)
                data = b''
                line = None
                while True:
                    chunk = sock.recv(64)
                    if not chunk:
                        break
                    data += chunk
                    if b'\n' in data:
                        line, _rest = data.split(b'\n', 1)
                        break
                if line:
                    try:
                        ack = ujson.loads(line.decode('utf-8'))
                        log('ACK from server: {}'.format(ack))
                    except Exception:
                        log('ACK raw: {}'.format(line.decode('utf-8', errors='replace')))
            except Exception as e:
                # timeout or read error - not fatal
                log('No ACK (timeout/error): {}'.format(e))
            finally:
                sock.settimeout(None)
        except Exception as e:
            log('TCP send error: {}'.format(e))
            try:
                sock.close()
            except Exception:
                pass
            sock = None

    time.sleep(1)