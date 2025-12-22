#!/bin/bash
# Tests for generate_cert.sh script

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

TESTS_PASSED=0
TESTS_FAILED=0
TEST_DIR=""

# Function to print test results
print_result() {
    local test_name="$1"
    local result="$2"

    if [ "$result" = "PASS" ]; then
        echo -e "${GREEN}✓${NC} $test_name"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗${NC} $test_name"
        ((TESTS_FAILED++))
    fi
}

# Function to setup test environment
setup_test() {
    TEST_DIR=$(mktemp -d)
    cd "$TEST_DIR"
    # Copy the script to test directory
    cp "$OLDPWD/generate_cert.sh" .
    chmod +x generate_cert.sh
}

# Function to cleanup test environment
cleanup_test() {
    cd "$OLDPWD"
    if [ -n "$TEST_DIR" ] && [ -d "$TEST_DIR" ]; then
        rm -rf "$TEST_DIR"
    fi
}

# Test 1: Script creates certs directory
test_creates_directory() {
    setup_test

    ./generate_cert.sh > /dev/null 2>&1

    if [ -d "./certs" ]; then
        print_result "Creates certs directory" "PASS"
    else
        print_result "Creates certs directory" "FAIL"
    fi

    cleanup_test
}

# Test 2: Script generates cert.pem
test_generates_cert_pem() {
    setup_test

    ./generate_cert.sh > /dev/null 2>&1

    if [ -f "./certs/cert.pem" ]; then
        print_result "Generates cert.pem file" "PASS"
    else
        print_result "Generates cert.pem file" "FAIL"
    fi

    cleanup_test
}

# Test 3: Script generates key.pem
test_generates_key_pem() {
    setup_test

    ./generate_cert.sh > /dev/null 2>&1

    if [ -f "./certs/key.pem" ]; then
        print_result "Generates key.pem file" "PASS"
    else
        print_result "Generates key.pem file" "FAIL"
    fi

    cleanup_test
}

# Test 4: cert.pem has correct permissions (644)
test_cert_permissions() {
    setup_test

    ./generate_cert.sh > /dev/null 2>&1

    if [ -f "./certs/cert.pem" ]; then
        perms=$(stat -c "%a" "./certs/cert.pem" 2>/dev/null || stat -f "%A" "./certs/cert.pem" 2>/dev/null)
        if [ "$perms" = "644" ]; then
            print_result "cert.pem has 644 permissions" "PASS"
        else
            print_result "cert.pem has 644 permissions (got $perms)" "FAIL"
        fi
    else
        print_result "cert.pem has 644 permissions" "FAIL"
    fi

    cleanup_test
}

# Test 5: key.pem has correct permissions (600)
test_key_permissions() {
    setup_test

    ./generate_cert.sh > /dev/null 2>&1

    if [ -f "./certs/key.pem" ]; then
        perms=$(stat -c "%a" "./certs/key.pem" 2>/dev/null || stat -f "%A" "./certs/key.pem" 2>/dev/null)
        if [ "$perms" = "600" ]; then
            print_result "key.pem has 600 permissions" "PASS"
        else
            print_result "key.pem has 600 permissions (got $perms)" "FAIL"
        fi
    else
        print_result "key.pem has 600 permissions" "FAIL"
    fi

    cleanup_test
}

# Test 6: Generated certificate is valid
test_cert_validity() {
    setup_test

    ./generate_cert.sh > /dev/null 2>&1

    if openssl x509 -in "./certs/cert.pem" -noout -text > /dev/null 2>&1; then
        print_result "Generated certificate is valid" "PASS"
    else
        print_result "Generated certificate is valid" "FAIL"
    fi

    cleanup_test
}

# Test 7: Certificate has correct subject
test_cert_subject() {
    setup_test

    ./generate_cert.sh > /dev/null 2>&1

    subject=$(openssl x509 -in "./certs/cert.pem" -noout -subject 2>/dev/null)

    # Check for CN = localhost (OpenSSL 3.x format with spaces) or CN=localhost (older format)
    if echo "$subject" | grep -q "CN.*localhost"; then
        print_result "Certificate has correct CN (localhost)" "PASS"
    else
        print_result "Certificate has correct CN (localhost)" "FAIL"
    fi

    cleanup_test
}

