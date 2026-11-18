# CAR Property Finder

A Windows application for finding CAR properties by latitude and longitude, checking their boundaries, and downloading their geographic files.

## Requirements

- Windows 10 or 11
- Python 3.10 or newer. During installation, select **Add Python to PATH**.
- An internet connection
- Google Chrome, if you want to open a property statement

## Setup

1. Extract the project to a writable folder.
2. Double-click `setup.bat` and wait for setup to finish. This installs the required Python packages and Playwright browser files.
3. Double-click `start_gui.bat` to open the application.

You only need to run setup once. Use `start_gui.bat` for future sessions.

## Find a property

1. Choose **English** or **Português (Brasil)** at the top of the window.
2. Enter the **latitude** and **longitude**. For decimal coordinates in Brazil, south and west are negative. For example:

   ```text
   Latitude:  -23.266165
   Longitude: -53.290072
   ```

   Degrees, minutes and seconds are also accepted, for example `8°15'54.921"S`. You can use **Use sample coordinates** to fill in an example.
3. Select **Find property** and wait while the application searches CAR and checks the property boundaries.
4. Select a CAR registration from the results list. Its municipality, area, and boundary status appear below the list.
5. Check the boundary status:
   - **Point inside boundary**: the entered point is inside the downloaded boundary.
   - **Point outside boundary**: the point is outside it. The displayed distance is approximately how far it is from the nearest boundary.
   - **Boundary could not be checked**: the boundary was unavailable or could not be read, so the result is unverified.
6. For the selected property, choose **Download ZIP**, select a save location, and wait for the confirmation. The application checks the ZIP before saving it.
7. Choose **Open statement in Chrome** to open the selected property's statement page in your regular Chrome browser. This opens a web page; it does not automatically save a PDF.

To search again, enter new coordinates and select **Find property**. You can cancel an active search with **Cancel**. The window opens maximized, can be resized, and supports scrolling.

The desktop interface separates coordinate entry, search progress, and property results into distinct panels. On narrow windows, action buttons stack to stay easy to use.

## Understanding the results

The app queries the CAR coordinate service ten times and checks the boundaries of the distinct properties returned. Repeated requests may return different properties, and ten requests **do not guarantee that every property at the location will be found**. If some requests or boundary checks fail, results may be incomplete. Boundary distances are approximate; review the registration and property details before using the result.

## Troubleshooting

- **Setup fails:** Check that Python is installed, available in PATH, and that you have an internet connection. Run `setup.bat` again.
- **No results or incomplete results:** Check the coordinates and connection, then try again. The CAR service may be unavailable or may not return a property for the point.
- **Boundary could not be checked:** Try again later. Do not assume an unverified property contains the point.
- **ZIP download fails:** Check the internet connection and save location. If the error mentions certificate verification, contact your network or system administrator; do not disable certificate verification.
- **Statement does not open:** Make sure Google Chrome is installed.

## Command-line option

`start.bat` runs the separate command-line browser workflow. Its behavior differs from the desktop interface: it opens the CAR site in an automated browser and leaves the user to continue there. Run `start.bat --help` for available options.
