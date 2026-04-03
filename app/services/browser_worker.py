"""
browser_worker.py — standalone Playwright subprocess
Full booking + payment flow on Booking.com

Steps:
  1. Open Booking.com
  2. Login (saved session or credentials)
  3. Search city + dates
  4. Open chosen hotel page
  5. Click Reserve
  6. Fill guest details (name / email / phone)
  7. Payment page:
     - Use already-saved payment method if available
     - OR fill card details if provided
  8. Confirm Booking button (only if auto_confirm=True)
  9. Screenshot every step

Run: python browser_worker.py <data.json> <result.json>
"""
import sys, os, json, asyncio

def main():
    if len(sys.argv) < 3:
        sys.exit(1)
    data_path, result_path = sys.argv[1], sys.argv[2]
    with open(data_path, encoding="utf-8") as f:
        args = json.load(f)
    result = asyncio.run(_run(args))
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(result, f)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ASYNC FLOW
# ═══════════════════════════════════════════════════════════════════════════════
async def _run(args: dict) -> dict:
    from playwright.async_api import async_playwright, TimeoutError as PWT

    booking_data    = args["booking_data"]
    session_id      = args["session_id"]
    hotel_link      = args.get("hotel_link", "")
    headless        = args.get("headless", False)
    slow_mo         = args.get("slow_mo", 700)
    auth_file       = args.get("auth_file", "")
    screenshots_dir = args["screenshots_dir"]
    creds           = args.get("creds", {})
    payment         = args.get("payment", {})
    auto_confirm    = args.get("auto_confirm", False)
    guest           = args.get("guest", {})

    screenshots = []
    session_dir = os.path.join(screenshots_dir, session_id)
    os.makedirs(session_dir, exist_ok=True)

    def ts():
        from datetime import datetime
        return datetime.now().strftime("%H%M%S_%f")[:10]

    async def snap(page, label):
        path = os.path.join(session_dir, f"{ts()}_{label}.png")
        try:
            await page.screenshot(path=path, full_page=True)
            screenshots.append(path)
            print(f"[SNAP] {label}", flush=True)
        except Exception as e:
            print(f"[SNAP-FAIL] {label}: {e}", flush=True)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=headless,
            slow_mo=slow_mo,
            args=["--start-maximized"],
        )
        ctx_args = dict(
            viewport=None,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
        )
        if auth_file and os.path.exists(auth_file):
            context = await browser.new_context(storage_state=auth_file, **ctx_args)
            print("[AUTH] Reusing saved session", flush=True)
        else:
            context = await browser.new_context(**ctx_args)

        page = await context.new_page()

        try:
            # ── STEP 1: Homepage ──────────────────────────────────────────
            print("[STEP 1] Opening Booking.com", flush=True)
            await page.goto("https://www.booking.com", timeout=30_000)
            await page.wait_for_load_state("domcontentloaded")
            await page.wait_for_timeout(1500)
            await _dismiss_popups(page, PWT)
            await snap(page, "01_homepage")

            # ── STEP 2: Login ─────────────────────────────────────────────
            email    = creds.get("email", "")
            password = creds.get("password", "")
            if not (auth_file and os.path.exists(auth_file)) and email and password:
                print("[STEP 2] Logging in…", flush=True)
                await _login(page, email, password, snap, PWT, context, auth_file)

            # ── STEP 3: Search ────────────────────────────────────────────
            location = booking_data.get("location", "")
            checkin  = booking_data.get("checkin", "")
            checkout = booking_data.get("checkout", "")
            guests   = int(booking_data.get("guests", 2))
            print(f"[STEP 3] Searching: {location}", flush=True)
            await _search(page, location, checkin, checkout, guests, snap, PWT)

            # ── STEP 4: Hotel page ────────────────────────────────────────
            if hotel_link and hotel_link.startswith("https://www.booking.com"):
                print("[STEP 4] Opening hotel page", flush=True)
                await page.goto(hotel_link, timeout=25_000)
                await page.wait_for_load_state("networkidle", timeout=15_000)
                await _dismiss_popups(page, PWT)
                await snap(page, "05_hotel_page")

                # ── STEP 5: Click Reserve ─────────────────────────────────
                print("[STEP 5] Clicking Reserve…", flush=True)
                reserved = await _click_reserve(page, snap, PWT)

                if reserved:
                    await page.wait_for_load_state("networkidle", timeout=15_000)
                    await _dismiss_popups(page, PWT)
                    await snap(page, "06_after_reserve")

                    # ── STEP 6: Fill guest details ────────────────────────
                    print("[STEP 6] Filling guest details…", flush=True)
                    await _fill_guest_details(page, guest, snap, PWT)

                    # ── STEP 7: Payment page ──────────────────────────────
                    print("[STEP 7] Handling payment…", flush=True)
                    payment_done = await _handle_payment(
                        page, payment, snap, PWT)

                    # ── STEP 8: Confirm booking ───────────────────────────
                    if auto_confirm and payment_done:
                        print("[STEP 8] Confirming booking…", flush=True)
                        confirmed = await _confirm_booking(page, snap, PWT)
                        if confirmed:
                            await snap(page, "09_booking_confirmed")
                            return {
                                "status":      "booked",
                                "message":     "Booking confirmed and payment processed!",
                                "screenshots": screenshots,
                            }
                    else:
                        await snap(page, "08_payment_page_ready")
                        return {
                            "status":   "payment_ready",
                            "message":  "Reached payment page. Review and confirm manually.",
                            "screenshots": screenshots,
                        }

            return {
                "status":      "success",
                "message":     "Browser automation completed. Screenshots saved.",
                "screenshots": screenshots,
            }

        except Exception as exc:
            print(f"[ERROR] {exc}", flush=True)
            await snap(page, "error_state")
            return {"status": "error", "message": str(exc),
                    "screenshots": screenshots}
        finally:
            await context.close()
            await browser.close()


