"""Unit tests for data validation utilities.

Tests cover:
- Schema validation (expected columns and types)
- Null value checks
- Date range validation
- Outlier detection
- Geographic code validation (LA, LSOA codes)
- Postcode validation
- Batch validation runner
"""

import polars as pl
import pytest

from src.data.validators import (
    ValidationError,
    ValidationResult,
    check_date_range,
    check_geographic_codes,
    check_nulls,
    check_outliers,
    run_all_validations,
    validate_la_code,
    validate_lsoa_code,
    validate_postcode,
    validate_schema,
)


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_validation_result_creation(self):
        """Test creating a ValidationResult."""
        result = ValidationResult(
            passed=True,
            message="Test passed",
            details={"count": 10},
        )

        assert result.passed is True
        assert result.message == "Test passed"
        assert result.details == {"count": 10}

    def test_validation_result_without_details(self):
        """Test ValidationResult without details."""
        result = ValidationResult(passed=False, message="Test failed")

        assert result.passed is False
        assert result.message == "Test failed"
        assert result.details is None


class TestValidateSchema:
    """Tests for validate_schema function."""

    def test_schema_validation_success(self):
        """Test successful schema validation."""
        df = pl.DataFrame(
            {
                "year": [2023, 2024],
                "emissions": [100.0, 95.0],
                "name": ["Bristol", "Bath"],
            }
        )
        expected = {"year": int, "emissions": float, "name": str}

        result = validate_schema(df, expected)

        assert result.passed is True
        assert "passed" in result.message.lower()

    def test_schema_validation_missing_column(self):
        """Test schema validation with missing column."""
        df = pl.DataFrame({"year": [2023], "emissions": [100.0]})
        expected = {"year": int, "emissions": float, "name": str}

        result = validate_schema(df, expected)

        assert result.passed is False
        assert "Missing columns" in result.details["issues"][0]

    def test_schema_validation_type_mismatch(self):
        """Test schema validation with type mismatch."""
        df = pl.DataFrame({"year": ["2023", "2024"]})  # String instead of int
        expected = {"year": int}

        result = validate_schema(df, expected)

        assert result.passed is False
        assert "Type mismatches" in result.details["issues"][0]

    def test_schema_validation_extra_columns_allowed(self):
        """Test schema validation allows extra columns by default."""
        df = pl.DataFrame({"year": [2023], "extra": ["data"]})
        expected = {"year": int}

        result = validate_schema(df, expected, allow_extra_columns=True)

        assert result.passed is True

    def test_schema_validation_extra_columns_forbidden(self):
        """Test schema validation fails with extra columns when not allowed."""
        df = pl.DataFrame({"year": [2023], "extra": ["data"]})
        expected = {"year": int}

        result = validate_schema(df, expected, allow_extra_columns=False)

        assert result.passed is False
        assert "Unexpected columns" in result.details["issues"][0]


class TestCheckNulls:
    """Tests for check_nulls function."""

    def test_check_nulls_no_nulls(self):
        """Test null check with no null values."""
        df = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})

        result = check_nulls(df)

        assert result.passed is True

    def test_check_nulls_with_nulls(self):
        """Test null check with null values."""
        df = pl.DataFrame({"a": [1, None, 3], "b": [4, 5, 6]})

        result = check_nulls(df)

        assert result.passed is False
        assert "a" in result.details["null_columns"]
        assert result.details["null_counts"]["a"] == 1

    def test_check_nulls_specific_columns(self):
        """Test null check on specific columns only."""
        df = pl.DataFrame({"a": [1, None, 3], "b": [4, None, 6]})

        result = check_nulls(df, columns=["a"])

        assert result.passed is False
        assert "a" in result.details["null_columns"]
        assert "b" not in result.details["null_columns"]

    def test_check_nulls_allow_null_columns(self):
        """Test null check with allowed null columns."""
        df = pl.DataFrame({"a": [1, None, 3], "b": [4, 5, 6]})

        result = check_nulls(df, allow_null_columns=["a"])

        assert result.passed is True


class TestCheckDateRange:
    """Tests for check_date_range function."""

    def test_date_range_validation_success(self):
        """Test successful date range validation."""
        df = pl.DataFrame({"year": [2020, 2021, 2022]})

        result = check_date_range(df, "year", min_date=2020, max_date=2023)

        assert result.passed is True
        assert result.details["actual_min"] == 2020
        assert result.details["actual_max"] == 2022

    def test_date_range_validation_below_minimum(self):
        """Test date range validation with value below minimum."""
        df = pl.DataFrame({"year": [2019, 2020, 2021]})

        result = check_date_range(df, "year", min_date=2020, max_date=2023)

        assert result.passed is False
        assert "before allowed minimum" in result.details["issues"][0]

    def test_date_range_validation_above_maximum(self):
        """Test date range validation with value above maximum."""
        df = pl.DataFrame({"year": [2020, 2021, 2024]})

        result = check_date_range(df, "year", min_date=2020, max_date=2023)

        assert result.passed is False
        assert "after allowed maximum" in result.details["issues"][0]

    def test_date_range_validation_missing_column(self):
        """Test date range validation with missing column."""
        df = pl.DataFrame({"other": [2020]})

        result = check_date_range(df, "year", min_date=2020, max_date=2023)

        assert result.passed is False
        assert "not found" in result.message.lower()

    def test_date_range_validation_no_limits(self):
        """Test date range validation with no limits."""
        df = pl.DataFrame({"year": [1900, 2020, 2100]})

        result = check_date_range(df, "year")

        assert result.passed is True


