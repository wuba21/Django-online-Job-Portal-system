import io
from unittest.mock import patch
from PIL import Image, ImageDraw
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from accounts.models import Company, User
from accounts.license_validator import (
    validate_tin_structure,
    verify_ethiopian_business_license,
)


class TestLicenseVerification(TestCase):
    def setUp(self):
        self.employer_user = User.objects.create_user(
            email="employer@example.com",
            password="SecurePassword123!",
            role="employer",
            first_name="Test",
            last_name="Employer",
        )
        self.company, _ = Company.objects.get_or_create(
            user=self.employer_user,
            defaults={"name": "Test Company PLC"}
        )

    def _create_test_image(self, text="Sample text", with_seal=True):
        img = Image.new("RGB", (600, 800), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.text((50, 50), text, fill=(0, 0, 0))
        if with_seal:
            for r in range(40, 48):
                draw.ellipse([250 - r, 350 - r, 250 + r, 350 + r], outline=(60, 20, 160), width=2)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def test_tin_structure_validation(self):
        # 10-digit valid numbers
        is_valid, msg = validate_tin_structure("0002847591")
        self.assertTrue(is_valid)

        # Invalid TIN lengths
        is_valid, msg = validate_tin_structure("12345")
        self.assertFalse(is_valid)
        self.assertIn("10 digits", msg)

    @patch("accounts.license_validator.verify_license_with_gemini_vision")
    def test_tin_certificate_filename_rejection(self, mock_gemini):
        # Mock Gemini reporting offline or returning false
        mock_gemini.return_value = {"success": False, "error": "Offline"}

        file_bytes = self._create_test_image("Government Document", with_seal=True)
        uploaded = SimpleUploadedFile("tin_certificate_scan.png", file_bytes, content_type="image/png")

        result = verify_ethiopian_business_license(
            uploaded,
            tin_input="0002847591",
            company_name="Ethio Telecom"
        )
        self.assertFalse(result["is_valid"])
        self.assertTrue("trade license" in result["error_message"].lower() or "tin" in result["error_message"].lower())

    @patch("accounts.license_validator.verify_license_with_gemini_vision")
    def test_sample_page_filename_rejection(self, mock_gemini):
        mock_gemini.return_value = {"success": False, "error": "Offline"}

        file_bytes = self._create_test_image("Sample Template Page", with_seal=True)
        uploaded = SimpleUploadedFile("sample_license_template.png", file_bytes, content_type="image/png")

        result = verify_ethiopian_business_license(
            uploaded,
            tin_input="0002847591",
            company_name="Ethio Telecom"
        )
        self.assertFalse(result["is_valid"])
        self.assertTrue(
            "sample" in result["error_message"].lower() or "trade license" in result["error_message"].lower()
        )

    def test_view_get_authenticated(self):
        self.client.login(email="employer@example.com", password="SecurePassword123!")
        response = self.client.get(reverse("accounts:employer-verify-license"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Business License Verification")

    def test_view_post_unsupported_file_extension(self):
        self.client.login(email="employer@example.com", password="SecurePassword123!")
        fake_file = SimpleUploadedFile("malicious.exe", b"fake binary data", content_type="application/octet-stream")
        response = self.client.post(reverse("accounts:employer-verify-license"), {
            "company_name": "Test Company PLC",
            "tin_number": "0002847591",
            "license_document": fake_file,
        })
        self.assertEqual(response.status_code, 200)
        # Should not crash with 500; should show error message
        self.assertContains(response, "Unsupported file format")

    @patch("accounts.license_validator.verify_license_with_gemini_vision")
    def test_view_post_tin_certificate_rejected(self, mock_gemini):
        mock_gemini.return_value = {
            "success": True,
            "data": {
                "is_valid": False,
                "confidence": 98,
                "document_type": "Taxpayer Registration Certificate",
                "rejection_reason": "The uploaded document is a Taxpayer Registration Certificate (TIN Certificate), not an official Commercial Business Trade License.",
            }
        }
        self.client.login(email="employer@example.com", password="SecurePassword123!")
        file_bytes = self._create_test_image("Ministry of Revenues TIN Registration Certificate", with_seal=True)
        tin_doc = SimpleUploadedFile("tin_registration_cert.png", file_bytes, content_type="image/png")

        response = self.client.post(reverse("accounts:employer-verify-license"), {
            "company_name": "Test Company PLC",
            "tin_number": "0002847591",
            "license_document": tin_doc,
        })
        self.assertEqual(response.status_code, 200)
        self.company.refresh_from_db()
        self.assertEqual(self.company.license_status, "rejected")
        self.assertFalse(self.company.is_license_verified)
        self.assertContains(response, "Taxpayer Registration Certificate")

    @patch("accounts.license_validator.verify_license_with_gemini_vision")
    def test_view_post_valid_trade_license_approved(self, mock_gemini):
        mock_gemini.return_value = {
            "success": True,
            "data": {
                "is_valid": True,
                "confidence": 96,
                "document_type": "Trade License",
                "stamp_detected": True,
                "detected_tin": "0002847591",
                "detected_company_name": "Ethio Telecom",
                "verification_points": ["Valid Trade License verified", "Official circular seal detected"],
            }
        }
        self.client.login(email="employer@example.com", password="SecurePassword123!")
        file_bytes = self._create_test_image("Commercial Business License", with_seal=True)
        trade_doc = SimpleUploadedFile("trade_license.png", file_bytes, content_type="image/png")

        response = self.client.post(reverse("accounts:employer-verify-license"), {
            "company_name": "Ethio Telecom",
            "tin_number": "0002847591",
            "license_document": trade_doc,
        })
        self.assertEqual(response.status_code, 302)
        self.company.refresh_from_db()
        self.assertEqual(self.company.license_status, "verified")
        self.assertTrue(self.company.is_license_verified)

    @patch("accounts.license_validator.verify_ethiopian_business_license")
    def test_view_post_unexpected_exception_prevents_500_error(self, mock_verify):
        # Simulate unexpected crash in verification engine
        mock_verify.side_effect = RuntimeError("Simulated internal parser crash")
        self.client.login(email="employer@example.com", password="SecurePassword123!")

        file_bytes = self._create_test_image("Trade License", with_seal=True)
        doc = SimpleUploadedFile("license.png", file_bytes, content_type="image/png")

        response = self.client.post(reverse("accounts:employer-verify-license"), {
            "company_name": "Test Company PLC",
            "tin_number": "0002847591",
            "license_document": doc,
        })
        # Must return 200 with friendly message, NEVER 500 error!
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "An unexpected error occurred while processing your document")