# ═══════════════════════════════════════════════════════════════════════════════
# STEP IMPLEMENTATIONS
# ═══════════════════════════════════════════════════════════════════════════════

async def _dismiss_popups(page, PWT):
    for sel in [
        "button#onetrust-accept-btn-handler",
        "button[data-gdpr-consent='accept']",
        "button:has-text('Accept')",
        "button:has-text('Accept all')",
        "button:has-text('I agree')",
        "[data-testid='accept-button']",
        "[aria-label='Dismiss sign-in info.']",
        "button:has-text('Dismiss')",
        "button:has-text('Close')",
    ]:
        try:
            await page.wait_for_selector(sel, timeout=1_500)
            await page.click(sel)
            print(f"[POPUP] Dismissed: {sel}", flush=True)
            await page.wait_for_timeout(500)
        except Exception:
            pass


async def _login(page, email, password, snap, PWT, context, auth_file):
    try:
        await page.click("a[href*='sign-in'], button:has-text('Sign in')", timeout=6_000)
        await page.wait_for_load_state("domcontentloaded")
        await snap(page, "02_login_page")

        await page.wait_for_selector("input[name='username'], input[type='email']", timeout=8_000)
        await page.fill("input[name='username'], input[type='email']", email)
        await page.click("button[type='submit']")
        await page.wait_for_load_state("domcontentloaded")
        await snap(page, "02b_email_entered")

        await page.wait_for_selector("input[type='password']", timeout=8_000)
        await page.fill("input[type='password']", password)
        await snap(page, "02c_password_filled")
        await page.click("button[type='submit']")
        await page.wait_for_load_state("networkidle", timeout=12_000)
        await snap(page, "02d_logged_in")

        if auth_file:
            await context.storage_state(path=auth_file)
            print("[AUTH] Session saved", flush=True)
    except PWT:
        print("[AUTH] Timed out — continuing without login", flush=True)
        await snap(page, "02_login_skipped")
    except Exception as e:
        print(f"[AUTH] Skipped: {e}", flush=True)


async def _search(page, location, checkin, checkout, guests, snap, PWT):
    SEARCH_BOX = [
        "input[name='ss']",
        "[data-testid='destination-container'] input",
        "[data-testid='searchbox-destination-input']",
        "input[placeholder*='Where']",
        "input[placeholder*='Destination']",
        "input[placeholder*='where']",
        "#ss",
    ]
    try:
        search_box = None
        for sel in SEARCH_BOX:
            try:
                await page.wait_for_selector(sel, timeout=4_000)
                search_box = sel
                print(f"[SEARCH] Box found: {sel}", flush=True)
                break
            except PWT:
                continue

        if not search_box:
            await snap(page, "03_search_failed")
            return

        await page.click(search_box)
        await page.fill(search_box, "")
        await page.type(search_box, location, delay=80)
        await snap(page, "03a_city_typed")

        try:
            await page.wait_for_selector(
                "[data-testid='autocomplete-results-container']", timeout=4_000)
            await page.keyboard.press("ArrowDown")
            await snap(page, "03b_autocomplete")
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(800)
            await snap(page, "03c_city_selected")
        except PWT:
            pass

        if checkin:
            try:
                for ci_sel in ["[data-testid='searchbox-dates-container']",
                               "[data-testid='date-display-field-start']"]:
                    try:
                        await page.wait_for_selector(ci_sel, timeout=3_000)
                        await page.click(ci_sel)
                        await page.wait_for_timeout(500)
                        break
                    except PWT:
                        pass

                await page.wait_for_selector(f"span[data-date='{checkin}']", timeout=6_000)
                await page.click(f"span[data-date='{checkin}']")
                await page.wait_for_timeout(400)
                await page.click(f"span[data-date='{checkout}']")
                await snap(page, "03d_dates_selected")
            except PWT:
                print("[SEARCH] Date picker not found — skipping", flush=True)

        await snap(page, "03e_form_ready")
        await page.click("button[type='submit']")
        await page.wait_for_load_state("networkidle", timeout=20_000)
        await snap(page, "04_search_results")

    except Exception as e:
        print(f"[SEARCH] {e}", flush=True)
        try:
            await page.wait_for_load_state("networkidle", timeout=8_000)
            await snap(page, "04_fallback")
        except Exception:
            pass


