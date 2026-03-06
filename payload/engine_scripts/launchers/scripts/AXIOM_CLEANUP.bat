@echo off
REM AXIOM CLEANUP SCRIPT
REM Run this AFTER closing Obsidian to remove redundant axiom folders
REM All content has been verified as duplicate or already in 00_AXIOMS

echo ========================================
echo AXIOM CLEANUP SCRIPT
echo ========================================
echo.
echo This will move redundant axiom folders to .trash
echo Press Ctrl+C to cancel, or
pause

echo.
echo Moving redundant folders to .trash...
echo.

REM Main redundant folders
echo [1/8] Moving AXIOM CHAPTERS (unique chapters already copied)...
if exist "O:\_Theophysics_v3\AXIOM CHAPTERS" (
    move /Y "O:\_Theophysics_v3\AXIOM CHAPTERS" "O:\_Theophysics_v3\.trash\AXIOM_CHAPTERS_REDUNDANT"
    echo     DONE
) else (
    echo     Already moved or deleted
)

echo [2/8] Moving GO FOLDER\_AXIOMS_001-188 (all axioms already in 00_AXIOMS)...
if exist "O:\_Theophysics_v3\GO FOLDER\_AXIOMS_001-188" (
    move /Y "O:\_Theophysics_v3\GO FOLDER\_AXIOMS_001-188" "O:\_Theophysics_v3\.trash\_AXIOMS_001-188_REDUNDANT"
    echo     DONE
) else (
    echo     Already moved or deleted
)

echo [3/8] Moving THE Axioms Vault (3.7M duplicate vault)...
if exist "O:\_Theophysics_v3\THE Axioms Vault" (
    move /Y "O:\_Theophysics_v3\THE Axioms Vault" "O:\_Theophysics_v3\.trash\THE_Axioms_Vault_REDUNDANT"
    echo     DONE
) else (
    echo     Already moved or deleted
)

echo [4/8] Moving 00_Canonical\01_AXIOMS (50M old format duplicates)...
if exist "O:\_Theophysics_v3\00_Canonical\01_AXIOMS" (
    move /Y "O:\_Theophysics_v3\00_Canonical\01_AXIOMS" "O:\_Theophysics_v3\.trash\01_AXIOMS_CANONICAL_REDUNDANT"
    echo     DONE
) else (
    echo     Already moved or deleted
)

echo [5/8] Moving 00_Canonical\_AXIOM_ARCHIVE_SUBFOLDERS...
if exist "O:\_Theophysics_v3\00_Canonical\_AXIOM_ARCHIVE_SUBFOLDERS" (
    move /Y "O:\_Theophysics_v3\00_Canonical\_AXIOM_ARCHIVE_SUBFOLDERS" "O:\_Theophysics_v3\.trash\_AXIOM_ARCHIVE_SUBFOLDERS_REDUNDANT"
    echo     DONE
) else (
    echo     Already moved or deleted
)

echo [6/8] Moving 00_Canonical\_ARCHIVE\Opus\Axioms...
if exist "O:\_Theophysics_v3\00_Canonical\_ARCHIVE\Opus\Axioms" (
    move /Y "O:\_Theophysics_v3\00_Canonical\_ARCHIVE\Opus\Axioms" "O:\_Theophysics_v3\.trash\Opus_Axioms_REDUNDANT"
    echo     DONE
) else (
    echo     Already moved or deleted
)

echo [7/8] Moving 00_Canonical\_ARCHIVE\SOCRATIC_AXIOMS...
if exist "O:\_Theophysics_v3\00_Canonical\_ARCHIVE\SOCRATIC_AXIOMS" (
    move /Y "O:\_Theophysics_v3\00_Canonical\_ARCHIVE\SOCRATIC_AXIOMS" "O:\_Theophysics_v3\.trash\SOCRATIC_AXIOMS_REDUNDANT"
    echo     DONE
) else (
    echo     Already moved or deleted
)

echo [8/11] Moving GO FOLDER\LOVE_AXIOMS...
if exist "O:\_Theophysics_v3\GO FOLDER\LOVE_AXIOMS" (
    move /Y "O:\_Theophysics_v3\GO FOLDER\LOVE_AXIOMS" "O:\_Theophysics_v3\.trash\LOVE_AXIOMS_REDUNDANT"
    echo     DONE
) else (
    echo     Already moved or deleted
)

echo [9/11] Moving 00_Canonical\00_PRIMORDIAL (PRIMORDIAL axioms already in 00_AXIOMS)...
if exist "O:\_Theophysics_v3\00_Canonical\00_PRIMORDIAL" (
    move /Y "O:\_Theophysics_v3\00_Canonical\00_PRIMORDIAL" "O:\_Theophysics_v3\.trash\00_PRIMORDIAL_REDUNDANT"
    echo     DONE
) else (
    echo     Already moved or deleted
)

echo [10/11] Deleting GO FOLDER axiom master files (corrupted/redundant)...
if exist "O:\_Theophysics_v3\GO FOLDER\_AXIOMS_MASTER_LIST.md" del /F "O:\_Theophysics_v3\GO FOLDER\_AXIOMS_MASTER_LIST.md"
if exist "O:\_Theophysics_v3\GO FOLDER\LOVE_AXIOMS_MASTER.md" del /F "O:\_Theophysics_v3\GO FOLDER\LOVE_AXIOMS_MASTER.md"
if exist "O:\_Theophysics_v3\GO FOLDER\STRUCTURAL_AXIOMS.md" del /F "O:\_Theophysics_v3\GO FOLDER\STRUCTURAL_AXIOMS.md"
echo     DONE

echo [11/11] Moving 00_Canonical\09_REFERENCES\Core_Knowledge\Axioms...
if exist "O:\_Theophysics_v3\00_Canonical\09_REFERENCES\Core_Knowledge\Axioms" (
    move /Y "O:\_Theophysics_v3\00_Canonical\09_REFERENCES\Core_Knowledge\Axioms" "O:\_Theophysics_v3\.trash\Core_Knowledge_Axioms_REDUNDANT"
    echo     DONE
) else (
    echo     Already moved or deleted
)

echo.
echo ========================================
echo CLEANUP COMPLETE!
echo ========================================
echo.
echo All redundant axiom folders moved to .trash
echo You can permanently delete .trash folder later if desired
echo.
pause
