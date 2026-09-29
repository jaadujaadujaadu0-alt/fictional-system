import os
import subprocess
import time
import sys
from playwright.sync_api import sync_playwright

# ==========================================
# DEFAULTS
# ==========================================
DEFAULT_EMAIL = "annieleonh.art9867@gmail.com"
DEFAULT_PHONE = "9261938961"

# ==========================================
# VNC SETUP FUNCTIONS
# ==========================================

def start_vnc_environment():
    """Starts Xvfb, Fluxbox, x11vnc, and noVNC in the background."""
    processes = []
    print("Starting Virtual Display (Xvfb)...")
    try:
        processes.append(subprocess.Popen(
            ["Xvfb", ":1", "-screen", "0", "1024x768x24"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        ))
        time.sleep(1.5)

        os.environ["DISPLAY"] = ":1"

        print("Starting Window Manager (Fluxbox)...")
        processes.append(subprocess.Popen(
            ["fluxbox"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        ))

        print("Starting VNC Server (x11vnc)...")
        processes.append(subprocess.Popen(
            ["x11vnc", "-display", ":1", "-nopw", "-forever", "-shared", "-rfbport", "5900"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        ))

        print("Starting Web VNC Client (noVNC)...")
        processes.append(subprocess.Popen(
            ["websockify", "--web=/usr/share/novnc", "6080", "localhost:5900"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        ))
        
        print("\n" + "="*50)
        print("VNC ENVIRONMENT STARTED SUCCESSFULLY")
        print("="*50)
        print("1. Go to the 'Ports' tab in Codespaces.")
        print("2. Find port 6080 and set its visibility to 'Public'.")
        print("3. Click the globe icon next to port 6080 to open the VNC viewer.")
        print("4. You will see the browser inside the VNC viewer.\n")
        
        return processes

    except FileNotFoundError as e:
        print(f"\n❌ ERROR: Missing required VNC package: {e.filename}")
        print("Please run: sudo apt-get update && sudo apt-get install -y xvfb x11vnc fluxbox websockify novnc")
        sys.exit(1)

def stop_vnc_environment(processes):
    print("\nStopping VNC environment...")
    for p in processes:
        p.terminate()
    print("VNC environment stopped.")

# ==========================================
# MAIN AUTOMATION SCRIPT
# ==========================================

def main():
    print("--- Apple Account Automation ---")
    # Use defaults if user just presses Enter
    email_input = input(f"Enter your email address [default: {DEFAULT_EMAIL}]: ")
    email = email_input if email_input.strip() else DEFAULT_EMAIL
    
    phone_input = input(f"Enter your phone number [default: {DEFAULT_PHONE}]: ")
    phone = phone_input if phone_input.strip() else DEFAULT_PHONE

    vnc_processes = start_vnc_environment()
    time.sleep(2)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()

            print("Navigating to Apple Account page...")
            page.goto("https://account.apple.com/account")
            
            # ==========================================
            # WAIT FOR THE IFRAME TO LOAD
            # ==========================================
            print("Waiting for the form iframe to be visible...")
            try:
                page.wait_for_selector("#aid-create-widget-iFrame", state="visible", timeout=60000)
                print("Iframe is visible. Switching context...")
            except Exception as e:
                print(f"Timeout waiting for iframe to be visible: {e}")
                browser.close()
                return

            frame = page.frame_locator("#aid-create-widget-iFrame")

            print("Waiting for form fields to render inside iframe...")
            try:
                frame.locator('input').first.wait_for(state="visible", timeout=60000)
                print("Form fields loaded successfully!")
            except Exception as e:
                print(f"Timeout waiting for form inside iframe: {e}")
                browser.close()
                return

            # ==========================================
            # FILLING THE FORM (Inside the iframe)
            # ==========================================
            print("Filling in name...")
            frame.locator('input[type="text"]').nth(0).fill("anish")
            frame.locator('input[type="text"]').nth(1).fill("sambar")

            print("Selecting Country/Region...")
            try:
                frame.locator("select").nth(0).select_option(label="Myanmar")
                print("Country selected.")
            except Exception as e:
                print(f"Could not select Country via dropdown: {e}")

            print("Selecting Birthday...")
            try:
                frame.locator('select[data-testid="select-month"]').select_option(label="January")
                frame.locator('select[data-testid="select-day"]').select_option(label="1")
                frame.locator('select[data-testid="select-year"]').select_option(label="2000")
                print("Birthday selected using data-testid and label.")
            except Exception as e:
                print(f"Failed with data-testid, trying generic nth()... Error: {e}")
                try:
                    selects = frame.locator("select")
                    selects.nth(1).select_option(label="January")
                    selects.nth(2).select_option(label="1")
                    selects.nth(3).select_option(label="2000")
                    print("Birthday selected using nth() and label.")
                except Exception as e2:
                    print(f"Failed to select Birthday completely: {e2}")

            print("Filling in credentials...")
            try:
                frame.locator('input[type="email"]').fill(email)
            except:
                frame.locator('input[type="text"]').nth(2).fill(email)
            
            frame.locator('input[type="password"]').nth(0).fill("Aa1+Aa1+")
            frame.locator('input[type="password"]').nth(1).fill("Aa1+Aa1+")

            print("Filling in phone number...")
            try:
                frame.locator("select").last.select_option(label="+95 (Myanmar)")
            except Exception as e:
                print(f"Could not select phone country code: {e}")
            
            frame.locator('input[type="tel"]').fill(phone)

            # ==========================================
            # HYBRID CAPTCHA HANDLING WITH ERROR RETRY
            # ==========================================
            print("\n" + "="*50)
            print(">>> CAPTCHA DETECTED: Entering hybrid mode...")
            print("="*50)
            
            while True:
                try:
                    # Re-locate CAPTCHA input and image each iteration
                    captcha_input = frame.locator('input[placeholder*="characters" i], input[placeholder*="image" i], input[name*="captcha" i], input[id*="captcha" i]').first
                    
                    # Locate the CAPTCHA image
                    try:
                        captcha_img = frame.locator('img[src*="captcha" i], img[src*="image" i], img[alt*="captcha" i]').first
                        if captcha_img.count() == 0:
                            # Fallback: look for an image near the input
                            captcha_img = captcha_input.locator('xpath=..').locator('img').first
                    except:
                        captcha_img = frame.locator('img').first
                    
                    # Take a screenshot of the CAPTCHA image and save it
                    captcha_img.wait_for(state="visible", timeout=10000)
                    captcha_img.screenshot(path="captcha.png")
                    print("\n[✔] CAPTCHA image successfully saved as 'captcha.png'.")
                    print("👉 Please open 'captcha.png' in your Codespace file explorer to view it.")
                    
                except Exception as e:
                    print(f"[!] Could not automatically save the CAPTCHA image: {e}")
                    print("    Please look at the VNC viewer to read the CAPTCHA manually.")

                # Prompt the user
                captcha_text = input("👉 Type the CAPTCHA characters and press Enter (or just press Enter to get a New Code): ")

                if captcha_text.strip() == "":
                    print("Requesting a new CAPTCHA code...")
                    try:
                        new_code_btn = frame.locator('text="New Code"').first
                        new_code_btn.click()
                        print("Clicked 'New Code'. Waiting for the image to refresh...")
                        page.wait_for_timeout(3000)
                    except Exception as e:
                        print(f"Could not click 'New Code' automatically: {e}")
                        print("Please click 'New Code' manually in the VNC viewer, then press Enter here.")
                        input("Press Enter to continue after clicking manually...")
                    continue # Loop back to the start to re-screenshot the new CAPTCHA

                # User typed a CAPTCHA, fill it in
                print("Filling in CAPTCHA and submitting...")
                if captcha_input:
                    captcha_input.fill(captcha_text)
                
                # Click Continue
                frame.get_by_role("button", name="Continue").click()
                
                # Wait a moment to see if an error occurs or if the page transitions
                page.wait_for_timeout(4000)
                
                # Check for the specific error message
                error_locator = frame.locator('text="Please enter the characters you see or hear to continue."')
                
                # If the error is visible, the CAPTCHA was wrong
                if error_locator.count() > 0 and error_locator.first.is_visible():
                    print("\n❌ [ERROR] Incorrect CAPTCHA! Let's try again.")
                    # Clear the input field so the user can try again
                    if captcha_input:
                        captcha_input.fill("")
                    continue # Loop back to the beginning to re-screenshot and ask again
                else:
                    # No error found, assume success
                    print("\n✅ CAPTCHA accepted! No error message detected.")
                    break # Exit the loop and proceed to the end of the script

            # ==========================================
            # FINISH
            # ==========================================
            print("Waiting 10 seconds before closing...")
            page.wait_for_timeout(10000)
            
            print("Process finished. Closing browser.")
            browser.close()

    except Exception as e:
        print(f"\n❌ An error occurred during automation: {e}")
    
    finally:
        stop_vnc_environment(vnc_processes)

if __name__ == "__main__":
    main()