async def _click_reserve(page, snap, PWT) -> bool:
    for sel in [
        "[data-testid='reservation-button']",
        "button:has-text('Reserve')",
        "button:has-text('I\\'ll reserve')",
        "button:has-text('Book now')",
        "a:has-text('Reserve')",
        "button:has-text('See availability')",
    ]:
        try:
            await page.wait_for_selector(sel, timeout=4_000)
            await page.click(sel)
            print(f"[RESERVE] Clicked: {sel}", flush=True)
            await snap(page, "05b_reserve_clicked")
            return True
        except PWT:
            continue
    print("[RESERVE] Button not found", flush=True)
    return False


async def _fill_guest_details(page, guest: dict, snap, PWT):
    """Fill guest name, email, phone on the booking details page."""
    first_name = guest.get("first_name", "")
    last_name  = guest.get("last_name", "")
    email      = guest.get("email", "")
    phone      = guest.get("phone", "")

    try:
        # first name
        for sel in ["input[name='firstname']", "input[id*='firstname']",
                    "[data-testid='guest-name-firstname'] input",
                    "input[placeholder*='First name']"]:
            try:
                await page.wait_for_selector(sel, timeout=3_000)
                await page.fill(sel, first_name)
                print(f"[GUEST] First name filled", flush=True)
                break
            except PWT:
                continue

        # last name
        for sel in ["input[name='lastname']", "input[id*='lastname']",
                    "[data-testid='guest-name-lastname'] input",
                    "input[placeholder*='Last name']"]:
            try:
                await page.wait_for_selector(sel, timeout=2_000)
                await page.fill(sel, last_name)
                print(f"[GUEST] Last name filled", flush=True)
                break
            except PWT:
                continue

        # email
        for sel in ["input[name='email']", "input[id*='email']",
                    "[data-testid='guest-email'] input",
                    "input[type='email']"]:
            try:
                await page.wait_for_selector(sel, timeout=2_000)
                await page.fill(sel, email)
                print(f"[GUEST] Email filled", flush=True)
                break
            except PWT:
                continue

        # phone
        for sel in ["input[name='phone']", "input[id*='phone']",
                    "[data-testid='guest-phone'] input",
                    "input[type='tel']"]:
            try:
                await page.wait_for_selector(sel, timeout=2_000)
                await page.fill(sel, phone)
                print(f"[GUEST] Phone filled", flush=True)
                break
            except PWT:
                continue

        await snap(page, "07_guest_details_filled")

        # click Continue / Next to reach payment page
        for sel in [
            "button:has-text('Next')",
            "button:has-text('Continue')",
            "button:has-text('Go to final step')",
            "input[type='submit']",
        ]:
            try:
                await page.wait_for_selector(sel, timeout=3_000)
                await page.click(sel)
                await page.wait_for_load_state("networkidle", timeout=12_000)
                print(f"[GUEST] Continued to next step", flush=True)
                break
            except PWT:
                continue

        await snap(page, "07b_after_guest_submit")

    except Exception as e:
        print(f"[GUEST] Error filling details: {e}", flush=True)
        await snap(page, "07_guest_error")