class TestCheckOutliers:
    """Tests for check_outliers function."""

    def test_outlier_detection_iqr_no_outliers(self):
        """Test outlier detection with no outliers."""
        df = pl.DataFrame({"value": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]})

        result = check_outliers(df, "value", method="iqr")

        assert result.passed is True

    def test_outlier_detection_iqr_with_outliers(self):
        """Test outlier detection with clear outliers."""
        df = pl.DataFrame({"value": [1, 2, 3, 4, 5, 6, 7, 8, 9, 100]})

        result = check_outliers(df, "value", method="iqr")

        assert result.passed is False
        assert result.details["outlier_count"] == 1

    def test_outlier_detection_iqr_custom_threshold(self):
        """Test outlier detection with custom threshold."""
        df = pl.DataFrame({"value": [1, 2, 3, 4, 5, 6, 7, 8, 9, 15]})

        # Stricter threshold (less tolerance for outliers)
        result = check_outliers(df, "value", method="iqr", threshold=1.0)

        assert result.passed is False

    def test_outlier_detection_missing_column(self):
        """Test outlier detection with missing column."""
        df = pl.DataFrame({"other": [1, 2, 3]})

        result = check_outliers(df, "value", method="iqr")

        assert result.passed is False
        assert "not found" in result.message.lower()

    def test_outlier_detection_invalid_method(self):
        """Test outlier detection with invalid method."""
        df = pl.DataFrame({"value": [1, 2, 3]})

        with pytest.raises(NotImplementedError):
            check_outliers(df, "value", method="invalid")


class TestValidateLACode:
    """Tests for validate_la_code function."""

    def test_valid_la_codes(self):
        """Test validation of valid LA codes."""
        valid_codes = [
            "E06000023",  # Bristol
            "E06000022",  # Bath and North East Somerset
            "E07000178",  # Oxford
            "S12000033",  # Aberdeen
            "W06000015",  # Cardiff
            "N09000003",  # Belfast
        ]

        for code in valid_codes:
            assert validate_la_code(code) is True

    def test_invalid_la_codes(self):
        """Test validation of invalid LA codes."""
        invalid_codes = [
            "invalid",
            "E0600023",  # Too few digits
            "E060000230",  # Too many digits
            "X06000023",  # Invalid prefix
            "E06000",  # Too short
            "",
            "123456789",
        ]

        for code in invalid_codes:
            assert validate_la_code(code) is False


class TestValidateLSOACode:
    """Tests for validate_lsoa_code function."""

    def test_valid_lsoa_codes_2021(self):
        """Test validation of valid 2021 LSOA codes."""
        valid_codes = [
            "E01000001",  # England
            "S01000001",  # Scotland
            "W01000001",  # Wales
            "N00000001",  # Northern Ireland
        ]

        for code in valid_codes:
            assert validate_lsoa_code(code, year=2021) is True

    def test_valid_lsoa_codes_2011(self):
        """Test validation of valid 2011 LSOA codes."""
        valid_codes = ["E01000001", "S01000001", "W01000001"]

        for code in valid_codes:
            assert validate_lsoa_code(code, year=2011) is True

    def test_invalid_lsoa_codes(self):
        """Test validation of invalid LSOA codes."""
        invalid_codes = [
            "invalid",
            "E0100001",  # Too few digits
            "E010000001",  # Too many digits
            "X01000001",  # Invalid prefix
            "",
            "12345678",
        ]

        for code in invalid_codes:
            assert validate_lsoa_code(code) is False

    def test_lsoa_code_invalid_year(self):
        """Test LSOA validation with invalid year."""
        with pytest.raises(ValueError) as exc_info:
            validate_lsoa_code("E01000001", year=2020)

        assert "2011 or 2021" in str(exc_info.value)


