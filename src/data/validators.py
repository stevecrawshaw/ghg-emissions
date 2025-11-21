"""Data validation utilities for GHG emissions and geographic data.

This module provides functions for:
- Schema validation (checking expected columns and data types)
- Data quality checks (nulls, outliers, date ranges)
- Geographic code validation (LA codes, LSOA codes, postcodes)

All functions accept Polars DataFrames and return validation results.
"""

import re
from dataclasses import dataclass
from typing import Any

import polars as pl


class ValidationError(Exception):
    """Exception raised when data validation fails.

    Attributes:
        message: Explanation of the validation failure
        details: Optional detailed information about what failed
    """

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Initialize the validation error.

        Args:
            message: Human-readable error description
            details: Optional dictionary with failure details
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


@dataclass
class ValidationResult:
    """Result of a data validation check.

    Attributes:
        passed: Whether the validation passed
        message: Description of the validation result
        details: Optional detailed information (counts, examples, etc.)
    """

    passed: bool
    message: str
    details: dict[str, Any] | None = None


def validate_schema(
    df: pl.DataFrame,
    expected_columns: dict[str, type],
    allow_extra_columns: bool = True,
) -> ValidationResult:
    """Validate that a DataFrame has the expected schema.

    Checks that all expected columns are present and have compatible data types.

    Args:
        df: DataFrame to validate
        expected_columns: Dictionary mapping column names to expected Python types
            (e.g., {"year": int, "emissions": float, "name": str})
        allow_extra_columns: If False, fail if DataFrame has extra columns
            not in expected_columns (default: True)

    Returns:
        ValidationResult with passed status and details

    Example:
        >>> df = pl.DataFrame({"year": [2023], "emissions": [100.0]})
        >>> expected = {"year": int, "emissions": float}
        >>> result = validate_schema(df, expected)
        >>> result.passed
        True
    """
    issues = []

    # Map Python types to Polars types
    type_mapping = {
        int: [
            pl.Int8,
            pl.Int16,
            pl.Int32,
            pl.Int64,
            pl.UInt8,
            pl.UInt16,
            pl.UInt32,
            pl.UInt64,
        ],
        float: [pl.Float32, pl.Float64],
        str: [pl.Utf8, pl.String],
        bool: [pl.Boolean],
    }

    # Check for missing columns
    missing_cols = set(expected_columns.keys()) - set(df.columns)
    if missing_cols:
        issues.append(f"Missing columns: {sorted(missing_cols)}")

    # Check for unexpected extra columns
    if not allow_extra_columns:
        extra_cols = set(df.columns) - set(expected_columns.keys())
        if extra_cols:
            issues.append(f"Unexpected columns: {sorted(extra_cols)}")

    # Check column types
    type_mismatches = {}
    for col_name, expected_type in expected_columns.items():
        if col_name in df.columns:
            actual_type = df[col_name].dtype
            expected_polars_types = type_mapping.get(expected_type, [])
            if actual_type not in expected_polars_types:
                type_mismatches[col_name] = {
                    "expected": expected_type.__name__,
                    "actual": str(actual_type),
                }

    if type_mismatches:
        issues.append(f"Type mismatches: {type_mismatches}")

    if issues:
        return ValidationResult(
            passed=False,
            message="Schema validation failed",
            details={"issues": issues, "column_count": len(df.columns)},
        )

    return ValidationResult(
        passed=True,
        message="Schema validation passed",
        details={"column_count": len(df.columns)},
    )


