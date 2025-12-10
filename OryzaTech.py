# ble_streamlit.py
import streamlit as st
import asyncio
from bleak import BleakClient, BleakScanner 
import json

# ---------------- BLE UUIDs ----------------
SERVICE_UUID = "19b10000-e8f2-537e-4f6c-d104768a1214"
CHARACTERISTIC_UUID = "19b10001-e8f2-537e-4f6c-d104768a1214"

# ---------------- Streamlit Setup ----------------
st.set_page_config(page_title="OryzaTech BLE Dashboard", layout="wide")
st.title("OryzaTech BLE Detection Dashboard")

# ---------------- Session State ----------------
if "devices" not in st.session_state:
    st.session_state.devices = []
if "last_detection" not in st.session_state:
    st.session_state.last_detection = {}
if "connected" not in st.session_state:
    st.session_state.connected = False
if "client" not in st.session_state:
    st.session_state.client = None

# ---------------- Scan BLE Devices ----------------
async def scan_ble():
    devices = await BleakScanner.discover()
    return devices

# ---------------- BLE Notification Callback ----------------
def notification_callback(sender, data):
    try:
        text = data.decode("utf-8")
        detection_json = json.loads(text)
        st.session_state.last_detection = detection_json
    except Exception as e:
        st.error(f"Failed to parse data: {e}")

# ---------------- Connect to Arduino ----------------
async def connect_and_listen(address):
    client = BleakClient(address)
    try:
        await client.connect()
        st.session_state.connected = True
        st.session_state.client = client

        await client.start_notify(CHARACTERISTIC_UUID, notification_callback)

        while client.is_connected:
            await asyncio.sleep(1)

    except Exception as e:
        st.error(f"Connection failed: {e}")
        st.session_state.connected = False
    finally:
        if client.is_connected:
            await client.disconnect()
        st.session_state.connected = False

# ---------------- UI: Scan & Connect ----------------
col1, col2 = st.columns([1, 1])
with col1:
    if st.button("Scan for Devices"):
        devices = asyncio.run(scan_ble())
        st.session_state.devices = devices
        st.success(f"Found {len(devices)} devices!")

with col2:
    device_options = {d.name or d.address: d.address for d in st.session_state.devices}
    selected_device = st.selectbox("Select Device", options=list(device_options.keys()))
    if st.button("Connect"):
        if selected_device:
            address = device_options[selected_device]
            st.info(f"Connecting to {selected_device}...")
            asyncio.run(connect_and_listen(address))

# ---------------- Display Detection Data ----------------
st.subheader("Live Detection Results")

if st.session_state.last_detection:
    detection = st.session_state.last_detection
    st.metric("Total Detections", detection.get("count", 0))

    detections_list = detection.get("detections", [])
    if detections_list:
        st.table(detections_list)
    else:
        st.info("No detections yet.")
else:
    st.info("No data received. Connect to a device and wait for detections.")