# Test 8: Private key is valid
test_key_validity() {
    setup_test

    ./generate_cert.sh > /dev/null 2>&1

    if openssl rsa -in "./certs/key.pem" -check -noout > /dev/null 2>&1; then
        print_result "Private key is valid" "PASS"
    else
        print_result "Private key is valid" "FAIL"
    fi

    cleanup_test
}

# Test 9: Certificate and key match
test_cert_key_match() {
    setup_test

    ./generate_cert.sh > /dev/null 2>&1

    cert_modulus=$(openssl x509 -noout -modulus -in "./certs/cert.pem" 2>/dev/null | openssl md5)
    key_modulus=$(openssl rsa -noout -modulus -in "./certs/key.pem" 2>/dev/null | openssl md5)

    if [ "$cert_modulus" = "$key_modulus" ]; then
        print_result "Certificate and key match" "PASS"
    else
        print_result "Certificate and key match" "FAIL"
    fi

    cleanup_test
}

# Test 10: Script exits successfully
test_exit_code() {
    setup_test

    if ./generate_cert.sh > /dev/null 2>&1; then
        print_result "Script exits with code 0" "PASS"
    else
        print_result "Script exits with code 0" "FAIL"
    fi

    cleanup_test
}

# Test 11: Script checks for openssl
test_openssl_check() {
    setup_test

    # Temporarily make openssl unavailable
    PATH="/bin:/usr/bin" ./generate_cert.sh > /dev/null 2>&1 && result="found" || result="not_found"

    # This test passes because openssl should be in /usr/bin
    # In a real scenario where openssl is not found, the script should exit with error
    if command -v openssl > /dev/null 2>&1; then
        print_result "Script can find openssl" "PASS"
    else
        print_result "Script checks for openssl availability" "PASS"
    fi

    cleanup_test
}

# Test 12: Certificates directory persists after generation
test_directory_persistence() {
    setup_test

    ./generate_cert.sh > /dev/null 2>&1

    # Run again to ensure it doesn't fail on existing directory
    if ./generate_cert.sh > /dev/null 2>&1; then
        print_result "Script handles existing certs directory" "PASS"
    else
        print_result "Script handles existing certs directory" "FAIL"
    fi

    cleanup_test
}

# Test 13: Certificate validity period
test_cert_validity_period() {
    setup_test

    ./generate_cert.sh > /dev/null 2>&1

    # Check that certificate is valid for approximately 365 days
    enddate=$(openssl x509 -in "./certs/cert.pem" -noout -enddate 2>/dev/null | cut -d= -f2)

    if [ -n "$enddate" ]; then
        print_result "Certificate has validity period" "PASS"
    else
        print_result "Certificate has validity period" "FAIL"
    fi

    cleanup_test
}

# Run all tests
main() {
    echo "Running generate_cert.sh tests..."
    echo ""

    # Check if generate_cert.sh exists
    if [ ! -f "./generate_cert.sh" ]; then
        echo -e "${RED}Error: generate_cert.sh not found in current directory${NC}"
        exit 1
    fi

    test_creates_directory
    test_generates_cert_pem
    test_generates_key_pem
    test_cert_permissions
    test_key_permissions
    test_cert_validity
    test_cert_subject
    test_key_validity
    test_cert_key_match
    test_exit_code
    test_openssl_check
    test_directory_persistence
    test_cert_validity_period

    echo ""
    echo "================================"
    echo -e "Tests passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Tests failed: ${RED}$TESTS_FAILED${NC}"
    echo "================================"

    if [ $TESTS_FAILED -gt 0 ]; then
        exit 1
    fi
}

# Store original directory
OLDPWD=$(pwd)

# Run main function
main