def check_nulls(
    df: pl.DataFrame,
    columns: list[str] | None = None,
    allow_null_columns: list[str] | None = None,
) -> ValidationResult:
    """Check for null values in specified columns.

    Args:
        df: DataFrame to check
        columns: List of columns to check for nulls.
            If None, checks all columns (default: None)
        allow_null_columns: List of columns where nulls are acceptable
            (default: None)

    Returns:
        ValidationResult with null counts for each column

    Example:
        >>> df = pl.DataFrame({"a": [1, 2, None], "b": [4, 5, 6]})
        >>> result = check_nulls(df)
        >>> result.passed
        False
        >>> result.details["null_columns"]
        ['a']
    """
    if columns is None:
        columns = df.columns

    if allow_null_columns is None:
        allow_null_columns = []

    # Check for nulls in each column
    null_counts = {}
    for col in columns:
        if col in df.columns:
            null_count = df[col].null_count()
            if null_count > 0:
                null_counts[col] = null_count

    # Filter out allowed null columns
    problematic_nulls = {
        col: count
        for col, count in null_counts.items()
        if col not in allow_null_columns
    }

    if problematic_nulls:
        total_nulls = sum(problematic_nulls.values())
        col_count = len(problematic_nulls)
        return ValidationResult(
            passed=False,
            message=f"Found {total_nulls} null values in {col_count} columns",
            details={
                "null_columns": list(problematic_nulls.keys()),
                "null_counts": problematic_nulls,
                "total_rows": df.height,
            },
        )

    return ValidationResult(
        passed=True,
        message="No unexpected null values found",
        details={"checked_columns": len(columns), "total_rows": df.height},
    )


def check_date_range(
    df: pl.DataFrame,
    date_column: str,
    min_date: int | None = None,
    max_date: int | None = None,
) -> ValidationResult:
    """Check that date/year values are within expected range.

    Args:
        df: DataFrame to check
        date_column: Name of the date/year column
        min_date: Minimum acceptable year (default: None, no minimum)
        max_date: Maximum acceptable year (default: None, no maximum)

    Returns:
        ValidationResult with date range details

    Example:
        >>> df = pl.DataFrame({"year": [2020, 2021, 2022]})
        >>> result = check_date_range(df, "year", min_date=2020, max_date=2023)
        >>> result.passed
        True
    """
    if date_column not in df.columns:
        return ValidationResult(
            passed=False,
            message=f"Date column '{date_column}' not found in DataFrame",
            details=None,
        )

    # Get min and max from data
    actual_min = df[date_column].min()
    actual_max = df[date_column].max()

    issues = []

    if min_date is not None and actual_min < min_date:
        issues.append(f"Minimum date {actual_min} is before allowed minimum {min_date}")

    if max_date is not None and actual_max > max_date:
        issues.append(f"Maximum date {actual_max} is after allowed maximum {max_date}")

    if issues:
        return ValidationResult(
            passed=False,
            message="Date range validation failed",
            details={
                "actual_min": actual_min,
                "actual_max": actual_max,
                "expected_min": min_date,
                "expected_max": max_date,
                "issues": issues,
            },
        )

    return ValidationResult(
        passed=True,
        message="Date range validation passed",
        details={
            "actual_min": actual_min,
            "actual_max": actual_max,
            "expected_min": min_date,
            "expected_max": max_date,
        },
    )


def check_outliers(
    df: pl.DataFrame,
    column: str,
    method: str = "iqr",
    threshold: float = 1.5,
) -> ValidationResult:
    """Check for outliers in a numeric column.

    Args:
        column: Column to check for outliers
        df: DataFrame to check
        method: Outlier detection method. Options:
            - "iqr": Interquartile range method (default)
            - "zscore": Z-score method (not yet implemented)
        threshold: Threshold multiplier for outlier detection
            For IQR: multiplier of IQR (default: 1.5)
            For zscore: number of standard deviations (default: 3.0)

    Returns:
        ValidationResult with outlier details

    Example:
        >>> df = pl.DataFrame({"value": [1, 2, 3, 4, 5, 100]})
        >>> result = check_outliers(df, "value")
        >>> result.passed
        False
        >>> result.details["outlier_count"]
        1
    """
    if column not in df.columns:
        return ValidationResult(
            passed=False,
            message=f"Column '{column}' not found in DataFrame",
            details=None,
        )

    if method == "iqr":
        # Calculate IQR
        q1 = df[column].quantile(0.25)
        q3 = df[column].quantile(0.75)
        iqr = q3 - q1

        # Calculate bounds
        lower_bound = q1 - (threshold * iqr)
        upper_bound = q3 + (threshold * iqr)

        # Find outliers
        outliers = df.filter(
            (pl.col(column) < lower_bound) | (pl.col(column) > upper_bound)
        )

        outlier_count = outliers.height

        if outlier_count > 0:
            return ValidationResult(
                passed=False,
                message=f"Found {outlier_count} outliers using IQR method",
                details={
                    "outlier_count": outlier_count,
                    "total_rows": df.height,
                    "outlier_percentage": (outlier_count / df.height) * 100,
                    "lower_bound": lower_bound,
                    "upper_bound": upper_bound,
                    "q1": q1,
                    "q3": q3,
                    "iqr": iqr,
                },
            )

        return ValidationResult(
            passed=True,
            message="No outliers found using IQR method",
            details={
                "total_rows": df.height,
                "lower_bound": lower_bound,
                "upper_bound": upper_bound,
                "q1": q1,
                "q3": q3,
                "iqr": iqr,
            },
        )

    msg = f"Outlier detection method '{method}' not implemented"
    raise NotImplementedError(msg)


