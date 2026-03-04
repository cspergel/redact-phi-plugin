"""Tests for column classifier."""
import pytest

from server.column_classifier import ColumnClassifier, ColumnClassification


class TestColumnClassifier:
    def setup_method(self):
        self.classifier = ColumnClassifier()

    # --- PHI columns ---
    def test_patient_name_column(self):
        result = self.classifier.classify("Patient Name")
        assert result.is_phi is True
        assert result.phi_type == "PATIENT_NAME"

    def test_name_column(self):
        result = self.classifier.classify("Name")
        assert result.is_phi is True
        assert result.phi_type == "PATIENT_NAME"

    def test_dob_column(self):
        result = self.classifier.classify("DOB")
        assert result.is_phi is True
        assert result.phi_type == "DOB"

    def test_date_of_birth_column(self):
        result = self.classifier.classify("Date of Birth")
        assert result.is_phi is True
        assert result.phi_type == "DOB"

    def test_mrn_column(self):
        result = self.classifier.classify("MRN")
        assert result.is_phi is True
        assert result.phi_type == "MRN"

    def test_medical_record_number_column(self):
        result = self.classifier.classify("Medical Record Number")
        assert result.is_phi is True
        assert result.phi_type == "MRN"

    def test_ssn_column(self):
        result = self.classifier.classify("SSN")
        assert result.is_phi is True
        assert result.phi_type == "SSN"

    def test_phone_column(self):
        result = self.classifier.classify("Phone Number")
        assert result.is_phi is True
        assert result.phi_type == "PHONE"

    def test_email_column(self):
        result = self.classifier.classify("Email")
        assert result.is_phi is True
        assert result.phi_type == "EMAIL"

    def test_provider_name_column(self):
        result = self.classifier.classify("Rendering Provider")
        assert result.is_phi is True
        assert result.phi_type == "PROVIDER_NAME"

    def test_attending_physician(self):
        result = self.classifier.classify("Attending Physician")
        assert result.is_phi is True
        assert result.phi_type == "PROVIDER_NAME"

    def test_facility_column(self):
        result = self.classifier.classify("Facility Name")
        assert result.is_phi is True
        assert result.phi_type == "FACILITY"

    def test_admission_date(self):
        result = self.classifier.classify("Admission Date")
        assert result.is_phi is True
        assert result.phi_type == "DATE"

    def test_discharge_date(self):
        result = self.classifier.classify("Discharge Date")
        assert result.is_phi is True
        assert result.phi_type == "DATE"

    def test_address_column(self):
        result = self.classifier.classify("Address")
        assert result.is_phi is True
        assert result.phi_type == "STREET_ADDRESS"

    def test_npi_column(self):
        result = self.classifier.classify("NPI")
        assert result.is_phi is True
        assert result.phi_type == "NPI"

    # --- Non-PHI columns ---
    def test_cpt_code_column(self):
        result = self.classifier.classify("CPT Code")
        assert result.is_phi is False

    def test_icd10_column(self):
        result = self.classifier.classify("ICD-10")
        assert result.is_phi is False

    def test_diagnosis_code_column(self):
        result = self.classifier.classify("Diagnosis Code")
        assert result.is_phi is False

    def test_charges_column(self):
        result = self.classifier.classify("Charges")
        assert result.is_phi is False

    def test_amount_column(self):
        result = self.classifier.classify("Total Amount")
        assert result.is_phi is False

    def test_units_column(self):
        result = self.classifier.classify("Units")
        assert result.is_phi is False

    def test_modifier_column(self):
        result = self.classifier.classify("Modifier")
        assert result.is_phi is False

    def test_place_of_service_column(self):
        result = self.classifier.classify("Place of Service")
        assert result.is_phi is False

    def test_case_insensitive(self):
        result = self.classifier.classify("patient name")
        assert result.is_phi is True
        assert result.phi_type == "PATIENT_NAME"

    def test_classify_headers_batch(self):
        headers = ["Patient Name", "DOB", "MRN", "CPT Code", "Charges"]
        results = self.classifier.classify_headers(headers)
        assert results["Patient Name"].is_phi is True
        assert results["DOB"].is_phi is True
        assert results["MRN"].is_phi is True
        assert results["CPT Code"].is_phi is False
        assert results["Charges"].is_phi is False
