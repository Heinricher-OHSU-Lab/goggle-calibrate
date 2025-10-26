# Serial Port Configuration Guide

This configuration is typically done once during initial setup.

## Step 1: Find the Serial Port Path

1. Open **Terminal** by clicking the Terminal icon in the Dock

2. Run this command to list available USB serial devices:
   ```bash
   ls /dev/tty.usb*
   ```

3. You should see output like:
   ```
   /dev/tty.usbserial-0001
   ```

   **Tip**: If multiple devices are listed, try disconnecting and reconnecting the goggles USB cable, then run the command again to see which device appears/disappears.

4. Copy or write down the full path (e.g., `/dev/tty.usbserial-0001`)

## Step 2: Edit the Configuration File

1. In Terminal, open the configuration file:
   ```bash
   open ~/Documents/Calibration/config/experiment_config.json
   ```

2. Find the line that says `"serial_port":` - it will look like:
   ```json
   "serial_port": "/dev/tty.usbserial-DO02ADIS",
   ```

3. Replace the path value with the path you found in Step 1:
   ```json
   "serial_port": "/dev/tty.usbserial-0001",
   ```

   **Important**: Keep the quotation marks and comma exactly as shown.

4. Find the line that says `"baud_rate":` - it will look like:
   ```json
   "baud_rate": 9600,
   ```

5. If the value is not already `115200`, change it to:
   ```json
   "baud_rate": 115200,
   ```

   **Important**: No quotation marks around the number, but keep the comma.

6. Save the file (`Cmd + S`) and close TextEdit

## Step 3: Verify the Configuration

1. Run the calibration program (double-click the "Run Calibration" app icon)

2. If successful, the program should start normally and be able to control the goggles.

3. If you see an error about the serial port, double-check that:
   - The path in `config.json` exactly matches what you found in Step 1
   - The quotation marks and comma are still in place
   - There are no typos in the path

## Troubleshooting

**No devices found when running `ls /dev/tty.usb*`**
- Check that the goggles USB cable is plugged in
- Try a different USB port on your computer
- Check that the goggles are powered on

**Multiple devices listed**
- Unplug the goggles USB cable
- Run `ls /dev/tty.usb*` to see remaining devices
- Plug the goggles back in
- Run `ls /dev/tty.usb*` again - the new device that appears is the correct one

**Program still reports serial port connection error**
- Verify the path in `config.json` is spelled exactly as shown in Terminal
- Make sure you kept the quotation marks around the path
- Make sure the comma after the closing quotation mark is still there
- Try quitting and restarting Terminal, then running the program again