def validate_la_code(code: str) -> bool:
    """Validate a UK Local Authority code.

    LA codes follow the format: E06000001, E07000001, etc. (England)
    or S12000001 (Scotland), W06000001 (Wales), N09000001 (Northern Ireland).

    Args:
        code: Local authority code to validate

    Returns:
        True if code is valid format, False otherwise

    Example:
        >>> validate_la_code("E06000023")  # Bristol
        True
        >>> validate_la_code("invalid")
        False
    """
    # Pattern: Letter + 8 digits
    pattern = r"^[EWSN]\d{8}$"
    return bool(re.match(pattern, code))


def validate_lsoa_code(code: str, year: int = 2021) -> bool:
    """Validate a UK Lower Super Output Area (LSOA) code.

    LSOA codes follow the format: E01000001 (2021) or E01000001 (2011).

    Args:
        code: LSOA code to validate
        year: Census year (2011 or 2021, default: 2021)

    Returns:
        True if code is valid format, False otherwise

    Raises:
        ValueError: If year is not 2011 or 2021

    Example:
        >>> validate_lsoa_code("E01000001")
        True
        >>> validate_lsoa_code("invalid")
        False
    """
    if year not in [2011, 2021]:
        msg = f"Year must be 2011 or 2021, got {year}"
        raise ValueError(msg)

    # Pattern: E01 + 6 digits (England)
    # S01 + 6 digits (Scotland)
    # W01 + 7 digits (Wales)
    # N00 + 6 digits (Northern Ireland - 2021 only)
    pattern = r"^([ESW]01\d{6}|N00\d{6})$"
    return bool(re.match(pattern, code))


def check_geographic_codes(
    df: pl.DataFrame,
    column: str,
    code_type: str,
    year: int | None = None,
) -> ValidationResult:
    """Check that geographic codes in a column are valid.

    Args:
        df: DataFrame to check
        column: Column containing geographic codes
        code_type: Type of code. Options: "la", "lsoa", "msoa"
        year: Census year for LSOA/MSOA codes (2011 or 2021, default: 2021)

    Returns:
        ValidationResult with invalid code details

    Example:
        >>> df = pl.DataFrame({"la_code": ["E06000023", "E06000022", "invalid"]})
        >>> result = check_geographic_codes(df, "la_code", "la")
        >>> result.passed
        False
        >>> result.details["invalid_count"]
        1
    """
    if column not in df.columns:
        return ValidationResult(
            passed=False,
            message=f"Column '{column}' not found in DataFrame",
            details=None,
        )

    if year is None:
        year = 2021

    # Get unique codes
    unique_codes = df[column].unique().to_list()

    # Validate each code
    invalid_codes = []
    for code in unique_codes:
        if code is None:
            continue  # Handle nulls separately with check_nulls()

        is_valid = False
        if code_type == "la":
            is_valid = validate_la_code(str(code))
        elif code_type == "lsoa":
            is_valid = validate_lsoa_code(str(code), year)
        elif code_type == "msoa":
            # MSOA codes similar to LSOA but E02/S02/W02/N00
            pattern = r"^([ESW]02\d{6}|N00\d{6})$"
            is_valid = bool(re.match(pattern, str(code)))
        else:
            msg = f"Unknown code type: {code_type}"
            raise ValueError(msg)

        if not is_valid:
            invalid_codes.append(str(code))

    if invalid_codes:
        # Count how many rows have invalid codes
        invalid_count = df.filter(pl.col(column).is_in(invalid_codes)).height

        return ValidationResult(
            passed=False,
            message=f"Found {len(invalid_codes)} invalid {code_type.upper()} codes",
            details={
                "invalid_codes": invalid_codes[:10],  # Show first 10
                "invalid_count": len(invalid_codes),
                "invalid_rows": invalid_count,
                "total_unique_codes": len(unique_codes),
                "total_rows": df.height,
            },
        )

    return ValidationResult(
        passed=True,
        message=f"All {code_type.upper()} codes are valid",
        details={
            "total_unique_codes": len(unique_codes),
            "total_rows": df.height,
        },
    )