async def _handle_payment(page, payment: dict, snap, PWT) -> bool:
    """
    Handle payment page.
    1. Check if a saved payment method already exists → click it.
    2. Otherwise fill card number / expiry / CVV from payment dict.
    Returns True if payment details are ready, False on failure.
    """
    await snap(page, "08a_payment_page")

    card_number = payment.get("card_number", "").replace(" ", "")
    expiry_mm   = payment.get("expiry_month", "")
    expiry_yy   = payment.get("expiry_year", "")
    cvv         = payment.get("cvv", "")
    name_card   = payment.get("name_on_card", "")

    # ── Check for saved payment method ────────────────────────────────────
    saved_selectors = [
        "[data-testid='saved-payment-method']",
        "[data-testid='payment-method-saved']",
        "input[name='payment_option'][value*='saved']",
        ".saved-payment-method",
        "label:has-text('saved card')",
        "label:has-text('Saved card')",
    ]
    for sel in saved_selectors:
        try:
            await page.wait_for_selector(sel, timeout=3_000)
            await page.click(sel)
            print(f"[PAYMENT] Selected saved payment method: {sel}", flush=True)
            await snap(page, "08b_saved_payment_selected")
            return True
        except PWT:
            continue

    # ── No saved method — fill card details ───────────────────────────────
    if not card_number:
        print("[PAYMENT] No saved method and no card details provided", flush=True)
        await snap(page, "08b_payment_no_card")
        return False

    print("[PAYMENT] Filling card details…", flush=True)
    filled = False

    # card number (may be inside an iframe on Booking.com)
    for sel in ["input[name='cc_number']", "input[id*='cc_number']",
                "input[placeholder*='Card number']", "input[placeholder*='card number']",
                "[data-testid='credit-card-number'] input"]:
        try:
            await page.wait_for_selector(sel, timeout=3_000)
            await page.fill(sel, card_number)
            print("[PAYMENT] Card number filled", flush=True)
            filled = True
            break
        except PWT:
            continue

    if not filled:
        # try inside payment iframe
        try:
            frames = page.frames
            for frame in frames:
                for sel in ["input[name='cc_number']",
                            "input[placeholder*='Card number']",
                            "input[placeholder*='card number']"]:
                    try:
                        await frame.wait_for_selector(sel, timeout=2_000)
                        await frame.fill(sel, card_number)
                        print("[PAYMENT] Card number filled (iframe)", flush=True)
                        filled = True
                        break
                    except Exception:
                        continue
                if filled:
                    break
        except Exception as e:
            print(f"[PAYMENT] iframe attempt failed: {e}", flush=True)

    # expiry month
    for sel in ["select[name='cc_exp_month']", "[data-testid='expiry-month'] select",
                "select[id*='exp_month']"]:
        try:
            await page.wait_for_selector(sel, timeout=2_000)
            await page.select_option(sel, value=expiry_mm.lstrip("0") or expiry_mm)
            print("[PAYMENT] Expiry month set", flush=True)
            break
        except PWT:
            continue

    # expiry year
    for sel in ["select[name='cc_exp_year']", "[data-testid='expiry-year'] select",
                "select[id*='exp_year']"]:
        try:
            await page.wait_for_selector(sel, timeout=2_000)
            await page.select_option(sel, value=expiry_yy)
            print("[PAYMENT] Expiry year set", flush=True)
            break
        except PWT:
            continue

    # CVV
    for sel in ["input[name='cc_cvc']", "input[id*='cvc']", "input[id*='cvv']",
                "input[placeholder*='CVC']", "input[placeholder*='CVV']",
                "[data-testid='cvc'] input"]:
        try:
            await page.wait_for_selector(sel, timeout=2_000)
            await page.fill(sel, cvv)
            print("[PAYMENT] CVV filled", flush=True)
            break
        except PWT:
            continue

    # name on card
    for sel in ["input[name='cc_name']", "input[id*='cc_name']",
                "input[placeholder*='Name on card']", "input[placeholder*='Cardholder']"]:
        try:
            await page.wait_for_selector(sel, timeout=2_000)
            await page.fill(sel, name_card)
            print("[PAYMENT] Name on card filled", flush=True)
            break
        except PWT:
            continue

    await snap(page, "08c_card_details_filled")
    return filled


async def _confirm_booking(page, snap, PWT) -> bool:
    """Click the final Confirm / Complete booking button."""
    confirm_selectors = [
        "button:has-text('Complete booking')",
        "button:has-text('Confirm booking')",
        "button:has-text('Confirm reservation')",
        "button:has-text('Pay now')",
        "button:has-text('Book and pay')",
        "[data-testid='confirm-button']",
        "input[type='submit'][value*='Confirm']",
        "input[type='submit'][value*='Complete']",
    ]
    for sel in confirm_selectors:
        try:
            await page.wait_for_selector(sel, timeout=4_000)
            await page.click(sel)
            print(f"[CONFIRM] Clicked: {sel}", flush=True)
            await page.wait_for_load_state("networkidle", timeout=20_000)
            await snap(page, "09_confirmed")
            return True
        except PWT:
            continue
    print("[CONFIRM] Confirm button not found", flush=True)
    await snap(page, "08d_confirm_not_found")
    return False


if __name__ == "__main__":
    main()