class TestCheckGeographicCodes:
    """Tests for check_geographic_codes function."""

    def test_check_geographic_codes_all_valid(self):
        """Test geographic code check with all valid codes."""
        df = pl.DataFrame({"la_code": ["E06000023", "E06000022", "E06000024"]})

        result = check_geographic_codes(df, "la_code", "la")

        assert result.passed is True

    def test_check_geographic_codes_some_invalid(self):
        """Test geographic code check with some invalid codes."""
        df = pl.DataFrame({"la_code": ["E06000023", "invalid", "E06000024"]})

        result = check_geographic_codes(df, "la_code", "la")

        assert result.passed is False
        assert "invalid" in result.details["invalid_codes"]
        assert result.details["invalid_count"] == 1

    def test_check_geographic_codes_lsoa(self):
        """Test LSOA code checking."""
        df = pl.DataFrame({"lsoa": ["E01000001", "E01000002", "invalid"]})

        result = check_geographic_codes(df, "lsoa", "lsoa")

        assert result.passed is False
        assert result.details["invalid_count"] == 1

    def test_check_geographic_codes_msoa(self):
        """Test MSOA code checking."""
        df = pl.DataFrame({"msoa": ["E02000001", "E02000002", "invalid"]})

        result = check_geographic_codes(df, "msoa", "msoa")

        assert result.passed is False

    def test_check_geographic_codes_missing_column(self):
        """Test geographic code check with missing column."""
        df = pl.DataFrame({"other": ["E06000023"]})

        result = check_geographic_codes(df, "la_code", "la")

        assert result.passed is False
        assert "not found" in result.message.lower()

    def test_check_geographic_codes_unknown_type(self):
        """Test geographic code check with unknown code type."""
        df = pl.DataFrame({"code": ["E06000023"]})

        with pytest.raises(ValueError) as exc_info:
            check_geographic_codes(df, "code", "unknown")

        assert "Unknown code type" in str(exc_info.value)


class TestValidatePostcode:
    """Tests for validate_postcode function."""

    def test_valid_postcodes(self):
        """Test validation of valid UK postcodes."""
        valid_postcodes = [
            "BS1 1AA",  # Bristol
            "BS16 7JP",
            "BS11AA",  # No space (also valid)
            "SW1A 1AA",  # Westminster
            "EC1A 1BB",  # City of London
            "W1A 0AX",  # BBC
            "M1 1AE",  # Manchester
            "B33 8TH",  # Birmingham
            "CR2 6XH",  # Croydon
            "DN55 1PT",  # Doncaster
        ]

        for postcode in valid_postcodes:
            assert validate_postcode(postcode) is True, (
                f"Expected {postcode} to be valid"
            )

    def test_invalid_postcodes(self):
        """Test validation of invalid postcodes."""
        invalid_postcodes = [
            "invalid",
            "BS1",  # Too short
            "BS1 1",  # Incomplete
            "12345",  # Numbers only
            "AAAA AAAA",  # Letters only
            "",
            "BS1 1AA 1",  # Too long
        ]

        for postcode in invalid_postcodes:
            assert validate_postcode(postcode) is False, (
                f"Expected {postcode} to be invalid"
            )

    def test_postcode_case_insensitive(self):
        """Test postcode validation is case insensitive."""
        assert validate_postcode("bs1 1aa") is True
        assert validate_postcode("BS1 1AA") is True
        assert validate_postcode("Bs1 1Aa") is True


class TestRunAllValidations:
    """Tests for run_all_validations function."""

    def test_run_all_validations_all_pass(self):
        """Test running multiple validations that all pass."""
        df = pl.DataFrame(
            {
                "year": [2020, 2021, 2022],
                "emissions": [100.0, 95.0, 90.0],
                "la_code": ["E06000023", "E06000022", "E06000024"],
            }
        )

        validations = [
            {"type": "schema", "expected": {"year": int, "emissions": float}},
            {"type": "nulls"},
            {
                "type": "date_range",
                "column": "year",
                "min_date": 2020,
                "max_date": 2025,
            },
            {"type": "geographic_codes", "column": "la_code", "code_type": "la"},
        ]

        results = run_all_validations(df, validations)

        assert len(results) == 4
        assert all(result.passed for result in results.values())

    def test_run_all_validations_some_fail(self):
        """Test running multiple validations with some failures."""
        df = pl.DataFrame(
            {
                "year": [2010, 2020, 2021],  # 2010 is before min
                "emissions": [100.0, None, 90.0],  # Has null
            }
        )

        validations = [
            {"type": "nulls"},
            {
                "type": "date_range",
                "column": "year",
                "min_date": 2015,
                "max_date": 2025,
            },
        ]

        results = run_all_validations(df, validations)

        assert len(results) == 2
        assert not all(result.passed for result in results.values())

    def test_run_all_validations_with_names(self):
        """Test running validations with custom names."""
        df = pl.DataFrame({"year": [2020, 2021]})

        validations = [
            {"type": "nulls", "name": "null_check"},
            {"type": "date_range", "name": "year_range", "column": "year"},
        ]

        results = run_all_validations(df, validations)

        assert "null_check" in results
        assert "year_range" in results

    def test_run_all_validations_unknown_type(self):
        """Test running validation with unknown type."""
        df = pl.DataFrame({"year": [2020]})

        validations = [{"type": "unknown_validation"}]

        results = run_all_validations(df, validations)

        assert len(results) == 1
        assert list(results.values())[0].passed is False
        assert "Unknown validation type" in list(results.values())[0].message


class TestValidationError:
    """Tests for ValidationError exception."""

    def test_validation_error_with_message_only(self):
        """Test ValidationError with message only."""
        error = ValidationError("Validation failed")

        assert str(error) == "Validation failed"
        assert error.message == "Validation failed"
        assert error.details == {}

    def test_validation_error_with_details(self):
        """Test ValidationError with details."""
        details = {"column": "year", "invalid_count": 5}
        error = ValidationError("Validation failed", details=details)

        assert error.message == "Validation failed"
        assert error.details == details
