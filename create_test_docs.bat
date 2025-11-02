@echo off
REM Create test legal documents

echo Creating test documents...

set TEST_DIR=%USERPROFILE%\Documents\LegalDocs
mkdir "%TEST_DIR%" 2>nul

echo Creating sample contract...
(
echo Sample Legal Contract
echo.
echo This is a test contract for OnMyPC Legal AI.
echo.
echo TERMS AND CONDITIONS
echo.
echo 1. PARTIES
echo This Agreement is entered between Party A and Party B.
echo.
echo 2. NON-COMPETE CLAUSE
echo The Employee agrees not to engage in any business that competes
echo with the Company for a period of 2 years after termination.
echo.
echo 3. CONFIDENTIALITY
echo All proprietary information must be kept confidential.
echo.
echo 4. ARBITRATION
echo Any disputes shall be resolved through binding arbitration
echo in accordance with the rules of the American Arbitration Association.
echo.
echo 5. TERMINATION
echo This agreement may be terminated with 30 days written notice.
echo.
echo 6. LIABILITY
echo The Company's liability is limited to the amount paid under this contract.
) > "%TEST_DIR%\sample_contract.txt"

echo Creating sample NDA...
(
echo Non-Disclosure Agreement
echo.
echo MUTUAL NDA between Company X and Company Y
echo.
echo WHEREAS, both parties wish to explore a business relationship
echo and need to exchange confidential information.
echo.
echo 1. DEFINITION OF CONFIDENTIAL INFORMATION
echo Confidential Information includes all technical, business, and
echo financial information disclosed by either party.
echo.
echo 2. OBLIGATIONS
echo The receiving party agrees to:
echo - Keep all information confidential
echo - Use information only for evaluation purposes
echo - Not disclose to third parties
echo.
echo 3. TERM
echo This agreement is effective for 3 years from the date of signing.
echo.
echo 4. RETURN OF MATERIALS
echo Upon termination, all confidential materials must be returned.
) > "%TEST_DIR%\nda_template.txt"

echo Creating sample policy...
(
echo Employee Handbook - Legal Policies
echo.
echo COMPANY POLICIES AND PROCEDURES
echo.
echo 1. EQUAL OPPORTUNITY EMPLOYMENT
echo Our company is an equal opportunity employer and does not
echo discriminate based on race, color, religion, sex, or national origin.
echo.
echo 2. HARASSMENT POLICY
echo We maintain a zero-tolerance policy for harassment of any kind.
echo All complaints will be investigated promptly.
echo.
echo 3. INTELLECTUAL PROPERTY
echo All work product created by employees belongs to the Company.
echo.
echo 4. DATA PROTECTION
echo Employees must comply with GDPR and other data protection regulations.
echo.
echo 5. DISPUTE RESOLUTION
echo Internal disputes should be reported to HR and will be handled
echo through our internal grievance procedure.
) > "%TEST_DIR%\employee_policy.txt"

echo.
echo ✓ Created 3 test documents in: %TEST_DIR%
echo.
echo Documents created:
echo   - sample_contract.txt
echo   - nda_template.txt
echo   - employee_policy.txt
echo.
echo Now run the app and select this folder!
pause
