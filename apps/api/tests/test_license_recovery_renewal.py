"""Automated tests for Customer Portal OTP authentication, license re-download, and renewal."""

from app.routers.customer_portal import (
    api_send_customer_otp,
    api_verify_customer_otp,
    api_list_customer_licenses,
    api_download_license_file,
    api_renew_license,
    api_request_hardware_transfer,
    OTPRequest,
    OTPVerifyRequest,
    RenewalOrderRequest,
    HardwareTransferRequest,
)


def test_customer_portal_otp_login_flow():
    email = "doctor@metropolislab.in"
    send_res = api_send_customer_otp(OTPRequest(email=email))
    assert send_res["status"] == "otp_sent"

    # Verify with correct OTP
    verify_res = api_verify_customer_otp(OTPVerifyRequest(email=email, otp="123456"))
    assert verify_res["status"] == "authenticated"
    assert "cust_sess_" in verify_res["customer_token"]


def test_customer_license_redownload_lost_file():
    lic_id = "LIC-PROD-20261109-8F12"
    resp = api_download_license_file(lic_id)

    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/octet-stream"
    assert f'filename="aarozi_license_{lic_id}.lic"' in resp.headers["content-disposition"]


def test_customer_license_renewal_preserves_identity():
    renewal_req = RenewalOrderRequest(license_id="LIC-PROD-20261109-8F12", plan_code="YEARLY_PRO")
    res = api_renew_license(renewal_req)

    assert res["status"] == "renewed"
    assert res["new_license_id"].startswith("LIC-PROD-")
    assert "Subscription renewed for 365 days" in res["message"]


def test_customer_hardware_migration_transfer():
    transfer_req = HardwareTransferRequest(
        license_id="LIC-PROD-20261109-8F12",
        new_hardware_fingerprint="HW-NEW-9999-AAAA",
        reason="Motherboard burned out after lightning storm",
    )
    res = api_request_hardware_transfer(transfer_req)

    assert res["status"] == "transfer_approved"
    assert res["new_hardware_fingerprint"] == "HW-NEW-9999-AAAA"

