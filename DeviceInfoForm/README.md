# Device Information Form

A simple Windows Forms application for entering device information.

## Features

The application provides input fields for:
- **Model no. (Model)** - Device model number
- **IMEI (DeviceId)** - Device IMEI number  
- **CSC (CustomerCode)** - Customer Service Code
- **OTA source (FirmwareVersion)** - Over-the-Air firmware source

## How to Use

1. **For Windows Users:**
   - Navigate to `bin/Release/net8.0-windows/`
   - Double-click `DeviceInfoForm.exe` to run the application
   - Or run from command line: `dotnet DeviceInfoForm.dll`

2. **Application Usage:**
   - Fill in the input fields with your device information
   - Click **Submit** to display the entered information
   - Click **Clear** to clear all input fields

## Requirements

- .NET 8.0 Runtime (Windows)
- Windows operating system (for Windows Forms)

## Building from Source

To rebuild the application:
```bash
cd DeviceInfoForm
dotnet build --configuration Release
```

The executable will be generated in `bin/Release/net8.0-windows/`