def validate_postcode(postcode: str) -> bool:
    """Validate a UK postcode format.

    Validates against standard UK postcode formats (e.g., BS1 1AA, BS16 7JP).
    Note: This only validates format, not whether the postcode exists.

    Args:
        postcode: Postcode to validate (with or without space)

    Returns:
        True if postcode is valid format, False otherwise

    Example:
        >>> validate_postcode("BS1 1AA")
        True
        >>> validate_postcode("BS11AA")  # Also valid (no space)
        True
        >>> validate_postcode("invalid")
        False
    """
    # Remove spaces for validation
    postcode_clean = postcode.replace(" ", "").upper()

    # UK postcode pattern (comprehensive)
    # Area: 1-2 letters
    # District: 1-2 digits (optional letter suffix)
    # Sector: 1 digit
    # Unit: 2 letters
    pattern = r"^[A-Z]{1,2}\d{1,2}[A-Z]?\d[A-Z]{2}$"
    return bool(re.match(pattern, postcode_clean))


def run_all_validations(
    df: pl.DataFrame,
    validations: list[dict[str, Any]],
) -> dict[str, ValidationResult]:
    """Run multiple validation checks on a DataFrame.

    Args:
        df: DataFrame to validate
        validations: List of validation configurations, each a dict with:
            - "type": Validation type ("schema", "nulls", "date_range", etc.)
            - Additional keys depending on validation type

    Returns:
        Dictionary mapping validation names to ValidationResults

    Example:
        >>> df = pl.DataFrame({"year": [2020, 2021], "emissions": [100.0, 95.0]})
        >>> validations = [
        ...     {"type": "schema", "expected": {"year": int, "emissions": float}},
        ...     {"type": "nulls"},
        ...     {"type": "date_range", "column": "year", "min": 2020, "max": 2025},
        ... ]
        >>> results = run_all_validations(df, validations)
        >>> all(r.passed for r in results.values())
        True
    """
    results = {}

    for i, validation in enumerate(validations):
        val_type = validation.get("type")
        val_name = validation.get("name", f"{val_type}_{i}")

        if val_type == "schema":
            results[val_name] = validate_schema(
                df,
                validation["expected"],
                validation.get("allow_extra_columns", True),
            )
        elif val_type == "nulls":
            results[val_name] = check_nulls(
                df,
                validation.get("columns"),
                validation.get("allow_null_columns"),
            )
        elif val_type == "date_range":
            results[val_name] = check_date_range(
                df,
                validation["column"],
                validation.get("min_date"),
                validation.get("max_date"),
            )
        elif val_type == "outliers":
            results[val_name] = check_outliers(
                df,
                validation["column"],
                validation.get("method", "iqr"),
                validation.get("threshold", 1.5),
            )
        elif val_type == "geographic_codes":
            results[val_name] = check_geographic_codes(
                df,
                validation["column"],
                validation["code_type"],
                validation.get("year"),
            )
        else:
            results[val_name] = ValidationResult(
                passed=False,
                message=f"Unknown validation type: {val_type}",
                details=None,
            )

    return results
